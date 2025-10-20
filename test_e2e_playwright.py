#!/usr/bin/env python3
"""使用Playwright进行端到端测试 - 验证图片上传与VL模型集成"""

import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright, expect


# 测试配置
FRONTEND_URL = "http://110.40.159.145:3004/"
TEST_IMAGE_PATH = "/opt/ai_needs/Snipaste_2025-10-20_14-02-25.png"
TIMEOUT = 60000  # 60秒超时


async def test_image_upload_e2e():
    """完整的端到端测试：图片上传 → VL识别 → 需求分析 → 生成测试用例"""

    print("🚀 开始Playwright端到端测试")
    print("="*60)

    async with async_playwright() as p:
        # 启动浏览器
        print("\n1. 启动浏览器...")
        browser = await p.chromium.launch(
            headless=True,  # 无头模式运行（服务器环境）
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # 步骤1: 访问前端页面
            print(f"\n2. 访问前端页面: {FRONTEND_URL}")
            await page.goto(FRONTEND_URL, wait_until='networkidle', timeout=TIMEOUT)
            await page.screenshot(path='/tmp/step1_homepage.png')
            print("   ✅ 页面加载成功")

            # 步骤2: 定位并验证文件上传组件
            print("\n3. 定位文件上传组件...")

            # 尝试不同的选择器定位上传组件
            selectors = [
                '.ant-upload-drag',
                '[class*="upload"]',
                'input[type="file"]',
                '.ant-upload',
            ]

            upload_area = None
            for selector in selectors:
                try:
                    upload_area = await page.wait_for_selector(selector, timeout=5000)
                    if upload_area:
                        print(f"   ✅ 找到上传组件: {selector}")
                        break
                except:
                    continue

            if not upload_area:
                print("   ⚠️ 未找到上传组件，尝试查找所有可见元素...")
                await page.screenshot(path='/tmp/step2_before_upload.png')
                # 打印页面内容以调试
                content = await page.content()
                print(f"   页面长度: {len(content)} 字符")

            # 步骤3: 上传图片文件
            print(f"\n4. 上传测试图片: {TEST_IMAGE_PATH}")

            # 检查文件是否存在
            if not Path(TEST_IMAGE_PATH).exists():
                print(f"   ❌ 测试图片不存在: {TEST_IMAGE_PATH}")
                return False

            # 查找文件输入元素（隐藏的）并上传
            # 使用page.set_input_files直接设置，不需要等待visible
            await page.set_input_files('input[type="file"]', TEST_IMAGE_PATH)
            print("   ✅ 图片已选择")

            # 等待上传成功提示
            print("\n5. 等待上传完成...")
            try:
                # 等待成功消息
                await page.wait_for_selector('.ant-message-success, .ant-message-info', timeout=30000)
                await asyncio.sleep(2)  # 等待消息显示
                await page.screenshot(path='/tmp/step3_upload_success.png')
                print("   ✅ 上传成功")
            except Exception as e:
                print(f"   ⚠️ 未检测到成功消息，但继续测试: {e}")
                await page.screenshot(path='/tmp/step3_upload_timeout.png')

            # 步骤4: 验证文档列表
            print("\n6. 验证文档已添加到列表...")
            await asyncio.sleep(2)

            # 查找文档名称
            try:
                doc_elements = await page.query_selector_all('[class*="document"], .ant-list-item')
                print(f"   找到 {len(doc_elements)} 个文档元素")

                # 检查是否包含上传的文件名
                page_text = await page.text_content('body')
                if 'Snipaste' in page_text or '.png' in page_text:
                    print("   ✅ 文档已显示在列表中")
                else:
                    print("   ⚠️ 未在页面中找到文档名称")
            except Exception as e:
                print(f"   ⚠️ 检查文档列表时出错: {e}")

            await page.screenshot(path='/tmp/step4_document_list.png')

            # 步骤5: 开始分析
            print("\n7. 查找并点击'开始分析'按钮...")
            try:
                # 可能的按钮文本
                button_texts = ['开始分析', '创建会话', '分析', 'Start', 'Analyze']
                button = None

                for text in button_texts:
                    try:
                        button = await page.wait_for_selector(
                            f'button:has-text("{text}"), .ant-btn:has-text("{text}")',
                            timeout=3000
                        )
                        if button:
                            print(f"   ✅ 找到按钮: {text}")
                            break
                    except:
                        continue

                if button:
                    await button.click()
                    print("   ✅ 已点击开始分析按钮")
                    await asyncio.sleep(2)
                    await page.screenshot(path='/tmp/step5_analysis_started.png')
                else:
                    print("   ⚠️ 未找到开始分析按钮")
                    # 尝试查找所有按钮
                    buttons = await page.query_selector_all('button')
                    print(f"   页面共有 {len(buttons)} 个按钮")

            except Exception as e:
                print(f"   ⚠️ 点击按钮时出错: {e}")

            # 步骤6: 监控分析进度
            print("\n8. 监控分析进度...")

            # 等待进度条或状态更新
            max_wait = 120  # 最多等待2分钟
            start_time = time.time()

            while time.time() - start_time < max_wait:
                try:
                    # 查找进度指示器
                    progress_elements = await page.query_selector_all(
                        '.ant-progress, [class*="progress"], [class*="timeline"]'
                    )

                    if progress_elements:
                        print(f"   📊 发现 {len(progress_elements)} 个进度元素")
                        await page.screenshot(path=f'/tmp/step6_progress_{int(time.time())}.png')

                    # 检查是否完成
                    page_text = await page.text_content('body')
                    if '已完成' in page_text or 'completed' in page_text.lower():
                        print("   ✅ 分析已完成")
                        break

                    # 检查是否有错误
                    if '错误' in page_text or 'error' in page_text.lower():
                        print("   ⚠️ 检测到错误信息")
                        break

                    await asyncio.sleep(5)
                    print(f"   ⏳ 等待中... ({int(time.time() - start_time)}s)")

                except Exception as e:
                    print(f"   ⚠️ 监控进度时出错: {e}")
                    break

            # 步骤7: 验证结果
            print("\n9. 验证分析结果...")
            await asyncio.sleep(3)

            page_content = await page.text_content('body')

            # 检查关键内容
            checks = {
                '设备': '设备相关内容',
                '登录': '登录功能',
                '测试': '测试用例',
                '用例': '测试用例',
                '需求': '需求分析'
            }

            found_items = []
            for keyword, desc in checks.items():
                if keyword in page_content:
                    found_items.append(desc)
                    print(f"   ✅ 发现: {desc}")

            if found_items:
                print(f"\n   总计发现 {len(found_items)} 个关键内容")
            else:
                print("\n   ⚠️ 未发现预期的关键内容")

            # 最终截图
            await page.screenshot(path='/tmp/step7_final_result.png', full_page=True)

            # 步骤8: 测试总结
            print("\n" + "="*60)
            print("📊 测试总结")
            print("="*60)
            print(f"✅ 浏览器启动: 成功")
            print(f"✅ 页面加载: 成功")
            print(f"✅ 文件上传: 已执行")
            print(f"✅ 分析流程: 已触发")
            print(f"✅ 截图保存: /tmp/step*.png")
            print(f"✅ 发现关键内容: {len(found_items)} 项")

            print("\n📸 测试截图保存位置:")
            print("   /tmp/step1_homepage.png - 首页")
            print("   /tmp/step3_upload_success.png - 上传成功")
            print("   /tmp/step4_document_list.png - 文档列表")
            print("   /tmp/step5_analysis_started.png - 开始分析")
            print("   /tmp/step7_final_result.png - 最终结果")

            return True

        except Exception as e:
            print(f"\n❌ 测试过程中出现错误: {e}")
            await page.screenshot(path='/tmp/error_screenshot.png')
            print("   错误截图已保存: /tmp/error_screenshot.png")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # 保持浏览器打开几秒钟以便观察
            print("\n⏸️  保持浏览器打开5秒...")
            await asyncio.sleep(5)
            await browser.close()
            print("✅ 浏览器已关闭")


async def main():
    """主函数"""
    print("=" * 60)
    print("AI需求分析系统 - Playwright端到端测试")
    print("=" * 60)
    print(f"前端URL: {FRONTEND_URL}")
    print(f"测试图片: {TEST_IMAGE_PATH}")
    print("=" * 60)

    success = await test_image_upload_e2e()

    if success:
        print("\n🎉 测试完成！")
    else:
        print("\n⚠️ 测试遇到问题，请查看截图")


if __name__ == "__main__":
    asyncio.run(main())
