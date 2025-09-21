from __future__ import annotations

from typing import Iterable, List

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ..core.models import ChatMessage, ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(payload: ChatRequest, request: Request) -> StreamingResponse:
    service = request.app.state.multimind
    messages: List[ChatMessage] = []
    if payload.system_prompt:
        messages.append(ChatMessage(role="system", content=payload.system_prompt))
    messages.extend(payload.messages)

    def event_stream() -> Iterable[str]:
        for chunk in service.stream_chat(messages, model=payload.model):
            yield f"data:{chunk}\n\n"
        yield "data:[DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/models")
async def list_models(request: Request) -> JSONResponse:
    service = request.app.state.multimind
    return JSONResponse({"models": service.get_models()})


@router.get("/router")
async def get_router(request: Request) -> JSONResponse:
    service = request.app.state.multimind
    return JSONResponse(service.get_router())
