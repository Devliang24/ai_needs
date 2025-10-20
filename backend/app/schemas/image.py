"""Schemas for image analysis."""

from pydantic import BaseModel, Field
from typing import Optional


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis (file upload handled separately)."""
    pass


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis."""
    success: bool = Field(description="Whether the analysis was successful")
    message: str = Field(description="Status message")
    extracted_text: str = Field(description="Extracted requirement text from the image")
    text_length: int = Field(description="Length of extracted text in characters")
    model_used: str = Field(description="VL model used for extraction")
    filename: Optional[str] = Field(None, description="Original filename")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Successfully extracted requirements from image",
                "extracted_text": "1. 后端接收设备主要功能...",
                "text_length": 1887,
                "model_used": "qwen-vl-plus",
                "filename": "requirements.png"
            }
        }
    }