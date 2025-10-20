import asyncio
import os
from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("REDIS_URL", "fakeredis://")
os.environ.setdefault("LLM_MODE", "mock")

from app.cache import session_events  # noqa: E402  pylint: disable=wrong-import-position
from app.main import app  # noqa: E402  pylint: disable=wrong-import-position


@pytest.mark.asyncio
async def test_full_workflow_generates_results_and_exports():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        file_content = b"User login requirement\nSystem should allow users to login with username and password."
        files = {"file": ("login.txt", BytesIO(file_content), "text/plain")}
        upload_response = await client.post("/api/uploads", files=files)
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document"]["id"]

        create_response = await client.post(
            "/api/sessions",
            json={"document_ids": [document_id], "config": {"target": "test"}},
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]

        detail_response = await client.get(f"/api/sessions/{session_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["id"] == session_id
        assert detail_data["documents"], "session detail should include uploaded documents"

        result_payload = None
        for _ in range(40):
            response = await client.get(f"/api/sessions/{session_id}/results")
            assert response.status_code == 200
            data = response.json()
            if data["version"] > 0:
                result_payload = data
                break
            await asyncio.sleep(0.1)

        assert result_payload is not None, "workflow did not produce results in time"
        assert result_payload["test_cases"]["modules"], "test cases should be generated"

        excel_response = await client.post(
            f"/api/sessions/{session_id}/exports/excel",
            json={"result_version": result_payload["version"]},
        )
        assert excel_response.status_code == 200
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in excel_response.headers["content-type"]
        )
        assert len(excel_response.content) > 0

        xmind_response = await client.post(
            f"/api/sessions/{session_id}/exports/xmind",
            json={"result_version": result_payload["version"]},
        )
        assert xmind_response.status_code == 200
        assert "application/vnd.xmind.workbook" in xmind_response.headers["content-type"]
        assert len(xmind_response.content) > 0

    # Validate websocket history contains staged events
    events = await session_events.fetch_events(session_id)
    stages = {event.get("stage") for event in events}
    assert stages
    assert "requirement_analysis" in stages or "system" in stages
