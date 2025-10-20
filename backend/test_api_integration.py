#!/usr/bin/env python3
"""完整的API集成测试脚本"""

import asyncio
import aiohttp
import aiofiles
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# API配置
API_BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "/app/test_image.png"


async def test_health_check():
    """测试健康检查接口"""
    print("\n" + "="*60)
    print("1. 测试健康检查接口")
    print("-"*60)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/healthz") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查成功: {data}")
                    return True
                else:
                    print(f"❌ 健康检查失败: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 无法连接到API服务器: {e}")
            return False


async def test_image_analysis_api():
    """测试图片分析API接口"""
    print("\n" + "="*60)
    print("2. 测试图片分析API (/api/images/analyze)")
    print("-"*60)

    if not Path(TEST_IMAGE_PATH).exists():
        print(f"❌ 测试图片不存在: {TEST_IMAGE_PATH}")
        return None

    async with aiohttp.ClientSession() as session:
        try:
            # 读取图片文件
            async with aiofiles.open(TEST_IMAGE_PATH, 'rb') as f:
                file_data = await f.read()

            # 构建表单数据
            data = aiohttp.FormData()
            data.add_field('file',
                          file_data,
                          filename='requirements.png',
                          content_type='image/png')

            print(f"📤 上传图片到: {API_BASE_URL}/api/images/analyze")
            print(f"   文件大小: {len(file_data)/1024:.2f} KB")

            start_time = time.time()
            async with session.post(f"{API_BASE_URL}/api/images/analyze", data=data) as response:
                elapsed_time = time.time() - start_time

                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 分析成功！耗时: {elapsed_time:.2f}秒")
                    print(f"   提取文本长度: {result.get('text_length', 0)} 字符")
                    print(f"   使用模型: {result.get('model_used', 'unknown')}")
                    print(f"   文件名: {result.get('filename', 'unknown')}")

                    if result.get('extracted_text'):
                        print("\n📝 提取内容预览（前300字符）:")
                        print("-"*40)
                        print(result['extracted_text'][:300])
                        print("-"*40)

                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ 分析失败: HTTP {response.status}")
                    print(f"   错误信息: {error_text}")
                    return None

        except Exception as e:
            print(f"❌ API调用失败: {e}")
            return None


async def test_document_upload():
    """测试文档上传接口"""
    print("\n" + "="*60)
    print("3. 测试文档上传接口 (/api/uploads)")
    print("-"*60)

    if not Path(TEST_IMAGE_PATH).exists():
        print(f"❌ 测试图片不存在: {TEST_IMAGE_PATH}")
        return None

    async with aiohttp.ClientSession() as session:
        try:
            async with aiofiles.open(TEST_IMAGE_PATH, 'rb') as f:
                file_data = await f.read()

            data = aiohttp.FormData()
            data.add_field('file',
                          file_data,
                          filename='test_requirements.png',
                          content_type='image/png')

            print(f"📤 上传文档到: {API_BASE_URL}/api/uploads")

            async with session.post(f"{API_BASE_URL}/api/uploads", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 上传成功！")
                    print(f"   文档ID: {result.get('document', {}).get('id')}")
                    print(f"   原始名称: {result.get('document', {}).get('original_name')}")
                    print(f"   是否重复: {result.get('is_duplicate', False)}")
                    print(f"   文件大小: {result.get('document', {}).get('size', 0)} bytes")
                    return result.get('document', {}).get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 上传失败: HTTP {response.status}")
                    print(f"   错误: {error_text}")
                    return None

        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return None


async def test_create_session(document_id: str):
    """创建分析会话"""
    print("\n" + "="*60)
    print("4. 创建分析会话 (/api/sessions)")
    print("-"*60)

    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "document_ids": [document_id],
                "config": {
                    "enable_review": True,
                    "model": "qwen-plus"
                },
                "created_by": "api_test"
            }

            print(f"📤 创建会话，文档ID: {document_id}")

            async with session.post(
                f"{API_BASE_URL}/api/sessions",
                json=payload
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    session_id = result.get('session_id')
                    print(f"✅ 会话创建成功！")
                    print(f"   会话ID: {session_id}")
                    print(f"   状态: {result.get('status')}")
                    print(f"   过期时间: {result.get('expires_at')}")
                    return session_id
                else:
                    error_text = await response.text()
                    print(f"❌ 创建会话失败: HTTP {response.status}")
                    print(f"   错误: {error_text}")
                    return None

        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            return None


async def monitor_session(session_id: str, max_wait: int = 300):
    """监控会话进度"""
    print("\n" + "="*60)
    print("5. 监控会话进度")
    print("-"*60)

    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        last_stage = None

        while time.time() - start_time < max_wait:
            try:
                async with session.get(f"{API_BASE_URL}/api/sessions/{session_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        current_stage = data.get('current_stage')
                        progress = data.get('progress', 0)
                        status = data.get('status')

                        if current_stage != last_stage:
                            print(f"\n📊 阶段更新: {current_stage}")
                            last_stage = current_stage

                        print(f"   进度: {progress*100:.1f}% | 状态: {status}", end='\r')

                        if status == 'completed':
                            print(f"\n✅ 会话完成！总耗时: {time.time()-start_time:.1f}秒")
                            return True
                        elif status == 'failed':
                            print(f"\n❌ 会话失败！")
                            return False
                        elif status == 'awaiting_confirmation':
                            print(f"\n⏸️  等待人工确认...")
                            # 这里可以自动确认或等待
                            return await confirm_session(session_id, current_stage)

                await asyncio.sleep(2)

            except Exception as e:
                print(f"\n⚠️ 监控出错: {e}")
                await asyncio.sleep(5)

        print(f"\n⏱️ 监控超时（{max_wait}秒）")
        return False


async def confirm_session(session_id: str, stage: str):
    """确认会话继续"""
    print(f"\n🔄 自动确认阶段: {stage}")

    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "stage": stage,
                "decision": "approve",
                "comment": "自动测试确认"
            }

            async with session.post(
                f"{API_BASE_URL}/api/sessions/{session_id}/confirm",
                json=payload
            ) as response:
                if response.status in [200, 202]:
                    print(f"✅ 确认成功，继续处理...")
                    # 继续监控
                    return await monitor_session(session_id)
                else:
                    error_text = await response.text()
                    print(f"❌ 确认失败: {error_text}")
                    return False

        except Exception as e:
            print(f"❌ 确认失败: {e}")
            return False


async def get_session_results(session_id: str):
    """获取会话结果"""
    print("\n" + "="*60)
    print("6. 获取分析结果")
    print("-"*60)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/api/sessions/{session_id}/results") as response:
                if response.status == 200:
                    results = await response.json()
                    print(f"✅ 获取结果成功！")

                    # 显示分析结果
                    if results.get('analysis'):
                        print("\n📋 需求分析结果:")
                        print("-"*40)
                        analysis_str = json.dumps(results['analysis'], ensure_ascii=False, indent=2)
                        print(analysis_str[:500] + "..." if len(analysis_str) > 500 else analysis_str)

                    # 显示测试用例统计
                    if results.get('test_cases'):
                        test_cases = results['test_cases']
                        if isinstance(test_cases, dict) and 'test_cases' in test_cases:
                            cases_list = test_cases['test_cases']
                            print(f"\n📊 测试用例统计:")
                            print(f"   总数: {len(cases_list)} 个")

                            # 统计优先级
                            priorities = {}
                            for case in cases_list:
                                priority = case.get('priority', 'unknown')
                                priorities[priority] = priorities.get(priority, 0) + 1

                            for priority, count in priorities.items():
                                print(f"   {priority}: {count} 个")

                    return results
                else:
                    error_text = await response.text()
                    print(f"❌ 获取结果失败: {error_text}")
                    return None

        except Exception as e:
            print(f"❌ 获取结果失败: {e}")
            return None


async def test_cache_effectiveness():
    """测试缓存机制"""
    print("\n" + "="*60)
    print("7. 测试缓存机制")
    print("-"*60)

    if not Path(TEST_IMAGE_PATH).exists():
        print(f"❌ 测试图片不存在")
        return

    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(TEST_IMAGE_PATH, 'rb') as f:
            file_data = await f.read()

        print("第一次调用（应该调用API）...")
        data1 = aiohttp.FormData()
        data1.add_field('file', file_data, filename='test1.png', content_type='image/png')

        start_time1 = time.time()
        async with session.post(f"{API_BASE_URL}/api/images/analyze", data=data1) as response:
            elapsed1 = time.time() - start_time1
            result1 = await response.json() if response.status == 200 else None

        print(f"   耗时: {elapsed1:.2f}秒")

        print("\n第二次调用（应该使用缓存）...")
        data2 = aiohttp.FormData()
        data2.add_field('file', file_data, filename='test2.png', content_type='image/png')

        start_time2 = time.time()
        async with session.post(f"{API_BASE_URL}/api/images/analyze", data=data2) as response:
            elapsed2 = time.time() - start_time2
            result2 = await response.json() if response.status == 200 else None

        print(f"   耗时: {elapsed2:.2f}秒")

        if result1 and result2:
            if elapsed2 < elapsed1 * 0.5:  # 第二次应该快很多
                print(f"✅ 缓存机制有效！加速比: {elapsed1/elapsed2:.1f}x")
            else:
                print(f"⚠️ 缓存可能未生效，时间差异不明显")


async def main():
    """主测试函数"""
    print("🚀 AI需求分析系统 - 完整API集成测试")
    print("="*60)

    # 1. 健康检查
    if not await test_health_check():
        print("\n❌ 服务器未响应，请检查服务是否运行")
        return

    # 2. 测试图片分析API
    analysis_result = await test_image_analysis_api()
    if not analysis_result:
        print("\n⚠️ 图片分析API测试失败")

    # 3. 上传文档
    document_id = await test_document_upload()
    if not document_id:
        print("\n❌ 文档上传失败，无法继续")
        return

    # 4. 创建会话
    session_id = await test_create_session(document_id)
    if not session_id:
        print("\n❌ 会话创建失败")
        return

    # 5. 监控会话进度
    success = await monitor_session(session_id)
    if not success:
        print("\n⚠️ 会话处理未完成")

    # 6. 获取结果
    results = await get_session_results(session_id)
    if not results:
        print("\n⚠️ 未能获取结果")

    # 7. 测试缓存
    await test_cache_effectiveness()

    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("\n📝 测试总结:")
    print("- 图片分析API: " + ("✅ 通过" if analysis_result else "❌ 失败"))
    print("- 文档上传: " + ("✅ 通过" if document_id else "❌ 失败"))
    print("- 会话创建: " + ("✅ 通过" if session_id else "❌ 失败"))
    print("- 工作流执行: " + ("✅ 通过" if success else "❌ 失败"))
    print("- 结果获取: " + ("✅ 通过" if results else "❌ 失败"))


if __name__ == "__main__":
    asyncio.run(main())