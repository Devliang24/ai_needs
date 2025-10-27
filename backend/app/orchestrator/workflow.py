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
from app.llm.autogen_runner import (
    AutogenOutputs,
    run_analysis,
    run_requirement_analysis,
    run_test_generation,
    run_quality_review,
    run_test_completion,
)
from app.llm.vision_client_enhanced import extract_requirements_with_retry, is_vl_available
from app.models.document import Document
from app.models.session import AgentStage, SessionStatus
from app.parsers.text_extractor import extract_text
from app.config import settings
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

import re

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
    duration_seconds: float | None = None


def _parse_markdown_test_cases(markdown_text: str) -> dict:
    """解析Markdown格式的测试用例为JSON结构.

    Args:
        markdown_text: Markdown格式的测试用例文本

    Returns:
        dict: {"modules": [{"name": "模块名", "cases": [...]}]} 格式
    """
    if not markdown_text or not isinstance(markdown_text, str):
        logger.warning("Markdown文本为空或无效")
        return {"modules": []}

    modules = []

    # 按## 分割模块
    module_sections = re.split(r'\n##\s+', markdown_text)

    for section in module_sections:
        if not section.strip():
            continue

        lines = section.strip().split('\n')
        if not lines:
            continue

        # 第一行是模块名
        module_name = lines[0].strip().lstrip('#').strip()
        if not module_name:
            continue

        # 查找表格
        table_start_idx = -1
        for i, line in enumerate(lines):
            # 查找表格头（包含 | 用例ID | 或类似的标记）
            if '|' in line and ('用例' in line or 'ID' in line or '标题' in line):
                table_start_idx = i
                break

        if table_start_idx == -1:
            logger.warning(f"模块 '{module_name}' 未找到测试用例表格")
            continue

        # 跳过表头和分隔线
        data_start_idx = table_start_idx + 2
        if data_start_idx >= len(lines):
            continue

        cases = []
        case_id_counter = 1

        for line in lines[data_start_idx:]:
            line = line.strip()

            # 如果遇到新的标题或空行，停止解析当前表格
            if not line or line.startswith('#') or not line.startswith('|'):
                break

            # 解析表格行
            cells = [cell.strip() for cell in line.split('|')]
            # 去除首尾的空元素
            cells = [c for c in cells if c]

            if len(cells) < 2:
                continue

            # 提取字段（灵活处理不同列数）
            case_id = cells[0] if len(cells) > 0 else f"TC-{module_name}-{case_id_counter:02d}"
            title = cells[1] if len(cells) > 1 else "未命名测试用例"
            preconditions = cells[2] if len(cells) > 2 else None
            steps = cells[3] if len(cells) > 3 else None
            expected = cells[4] if len(cells) > 4 else None
            priority = cells[5] if len(cells) > 5 else None

            # 清理和格式化
            def clean_field(text):
                if not text or text == '-':
                    return None
                # 处理<br>标签
                text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
                return text.strip()

            case = {
                "id": clean_field(case_id) or f"TC-{module_name}-{case_id_counter:02d}",
                "title": clean_field(title) or "未命名测试用例",
            }

            preconditions_clean = clean_field(preconditions)
            if preconditions_clean:
                case["preconditions"] = preconditions_clean

            steps_clean = clean_field(steps)
            if steps_clean:
                case["steps"] = steps_clean

            expected_clean = clean_field(expected)
            if expected_clean:
                case["expected"] = expected_clean

            priority_clean = clean_field(priority)
            if priority_clean:
                case["priority"] = priority_clean.upper()

            cases.append(case)
            case_id_counter += 1

        if cases:
            modules.append({
                "name": module_name,
                "cases": cases
            })
            logger.info(f"解析模块 '{module_name}': {len(cases)} 个测试用例")

    logger.info(f"Markdown解析完成: {len(modules)} 个模块, 共 {sum(len(m['cases']) for m in modules)} 个测试用例")
    return {"modules": modules}


def _parse_review_markdown(markdown_text: str) -> dict:
    """解析质量评审Markdown为结构化数据.

    Args:
        markdown_text: Markdown格式的评审报告

    Returns:
        dict: {
            "summary": "评审摘要文本",
            "defects": ["缺陷1", "缺陷2", ...],
            "suggestions": ["建议1", "建议2", ...]
        }
    """
    if not markdown_text or not isinstance(markdown_text, str):
        logger.warning("评审Markdown文本为空或无效")
        return {"summary": "", "defects": [], "suggestions": []}

    result = {
        "summary": "",
        "defects": [],
        "suggestions": []
    }

    # 按## 分割章节
    sections = re.split(r'\n##\s+', markdown_text)

    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().split('\n')
        if not lines:
            continue

        # 第一行是章节标题
        section_title = lines[0].strip().lstrip('#').strip().lower()
        content_lines = lines[1:] if len(lines) > 1 else []

        # 提取内容
        if '评审摘要' in section_title or 'summary' in section_title:
            # 评审摘要：提取所有非空行作为摘要
            summary_parts = []
            for line in content_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    summary_parts.append(line)
            result["summary"] = '\n'.join(summary_parts)

        elif '缺陷' in section_title or 'defect' in section_title or '问题' in section_title:
            # 发现的缺陷：提取列表项
            for line in content_lines:
                line = line.strip()
                # 匹配列表项（- 或 * 或 数字.）
                match = re.match(r'^[-*]\s+(.+)$', line) or re.match(r'^\d+\.\s+(.+)$', line)
                if match:
                    result["defects"].append(match.group(1).strip())

        elif '建议' in section_title or 'suggest' in section_title or '改进' in section_title:
            # 改进建议：提取列表项
            for line in content_lines:
                line = line.strip()
                # 匹配列表项（- 或 * 或 数字.）
                match = re.match(r'^[-*]\s+(.+)$', line) or re.match(r'^\d+\.\s+(.+)$', line)
                if match:
                    result["suggestions"].append(match.group(1).strip())

    logger.info(f"评审报告解析完成: 摘要长度={len(result['summary'])}, 缺陷数={len(result['defects'])}, 建议数={len(result['suggestions'])}")
    return result


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
            AgentStage.requirement_analysis: "需求分析",
            AgentStage.confirmation: "确认",
            AgentStage.test_generation: "用例生成",
            AgentStage.review: "质量评审",
            AgentStage.test_completion: "用例补全",
            AgentStage.completed: "完成",
        }
        self._vl_config = settings.get_vl_config()
        self._pdf_ocr_config = settings.get_pdf_ocr_config()

    def _get_document_suffix(self, document: Document) -> str:
        if document.original_name:
            suffix = Path(document.original_name).suffix.lower()
            if suffix:
                return suffix
        return Path(document.storage_path).suffix.lower()


    async def execute(self) -> None:
        # Refresh VL 配置，确保每次执行都使用最新设置
        self._vl_config = settings.get_vl_config()
        self._pdf_ocr_config = settings.get_pdf_ocr_config()

        session = await session_repository.get_session(self.db_session, self.session_id)
        if session is None:
            logger.warning("Session %s not found", self.session_id)
            return

        await session_repository.update_session_status(
            self.db_session,
            session_id=self.session_id,
            from_status=session.status,
            to_status=SessionStatus.processing,
            stage=AgentStage.requirement_analysis,
            progress=0.12,
        )
        await self.db_session.commit()

        await self._emit_system_message("分析流程已开始，正在处理文档...", progress=0.12)

        # 准备文档数据供需求分析智能体使用
        document_data: list[dict] = []
        is_multimodal = settings.analysis_multimodal_enabled

        for document in session.documents:
            suffix = self._get_document_suffix(document)
            doc_name = document.original_name or document.id

            if is_multimodal:
                # 多模态模式：直接传递文件路径，让多模态模型处理
                logger.info(f"多模态模式 - 准备文档: {doc_name}")
                doc_type = "image" if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif"} else (
                    "pdf" if suffix == ".pdf" else "text"
                )

                # 对于非图片/PDF，仍需提取文本内容
                text_content = ""
                if doc_type == "text":
                    try:
                        text_content = extract_text(document.storage_path, original_name=document.original_name)
                    except Exception as exc:
                        logger.warning(f"文本提取失败: {doc_name}, error={exc}", exc_info=True)

                document_data.append({
                    "path": document.storage_path,
                    "type": doc_type,
                    "content": text_content,  # 多模态模式下图片/PDF的content为空
                    "name": doc_name,
                })

            else:
                # 文本模式：需要预先提取/OCR所有文档
                logger.info(f"文本模式 - 处理文档: {doc_name}")

                # 判断是否为图片文件
                if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
                    # 图片文件：使用VL模型提取需求内容
                    vl_text = ""
                    if self._vl_config.get("enabled") and self._vl_config.get("api_key") and is_vl_available():
                        try:
                            vl_text = await extract_requirements_with_retry(
                                Path(document.storage_path),
                                api_key=self._vl_config.get("api_key"),
                                model=self._vl_config.get("model"),
                                base_url=self._vl_config.get("base_url"),
                                use_cache=True,
                                prompt_mode="requirement",  # 需求分析模式
                            )
                        except Exception as exc:
                            logger.warning(f"VL模型处理图片失败: {doc_name}, error={exc}", exc_info=True)

                    document_data.append({
                        "path": document.storage_path,
                        "type": "image",
                        "content": vl_text or "[图片内容识别失败]",
                        "name": doc_name,
                    })

                elif suffix == ".pdf":
                    # PDF文件：优先使用PDF OCR
                    pdf_content = ""
                    if self._pdf_ocr_config.get("enabled") and self._pdf_ocr_config.get("api_key") and is_vl_available() and fitz is not None:
                        try:
                            with fitz.open(document.storage_path) as pdf_doc:  # type: ignore[arg-type]
                                if pdf_doc.page_count > 0:
                                    page = pdf_doc.load_page(0)
                                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                                    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                                    pix.save(tmp_file.name)
                                    tmp_file.close()
                                    tmp_path = Path(tmp_file.name)
                                    try:
                                        pdf_content = await extract_requirements_with_retry(
                                            tmp_path,
                                            api_key=self._pdf_ocr_config.get("api_key"),
                                            model=self._pdf_ocr_config.get("model"),
                                            base_url=self._pdf_ocr_config.get("base_url"),
                                            use_cache=True,
                                            prompt_mode="requirement",
                                        )
                                    finally:
                                        try:
                                            tmp_path.unlink()
                                        except Exception:
                                            pass
                        except Exception as exc:
                            logger.warning(f"PDF OCR处理失败: {doc_name}, error={exc}", exc_info=True)

                    # 回退到文本提取
                    if not pdf_content:
                        try:
                            pdf_content = extract_text(document.storage_path, original_name=document.original_name)
                        except Exception as exc:
                            logger.warning(f"PDF文本提取失败: {doc_name}, error={exc}", exc_info=True)

                    document_data.append({
                        "path": document.storage_path,
                        "type": "pdf",
                        "content": pdf_content or "[PDF内容提取失败]",
                        "name": doc_name,
                    })

                else:
                    # 其他文本文件
                    try:
                        text = extract_text(document.storage_path, original_name=document.original_name)
                    except Exception as exc:
                        logger.warning(f"文本提取失败: {doc_name}, error={exc}", exc_info=True)
                        text = ""

                    document_data.append({
                        "path": document.storage_path,
                        "type": "text",
                        "content": text or "[文本提取失败]",
                        "name": doc_name,
                    })

        # 开始调用AutoGen智能体进行需求分析
        await self._emit_system_message(
            "文档处理完成，开始调用AutoGen智能体进行需求分析...",
            progress=0.18,
        )
        logger.info("开始逐个调用 AutoGen 智能体...")

        merged_markdown = ""
        stage_durations: dict[AgentStage, float] = {}

        def _format_seconds(value: float) -> str:
            rounded = max(0.0, value)
            if rounded == 0:
                return "0"
            formatted = f"{rounded:.2f}"
            if formatted.endswith(".00"):
                return formatted[:-3]
            return formatted.rstrip("0").rstrip(".") or "0"

        try:
            # 1. 需求分析阶段（非流式输出）
            logger.info("执行需求分析智能体（非流式输出）...")

            analysis_started_at = time.time()
            analysis_payload, analysis_content = await asyncio.to_thread(
                run_requirement_analysis, document_data, None
            )
            analysis_duration = time.time() - analysis_started_at
            stage_durations[AgentStage.requirement_analysis] = analysis_duration
            analysis_display_content = analysis_content or ""
            analysis_result = StageResult(
                stage=AgentStage.requirement_analysis,
                sender="需求分析师",
                content=analysis_display_content,
                payload=analysis_payload,
                progress=0.3,
                duration_seconds=analysis_duration,
            )
            await self._handle_stage_result(
                analysis_result,
                skip_confirmation=False,
                needs_confirmation=True,
            )

            # 2. 测试用例生成阶段（非流式输出）
            logger.info("执行测试用例生成智能体（非流式输出）...")

            test_started_at = time.time()
            test_payload, test_content = await asyncio.to_thread(
                run_test_generation, analysis_payload, None
            )
            test_duration = time.time() - test_started_at
            stage_durations[AgentStage.test_generation] = test_duration
            test_display_content = test_content or ""

            # 解析测试用例Markdown为JSON，用于前端表格显示
            test_cases_json = _parse_markdown_test_cases(test_display_content)

            test_result = StageResult(
                stage=AgentStage.test_generation,
                sender="测试工程师",
                content=test_display_content,
                payload=test_cases_json,  # 传递解析后的JSON
                progress=0.6,
                duration_seconds=test_duration,
            )
            await self._handle_stage_result(
                test_result,
                skip_confirmation=False,
                needs_confirmation=True,
            )

            # 3. 质量评审阶段（非流式输出）
            logger.info("执行质量评审智能体（非流式输出）...")

            review_started_at = time.time()
            review_payload, review_content = await asyncio.to_thread(
                run_quality_review, test_content, None
            )
            review_duration = time.time() - review_started_at
            stage_durations[AgentStage.review] = review_duration
            review_display_content = review_content or ""

            # 解析评审报告Markdown为结构化数据，用于前端结构化显示
            review_structured = _parse_review_markdown(review_display_content)

            review_result = StageResult(
                stage=AgentStage.review,
                sender="质量评审员",
                content=review_display_content,  # 保留原始Markdown作为备份
                payload=review_structured,  # 传递结构化数据
                progress=0.8,
                duration_seconds=review_duration,
            )
            await self._handle_stage_result(
                review_result,
                skip_confirmation=False,
                needs_confirmation=True,
            )

            # 4. 用例补全阶段（非流式输出）
            logger.info("执行用例补全智能体（非流式输出）...")

            completion_started_at = time.time()
            completion_payload, completion_content = await asyncio.to_thread(
                run_test_completion, test_content, review_content, None
            )
            completion_duration = time.time() - completion_started_at
            stage_durations[AgentStage.test_completion] = completion_duration
            completion_display_content = completion_content or ""

            # 解析补充用例Markdown为JSON，用于前端表格显示
            completion_cases_json = _parse_markdown_test_cases(completion_display_content)

            completion_result = StageResult(
                stage=AgentStage.test_completion,
                sender="测试补全工程师",
                content=completion_display_content,
                payload=completion_cases_json,  # 传递解析后的JSON
                progress=0.9,
                duration_seconds=completion_duration,
            )
            await self._handle_stage_result(
                completion_result,
                skip_confirmation=False,
                needs_confirmation=True,
            )

            # 5. 准备最终结果（解析Markdown并合并JSON）
            logger.info("准备最终结果...")

            # 解析测试用例生成和补全的Markdown为JSON
            test_cases_json = _parse_markdown_test_cases(test_display_content)
            completion_cases_json = _parse_markdown_test_cases(completion_display_content)

            # 合并测试用例（使用autogen_runner的合并函数）
            from app.llm.autogen_runner import _merge_test_cases
            merged_test_cases = _merge_test_cases(test_cases_json, completion_cases_json)

            logger.info(f"合并后的测试用例: {len(merged_test_cases.get('modules', []))} 个模块")

            # 准备最终结果
            summary = analysis_payload
            metrics = {}  # Markdown模式下metrics为空

            # 为completed阶段准备简洁的文本内容（用于日志和备份）
            merged_markdown = f"测试用例生成完成，共 {sum(len(m.get('cases', [])) for m in merged_test_cases.get('modules', []))} 个测试用例"

        except Exception as exc:
            # 当 LLM 出错时，直接以错误提示告知前端，避免界面无响应
            logger.exception("AutoGen 执行失败，返回错误提示: %s", exc)

            # 推送错误信息，直接提示模型响应失败
            file_names = ", ".join(
                (doc.original_name or "未命名文件") for doc in session.documents
            )
            content = (
                "未能完成智能体深度分析。\n\n"
                f"文件：{file_names}\n\n"
                "提示：模型响应失败，请检查模型配置或稍后重试。"
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

        # 发送"完成"阶段事件
        total_duration = sum(stage_durations.values()) if stage_durations else None
        completed_result = StageResult(
            stage=AgentStage.completed,
            sender="测试工程师",
            content=merged_markdown or "测试用例生成完成",
            payload=merged_test_cases,  # 传递合并后的测试用例JSON
            progress=0.95,
            duration_seconds=total_duration,
        )

        # 先保存最终结果，确保导出接口可立即读取
        await session_repository.add_session_result(
            self.db_session,
            session_id=self.session_id,
            summary=summary,
            payload=merged_test_cases,  # 保存合并后的测试用例
            metrics=metrics,
            stage=AgentStage.completed,
            progress=1.0,
        )
        await self.db_session.commit()

        # 再发送"完成"阶段事件
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
            "分析流程完成，所有结果已生成。",
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
        if result.duration_seconds is not None:
            event["duration_seconds"] = float(result.duration_seconds)

        # 调试日志：记录发送的payload结构
        logger.info(
            f"发送WebSocket事件: stage={result.stage.value}, "
            f"payload_keys={list(result.payload.keys()) if isinstance(result.payload, dict) else 'not-dict'}, "
            f"content_length={len(result.content) if result.content else 0}"
        )
        if isinstance(result.payload, dict):
            if "error" in result.payload:
                logger.warning(f"payload包含错误信息: {result.payload.get('error')}")
            if "modules" in result.payload:
                modules = result.payload.get("modules", [])
                logger.info(f"payload包含 {len(modules) if isinstance(modules, list) else 'invalid'} 个模块")

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

                    # 发送系统消息 - 根据不同阶段提供不同的反馈
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
