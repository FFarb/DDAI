from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import select

from .api import chat, rag, scripts, settings, ws
from .core.db import Database
from .core.jobs import JobQueue
from .core.models import AppConfig, ScriptRun, ensure_directories
from .core.multimind_service import MultiMindService
from .core.rag_service import RagService
from .core.script_runner import ScriptRunner

app = FastAPI(title="MultiMind Studio API")

config = AppConfig()
ensure_directories(config)
database = Database(config.database_url)
database.init_db()
rag_service = RagService(config.vectorstore_path)
multimind_service = MultiMindService(config)
job_queue = JobQueue()


def _on_run_complete(result: Dict[str, Any]) -> None:
    with database.session() as session:
        run_entry = session.exec(select(ScriptRun).where(ScriptRun.run_id == result["run_id"])).first()
        if run_entry:
            run_entry.status = result.get("status", run_entry.status)
            run_entry.finished_at = datetime.utcnow()
            run_entry.stdout_path = result.get("stdout_path")
            run_entry.stderr_path = result.get("stderr_path")
            run_entry.artifacts_path = result.get("artifacts_path")
            session.add(run_entry)


def _register_jobs() -> None:
    job_queue.register("rag_index_file", rag_service.handle_index_job)


script_runner = ScriptRunner(config.workspace_path, on_complete=_on_run_complete)
_register_jobs()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    job_queue.start()
    app.state.config = config
    app.state.db = database
    app.state.rag = rag_service
    app.state.runner = script_runner
    app.state.multimind = multimind_service
    app.state.jobs = job_queue


@app.on_event("shutdown")
async def shutdown_event() -> None:
    job_queue.stop()


@app.get("/health")
async def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "ok"})


app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(scripts.router)
app.include_router(settings.router)
app.include_router(ws.router)
