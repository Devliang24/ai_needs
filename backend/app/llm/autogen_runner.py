"""AutoGen-based workflow runner using Qwen-compatible OpenAI API."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Callable

try:  # pragma: no cover - optional dependency
    from autogen import AssistantAgent
except Exception:  # pragma: no cover
    AssistantAgent = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from app.config import settings

logger = logging.getLogger(__name__)


def _extract_json(content: str) -> dict:
    logger.info(f"尝试从响应中提取 JSON，响应长度: {len(content) if content else 0}")
    logger.debug(f"原始响应内容: {content[:500] if content else 'None'}")
    try:
        start = content.index("{")
        end = content.rfind("}") + 1
        json_str = content[start:end]
        result = json.loads(json_str)
        logger.info(f"成功提取 JSON，包含 {len(result)} 个字段: {list(result.keys())}")
        return result
    except Exception as e:
        logger.error(f"JSON 提取失败: {e}")
        logger.error(f"原始响应内容（前1000字符）: {content[:1000] if content else 'None'}")
        # 返回空的modules结构，而不是raw字段，避免前端显示"暂无测试用例"时用户无法知道发生了什么
        # 前端会检测到modules为空数组并显示友好的错误提示
        return {"modules": [], "error": f"JSON解析失败: {str(e)}", "raw_response": content[:500] if content else ""}


def _agent(system_message: str, agent_type: str = "default") -> AssistantAgent:
    """创建智能体，根据类型使用不同的模型配置."""
    if AssistantAgent is None:  # pragma: no cover - handled by caller
        raise RuntimeError("AutoGen 未安装，无法启用 autogen 模式")

    # 获取智能体专用配置
    if agent_type in ("analysis", "test", "review"):
        config = settings.get_agent_config(agent_type)
    else:
        # fallback 到默认配置
        config = {
            "model": settings.qwen_model,
            "base_url": settings.qwen_base_url,
            "api_key": settings.qwen_api_key,
        }

    logger.info(f"创建 {agent_type} 智能体，使用模型: {config['model']}")

    return AssistantAgent(
        name=f"{agent_type}_agent",
        system_message=system_message,
        llm_config={
            "config_list": [config],
            "timeout": settings.llm_timeout,
        },
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config=False,
    )


def _generate(agent: AssistantAgent, prompt: str) -> str:
    logger.info(f"发送 Prompt 到 LLM，长度: {len(prompt)}")
    logger.debug(f"Prompt 内容前500字符: {prompt[:500]}")
    try:
        reply = agent.generate_reply(messages=[{"role": "user", "content": prompt}])
        logger.info(f"收到 LLM 响应，类型: {type(reply)}")
        logger.debug(f"完整响应: {reply}")

        if isinstance(reply, str):
            logger.info(f"响应是字符串，长度: {len(reply)}")
            return reply
        if isinstance(reply, dict):
            content = reply.get("content", "")
            logger.info(f"响应是字典，提取 content 字段，长度: {len(content)}")
            return content

        result = str(reply)
        logger.warning(f"响应类型未知，转为字符串: {result[:200]}")
        return result
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}", exc_info=True)
        raise


def _generate_streaming(
    system_message: str,
    prompt: str,
    agent_type: str = "default",
    on_chunk: Callable[[str], None] | None = None,
) -> str:
    """流式生成LLM响应,逐chunk回调.

    Args:
        system_message: 系统提示
        prompt: 用户提示
        agent_type: 智能体类型
        on_chunk: 回调函数,接收每个chunk

    Returns:
        完整的响应内容
    """
    if OpenAI is None:
        raise RuntimeError("OpenAI 未安装，无法启用流式模式")

    # 获取智能体配置
    if agent_type in ("analysis", "test", "review"):
        config = settings.get_agent_config(agent_type)
    else:
        config = {
            "model": settings.qwen_model,
            "base_url": settings.qwen_base_url,
            "api_key": settings.qwen_api_key,
        }

    logger.info(f"流式生成: {agent_type} 智能体，使用模型: {config['model']}")

    client = OpenAI(
        api_key=config["api_key"],
        base_url=config.get("base_url"),
        timeout=settings.llm_timeout,
    )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]

    try:
        stream = client.chat.completions.create(
            model=config["model"],
            messages=messages,
            stream=True,
        )

        full_content = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_content += delta.content
                    if on_chunk:
                        on_chunk(delta.content)

        logger.info(f"流式生成完成，总长度: {len(full_content)}")
        return full_content

    except Exception as e:
        logger.error(f"流式LLM调用失败: {e}", exc_info=True)
        raise


@dataclass
class AutogenOutputs:
    summary: dict
    base_test_cases: dict
    completion_cases: dict
    merged_test_cases: dict
    metrics: dict
    analysis_message: str
    test_message: str
    review_message: str
    completion_message: str


def _collect_module_cases(payload: dict) -> list:
    if not isinstance(payload, dict):
        return []
    modules = payload.get("modules")
    if isinstance(modules, list):
        return modules
    return []


def _merge_test_cases(base: dict, supplement: dict) -> dict:
    merged: dict[str, list] = {}
    result = {"modules": []}

    def normalize_name(module: dict) -> str | None:
        if not isinstance(module, dict):
            return None
        name = module.get("name") or module.get("module")
        if isinstance(name, str) and name.strip():
            return name.strip()
        return None

    for source in (base, supplement):
        modules = _collect_module_cases(source) if isinstance(source, dict) else []
        for module in modules:
            if not isinstance(module, dict):
                continue
            name = normalize_name(module)
            if not name:
                continue
            if name not in merged:
                merged[name] = []
                result["modules"].append({"name": name, "cases": merged[name]})

            existing_ids = {
                case.get("id")
                for case in merged[name]
                if isinstance(case, dict) and isinstance(case.get("id"), str)
            }
            for case in module.get("cases", []):
                if not isinstance(case, dict):
                    continue
                case_id = case.get("id")
                if isinstance(case_id, str) and case_id in existing_ids:
                    continue
                merged[name].append(case)
    return result


def run_requirement_analysis(
    document_data: list[dict],
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[dict, str]:
    """执行需求分析阶段（支持多模态和流式输出）.

    Args:
        document_data: 文档数据列表，每项包含:
            - path: 文件路径
            - type: "image" / "pdf" / "text"
            - content: 提取的文本内容（文本模式下使用）
            - name: 文档名称
        on_chunk: 可选的流式回调函数

    Returns:
        tuple[dict, str]: (需求分析JSON结果, 原始响应内容)
    """
    from app.config import settings

    # 检查是否启用多模态模式
    if settings.analysis_multimodal_enabled:
        logger.info("使用多模态分析模式（直接处理图片/PDF）")
        return _run_multimodal_analysis(document_data, on_chunk=on_chunk)
    else:
        logger.info("使用文本分析模式（预处理+文本分析）")
        return _run_text_based_analysis(document_data, on_chunk=on_chunk)


def _run_multimodal_analysis(
    document_data: list[dict],
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[dict, str]:
    """使用多模态VL模型直接分析图片/PDF（保留视觉信息）."""
    from app.llm.multimodal_client import analyze_with_multimodal
    from app.config import settings

    logger.info("=" * 50)
    logger.info("阶段 1/4: 需求分析（多模态视觉理解模式）")
    logger.info(f"输入文档数量: {len(document_data)}")
    logger.info("=" * 50)

    # 获取多模态模型配置
    config = settings.get_agent_config("analysis")
    logger.info(f"使用多模态模型: {config['model']}")

    # 收集所有分析结果
    all_analysis_results = []
    total_docs = len(document_data)

    def emit_progress(message: str) -> None:
        if on_chunk is None:
            return
        try:
            on_chunk(f"{message}\n")
        except Exception:
            logger.exception("多模态分析进度回调失败: %s", message)

    for idx, doc in enumerate(document_data, 1):
        doc_type = doc.get("type", "text")
        doc_name = doc.get("name", f"文档{idx}")
        doc_path = Path(doc.get("path", ""))

        if doc_type in ["image", "pdf"]:
            # 使用多模态模型直接分析图片/PDF
            logger.info(f"正在使用多模态模型分析 {doc_type} 文件: {doc_name}")
            emit_progress(f"正在分析第 {idx}/{total_docs} 个文档：{doc_name}")

            try:
                # 异步调用转同步
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        analyze_with_multimodal(
                            file_path=doc_path,
                            api_key=config["api_key"],
                            model=config["model"],
                            base_url=config.get("base_url"),
                        )
                    )
                    all_analysis_results.append(result)
                    logger.info(f"文档 {doc_name} 多模态分析成功")
                    emit_progress(f"已完成第 {idx}/{total_docs} 个文档：{doc_name}")
                finally:
                    asyncio.set_event_loop(None)
                    loop.close()

            except Exception as e:
                logger.error(f"多模态分析失败: {doc_name}, error={e}", exc_info=True)
                # 回退到文本内容
                fallback_text = doc.get("content", "")
                if fallback_text:
                    all_analysis_results.append(f"文档 {doc_name}（多模态分析失败，使用文本内容）:\n{fallback_text}")
                else:
                    all_analysis_results.append(f"文档 {doc_name}: [多模态分析失败且无文本内容]")
                emit_progress(f"文档 {doc_name} 多模态分析失败，已回退到文本内容")

        else:
            # 纯文本文件，直接使用提取的内容
            text_content = doc.get("content", "")
            all_analysis_results.append(f"=== 文档 {idx}: {doc_name} (text) ===\n{text_content}")
            emit_progress(f"已加载文本文档 {idx}/{total_docs}：{doc_name}")

    # 合并所有结果
    combined_analysis = "\n\n".join(all_analysis_results)
    logger.info(f"所有文档分析完成，总长度: {len(combined_analysis)} 字符")
    emit_progress("所有文档分析完毕，正在整理结构化结果...")

    # 提取JSON
    analysis_payload = _extract_json(combined_analysis)
    logger.info(f"多模态需求分析完成，提取的字段: {list(analysis_payload.keys())}")
    emit_progress("结构化需求分析结果已生成。")

    return analysis_payload, combined_analysis


def _run_text_based_analysis(
    document_data: list[dict],
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[dict, str]:
    """传统文本模式分析（预处理+流式生成）."""
    logger.info("=" * 50)
    logger.info("阶段 1/4: 需求分析（文本模式）")
    logger.info(f"输入文档数量: {len(document_data)}")
    logger.info("=" * 50)

    # 构建综合文档内容
    combined_content_parts = []
    for idx, doc in enumerate(document_data, 1):
        doc_name = doc.get("name", f"文档{idx}")
        doc_type = doc.get("type", "text")
        doc_content = doc.get("content", "")

        combined_content_parts.append(f"=== 文档 {idx}: {doc_name} ({doc_type}) ===")
        combined_content_parts.append(doc_content)
        combined_content_parts.append("")

    documents_text = "\n".join(combined_content_parts)
    logger.info(f"合并后文档长度: {len(documents_text)} 字符")

    system_message = (
        "你是一位资深需求分析师。请仔细阅读需求文档,识别并提取文档中的所有具体功能模块、业务场景和业务规则。"
        "必须基于文档的实际内容进行分析,不要使用泛化的占位符(如'模块1'、'场景1')。"
        "输出JSON格式,包含: modules (name为实际模块名, scenarios为具体场景描述[], rules为具体规则描述[]), risks[]。"
    )
    analysis_prompt = (
        "请根据以下需求文档进行详细分析。重要提示:\n"
        "1. 必须提取文档中的实际功能模块名称(如'设备登录'、'网络设置'、'国标平台')，不要使用'模块1'、'模块2'等占位符\n"
        "2. 必须描述文档中的具体业务场景(如'用户密码登录'、'8路视频通道接入')，不要使用'场景1'、'场景2'等占位符\n"
        "3. 必须提取文档中的具体业务规则和性能指标(如'启动时间≤2分钟'、'视频延时≤50ms')\n"
        "4. 输出JSON格式: {\"modules\": [{\"name\": \"实际模块名\", \"scenarios\": [{\"description\": \"具体场景描述\"}], \"rules\": [{\"description\": \"具体规则描述\"}]}], \"risks\": [{\"description\": \"风险描述\"}]}\n\n"
        f"需求文档内容:\n{documents_text[:8000]}"
    )

    # 使用流式生成
    analysis_content = _generate_streaming(
        system_message=system_message,
        prompt=analysis_prompt,
        agent_type="analysis",
        on_chunk=on_chunk,
    )
    analysis_payload = _extract_json(analysis_content)
    logger.info(f"需求分析完成，提取的字段: {list(analysis_payload.keys())}")

    return analysis_payload, analysis_content


def run_test_generation(
    analysis_payload: dict,
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[dict, str]:
    """执行测试用例生成阶段（流式输出Markdown）.

    Args:
        analysis_payload: 需求分析结果
        on_chunk: 可选的流式回调函数

    Returns:
        tuple[dict, str]: (空dict, Markdown格式的测试用例文本)
    """
    logger.info("=" * 50)
    logger.info("阶段 2/4: 测试用例生成（Markdown格式）")
    logger.info("=" * 50)

    system_message = (
        "你是一位资深测试工程师。根据需求分析结果,为每个具体功能模块生成详细的测试用例。"
        "请以Markdown格式输出,包含清晰的章节结构和表格。"
    )
    test_prompt = (
        "以下是需求分析结果,请以Markdown格式生成测试用例。要求:\n"
        "1. 按功能模块组织,每个模块使用 ## 标题\n"
        "2. 使用表格展示测试用例,包含列: 用例ID | 标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级\n"
        "3. 测试步骤和前置条件使用简洁的文本描述或编号列表\n"
        "4. 覆盖正常流程、异常处理、边界条件等场景\n"
        "5. 专注于功能行为和业务逻辑的验证\n\n"
        f"需求分析结果:\n{json.dumps(analysis_payload, ensure_ascii=False)}"
    )

    # 使用流式生成
    test_content = _generate_streaming(
        system_message=system_message,
        prompt=test_prompt,
        agent_type="test",
        on_chunk=on_chunk,
    )
    logger.info("测试用例生成完成（Markdown格式）")

    return {}, test_content  # payload为空，只返回Markdown文本


def run_quality_review(
    test_content: str,
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[dict, str]:
    """执行质量评审阶段（流式输出Markdown）.

    Args:
        test_content: Markdown格式的测试用例文本
        on_chunk: 可选的流式回调函数

    Returns:
        tuple[dict, str]: (空dict, Markdown格式的评审报告)
    """
    logger.info("=" * 50)
    logger.info("阶段 3/4: 质量评审（Markdown格式）")
    logger.info("=" * 50)

    system_message = (
        "你是质量评审专家。仔细评审测试用例的完整性和准确性,以Markdown格式输出评审报告。"
    )
    review_prompt = (
        "请评审以下测试用例,以Markdown格式输出评审报告。要求:\n"
        "1. 使用 ## 评审摘要 章节,说明覆盖率评估和整体评价\n"
        "2. 使用 ## 发现的缺陷 章节,列出具体缺陷和遗漏的功能点\n"
        "3. 使用 ## 改进建议 章节,提供针对性的改进建议\n"
        "4. 重点关注功能行为的完整性(主流程、异常流程、边界条件等)\n\n"
        f"测试用例:\n{test_content}"
    )

    review_content = _generate_streaming(
        system_message=system_message,
        prompt=review_prompt,
        agent_type="review",
        on_chunk=on_chunk,
    )
    logger.info("质量评审完成（Markdown格式）")

    return {}, review_content  # payload为空，只返回Markdown文本


def run_test_completion(
    test_content: str,
    review_content: str,
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[dict, str]:
    """执行用例补全阶段（流式输出Markdown）.

    Args:
        test_content: Markdown格式的测试用例文本
        review_content: Markdown格式的评审报告
        on_chunk: 可选的流式回调函数

    Returns:
        tuple[dict, str]: (空dict, Markdown格式的补充测试用例)
    """
    logger.info("=" * 50)
    logger.info("阶段 4/4: 用例补全（Markdown格式）")
    logger.info("=" * 50)

    system_message = (
        "你是一位测试补全工程师。根据质量评审发现的缺口与建议,以Markdown格式补充缺失的测试用例。"
    )
    completion_prompt = (
        "请根据质量评审的缺陷和建议,以Markdown格式补充测试用例。要求:\n"
        "1. 使用与原测试用例相同的Markdown表格格式\n"
        "2. 只补充缺失的用例,不重复已有内容\n"
        "3. 按功能模块组织,每个模块使用 ## 标题\n"
        "4. 每条测试用例包含明确的步骤和可验证的预期结果\n\n"
        f"原始测试用例:\n{test_content}\n\n"
        f"质量评审报告:\n{review_content}"
    )

    # 使用流式生成
    completion_content = _generate_streaming(
        system_message=system_message,
        prompt=completion_prompt,
        agent_type="test",
        on_chunk=on_chunk,
    )
    logger.info("用例补全完成（Markdown格式）")

    return {}, completion_content  # payload为空，只返回Markdown文本


# 保留原有的run_analysis函数用于兼容性(已弃用)
def run_analysis(documents_text: str) -> AutogenOutputs:
    """[已弃用] 一次性执行所有智能体分析.

    建议使用新的分阶段函数: run_requirement_analysis, run_test_generation,
    run_quality_review, run_test_completion
    """
    if AssistantAgent is None:
        raise RuntimeError("AutoGen 未安装，无法运行真实智能体")

    logger.warning("run_analysis 已弃用，建议使用分阶段函数")

    # 调用新的分阶段函数
    analysis_payload, analysis_content = run_requirement_analysis(documents_text)
    test_payload, test_content = run_test_generation(analysis_payload)
    review_payload, review_content = run_quality_review(test_payload)
    completion_payload, completion_content = run_test_completion(
        analysis_payload, test_payload, review_payload
    )

    merged_cases = _merge_test_cases(test_payload, completion_payload)

    logger.info("=" * 50)
    logger.info("AutoGen 多智能体分析流程完成")
    logger.info("=" * 50)

    return AutogenOutputs(
        summary=analysis_payload,
        base_test_cases=test_payload,
        completion_cases=completion_payload if isinstance(completion_payload, dict) else {},
        merged_test_cases=merged_cases,
        metrics=review_payload,
        analysis_message=analysis_content,
        test_message=test_content,
        review_message=review_content,
        completion_message=completion_content,
    )
