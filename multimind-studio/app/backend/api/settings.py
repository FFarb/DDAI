from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..core.models import AppSetting, SettingsPayload

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings(request: Request) -> JSONResponse:
    with request.app.state.db.session() as session:
        entry = session.get(AppSetting, "app")
        data = json.loads(entry.value) if entry else {}
    return JSONResponse({"settings": data})


@router.post("")
async def save_settings(payload: SettingsPayload, request: Request) -> JSONResponse:
    data_json = json.dumps(payload.data)
    with request.app.state.db.session() as session:
        entry = session.get(AppSetting, "app")
        if entry is None:
            entry = AppSetting(key="app", value=data_json)
        else:
            entry.value = data_json
        session.add(entry)
        session.commit()
    return JSONResponse({"status": "ok"})
