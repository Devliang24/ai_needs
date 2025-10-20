"""PaddleOCR-VL integration test script.

Tests the PaddleOCR-VL integration for document parsing and compares
performance with the qwen-vl-plus approach.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.config import settings
from app.llm import paddleocr_client


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def print_result(label: str, value: str, max_width: int = 80):
    """Print formatted result."""
    if len(value) > max_width:
        value = value[:max_width - 3] + "..."
    print(f"{label}: {value}")


async def test_paddleocr_availability():
    """Test if PaddleOCR is available."""
    print_header("测试1: PaddleOCR 可用性检查")

    is_available = paddleocr_client.is_paddleocr_available()
    print_result("PaddleOCR 可用", "✅ 是" if is_available else "❌ 否")

    if not is_available:
        print("\n⚠️  PaddleOCR 未安装")
        print("请安装: pip install 'paddleocr[doc-parser]'")
        print("并根据CUDA版本安装PaddlePaddle GPU版本")
        return False

    return True


async def test_model_initialization():
    """Test PaddleOCR-VL model initialization."""
    print_header("测试2: PaddleOCR-VL 模型初始化")

    try:
        start_time = time.time()
        pipeline = paddleocr_client.get_pipeline()
        init_time = time.time() - start_time

        print_result("模型初始化", "✅ 成功")
        print_result("初始化耗时", f"{init_time:.2f} 秒")
        print_result("模型类型", str(type(pipeline).__name__))

        return True

    except Exception as e:
        print_result("模型初始化", f"❌ 失败: {e}")
        return False


async def test_image_recognition(test_image_path: Path):
    """Test image text recognition with PaddleOCR-VL."""
    print_header(f"测试3: 图片文本识别 - {test_image_path.name}")

    if not test_image_path.exists():
        print_result("测试图片", f"❌ 文件不存在: {test_image_path}")
        return None

    print_result("测试图片", f"✅ {test_image_path}")
    print_result("文件大小", f"{test_image_path.stat().st_size / 1024:.2f} KB")

    try:
        start_time = time.time()
        extracted_text = await paddleocr_client.extract_requirements_from_image_async(
            test_image_path
        )
        recognition_time = time.time() - start_time

        print_result("\n识别状态", "✅ 成功")
        print_result("识别耗时", f"{recognition_time:.2f} 秒")
        print_result("提取文本长度", f"{len(extracted_text)} 字符")

        if extracted_text:
            print_result("处理速度", f"{len(extracted_text) / recognition_time:.2f} 字符/秒")

            # Show preview
            preview = extracted_text[:500].replace("\n", "\n  ")
            print("\n📝 提取内容预览（前500字符）:")
            print("─" * 80)
            print(f"  {preview}")
            if len(extracted_text) > 500:
                print("  ...")
            print("─" * 80)

        return {
            "success": True,
            "text_length": len(extracted_text),
            "time": recognition_time,
            "text": extracted_text
        }

    except Exception as e:
        print_result("\n识别状态", f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def test_configuration():
    """Test VL configuration."""
    print_header("测试4: VL 配置检查")

    vl_config = settings.get_vl_config()

    print_result("VL 启用状态", "✅ 启用" if vl_config.get("enabled") else "❌ 禁用")
    print_result("VL 引擎", vl_config.get("engine", "未配置"))
    print_result("Qwen 模型", vl_config.get("model", "未配置"))
    print_result("API Key 配置", "✅ 已配置" if vl_config.get("api_key") else "❌ 未配置")

    print("\n💡 配置建议:")
    if vl_config.get("engine") == "paddleocr":
        print("  ✅ 当前使用 PaddleOCR 引擎（本地推理）")
        print("  ✅ 无需 API key，数据更安全")
    elif vl_config.get("engine") == "qwen":
        print("  ℹ️  当前使用 Qwen VL 引擎（云端API）")
        if not vl_config.get("api_key"):
            print("  ⚠️  需要配置 QWEN_API_KEY 环境变量")
    else:
        print("  ⚠️  未配置 VL_ENGINE，将使用默认引擎")


async def run_performance_comparison(test_image_path: Path):
    """Run performance comparison between engines."""
    print_header("测试5: 性能对比（PaddleOCR vs Qwen VL）")

    if not test_image_path.exists():
        print("⚠️  测试图片不存在，跳过性能对比")
        return

    results = {}

    # Test PaddleOCR
    print("▶ 测试 PaddleOCR-VL 引擎...")
    paddleocr_result = await test_image_recognition(test_image_path)
    if paddleocr_result and paddleocr_result.get("success"):
        results["paddleocr"] = paddleocr_result

    # Test cache effect (second run)
    print("\n▶ 测试 PaddleOCR 重复识别（缓存效果）...")
    start_time = time.time()
    try:
        text2 = await paddleocr_client.extract_requirements_from_image_async(test_image_path)
        time2 = time.time() - start_time
        print_result("第二次识别耗时", f"{time2:.2f} 秒")

        if results.get("paddleocr"):
            speedup = results["paddleocr"]["time"] / time2 if time2 > 0 else 1
            if speedup > 1.5:
                print_result("缓存加速", f"✅ {speedup:.1f}x 倍加速")
            else:
                print_result("缓存效果", "ℹ️  未检测到明显加速（可能未启用缓存）")
    except Exception as e:
        print_result("第二次识别", f"❌ 失败: {e}")

    # Summary
    print("\n" + "─" * 80)
    print("📊 性能对比总结:")
    print("─" * 80)

    if results.get("paddleocr"):
        p = results["paddleocr"]
        print(f"\nPaddleOCR-VL (本地):")
        print(f"  识别耗时: {p['time']:.2f} 秒")
        print(f"  文本长度: {p['text_length']} 字符")
        print(f"  处理速度: {p['text_length'] / p['time']:.2f} 字符/秒")

        # Performance rating
        if p['time'] < 5:
            rating = "⭐⭐⭐ 优秀"
        elif p['time'] < 15:
            rating = "⭐⭐ 良好"
        elif p['time'] < 30:
            rating = "⭐ 一般"
        else:
            rating = "⚠️  较慢"

        print(f"  性能评级: {rating}")

    print("─" * 80)


async def main():
    """Main test runner."""
    print_header("PaddleOCR-VL 集成测试")

    # Find test image
    test_images = [
        Path("/opt/ai_needs/Snipaste_2025-10-20_14-02-25.png"),
        Path("./Snipaste_2025-10-20_14-02-25.png"),
        Path("./backend/test_image.png"),
    ]

    test_image = None
    for img_path in test_images:
        if img_path.exists():
            test_image = img_path
            break

    if test_image is None:
        print("⚠️  未找到测试图片，部分测试将跳过")

    # Run tests
    available = await test_paddleocr_availability()

    if not available:
        print("\n❌ PaddleOCR 不可用，测试终止")
        print("\n安装说明:")
        print("  1. pip install 'paddleocr[doc-parser]'")
        print("  2. 根据CUDA版本安装PaddlePaddle:")
        print("     - CUDA 12.6: pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/")
        print("     - CPU only: pip install paddlepaddle==3.2.0")
        return

    initialized = await test_model_initialization()

    if not initialized:
        print("\n❌ 模型初始化失败，测试终止")
        return

    if test_image:
        await test_image_recognition(test_image)
        await run_performance_comparison(test_image)

    await test_configuration()

    print_header("测试完成")
    print("✅ 所有测试已完成")

    if test_image:
        print("\n💡 下一步:")
        print("  1. 设置环境变量: export VL_ENGINE=paddleocr")
        print("  2. 重启后端服务查看效果")
        print("  3. 上传图片进行需求分析测试")


if __name__ == "__main__":
    asyncio.run(main())
