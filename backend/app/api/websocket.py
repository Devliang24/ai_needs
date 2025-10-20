"""WebSocket endpoint for real-time agent streaming."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.cache import session_events
from app.websocket.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    history = await session_events.fetch_events(session_id)
    for event in history:
        await websocket.send_json(event)

    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()

            # 解析并处理客户端发送的消息
            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "confirm_agent":
                    # 处理确认消息
                    stage = message.get("stage")
                    result_id = message.get("result_id")
                    payload = message.get("payload")

                    logger.info(f"收到确认消息: session={session_id}, stage={stage}, result_id={result_id}")

                    # 将确认信息存储到 Redis,供 workflow 等待
                    await session_events.set_confirmation(
                        session_id,
                        {
                            "stage": stage,
                            "result_id": result_id,
                            "payload": payload,
                            "confirmed": True
                        }
                    )

                    logger.info(f"确认信息已存储: session={session_id}")

            except json.JSONDecodeError:
                logger.warning(f"收到无效的JSON消息: {data}")
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")

    except WebSocketDisconnect:
        await manager.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
        await manager.disconnect(session_id, websocket)

