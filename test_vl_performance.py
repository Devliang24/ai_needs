#!/usr/bin/env python3
"""VL模型文本识别性能测试 - 测量识别时间"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/opt/ai_needs/backend')

from app.config import settings
from app.llm.vision_client import extract_requirements_from_image, is_vl_available


def test_vl_recognition_performance():
    """测试VL模型识别性能"""

    print("=" * 80)
    print("VL模型文本识别性能测试")
    print("=" * 80)

    # 测试图片
    test_image = Path("/opt/ai_needs/Snipaste_2025-10-20_14-02-25.png")

    if not test_image.exists():
        print(f"❌ 测试图片不存在: {test_image}")
        return

    # 获取图片信息
    file_size = test_image.stat().st_size
    print(f"\n📷 测试图片信息:")
    print(f"   文件名: {test_image.name}")
    print(f"   大小: {file_size:,} bytes ({file_size/1024:.2f} KB)")

    # 检查VL配置
    print(f"\n⚙️  VL模型配置:")
    vl_config = settings.get_vl_config()
    print(f"   模型: {vl_config['model']}")
    print(f"   启用状态: {vl_config['enabled']}")
    print(f"   API配置: {'已设置' if vl_config['api_key'] else '未设置'}")
    print(f"   DashScope可用: {is_vl_available()}")

    if not vl_config['enabled'] or not vl_config['api_key']:
        print("\n❌ VL模型未正确配置，无法测试")
        return

    print("\n" + "=" * 80)
    print("开始性能测试...")
    print("=" * 80)

    # 测试1: 首次识别（无缓存）
    print("\n📊 测试1: 首次识别（调用VL模型API）")
    print("-" * 80)

    try:
        start_time = time.time()
        print(f"⏱️  开始时间: {time.strftime('%H:%M:%S', time.localtime(start_time))}")

        extracted_text = extract_requirements_from_image(
            image_path=test_image,
            api_key=vl_config['api_key'],
            model=vl_config['model'],
            base_url=vl_config.get('base_url')
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"⏱️  结束时间: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
        print(f"⏱️  耗时: {elapsed_time:.3f} 秒")

        if extracted_text:
            text_length = len(extracted_text)
            print(f"\n✅ 识别成功!")
            print(f"   提取文本长度: {text_length:,} 字符")
            print(f"   处理速度: {text_length/elapsed_time:.2f} 字符/秒")
            print(f"   文件处理速度: {file_size/elapsed_time/1024:.2f} KB/秒")

            # 显示部分内容
            print(f"\n📝 提取内容预览（前200字符）:")
            print("-" * 80)
            print(extracted_text[:200])
            print("...")
            print("-" * 80)

            # 测试2: 使用缓存的识别（如果有缓存功能）
            print("\n📊 测试2: 重复识别（测试缓存效果）")
            print("-" * 80)

            try:
                start_time2 = time.time()
                print(f"⏱️  开始时间: {time.strftime('%H:%M:%S', time.localtime(start_time2))}")

                extracted_text2 = extract_requirements_from_image(
                    image_path=test_image,
                    api_key=vl_config['api_key'],
                    model=vl_config['model'],
                    base_url=vl_config.get('base_url')
                )

                end_time2 = time.time()
                elapsed_time2 = end_time2 - start_time2

                print(f"⏱️  结束时间: {time.strftime('%H:%M:%S', time.localtime(end_time2))}")
                print(f"⏱️  耗时: {elapsed_time2:.3f} 秒")

                if elapsed_time2 < elapsed_time * 0.5:
                    speedup = elapsed_time / elapsed_time2
                    print(f"\n✅ 检测到缓存效果!")
                    print(f"   加速比: {speedup:.2f}x")
                    print(f"   时间节省: {(elapsed_time - elapsed_time2):.3f} 秒 ({(1-elapsed_time2/elapsed_time)*100:.1f}%)")
                else:
                    print(f"\n⚠️  未检测到明显的缓存效果")
                    print(f"   可能原因: 缓存未启用或首次调用")

            except Exception as e:
                print(f"⚠️  第二次测试失败: {e}")

            # 性能统计总结
            print("\n" + "=" * 80)
            print("📊 性能统计总结")
            print("=" * 80)
            print(f"测试图片: {test_image.name}")
            print(f"文件大小: {file_size/1024:.2f} KB")
            print(f"VL模型: {vl_config['model']}")
            print(f"\n首次识别:")
            print(f"  ⏱️  耗时: {elapsed_time:.3f} 秒")
            print(f"  📝 文本长度: {text_length:,} 字符")
            print(f"  ⚡ 处理速度: {text_length/elapsed_time:.2f} 字符/秒")

            # 性能评级
            print(f"\n⭐ 性能评级:")
            if elapsed_time < 5:
                rating = "优秀 (< 5秒)"
            elif elapsed_time < 15:
                rating = "良好 (5-15秒)"
            elif elapsed_time < 30:
                rating = "一般 (15-30秒)"
            else:
                rating = "较慢 (> 30秒)"
            print(f"   {rating}")

            # 建议
            print(f"\n💡 建议:")
            if elapsed_time < 15:
                print(f"   ✅ 识别速度符合预期，满足生产环境要求")
            elif elapsed_time < 30:
                print(f"   ⚠️  识别速度可接受，建议启用缓存优化")
            else:
                print(f"   ⚠️  识别速度较慢，建议:")
                print(f"      - 检查网络连接")
                print(f"      - 考虑使用更快的VL模型")
                print(f"      - 启用缓存机制")

            return {
                'success': True,
                'elapsed_time': elapsed_time,
                'text_length': text_length,
                'file_size': file_size,
                'model': vl_config['model']
            }
        else:
            print(f"❌ 未提取到文本")
            return {'success': False}

    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\n❌ 识别失败")
        print(f"   错误: {e}")
        print(f"   已耗时: {elapsed_time:.3f} 秒")

        import traceback
        print(f"\n详细错误信息:")
        traceback.print_exc()

        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    print("\n")
    result = test_vl_recognition_performance()

    print("\n" + "=" * 80)
    if result and result.get('success'):
        print("✅ 测试完成!")
    else:
        print("❌ 测试失败，请检查配置和错误信息")
    print("=" * 80)
    print("\n")
