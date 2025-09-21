from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from ..core.models import RagQuery, RagQueryResponse

router = APIRouter(prefix="/api/rag", tags=["rag"])


def _get_workspace_uploads(request: Request) -> Path:
    config = request.app.state.config
    uploads_dir = config.workspace_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    collection_id: str = Form("default"),
) -> JSONResponse:
    uploads_dir = _get_workspace_uploads(request)
    destination = uploads_dir / file.filename
    destination.write_bytes(await file.read())

    job_queue = request.app.state.jobs
    job_queue.enqueue(
        "rag_index_file", {"file_path": str(destination), "collection_id": collection_id}
    )
    return JSONResponse({"status": "queued", "path": str(destination)})


@router.post("/index")
async def rebuild_index(request: Request, payload: Dict[str, str]) -> JSONResponse:
    collection_id = payload.get("collection_id", "default")
    rag_service = request.app.state.rag
    uploads_dir = _get_workspace_uploads(request)
    files = list(uploads_dir.glob("*"))
    count = rag_service.rebuild_collection(collection_id, files)
    return JSONResponse({"status": "ok", "indexed": count})


@router.post("/query")
async def query_rag(request: Request, payload: RagQuery) -> RagQueryResponse:
    rag_service = request.app.state.rag
    results = rag_service.query(payload.collection_id, payload.query, payload.top_k)
    contexts = results.get("contexts", [])
    answer = contexts[0] if contexts else "No context found."
    return RagQueryResponse(contexts=contexts, answer=answer)
