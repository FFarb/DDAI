from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlmodel import select

from ..core.models import Script, ScriptCreate, ScriptRun, ScriptUpdate

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


def _script_to_dict(script: Script) -> Dict[str, Any]:
    tags = [tag for tag in script.tags.split(",") if tag]
    return {
        "id": script.id,
        "name": script.name,
        "language": script.language,
        "path": script.path,
        "tags": tags,
        "created_at": script.created_at,
        "updated_at": script.updated_at,
    }


@router.get("")
async def list_scripts(request: Request) -> JSONResponse:
    with request.app.state.db.session() as session:
        scripts = session.exec(select(Script)).all()
        return JSONResponse({"scripts": [_script_to_dict(script) for script in scripts]})


@router.get("/{script_id}")
async def get_script(script_id: int, request: Request) -> JSONResponse:
    with request.app.state.db.session() as session:
        script = session.get(Script, script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
    config = request.app.state.config
    full_path = (config.workspace_path / script.path).resolve()
    content = ""
    if full_path.exists():
        content = full_path.read_text(encoding="utf-8")
    data = _script_to_dict(script)
    data["content"] = content
    return JSONResponse({"script": data})


@router.post("")
async def create_script(payload: ScriptCreate, request: Request) -> JSONResponse:
    config = request.app.state.config
    full_path = (config.workspace_path / payload.path).resolve()
    if not str(full_path).startswith(str(config.workspace_path.resolve())):
        raise HTTPException(status_code=400, detail="Path must be inside workspace")
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(payload.content, encoding="utf-8")

    tags = ",".join(payload.tags)
    script = Script(name=payload.name, language=payload.language, path=payload.path, tags=tags)
    with request.app.state.db.session() as session:
        session.add(script)
        session.commit()
        session.refresh(script)
    return JSONResponse({"script": _script_to_dict(script)})


@router.put("/{script_id}")
async def update_script(script_id: int, payload: ScriptUpdate, request: Request) -> JSONResponse:
    with request.app.state.db.session() as session:
        script = session.get(Script, script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        if payload.name is not None:
            script.name = payload.name
        if payload.language is not None:
            script.language = payload.language
        if payload.path is not None:
            script.path = payload.path
        if payload.tags is not None:
            script.tags = ",".join(payload.tags)
        if payload.content is not None:
            config = request.app.state.config
            full_path = (config.workspace_path / script.path).resolve()
            full_path.write_text(payload.content, encoding="utf-8")
        script.updated_at = datetime.utcnow()
        session.add(script)
        session.commit()
        session.refresh(script)
    return JSONResponse({"script": _script_to_dict(script)})


@router.delete("/{script_id}")
async def delete_script(script_id: int, request: Request) -> JSONResponse:
    with request.app.state.db.session() as session:
        script = session.get(Script, script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        session.delete(script)
        session.commit()
    return JSONResponse({"status": "deleted"})


@router.post("/run")
async def run_script(request: Request, payload: Dict[str, int]) -> JSONResponse:
    script_id = payload.get("script_id")
    if script_id is None:
        raise HTTPException(status_code=400, detail="script_id required")
    with request.app.state.db.session() as session:
        script = session.get(Script, script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
    config = request.app.state.config
    script_path = (config.workspace_path / script.path).resolve()
    runner = request.app.state.runner
    handle = runner.run_script(script_path, script.language)
    run_entry = ScriptRun(
        run_id=handle.run_id,
        script_id=script.id,
        script_name=script.name,
        status="running",
        stdout_path=str(handle.stdout_path),
        stderr_path=str(handle.stderr_path),
        artifacts_path=str(handle.artifacts_path),
    )
    with request.app.state.db.session() as session:
        session.add(run_entry)
        session.commit()
    return JSONResponse({"run_id": handle.run_id})


@router.post("/stop")
async def stop_run(request: Request, payload: Dict[str, str]) -> JSONResponse:
    run_id = payload.get("run_id")
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id required")
    runner = request.app.state.runner
    success = runner.stop(run_id)
    status = "stopped" if success else "not_found"
    if success:
        with request.app.state.db.session() as session:
            run_entry = session.exec(select(ScriptRun).where(ScriptRun.run_id == run_id)).first()
            if run_entry:
                run_entry.status = "stopped"
                run_entry.finished_at = datetime.utcnow()
                session.add(run_entry)
    return JSONResponse({"status": status})


@router.get("/runs/{run_id}/stream")
async def stream_run_logs(run_id: str, request: Request) -> StreamingResponse:
    runner = request.app.state.runner

    def event_stream():
        for chunk in runner.stream_logs(run_id):
            yield f"data:{chunk}\n\n"
        yield "data:[DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/runs/{run_id}/artifacts")
async def list_run_artifacts(run_id: str, request: Request) -> JSONResponse:
    runner = request.app.state.runner
    artifacts = runner.list_artifacts(run_id)
    if not artifacts:
        # fall back to persisted value in DB if available
        with request.app.state.db.session() as session:
            run_entry = session.exec(select(ScriptRun).where(ScriptRun.run_id == run_id)).first()
            if run_entry and run_entry.artifacts_path:
                path = Path(run_entry.artifacts_path)
                if path.exists():
                    artifacts = [item.name for item in path.iterdir() if item.is_file()]
    return JSONResponse({"artifacts": artifacts})
