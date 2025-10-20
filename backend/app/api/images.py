"""Image analysis API endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.base import get_db
from app.llm.vision_client_cached import extract_requirements_from_image_async, is_vl_available
from app.schemas.image import ImageAnalysisRequest, ImageAnalysisResponse
from app.services.documents import save_upload_file
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: Annotated[UploadFile, File()],
    db: AsyncSession = Depends(get_db)
) -> ImageAnalysisResponse:
    """
    分析上传的图片，提取需求文本。

    这个接口专门用于快速预览图片中的需求内容，不会创建完整的分析会话。

    Args:
        file: 上传的图片文件
        db: 数据库会话

    Returns:
        ImageAnalysisResponse: 包含提取的需求文本和元数据
    """
    # 检查VL模型是否可用
    if not is_vl_available():
        raise HTTPException(
            status_code=503,
            detail="Vision-Language model is not available. Please check dashscope installation."
        )

    # 获取VL配置
    vl_config = settings.get_vl_config()
    if not vl_config["enabled"]:
        raise HTTPException(
            status_code=503,
            detail="Vision-Language model is disabled in configuration."
        )

    if not vl_config["api_key"]:
        raise HTTPException(
            status_code=503,
            detail="API key is not configured for Vision-Language model."
        )

    # 验证文件类型
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg", "image/bmp"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}. Supported types: PNG, JPEG, JPG, BMP"
        )

    # 验证文件大小
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.max_file_size} bytes"
        )

    try:
        # 保存上传的文件到临时目录
        saved_path = await save_upload_file(file)

        logger.info(f"Analyzing image: {saved_path}")

        # 使用VL模型提取需求（带缓存）
        extracted_text = await extract_requirements_from_image_async(
            image_path=saved_path,
            api_key=vl_config["api_key"],
            model=vl_config["model"],
            base_url=vl_config.get("base_url"),
            use_cache=True,
            cache_ttl=7 * 24 * 60 * 60  # 7天缓存
        )

        # 清理临时文件
        try:
            Path(saved_path).unlink()
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {saved_path}: {e}")

        return ImageAnalysisResponse(
            success=True,
            message="Successfully extracted requirements from image",
            extracted_text=extracted_text,
            text_length=len(extracted_text),
            model_used=vl_config["model"],
            filename=file.filename
        )

    except Exception as e:
        logger.exception(f"Failed to analyze image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze image: {str(e)}"
        )