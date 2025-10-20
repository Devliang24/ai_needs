"""使用真实PDF文档的集成测试

本测试用例验证了使用V1.7.pdf作为测试文档的完整工作流程。

测试发现:
1. ✅ 文档上传功能正常 (7MB PDF上传成功)
2. ✅ 会话创建功能正常
3. ✅ PDF文本提取功能正常 (PyMuPDF可以解析16页PDF)
4. ❌ LLM处理超时问题 (120秒超时不足以处理大文档)

已知问题和改进建议:
- 问题: V1.7.pdf (7MB, 16页) 导致LLM请求超时 (120秒)
- 根本原因: 大文档需要更长的LLM处理时间,尤其是使用qwen-max模型
- 建议解决方案:
  1. 增加LLM_TIMEOUT环境变量到300秒以上
  2. 实现文档分块处理策略
  3. 在text_extractor中增加更严格的字符限制(当前4000字符可能仍然太多)
  4. 对大文档进行预处理,提取关键内容而非全文
  5. 添加重试机制,在超时时使用更短的文本重试
"""

import asyncio
import os
from io import BytesIO
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# 使用mock模式避免真实LLM调用超时
os.environ.setdefault("REDIS_URL", "fakeredis://")
os.environ.setdefault("LLM_MODE", "mock")

from app.main import app  # noqa: E402


def get_test_pdf_path() -> Path:
    """获取测试PDF路径 (支持容器内外环境)"""
    # 尝试多个可能的路径
    candidates = [
        Path("/opt/ai_needs/V1.7.pdf"),  # 宿主机路径
        Path("/app/../V1.7.pdf"),  # 容器内相对路径
        Path("./V1.7.pdf"),  # 当前目录
    ]
    for path in candidates:
        if path.exists():
            return path
    # 如果都不存在,使用测试文档的checksum路径
    stored_path = Path("/app/storage/uploads/8f06e1712f0996428ab997c164ca999c6120b37e3c36b84d2c229223e3d04723")
    if stored_path.exists():
        return stored_path
    raise FileNotFoundError("找不到V1.7.pdf测试文件")


@pytest.mark.asyncio
async def test_upload_real_pdf_document():
    """测试上传真实PDF文档 (V1.7.pdf)"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 检查PDF文件是否存在
        pdf_path = get_test_pdf_path()
        assert pdf_path.exists(), "V1.7.pdf 文件不存在"

        # 上传PDF文件
        with open(pdf_path, "rb") as f:
            files = {"file": ("V1.7.pdf", BytesIO(f.read()), "application/pdf")}
            upload_response = await client.post("/api/uploads", files=files)

        assert upload_response.status_code == 200, f"上传失败: {upload_response.text}"
        upload_data = upload_response.json()

        # 验证上传响应
        assert "document" in upload_data
        document = upload_data["document"]
        assert document["original_name"] == "V1.7.pdf"
        assert document["status"] == "uploaded"
        assert document["size"] > 0, "文档大小应大于0"

        # 验证文档ID格式
        document_id = document["id"]
        assert len(document_id) > 0
        assert "-" in document_id, "文档ID应为UUID格式"

        return document_id


@pytest.mark.asyncio
async def test_create_session_with_pdf():
    """测试使用PDF文档创建分析会话"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 先上传文档
        pdf_path = get_test_pdf_path()
        with open(pdf_path, "rb") as f:
            files = {"file": ("V1.7.pdf", BytesIO(f.read()), "application/pdf")}
            upload_response = await client.post("/api/uploads", files=files)

        document_id = upload_response.json()["document"]["id"]

        # 创建会话
        create_response = await client.post(
            "/api/sessions",
            json={"document_ids": [document_id], "config": {"target": "test"}},
        )

        assert create_response.status_code == 200, f"创建会话失败: {create_response.text}"
        session_data = create_response.json()

        # 验证会话响应
        assert "session_id" in session_data
        assert session_data["status"] == "created"

        session_id = session_data["session_id"]

        # 获取会话详情
        detail_response = await client.get(f"/api/sessions/{session_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()

        # 验证会话包含文档信息
        assert detail_data["id"] == session_id
        assert len(detail_data["documents"]) == 1
        assert detail_data["documents"][0]["original_name"] == "V1.7.pdf"

        return session_id


@pytest.mark.asyncio
async def test_full_pdf_workflow_with_mock():
    """完整的PDF工作流测试 (使用mock模式避免超时)

    注意: 此测试使用mock模式,不会调用真实LLM API。
    如需测试真实LLM调用,需要:
    1. 设置 LLM_MODE=autogen
    2. 增加 LLM_TIMEOUT 到 300 秒以上
    3. 考虑使用更小的测试文档
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. 上传PDF
        pdf_path = get_test_pdf_path()
        with open(pdf_path, "rb") as f:
            files = {"file": ("V1.7.pdf", BytesIO(f.read()), "application/pdf")}
            upload_response = await client.post("/api/uploads", files=files)

        assert upload_response.status_code == 200
        document_id = upload_response.json()["document"]["id"]

        # 2. 创建会话
        create_response = await client.post(
            "/api/sessions",
            json={"document_ids": [document_id], "config": {"target": "test"}},
        )

        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]

        # 3. 等待工作流完成 (mock模式下应该很快)
        result_payload = None
        for _ in range(40):
            response = await client.get(f"/api/sessions/{session_id}/results")
            assert response.status_code == 200
            data = response.json()
            if data["version"] > 0:
                result_payload = data
                break
            await asyncio.sleep(0.1)

        # 在mock模式下,应该能生成结果
        assert result_payload is not None, "工作流未在预期时间内完成"
        assert result_payload["test_cases"], "应生成测试用例"

        # 4. 测试导出功能
        # Excel导出
        excel_response = await client.post(
            f"/api/sessions/{session_id}/exports/excel",
            json={"result_version": result_payload["version"]},
        )
        assert excel_response.status_code == 200
        assert "spreadsheetml" in excel_response.headers["content-type"]
        assert len(excel_response.content) > 0

        # XMind导出
        xmind_response = await client.post(
            f"/api/sessions/{session_id}/exports/xmind",
            json={"result_version": result_payload["version"]},
        )
        assert xmind_response.status_code == 200
        assert "xmind" in xmind_response.headers["content-type"]
        assert len(xmind_response.content) > 0


@pytest.mark.asyncio
async def test_pdf_text_extraction():
    """测试PDF文本提取功能

    验证PyMuPDF能够正确提取V1.7.pdf的文本内容
    """
    from app.parsers.text_extractor import extract_text

    pdf_path = get_test_pdf_path()
    assert pdf_path.exists()

    # 提取文本 (限制4000字符)
    text = extract_text(str(pdf_path), limit=4000, original_name="V1.7.pdf")

    # 验证提取的文本
    assert len(text) > 0, "应能提取到文本内容"
    assert len(text) <= 4000, "文本长度不应超过限制"

    # 验证不是占位符消息
    assert "已上传" not in text, "不应返回占位符消息"
    assert "请在后端解析" not in text, "不应返回占位符消息"

    # PDF应包含一些中文内容
    # V1.7.pdf的第一页包含产品需求相关的中文文本
    assert any(ord(c) > 127 for c in text), "应包含非ASCII字符(中文)"


@pytest.mark.asyncio
async def test_session_results_structure():
    """测试会话结果的数据结构

    验证生成的测试用例、需求分析和统计数据符合预期格式
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 上传并创建会话
        pdf_path = get_test_pdf_path()
        with open(pdf_path, "rb") as f:
            files = {"file": ("V1.7.pdf", BytesIO(f.read()), "application/pdf")}
            upload_response = await client.post("/api/uploads", files=files)

        document_id = upload_response.json()["document"]["id"]

        create_response = await client.post(
            "/api/sessions",
            json={"document_ids": [document_id], "config": {"target": "test"}},
        )
        session_id = create_response.json()["session_id"]

        # 等待结果
        for _ in range(40):
            response = await client.get(f"/api/sessions/{session_id}/results")
            data = response.json()
            if data["version"] > 0:
                # 验证结果结构
                assert "analysis" in data
                assert "test_cases" in data
                assert "statistics" in data
                assert "version" in data
                assert "generated_at" in data

                # 验证测试用例结构
                test_cases = data["test_cases"]
                if "modules" in test_cases:
                    assert isinstance(test_cases["modules"], list)
                    if len(test_cases["modules"]) > 0:
                        module = test_cases["modules"][0]
                        assert "name" in module
                        assert "cases" in module

                        # 如果有用例,验证用例结构
                        if len(module["cases"]) > 0:
                            case = module["cases"][0]
                            # 用例应包含这些字段
                            expected_fields = {"id", "title", "steps", "expected"}
                            assert any(field in case for field in expected_fields), \
                                "测试用例应包含id/title/steps/expected等字段"

                return

            await asyncio.sleep(0.1)

        # Mock模式下应该能快速完成
        pytest.fail("工作流未在预期时间内完成")


# 性能基准测试
@pytest.mark.asyncio
@pytest.mark.slow
async def test_large_document_performance():
    """大文档处理性能测试

    标记为slow,仅在需要时运行:
    pytest -m slow tests/test_pdf_workflow.py
    """
    import time

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        pdf_path = get_test_pdf_path()

        # 测量上传时间
        start_upload = time.time()
        with open(pdf_path, "rb") as f:
            files = {"file": ("V1.7.pdf", BytesIO(f.read()), "application/pdf")}
            upload_response = await client.post("/api/uploads", files=files)
        upload_time = time.time() - start_upload

        assert upload_response.status_code == 200
        document_id = upload_response.json()["document"]["id"]

        # 测量会话创建时间
        start_session = time.time()
        create_response = await client.post(
            "/api/sessions",
            json={"document_ids": [document_id], "config": {"target": "test"}},
        )
        session_time = time.time() - start_session

        assert create_response.status_code == 200

        # 记录性能指标
        print(f"\n性能指标 (V1.7.pdf - 7MB, 16页):")
        print(f"  上传时间: {upload_time:.2f}秒")
        print(f"  会话创建: {session_time:.2f}秒")

        # 性能断言 (宽松的阈值)
        assert upload_time < 30, "上传时间不应超过30秒"
        assert session_time < 5, "会话创建不应超过5秒"
