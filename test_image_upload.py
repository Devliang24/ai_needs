#!/usr/bin/env python3
"""测试图片上传和VL模型文本提取功能的脚本"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/opt/ai_needs/backend')

from app.config import settings
from app.llm.vision_client import extract_requirements_from_image, is_vl_available
from app.parsers.text_extractor import extract_text


def test_vl_config():
    """测试VL模型配置"""
    print("=" * 60)
    print("1. 检查VL模型配置")
    print("-" * 60)

    vl_config = settings.get_vl_config()
    print(f"VL模型启用状态: {vl_config['enabled']}")
    print(f"VL模型名称: {vl_config['model']}")
    print(f"API密钥设置: {'已设置' if vl_config['api_key'] else '未设置'}")
    print(f"Base URL: {vl_config.get('base_url') or '使用默认'}")

    # 检查dashscope是否可用
    print(f"DashScope库可用: {is_vl_available()}")

    if not vl_config['enabled']:
        print("⚠️ VL模型未启用，请设置环境变量 VL_ENABLED=true")
        return False

    if not vl_config['api_key']:
        print("⚠️ API密钥未设置，请设置环境变量 QWEN_API_KEY 或 VL_API_KEY")
        return False

    if not is_vl_available():
        print("⚠️ DashScope库不可用，请安装: pip install dashscope>=1.24.6")
        return False

    print("✅ VL模型配置检查通过")
    return True


def test_image_extraction(image_path: str):
    """测试图片文本提取"""
    print("\n" + "=" * 60)
    print("2. 测试图片文本提取")
    print("-" * 60)

    image_file = Path(image_path)
    if not image_file.exists():
        print(f"❌ 图片文件不存在: {image_path}")
        return None

    print(f"测试图片: {image_file.name}")
    print(f"文件大小: {image_file.stat().st_size / 1024:.2f} KB")

    try:
        # 直接使用VL模型提取
        print("\n使用VL模型提取文本...")
        vl_config = settings.get_vl_config()

        extracted_text = extract_requirements_from_image(
            image_path=image_file,
            api_key=vl_config["api_key"],
            model=vl_config["model"],
            base_url=vl_config.get("base_url")
        )

        if extracted_text:
            print(f"✅ 成功提取文本，长度: {len(extracted_text)} 字符")
            print("\n提取内容预览（前500字符）:")
            print("-" * 40)
            print(extracted_text[:500])
            print("-" * 40)
            return extracted_text
        else:
            print("❌ 未能提取到文本")
            return None

    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return None


def test_text_extractor(image_path: str):
    """测试文本提取器的图片处理"""
    print("\n" + "=" * 60)
    print("3. 测试文本提取器集成")
    print("-" * 60)

    image_file = Path(image_path)
    if not image_file.exists():
        print(f"❌ 图片文件不存在: {image_path}")
        return None

    try:
        print("使用文本提取器处理图片...")
        extracted_text = extract_text(
            path=image_file,
            limit=10000,
            original_name=image_file.name
        )

        if extracted_text and not extracted_text.startswith("文档"):
            print(f"✅ 文本提取器成功处理，长度: {len(extracted_text)} 字符")
            print("\n提取内容预览（前500字符）:")
            print("-" * 40)
            print(extracted_text[:500])
            print("-" * 40)
            return extracted_text
        else:
            print("❌ 文本提取器未能处理图片")
            return None

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return None


async def test_upload_api():
    """测试上传API接口"""
    print("\n" + "=" * 60)
    print("4. 测试上传API接口")
    print("-" * 60)

    import aiohttp
    import aiofiles

    test_image = "/opt/ai_needs/Snipaste_2025-10-20_14-02-25.png"
    if not Path(test_image).exists():
        print(f"❌ 测试图片不存在: {test_image}")
        return None

    try:
        # 假设后端运行在默认端口
        api_url = "http://localhost:8000/api/uploads"

        async with aiofiles.open(test_image, 'rb') as f:
            file_data = await f.read()

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file',
                          file_data,
                          filename='test_requirements.png',
                          content_type='image/png')

            print(f"上传图片到: {api_url}")
            async with session.post(api_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 上传成功")
                    print(f"文档ID: {result.get('document', {}).get('id')}")
                    print(f"是否重复: {result.get('is_duplicate', False)}")
                    return result
                else:
                    text = await response.text()
                    print(f"❌ 上传失败: {response.status}")
                    print(f"错误信息: {text}")
                    return None

    except aiohttp.ClientError as e:
        print(f"⚠️ 无法连接到API服务器: {e}")
        print("请确保后端服务正在运行 (cd backend && python -m app.main)")
        return None
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return None


def main():
    """主测试函数"""
    print("🔍 AI需求分析系统 - 图片上传与VL模型测试")
    print("=" * 60)

    # 测试图片路径
    test_image = "/opt/ai_needs/Snipaste_2025-10-20_14-02-25.png"

    # 1. 检查配置
    if not test_vl_config():
        print("\n❌ 配置检查未通过，请先配置环境变量")
        return

    # 2. 测试VL模型直接提取
    extracted_text = test_image_extraction(test_image)
    if not extracted_text:
        print("\n⚠️ VL模型提取测试失败")

    # 3. 测试文本提取器集成
    extractor_text = test_text_extractor(test_image)
    if not extractor_text:
        print("\n⚠️ 文本提取器测试失败")

    # 4. 测试上传API（可选）
    print("\n" + "=" * 60)
    print("是否测试上传API接口？（需要后端服务运行）")
    user_input = input("输入 'y' 测试API，其他键跳过: ").strip().lower()

    if user_input == 'y':
        asyncio.run(test_upload_api())

    print("\n" + "=" * 60)
    print("测试完成！")

    if extracted_text:
        print("\n✅ VL模型功能正常，可以处理图片需求文档")
        print("下一步建议：")
        print("1. 启动后端服务测试完整工作流")
        print("2. 创建会话并使用图片进行需求分析")
        print("3. 验证多智能体协作生成测试用例")
    else:
        print("\n⚠️ 需要检查和修复VL模型集成")


if __name__ == "__main__":
    main()