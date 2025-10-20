"""AutoGen-based workflow runner using Qwen-compatible OpenAI API."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

try:  # pragma: no cover - optional dependency
    from autogen import AssistantAgent
except Exception:  # pragma: no cover
    AssistantAgent = None  # type: ignore

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
        logger.info(f"成功提取 JSON，包含 {len(result)} 个字段")
        return result
    except Exception as e:
        logger.warning(f"JSON 提取失败: {e}, 返回原始内容")
        return {"raw": content.strip() if content else "None"}


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


def run_requirement_analysis(documents_text: str) -> tuple[dict, str]:
    """执行需求分析阶段.

    Returns:
        tuple[dict, str]: (需求分析JSON结果, 原始响应内容)
    """
    if AssistantAgent is None:
        raise RuntimeError("AutoGen 未安装，无法运行真实智能体")

    logger.info("=" * 50)
    logger.info("阶段 1/4: 需求分析")
    logger.info(f"输入文档长度: {len(documents_text)} 字符")
    logger.info("=" * 50)

    analysis_agent = _agent(
        "你是一位资深需求分析师。请仔细阅读需求文档,识别并提取文档中的所有具体功能模块、业务场景和业务规则。必须基于文档的实际内容进行分析,不要使用泛化的占位符(如'模块1'、'场景1')。输出JSON格式,包含: modules (name为实际模块名, scenarios为具体场景描述[], rules为具体规则描述[]), risks[]。",
        agent_type="analysis"
    )
    analysis_prompt = (
        "请根据以下需求文档进行详细分析。重要提示:\n"
        "1. 必须提取文档中的实际功能模块名称(如'设备登录'、'网络设置'、'国标平台')，不要使用'模块1'、'模块2'等占位符\n"
        "2. 必须描述文档中的具体业务场景(如'用户密码登录'、'8路视频通道接入')，不要使用'场景1'、'场景2'等占位符\n"
        "3. 必须提取文档中的具体业务规则和性能指标(如'启动时间≤2分钟'、'视频延时≤50ms')\n"
        "4. 输出JSON格式: {\"modules\": [{\"name\": \"实际模块名\", \"scenarios\": [{\"description\": \"具体场景描述\"}], \"rules\": [{\"description\": \"具体规则描述\"}]}], \"risks\": [{\"description\": \"风险描述\"}]}\n\n"
        f"需求文档内容:\n{documents_text[:4000]}"
    )
    analysis_content = _generate(analysis_agent, analysis_prompt)
    analysis_payload = _extract_json(analysis_content)
    logger.info(f"需求分析完成，提取的字段: {list(analysis_payload.keys())}")

    return analysis_payload, analysis_content


def run_test_generation(analysis_payload: dict) -> tuple[dict, str]:
    """执行测试用例生成阶段.

    Args:
        analysis_payload: 需求分析结果

    Returns:
        tuple[dict, str]: (测试用例JSON结果, 原始响应内容)
    """
    if AssistantAgent is None:
        raise RuntimeError("AutoGen 未安装，无法运行真实智能体")

    logger.info("=" * 50)
    logger.info("阶段 2/4: 测试用例生成")
    logger.info("=" * 50)

    test_agent = _agent(
        "你是一位资深测试工程师。根据需求分析结果,为每个具体功能模块生成详细的测试用例。测试用例必须针对实际功能点,包含具体的测试步骤和预期结果,不要使用泛化描述。输出JSON格式: {\"modules\": [{\"name\": \"实际模块名\", \"cases\": [{\"id\": \"用例编号\", \"title\": \"具体测试标题\", \"preconditions\": [前置条件], \"steps\": [详细步骤], \"expected\": \"具体预期结果\", \"priority\": \"高/中/低\"}]}]}",
        agent_type="test"
    )
    test_prompt = (
        "以下是需求分析的JSON结果,请基于实际功能生成测试用例。重要提示:\n"
        "1. 保持需求分析中的实际模块名,不要改为'模块1'、'模块2'\n"
        "2. 测试用例标题必须针对具体功能(如'验证使用默认IP 192.168.1.21登录'、'验证8路视频通道接入'),不要使用'验证场景1'等泛化描述\n"
        "3. 测试步骤必须具体明确,包含实际参数值和操作细节\n"
        "4. 覆盖正常流程、异常处理、边界条件、状态切换等功能场景,确保每条业务规则都有对应验证\n"
        "5. 不要生成仅针对性能、吞吐、稳定性等非功能性测试; 专注于功能行为和业务逻辑的完整验证\n\n"
        f"需求分析结果:\n{json.dumps(analysis_payload, ensure_ascii=False)}"
    )
    test_content = _generate(test_agent, test_prompt)
    test_payload = _extract_json(test_content)
    logger.info(f"测试用例生成完成，提取的字段: {list(test_payload.keys())}")

    return test_payload, test_content


def run_quality_review(test_payload: dict) -> tuple[dict, str]:
    """执行质量评审阶段.

    Args:
        test_payload: 测试用例结果

    Returns:
        tuple[dict, str]: (评审JSON结果, 原始响应内容)
    """
    if AssistantAgent is None:
        raise RuntimeError("AutoGen 未安装，无法运行真实智能体")

    logger.info("=" * 50)
    logger.info("阶段 3/4: 质量评审")
    logger.info("=" * 50)

    review_agent = _agent(
        "你是质量评审专家。仔细评审测试用例的完整性和准确性,识别覆盖缺陷并提供改进建议。评审必须基于实际功能模块和测试用例的具体内容,指出哪些功能点遗漏了测试。输出JSON格式: {\"coverage\": 覆盖率百分比数值, \"gaps\": [具体缺陷描述], \"recommendations\": [具体改进建议]}",
        agent_type="review"
    )
    review_prompt = (
        "请评审以下测试用例,分析覆盖率并提供改进建议。重要提示:\n"
        "1. 在gaps中必须指出具体遗漏的功能功能点或业务场景(如'缺少对会员充值流程的异常处理测试'),不要使用泛化描述\n"
        "2. 在recommendations中提供针对性的改进建议,包含具体的功能测试场景和验证点\n"
        "3. 重点关注功能行为的完整性(主流程、异常流程、边界条件、状态切换等),不要围绕性能/吞吐/稳定性等非功能性内容\n"
        "4. coverage必须是数值(0-100),基于实际功能覆盖情况评估\n\n"
        f"测试用例JSON:\n{json.dumps(test_payload, ensure_ascii=False)}"
    )
    review_content = _generate(review_agent, review_prompt)
    review_payload = _extract_json(review_content)
    logger.info(f"质量评审完成，提取的字段: {list(review_payload.keys())}")

    return review_payload, review_content


def run_test_completion(analysis_payload: dict, test_payload: dict, review_payload: dict) -> tuple[dict, str]:
    """执行用例补全阶段.

    Args:
        analysis_payload: 需求分析结果
        test_payload: 测试用例结果
        review_payload: 质量评审结果

    Returns:
        tuple[dict, str]: (补全用例JSON结果, 原始响应内容)
    """
    if AssistantAgent is None:
        raise RuntimeError("AutoGen 未安装，无法运行真实智能体")

    logger.info("=" * 50)
    logger.info("阶段 4/4: 用例补全")
    logger.info("=" * 50)

    completion_agent = _agent(
        "你是一位测试补全工程师。根据质量评审发现的缺口与建议,补充缺失的测试用例。输出仅包含 JSON 对象: {\"modules\": [{\"name\": \"模块名称\", \"cases\": [{\"id\": \"唯一用例编号\", \"title\": \"具体测试标题\", \"preconditions\": [前置条件], \"steps\": [详细步骤], \"expected\": \"明确的预期结果\", \"priority\": \"P0/P1/P2/P3\"}]}]}。",
        agent_type="test"
    )
    completion_prompt = (
        "以下信息来自前序阶段,请基于质量评审的缺口(gaps)与建议(recommendations)生成补充测试用例。要求:\n"
        "1. 仅针对缺口与建议中提到的功能点新增测试,避免重复已有用例。\n"
        "2. 直接给出 JSON 结果,不要包含解释性文字。\n"
        "3. 若建议中提到覆盖不足的场景,需要补充至少一个高优先级(P0/P1)的验证。\n"
        "4. 每条测试步骤要包含明确行动和可验证的预期。\n\n"
        f"需求分析 JSON:\n{json.dumps(analysis_payload, ensure_ascii=False)}\n\n"
        f"现有测试用例 JSON:\n{json.dumps(test_payload, ensure_ascii=False)}\n\n"
        f"质量评审 JSON:\n{json.dumps(review_payload, ensure_ascii=False)}\n"
    )
    completion_content = _generate(completion_agent, completion_prompt)
    completion_payload = _extract_json(completion_content)
    logger.info(
        "补充测试用例生成完成，提取字段: %s",
        list(completion_payload.keys()),
    )

    return completion_payload, completion_content


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
