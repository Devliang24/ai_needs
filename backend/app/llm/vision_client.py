"""Vision-Language model client for image understanding."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from dashscope import MultiModalConversation
    from http import HTTPStatus
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logger.warning("dashscope not available, VL image recognition will be disabled")


REQUIREMENT_EXTRACTION_PROMPT = """请仔细分析这张图片中的需求文档信息，并提取以下内容：

1. **业务场景**：图片中描述的业务场景或用户故事
2. **功能点**：具体的功能需求和特性
3. **业务流程**：如果有流程图或步骤说明，请详细描述
4. **业务规则**：约束条件、验证规则、业务逻辑
5. **数据要求**：涉及的数据字段、格式、范围等
6. **界面元素**：如果是界面截图，描述页面布局、控件、交互等
7. **其他重要信息**：任何其他与需求相关的信息

请用清晰、结构化的文字输出，便于后续进行测试用例设计。如果图片中包含表格，请保留表格结构。如果包含流程图，请用文字描述流程的每个步骤和分支。"""


def extract_requirements_from_image(
    image_path: str | Path,
    api_key: str | None = None,
    model: str = "qwen-vl-max",
    base_url: str | None = None,
) -> str:
    """
    使用 VL 模型从图片中提取需求信息.

    Args:
        image_path: 图片文件路径
        api_key: DashScope API Key
        model: VL 模型名称，默认 qwen-vl-max
        base_url: 可选的 API base URL

    Returns:
        提取的需求文本

    Raises:
        Exception: 如果 dashscope 不可用或 API 调用失败
    """
    if not DASHSCOPE_AVAILABLE:
        raise ImportError("dashscope package is not installed. Please install it with: pip install dashscope>=1.24.6")

    if not api_key:
        raise ValueError("api_key is required for VL model")

    image_path = Path(image_path).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    logger.info(f"Using VL model {model} to extract requirements from image: {image_path}")

    # 构建消息
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{image_path}"},
                {"text": REQUIREMENT_EXTRACTION_PROMPT}
            ]
        }
    ]

    # 调用 VL 模型
    try:
        call_kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "result_format": "message",
            "api_key": api_key,
        }

        # 如果提供了 base_url，添加到参数中
        if base_url:
            call_kwargs["base_url"] = base_url

        response = MultiModalConversation.call(**call_kwargs)

        if response.status_code == HTTPStatus.OK:
            content = response.output.choices[0]["message"]["content"]

            # 处理返回值可能是列表的情况（如 qwen3-vl-plus 返回 [{'text': '...'}]）
            if isinstance(content, list) and len(content) > 0:
                # 提取列表中的文本内容
                if isinstance(content[0], dict) and 'text' in content[0]:
                    text_content = content[0]['text']
                    logger.info(f"Extracted text from list format, length: {len(text_content)} characters")
                    return text_content
                else:
                    # 如果列表中不是预期的字典格式，转换为字符串
                    text_content = str(content)
                    logger.warning(f"Unexpected list format in VL response, converting to string: {len(text_content)} characters")
                    return text_content
            elif isinstance(content, str):
                # 如果已经是字符串，直接返回
                logger.info(f"Successfully extracted {len(content)} characters from image")
                return content
            else:
                # 未知格式，转换为字符串
                text_content = str(content)
                logger.warning(f"Unexpected content type: {type(content)}, converting to string")
                return text_content
        else:
            error_msg = (
                f"VL model call failed - "
                f"Request ID: {response.request_id}, "
                f"Status: {response.status_code}, "
                f"Error code: {response.code}, "
                f"Error message: {response.message}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    except Exception as e:
        logger.exception(f"Failed to extract requirements from image: {e}")
        raise


def is_vl_available() -> bool:
    """检查 VL 模型是否可用."""
    return DASHSCOPE_AVAILABLE
