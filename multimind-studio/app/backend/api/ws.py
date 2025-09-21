from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await websocket.send_json({"message": "WebSocket endpoint ready."})
        while True:
            await websocket.receive_text()
            await websocket.send_json({"message": "No-op"})
    except WebSocketDisconnect:
        return
