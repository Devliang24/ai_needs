"""Test VL model integration for image requirement extraction."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


def test_vl_client_import():
    """Test that VL client can be imported."""
    from app.llm.vision_client import is_vl_available, extract_requirements_from_image

    # 检查函数是否可导入
    assert callable(is_vl_available)
    assert callable(extract_requirements_from_image)


def test_vl_config():
    """Test VL configuration."""
    from app.config import settings

    vl_config = settings.get_vl_config()

    # 检查配置字段
    assert "enabled" in vl_config
    assert "model" in vl_config
    assert "api_key" in vl_config
    assert vl_config["model"] == "qwen-vl-max"  # 默认模型


@patch('app.llm.vision_client.DASHSCOPE_AVAILABLE', True)
@patch('app.llm.vision_client.MultiModalConversation')
def test_extract_requirements_from_image_success(mock_mm_conv):
    """Test successful image requirement extraction."""
    from app.llm.vision_client import extract_requirements_from_image
    from http import HTTPStatus

    # 创建临时测试图片
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        test_image_path = f.name
        # 写入一个简单的 1x1 像素 PNG
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')

    try:
        # Mock 成功响应
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.output.choices = [
            {"message": {"content": "这是测试需求：用户登录功能"}}
        ]
        mock_mm_conv.call.return_value = mock_response

        # 调用提取函数
        result = extract_requirements_from_image(
            image_path=test_image_path,
            api_key="test-api-key",
            model="qwen-vl-max"
        )

        # 验证结果
        assert isinstance(result, str)
        assert len(result) > 0
        assert "测试需求" in result

        # 验证 API 被正确调用
        mock_mm_conv.call.assert_called_once()
        call_args = mock_mm_conv.call.call_args
        assert call_args[1]["model"] == "qwen-vl-max"
        assert call_args[1]["api_key"] == "test-api-key"

    finally:
        # 清理测试文件
        Path(test_image_path).unlink(missing_ok=True)


@patch('app.llm.vision_client.DASHSCOPE_AVAILABLE', False)
def test_extract_requirements_from_image_dashscope_unavailable():
    """Test handling when dashscope is not available."""
    from app.llm.vision_client import extract_requirements_from_image

    with pytest.raises(ImportError, match="dashscope package is not installed"):
        extract_requirements_from_image(
            image_path="/fake/path.png",
            api_key="test-key"
        )


def test_extract_requirements_from_image_no_api_key():
    """Test handling when API key is missing."""
    from app.llm.vision_client import extract_requirements_from_image

    with pytest.raises(ValueError, match="api_key is required"):
        extract_requirements_from_image(
            image_path="/fake/path.png",
            api_key=None
        )


def test_extract_requirements_from_image_file_not_found():
    """Test handling when image file doesn't exist."""
    from app.llm.vision_client import extract_requirements_from_image

    with pytest.raises(FileNotFoundError):
        extract_requirements_from_image(
            image_path="/non/existent/path.png",
            api_key="test-key"
        )


@patch('app.parsers.text_extractor.is_vl_available', return_value=True)
@patch('app.parsers.text_extractor.extract_requirements_from_image')
def test_text_extractor_uses_vl_for_images(mock_extract, mock_is_available):
    """Test that text extractor uses VL model for images."""
    from app.parsers.text_extractor import extract_text
    import tempfile

    # 创建临时图片文件
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        test_image_path = f.name
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')

    try:
        # Mock VL 提取结果
        mock_extract.return_value = "VL 提取的需求内容"

        # 调用 extract_text
        result = extract_text(test_image_path, original_name="test.png")

        # 验证使用了 VL 模型
        assert result == "VL 提取的需求内容"
        mock_extract.assert_called_once()

    finally:
        Path(test_image_path).unlink(missing_ok=True)
