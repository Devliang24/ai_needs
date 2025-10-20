"""Workflow orchestration bridging sessions, Redis events, and LLM agents."""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import session_events
from app.db import session_repository
from app.db.base import AsyncSessionLocal
from app.llm.autogen_runner import AutogenOutputs, run_analysis
from app.llm.vision_client_enhanced import extract_requirements_with_retry, is_vl_available
from app.models.document import Document
from app.models.session import AgentStage, SessionStatus
from app.parsers.text_extractor import extract_text
from app.config import settings
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no cover - fallback when PyMuPDF missing
    fitz = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
except Exception:  # pragma: no cover - fallback when Pillow missing
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore


@dataclass
class StageResult:
    stage: AgentStage
    sender: str
    content: str
    payload: dict
    progress: float


class AnalysisWorkflow:
    """Orchestrate asynchronous analysis workflow with AutoGen or simulation."""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    async def launch(self, session_id: str) -> None:
        task = asyncio.create_task(self._run(session_id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(self, session_id: str) -> None:
        logger.info("Starting workflow for session %s", session_id)
        async with AsyncSessionLocal() as db_session:
            executor = SessionWorkflowExecution(db_session=db_session, session_id=session_id)
            try:
                await executor.execute()
            except Exception as exc:  # pragma: no cover - unexpected runtime failures
                logger.exception("Workflow failed for session %s: %s", session_id, exc)


class SessionWorkflowExecution:
    def __init__(self, db_session: AsyncSession, session_id: str) -> None:
        self.db_session = db_session
        self.session_id = session_id
        self._stage_labels = {
            AgentStage.layout_analysis: "版面分析",
            AgentStage.requirement_analysis: "需求分析",
            AgentStage.confirmation: "确认",
            AgentStage.test_generation: "用例生成",
            AgentStage.review: "质量评审",
            AgentStage.test_completion: "用例补全",
            AgentStage.completed: "完成",
        }
        self._vl_config = settings.get_vl_config()

    def _get_document_suffix(self, document: Document) -> str:
        if document.original_name:
            suffix = Path(document.original_name).suffix.lower()
            if suffix:
                return suffix
        return Path(document.storage_path).suffix.lower()

    def _text_to_image(self, text: str) -> Path | None:
        if not text.strip():
            return None
        if Image is None or ImageDraw is None or ImageFont is None:  # pragma: no cover - optional dependency
            return None

        try:
            wrapped_lines = []
            for paragraph in text.splitlines():
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                wrapped_lines.extend(textwrap.wrap(paragraph, width=48) or [paragraph])
                if len(wrapped_lines) >= 120:
                    break
            if not wrapped_lines:
                wrapped_lines = ["未识别到文本内容"]

            font = ImageFont.load_default()
            try:
                base_bbox = font.getbbox("A")
                base_height = base_bbox[3]
            except AttributeError:  # pragma: no cover - compatibility fallback
                base_height = font.getsize("A")[1]
            line_height = base_height + 6

            def _measure_width(text_line: str) -> int:
                try:
                    bbox = font.getbbox(text_line)
                    return bbox[2]
                except AttributeError:  # pragma: no cover - compatibility fallback
                    return font.getsize(text_line)[0]

            image_width = max(_measure_width(line) for line in wrapped_lines) + 40
            image_height = line_height * len(wrapped_lines) + 40
            image = Image.new("RGB", (image_width, image_height), color="white")
            draw = ImageDraw.Draw(image)
            y = 20
            for line in wrapped_lines:
                draw.text((20, y), line, fill="black", font=font)
                y += line_height

            tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            image.save(tmp_file.name)
            tmp_file.close()
            return Path(tmp_file.name)
        except Exception:  # pragma: no cover - best effort
            return None

    def _prepare_document_image(self, document: Document, extracted_text: str) -> tuple[Path | None, Path | None]:
        suffix = self._get_document_suffix(document)
        # Directly use original file if it is an image
        if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
            return Path(document.storage_path), None

        # Convert first page of PDF to image when PyMuPDF is available
        if suffix == ".pdf" and fitz is not None:
            try:
                with fitz.open(document.storage_path) as pdf_doc:  # type: ignore[arg-type]
                    if pdf_doc.page_count == 0:
                        return None, None
                    page = pdf_doc.load_page(0)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    pix.save(tmp_file.name)
                    tmp_file.close()
                    return Path(tmp_file.name), Path(tmp_file.name)
            except Exception:
                logger.warning("无法将 PDF 转换为图片，改用文本内容", exc_info=True)

        # Fallback: render extracted text to image when possible
        rendered = self._text_to_image(extracted_text[:4000])
        if rendered is not None:
            return rendered, rendered

        return None, None

    def _cleanup_temp_path(self, path: Path | None) -> None:
        if path is None:
            return
        try:
            path.unlink()
        except FileNotFoundError:
            return
        except Exception:  # pragma: no cover - ignore cleanup issues
            logger.debug("临时文件清理失败: %s", path, exc_info=True)

    async def _generate_layout_entry(self, document: Document, extracted_text: str) -> dict:
        normalized_text = (extracted_text or "").strip()
        preview_source = "text_extractor"
        preview_text = normalized_text

        if self._vl_config.get("enabled") and self._vl_config.get("api_key") and is_vl_available():
            image_path, temp_path = self._prepare_document_image(document, normalized_text)
            if image_path is not None:
                try:
                    vl_text = await extract_requirements_with_retry(
                        image_path,
                        api_key=self._vl_config.get("api_key"),
                        model=self._vl_config.get("model"),
                        base_url=self._vl_config.get("base_url"),
                        use_cache=True,
                    )
                    if vl_text and vl_text.strip():
                        preview_text = vl_text.strip()
                        preview_source = "vl_model"
                except Exception:
                    logger.warning(
                        "VL 版面分析失败，使用文本提取内容。",
                        exc_info=True,
                    )
                finally:
                    self._cleanup_temp_path(temp_path)
        else:
            # 确保文本提取至少返回占位符
            if not preview_text:
                preview_text = "未识别到文本内容"

        limited_preview = preview_text.strip()[:2000] if preview_text else "未识别到文本内容"
        lines = [line for line in limited_preview.splitlines() if line.strip()]

        return {
            "document_id": document.id,
            "name": document.original_name or document.id,
            "char_count": len(limited_preview),
            "line_count": len(lines),
            "preview": limited_preview if limited_preview else "未识别到文本内容",
            "source": preview_source,
        }

    async def execute(self) -> None:
        # Refresh VL 配置，确保每次执行都使用最新设置
        self._vl_config = settings.get_vl_config()

        session = await session_repository.get_session(self.db_session, self.session_id)
        if session is None:
            logger.warning("Session %s not found", self.session_id)
            return

        await session_repository.update_session_status(
            self.db_session,
            session_id=self.session_id,
            from_status=session.status,
            to_status=SessionStatus.processing,
            stage=AgentStage.layout_analysis,
            progress=0.05,
        )
        await self.db_session.commit()

        await self._emit_system_message("分析流程已开始，准备解析文档。", progress=0.05)

        document_texts: list[tuple[Document, str]] = []
        for document in session.documents:
            try:
                text = extract_text(
                    document.storage_path,
                    original_name=document.original_name,
                )
            except Exception as exc:  # pragma: no cover - best effort extraction
                logger.warning(
                    "提取文档内容失败: session=%s document=%s error=%s",
                    self.session_id,
                    document.id,
                    exc,
                )
                text = ""
            document_texts.append((document, text or ""))

        layout_entries: list[dict] = []
        for document, text in document_texts:
            entry = await self._generate_layout_entry(document, text)
            layout_entries.append(entry)

        layout_markdown_lines: list[str] = ["以下为版面结构预览，请确认文档识别是否准确："]
        for idx, entry in enumerate(layout_entries, start=1):
            layout_markdown_lines.append("")
            layout_markdown_lines.append(f"### 文档 {idx}: {entry['name']}")
            layout_markdown_lines.append(f"- 字符数：{entry['char_count']}")
            layout_markdown_lines.append(f"- 有效段落数：{entry['line_count']}")
            source_label = "VL 模型" if entry.get("source") == "vl_model" else "文本提取"
            layout_markdown_lines.append(f"- 识别来源：{source_label}")
            if entry.get("preview"):
                layout_markdown_lines.append("")
                quoted_preview = str(entry["preview"]).replace("\n", "\n> ")
                layout_markdown_lines.append(f"> {quoted_preview}")

        layout_content = "\n".join(layout_markdown_lines).strip() or "未识别到文本内容。"

        layout_result = StageResult(
            stage=AgentStage.layout_analysis,
            sender="版面分析器",
            content=layout_content,
            payload={"documents": layout_entries},
            progress=0.12,
        )
        await self._handle_stage_result(
            layout_result,
            skip_confirmation=False,
            needs_confirmation=True,
        )

        documents_text = "\n\n".join(text for _doc, text in document_texts if text)
        if not documents_text:
            documents_text = "\n\n".join(
                str(entry.get("preview", "")) for entry in layout_entries if entry.get("preview")
            )

        logger.info("开始调用 AutoGen 进行分析...")
        try:
            outputs = await asyncio.to_thread(run_analysis, documents_text)
            (
                stage_results,
                summary,
                merged_test_cases,
                metrics,
            ) = self._from_autogen(outputs)
        except Exception as exc:
            # 当 LLM 出错时，优雅降级：
            # 1) 先把已提取的文档文本（或其节选）作为“需求分析师”的结果发给前端，
            # 2) 不进入确认等待，
            # 3) 通知系统消息并结束流程，避免前端空白。
            logger.exception("AutoGen 执行失败，使用文本提取结果作为回退: %s", exc)

            # 无论是否提取到文本，都推送一条“需求分析师”阶段的回退事件，避免前端空白
            preview = (documents_text or "").strip()
            if preview:
                snippet = preview[:1500]
                content = (
                    "未能完成智能体深度分析，已回退为图片/文档文本提取结果预览：\n\n" + snippet
                )
            else:
                # 构造友好的占位提示，包含文件名与后续建议
                file_names = ", ".join(
                    (doc.original_name or "未命名文件") for doc in session.documents
                )
                content = (
                    "未能完成智能体深度分析，且未从图片中提取到可读文本。\n\n"
                    f"文件：{file_names}\n\n"
                    "建议：\n"
                    "- 确认已配置并启用图像识别（VL）能力；\n"
                    "- 或上传包含文字的 PDF/Docx 文档；\n"
                    "- 也可稍后使用‘重新分析’重试。"
                )

            fallback = StageResult(
                stage=AgentStage.requirement_analysis,
                sender="需求分析师",
                content=content,
                payload={},
                progress=0.3,
            )
            await self._handle_stage_result(
                fallback, skip_confirmation=True, needs_confirmation=False
            )

            await self._emit_system_message(
                f"分析流程失败：{exc}",
                progress=0.95,
            )
            await session_repository.update_session_status(
                self.db_session,
                session_id=self.session_id,
                from_status=None,
                to_status=SessionStatus.completed,
                stage=AgentStage.completed,
                progress=1.0,
            )
            await self.db_session.commit()
            return

        # 为避免前端在收到“完成”阶段事件后立刻导出而数据库结果尚未写入，
        # 先发送非“完成”阶段事件，然后持久化结果，最后再发送“完成”阶段事件。
        non_completed = [r for r in stage_results if r.stage != AgentStage.completed]
        completed_result = next((r for r in stage_results if r.stage == AgentStage.completed), None)

        for result in non_completed:
            await self._handle_stage_result(result, skip_confirmation=False, needs_confirmation=True)

        # 先保存最终结果，确保导出接口可立即读取
        await session_repository.add_session_result(
            self.db_session,
            session_id=self.session_id,
            summary=summary,
            payload=merged_test_cases,
            metrics=metrics,
            stage=AgentStage.completed,
            progress=1.0,
        )
        await self.db_session.commit()

        # 再发送“完成”阶段事件
        if completed_result is not None:
            await self._handle_stage_result(completed_result)
            

        await session_repository.update_session_status(
            self.db_session,
            session_id=self.session_id,
            from_status=None,
            to_status=SessionStatus.completed,
            stage=AgentStage.completed,
            progress=1.0,
        )
        await self.db_session.commit()

        await self._emit_system_message(
            "分析流程完成，结果已生成，可在前端导出 XMind / Excel。",
            progress=1.0,
            status_value=SessionStatus.completed,
        )

    def _from_autogen(self, outputs: AutogenOutputs):
        def _count_cases(data: dict) -> int:
            if not isinstance(data, dict):
                return 0
            total = 0
            for module in data.get("modules", []) or []:
                if not isinstance(module, dict):
                    continue
                cases = module.get("cases")
                if isinstance(cases, list):
                    total += sum(1 for case in cases if isinstance(case, dict))
            return total

        base_case_count = _count_cases(outputs.base_test_cases)
        completion_case_count = _count_cases(outputs.completion_cases)
        merged_case_count = _count_cases(outputs.merged_test_cases)

        stage_results = [
            StageResult(
                stage=AgentStage.requirement_analysis,
                sender="需求分析师",
                content=outputs.analysis_message,
                payload=outputs.summary,
                progress=0.3,
            ),
            StageResult(
                stage=AgentStage.test_generation,
                sender="测试工程师",
                content=outputs.test_message or f"生成测试用例共 {base_case_count} 条",
                payload=outputs.base_test_cases,
                progress=0.6,
            ),
            StageResult(
                stage=AgentStage.review,
                sender="质量评审员",
                content=outputs.review_message,
                payload=outputs.metrics,
                progress=0.8,
            ),
            StageResult(
                stage=AgentStage.test_completion,
                sender="测试补全工程师",
                content=outputs.completion_message or f"补充测试用例 {completion_case_count} 条",
                payload=outputs.completion_cases,
                progress=0.9,
            ),
            StageResult(
                stage=AgentStage.completed,
                sender="测试工程师",
                content=f"合并后测试用例共 {merged_case_count} 条",
                payload=outputs.merged_test_cases,
                progress=0.95,
            ),
        ]
        return (
            stage_results,
            outputs.summary,
            outputs.merged_test_cases,
            outputs.metrics,
        )

    async def _handle_stage_result(self, result: StageResult, *, skip_confirmation: bool = True, needs_confirmation: bool = False) -> None:
        await session_repository.update_session_status(
            self.db_session,
            session_id=self.session_id,
            from_status=None,
            to_status=SessionStatus.processing,
            stage=result.stage,
            progress=result.progress,
        )
        await self.db_session.commit()

        event = {
            "type": "agent_message",
            "sender": result.sender,
            "stage": result.stage.value,
            "content": result.content,
            "payload": result.payload,
            "progress": result.progress,
            "needs_confirmation": bool(needs_confirmation),  # 标记需要确认
            "timestamp": time.time(),
        }
        await session_events.append_event(self.session_id, event)
        await session_events.set_status(
            self.session_id,
            {
                "stage": result.stage.value,
                "progress": result.progress,
                "status": (
                    SessionStatus.awaiting_confirmation.value
                    if needs_confirmation and not skip_confirmation
                    else SessionStatus.processing.value
                ),
            },
        )
        await manager.broadcast(self.session_id, event)

        # 等待用户确认（可跳过）
        if not skip_confirmation and needs_confirmation:
            confirmed = await self._wait_for_confirmation(result.stage)
            if not confirmed:
                # 用户拒绝或超时，抛出异常终止流程
                raise RuntimeError(f"阶段 {result.stage.value} 确认失败或超时")

    async def _wait_for_confirmation(self, stage: AgentStage, timeout: int = 300) -> bool:
        """等待用户确认当前阶段的结果.

        Returns:
            bool: True if confirmed, False if timeout or rejected
        """
        logger.info(f"等待用户确认 stage={stage.value}, session={self.session_id}")

        # 清除之前的确认数据
        await session_events.clear_confirmation(self.session_id)

        # 轮询等待确认 (每秒检查一次,最多等待timeout秒)
        for _ in range(timeout):
            await asyncio.sleep(1)

            confirmation = await session_events.get_confirmation(self.session_id)
            if confirmation and confirmation.get("stage") == stage.value:
                if confirmation.get("confirmed"):
                    logger.info(f"收到用户确认: stage={stage.value}, session={self.session_id}")

                    # 如果用户编辑了数据,更新payload
                    if "payload" in confirmation and confirmation["payload"]:
                        # 这里可以根据需要更新result的payload
                        logger.info(f"用户更新了payload数据")

                    # 清除确认数据
                    await session_events.clear_confirmation(self.session_id)

                    # 发送系统消息
                    if stage != AgentStage.test_completion:
                        stage_label = self._stage_labels.get(stage, stage.value)
                        await self._emit_system_message(
                            f"{stage_label}阶段已确认，继续执行",
                            progress=0.0,  # 进度在下个阶段更新
                        )

                    return True
                elif confirmation.get("rejected"):
                    logger.info(f"用户拒绝确认: stage={stage.value}, session={self.session_id}")
                    await session_events.clear_confirmation(self.session_id)
                    return False

        # 超时未确认,标记失败
        logger.warning(f"等待确认超时: stage={stage.value}, session={self.session_id}")
        await self._emit_system_message(
            f"等待确认超时，流程已终止",
            progress=0.0,
        )
        await session_repository.update_session_status(
            self.db_session,
            session_id=self.session_id,
            from_status=None,
            to_status=SessionStatus.failed,
            stage=stage,
            progress=0.0,
        )
        await self.db_session.commit()
        return False

    async def _emit_system_message(
        self,
        message: str,
        *,
        progress: float,
        status_value: SessionStatus | None = None,
    ) -> None:
        event = {
            "type": "system_message",
            "sender": "系统",
            "stage": "system",
            "content": message,
            "progress": progress,
            "timestamp": time.time(),
        }
        await session_events.append_event(self.session_id, event)
        await session_events.set_status(
            self.session_id,
            {
                "stage": event["stage"],
                "progress": progress,
                "status": (status_value or SessionStatus.processing).value,
            },
        )
        await manager.broadcast(self.session_id, event)


workflow = AnalysisWorkflow()
