"""Multimodal VL model client for requirement analysis with vision understanding."""

from __future__ import annotations

import asyncio
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
    logger.warning("dashscope not available, multimodal analysis will be disabled")


MULTIMODAL_ANALYSIS_PROMPT = """请仔细分析这份需求文档（图片/PDF），并提取结构化信息。

**分析要求：**
1. **功能模块**：识别文档中的所有功能模块，提取实际模块名称（不使用"模块1"等占位符）
2. **业务场景**：描述每个模块的具体业务场景和用户故事
3. **业务规则**：提取约束条件、验证规则、性能指标等
4. **视觉理解**（充分利用图像的视觉信息）：
   - 如果是流程图，请描述完整的流程步骤、分支条件和循环
   - 如果是UI原型/界面截图，请描述页面布局、控件类型（按钮、输入框、下拉框等）和交互方式
   - 如果是架构图/系统图，请描述系统组件、模块划分和它们之间的关系
   - 如果包含表格，请完整保留表格的行列结构和内容
   - 注意箭头、连线、颜色、图标等视觉元素的含义

**输出格式（严格JSON格式）：**
```json
{
  "modules": [
    {
      "name": "实际功能模块名（如：用户登录模块、订单管理模块）",
      "scenarios": [
        {"description": "具体业务场景描述（如：用户通过手机号+验证码登录）"}
      ],
      "rules": [
        {"description": "具体业务规则描述（如：验证码有效期5分钟，最多重发3次）"}
      ]
    }
  ],
  "risks": [
    {"description": "测试风险点描述"}
  ]
}
```

**重要提示：**
- 必须基于图片的**完整视觉信息**进行分析
- 提取文档中的**实际内容**，避免使用泛化占位符
- 如果图片包含多页或多个部分，请完整分析所有内容
- 输出必须是有效的JSON格式，不要添加markdown代码块标记
"""


class MultimodalAnalysisError(Exception):
    """多模态分析错误."""
    pass


async def analyze_with_multimodal(
    file_path: str | Path,
    api_key: str,
    model: str = "qwen3-vl-flash-2025-10-15",
    base_url: str | None = None,
    max_retries: int = 2,
) -> str:
    """使用多模态VL模型直接分析图片/PDF/DOCX中的需求信息.

    根据文件类型自动选择最佳模型：
    - PDF/DOCX: qwen-vl-ocr-latest (专业文档OCR)
    - 图片: qwen3-vl-flash-2025-10-15 (快速图片分析)

    Args:
        file_path: 文件路径（图片、PDF或DOCX）
        api_key: API密钥
        model: 默认模型名称（用于图片文件）
        base_url: API base URL
        max_retries: 最大重试次数

    Returns:
        分析结果（JSON格式字符串）

    Raises:
        MultimodalAnalysisError: 分析失败
        FileNotFoundError: 文件不存在
    """
    if not DASHSCOPE_AVAILABLE:
        raise ImportError("dashscope package is not installed")

    if not api_key:
        raise MultimodalAnalysisError("API key is required for multimodal analysis")

    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 根据文件类型自动选择最佳模型
    suffix = file_path.suffix.lower()

    if suffix in {'.pdf', '.docx', '.doc'}:
        # PDF/DOCX 使用专业 OCR 模型
        actual_model = "qwen-vl-ocr-latest"
        logger.info(f"检测到文档文件 {suffix}，使用 OCR 模型: {actual_model} 分析文件: {file_path.name}")
    elif suffix in {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}:
        # 图片使用快速模型
        actual_model = model
        logger.info(f"检测到图片文件 {suffix}，使用图片模型: {actual_model} 分析文件: {file_path.name}")
    else:
        # 其他文件类型使用默认模型
        actual_model = model
        logger.warning(f"未知文件类型 {suffix}，使用默认模型: {actual_model} 分析文件: {file_path.name}")

    # 构建多模态消息（直接使用原始文件，不需要转换）
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{file_path}"},
                {"text": MULTIMODAL_ANALYSIS_PROMPT}
            ]
        }
    ]

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            call_kwargs: dict[str, Any] = {
                "model": actual_model,
                "messages": messages,
                "result_format": "message",
                "api_key": api_key,
            }

            if base_url:
                call_kwargs["base_url"] = base_url

            # 在异步上下文中运行同步调用
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: MultiModalConversation.call(**call_kwargs)
            )

            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0]["message"]["content"]

                # 提取文本内容
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and 'text' in content[0]:
                        text_content = content[0]['text']
                        logger.info(f"多模态分析成功，返回内容长度: {len(text_content)} 字符")
                        return text_content
                    else:
                        logger.warning(f"Unexpected list format: {content}")
                        return str(content)
                elif isinstance(content, str):
                    logger.info(f"多模态分析成功，返回内容长度: {len(content)} 字符")
                    return content
                else:
                    logger.warning(f"Unexpected content type: {type(content)}")
                    return str(content)

            # 处理错误响应
            elif response.status_code == 401:
                raise MultimodalAnalysisError(f"Authentication failed: {response.message}")
            else:
                error_msg = (
                    f"Multimodal analysis failed - "
                    f"Status: {response.status_code}, "
                    f"Error: {response.code}, "
                    f"Message: {response.message}"
                )
                raise MultimodalAnalysisError(error_msg)

        except MultimodalAnalysisError as e:
            # 认证错误不重试
            if "Authentication failed" in str(e):
                raise
            last_error = e
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
                break

        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error during multimodal analysis: {e}", exc_info=True)
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                break

    # 所有重试都失败
    if last_error:
        raise MultimodalAnalysisError(f"Failed after {max_retries + 1} attempts: {last_error}")
    else:
        raise MultimodalAnalysisError("Unknown error occurred during multimodal analysis")


def is_multimodal_available() -> bool:
    """检查多模态模型是否可用."""
    return DASHSCOPE_AVAILABLE
