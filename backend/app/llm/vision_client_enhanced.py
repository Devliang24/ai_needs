"""Enhanced Vision-Language model client with retry logic and better error handling."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional
import time

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


class VLExtractionError(Exception):
    """VL模型提取错误的自定义异常."""
    pass


class VLRateLimitError(VLExtractionError):
    """VL模型API限流错误."""
    pass


class VLAuthError(VLExtractionError):
    """VL模型认证错误."""
    pass


async def extract_requirements_with_retry(
    image_path: str | Path,
    api_key: str | None = None,
    model: str = "qwen-vl-plus",
    base_url: str | None = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    use_cache: bool = True,
    cache_ttl: int = 7 * 24 * 60 * 60
) -> str:
    """
    使用VL模型从图片中提取需求信息，带有重试机制和增强的错误处理。

    Args:
        image_path: 图片文件路径
        api_key: DashScope API Key
        model: VL 模型名称
        base_url: 可选的 API base URL
        max_retries: 最大重试次数
        initial_delay: 初始重试延迟（秒）
        max_delay: 最大重试延迟（秒）
        exponential_base: 指数退避基数
        use_cache: 是否使用缓存
        cache_ttl: 缓存时间（秒）

    Returns:
        提取的需求文本

    Raises:
        VLExtractionError: VL模型相关错误
        FileNotFoundError: 图片文件不存在
        ValueError: 参数错误
    """
    if not DASHSCOPE_AVAILABLE:
        raise ImportError("dashscope package is not installed. Please install it with: pip install dashscope>=1.24.6")

    if not api_key:
        raise VLAuthError("API key is required for VL model")

    image_path = Path(image_path).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # 验证图片文件大小
    file_size_mb = image_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 10:
        logger.warning(f"Image file size ({file_size_mb:.2f} MB) exceeds recommended limit (10 MB)")

    # 尝试从缓存获取
    if use_cache:
        try:
            from app.cache.image_cache import get_cached_extraction, cache_extraction

            cached_text = await get_cached_extraction(image_path, model)
            if cached_text:
                logger.info(f"Using cached extraction for {image_path.name}")
                return cached_text
        except Exception as e:
            logger.warning(f"Cache check failed, proceeding without cache: {e}")

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

    # 重试逻辑
    last_error = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            call_kwargs: dict[str, Any] = {
                "model": model,
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

                # 处理不同格式的返回值
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and 'text' in content[0]:
                        text_content = content[0]['text']
                        logger.info(f"Extracted text from list format, length: {len(text_content)} characters")
                    else:
                        text_content = str(content)
                        logger.warning(f"Unexpected list format, converting to string")
                elif isinstance(content, str):
                    text_content = content
                    logger.info(f"Successfully extracted {len(text_content)} characters")
                else:
                    text_content = str(content)
                    logger.warning(f"Unexpected content type: {type(content)}")

                # 验证提取结果
                if not text_content or len(text_content.strip()) < 10:
                    raise VLExtractionError("Extracted text is too short or empty")

                # 缓存成功的结果
                if use_cache:
                    try:
                        from app.cache.image_cache import cache_extraction
                        await cache_extraction(image_path, model, text_content, cache_ttl)
                    except Exception as e:
                        logger.warning(f"Failed to cache result: {e}")

                return text_content

            # 处理错误响应
            elif response.status_code == 429:  # Rate limit
                raise VLRateLimitError(f"Rate limit exceeded: {response.message}")
            elif response.status_code == 401:  # Authentication
                raise VLAuthError(f"Authentication failed: {response.message}")
            else:
                error_msg = (
                    f"VL model call failed - "
                    f"Status: {response.status_code}, "
                    f"Error: {response.code}, "
                    f"Message: {response.message}"
                )
                raise VLExtractionError(error_msg)

        except VLAuthError:
            # 认证错误不重试
            raise

        except (VLRateLimitError, VLExtractionError, Exception) as e:
            last_error = e

            if attempt < max_retries:
                # 计算下次重试延迟
                if isinstance(e, VLRateLimitError):
                    # 限流错误使用更长的延迟
                    delay = min(delay * exponential_base * 2, max_delay)
                else:
                    delay = min(delay * exponential_base, max_delay)

                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
                break

    # 所有重试都失败
    if last_error:
        raise VLExtractionError(f"Failed after {max_retries + 1} attempts: {last_error}")
    else:
        raise VLExtractionError("Unknown error occurred during extraction")


async def extract_with_fallback(
    image_path: str | Path,
    vl_config: dict,
    use_ocr_fallback: bool = True
) -> tuple[str, str]:
    """
    使用VL模型提取文本，如果失败则尝试OCR降级。

    Args:
        image_path: 图片文件路径
        vl_config: VL模型配置
        use_ocr_fallback: 是否使用OCR作为降级方案

    Returns:
        (提取的文本, 使用的方法)
    """
    # 首先尝试VL模型
    try:
        text = await extract_requirements_with_retry(
            image_path=image_path,
            api_key=vl_config["api_key"],
            model=vl_config["model"],
            base_url=vl_config.get("base_url"),
            use_cache=True
        )
        return text, "vl_model"

    except VLAuthError:
        # 认证错误直接抛出
        raise

    except Exception as e:
        logger.error(f"VL model extraction failed: {e}")

        if use_ocr_fallback:
            logger.info("Attempting OCR fallback...")
            try:
                # 这里可以集成其他OCR服务
                # 例如：Tesseract, PaddleOCR, 阿里云OCR等
                # 暂时返回错误提示
                return f"[VL模型失败，OCR功能待实现] 原始错误: {e}", "ocr_fallback"
            except Exception as ocr_error:
                logger.error(f"OCR fallback also failed: {ocr_error}")
                raise VLExtractionError(f"Both VL and OCR failed: {e}")
        else:
            raise


def is_vl_available() -> bool:
    """检查 VL 模型是否可用."""
    return DASHSCOPE_AVAILABLE


async def validate_vl_config(config: dict) -> tuple[bool, str]:
    """
    验证VL配置是否正确。

    Args:
        config: VL配置字典

    Returns:
        (是否有效, 错误信息)
    """
    if not config.get("enabled"):
        return False, "VL model is disabled in configuration"

    if not config.get("api_key"):
        return False, "API key is not configured"

    if not is_vl_available():
        return False, "DashScope library is not available"

    # 可以尝试一个简单的API调用来验证密钥
    # 这里暂时只做基础检查
    return True, ""