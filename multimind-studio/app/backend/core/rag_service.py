from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Iterable, List
from uuid import uuid4

import chromadb
from chromadb.api import Collection

try:  # pragma: no cover - optional PDF dependency
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore


class RagService:
    def __init__(self, vectorstore_dir: Path):
        self.vectorstore_dir = vectorstore_dir
        self.client = chromadb.PersistentClient(path=str(vectorstore_dir))

    def _get_collection(self, collection_id: str) -> Collection:
        return self.client.get_or_create_collection(collection_id)

    def _extract_text(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix in {".txt", ".md", ".py", ".js"}:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf" and PdfReader:
            reader = PdfReader(str(file_path))
            text_buffer = io.StringIO()
            for page in reader.pages:
                text_buffer.write(page.extract_text() or "")
                text_buffer.write("\n")
            return text_buffer.getvalue()
        # Fallback: treat as UTF-8 text.
        return file_path.read_text(encoding="utf-8", errors="ignore")

    def add_file(self, collection_id: str, file_path: Path) -> None:
        collection = self._get_collection(collection_id)
        text = self._extract_text(file_path)
        if not text.strip():
            return
        document_id = f"{file_path.name}-{uuid4()}"
        collection.add(
            ids=[document_id],
            documents=[text],
            metadatas=[{"source": str(file_path)}],
        )

    def rebuild_collection(self, collection_id: str, files: Iterable[Path]) -> int:
        try:
            self.client.delete_collection(collection_id)
        except Exception:
            pass
        collection = self._get_collection(collection_id)
        count = 0
        for file_path in files:
            text = self._extract_text(file_path)
            if not text.strip():
                continue
            document_id = f"{file_path.name}-{uuid4()}"
            collection.add(
                ids=[document_id],
                documents=[text],
                metadatas=[{"source": str(file_path)}],
            )
            count += 1
        return count

    def query(self, collection_id: str, query: str, top_k: int = 3) -> Dict[str, List[str]]:
        collection = self._get_collection(collection_id)
        results = collection.query(query_texts=[query], n_results=top_k)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        contexts = []
        for doc, meta in zip(documents, metadatas):
            source = meta.get("source") if isinstance(meta, dict) else None
            contexts.append(f"Source: {source}\n{doc}")
        return {"contexts": contexts}

    def handle_index_job(self, payload: Dict[str, str]) -> None:
        collection_id = payload.get("collection_id", "default")
        file_path = Path(payload["file_path"])
        if file_path.exists():
            self.add_file(collection_id, file_path)
