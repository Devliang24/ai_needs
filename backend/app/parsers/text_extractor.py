"""Utility helpers to extract plain text from various document types."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no cover - fallback when PyMuPDF missing
    fitz = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import docx  # type: ignore
except Exception:  # pragma: no cover
    docx = None  # type: ignore


def _read_pdf(path: Path, limit: int) -> str:
    if fitz is None:
        return ""
    text_parts: list[str] = []
    with fitz.open(path) as document:  # type: ignore[arg-type]
        for page in document:
            text_parts.append(page.get_text())
            if len("\n".join(text_parts)) >= limit:
                break
    return "\n".join(text_parts)


def _read_docx(path: Path, limit: int) -> str:
    if docx is None:
        return ""
    document = docx.Document(path)  # type: ignore[call-arg]
    text_parts = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(text_parts)[:limit]


def _read_image_with_vl(path: Path, limit: int) -> str:
    """使用 VL 模型从图片中提取需求信息."""
    try:
        from app.config import settings
        from app.llm.vision_client import extract_requirements_from_image, is_vl_available

        # 检查 VL 模型是否可用
        if not is_vl_available():
            logger.warning("VL model not available, skipping image processing")
            return ""

        # 获取 VL 配置
        vl_config = settings.get_vl_config()
        if not vl_config["enabled"]:
            logger.info("VL model disabled in config, skipping image processing")
            return ""

        # 使用 VL 模型提取需求
        text = extract_requirements_from_image(
            image_path=path,
            api_key=vl_config["api_key"],
            model=vl_config["model"],
            base_url=vl_config.get("base_url"),
        )
        return text[:limit]

    except Exception as e:
        logger.exception(f"Failed to extract image with VL model: {e}")
        return ""


def extract_text(path: str | Path, limit: int = 4000, original_name: str | None = None) -> str:
    file_path = Path(path)

    # 优先从original_name获取文件扩展名,用于识别存储路径中没有扩展名的文件
    if original_name:
        suffix = Path(original_name).suffix.lower()
    else:
        suffix = file_path.suffix.lower()

    # 对于图片文件，只使用VL模型，不回退到文本读取
    if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
        try:
            text = _read_image_with_vl(file_path, limit)
            if text:
                return text
            # VL模型失败或返回空，返回占位符而不是读取二进制
            logger.warning(f"VL model failed to extract text from image: {file_path.name}")
            return f"图片 {original_name or file_path.name} 已上传，等待 VL 模型处理。"
        except Exception as e:
            logger.exception(f"Failed to process image {file_path.name}: {e}")
            return f"图片 {original_name or file_path.name} 处理失败，请检查 VL 模型配置。"

    # 其他文件类型的处理
    try:
        if suffix in {".txt", ".md", ".json", ".log"}:
            return file_path.read_text("utf-8", errors="ignore")[:limit]
        if suffix == ".pdf":
            text = _read_pdf(file_path, limit)
            if text:
                return text[:limit]
        if suffix == ".docx":
            text = _read_docx(file_path, limit)
            if text:
                return text
    except Exception:  # pragma: no cover - fall back to text read
        pass

    # Fallback: 尝试作为文本文件读取（仅用于未知文本格式）
    try:
        return file_path.read_text("utf-8", errors="ignore")[:limit]
    except Exception:  # pragma: no cover - binary fallback
        return f"文档 {original_name or file_path.name} 已上传，请在后端解析。"

