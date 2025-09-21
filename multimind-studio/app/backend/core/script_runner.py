from __future__ import annotations

import json
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Any, Callable, Dict, Iterator, List, Optional
from uuid import uuid4


@dataclass
class RunHandle:
    run_id: str
    process: subprocess.Popen
    stdout_path: Path
    stderr_path: Path
    artifacts_path: Path
    queue: "Queue[str]"
    status: str = "running"


class ScriptRunner:
    """Run scripts inside subprocesses and expose streaming logs."""

    def __init__(self, workspace: Path, on_complete: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.workspace = workspace
        self.on_complete = on_complete
        self._handles: Dict[str, RunHandle] = {}
        self._lock = threading.Lock()
        self._artifact_index: Dict[str, Path] = {}

    def run_script(self, script_path: Path, language: str) -> RunHandle:
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        run_id = str(uuid4())
        project_dir = script_path.parent
        artifacts_path = project_dir / "artifacts" / run_id
        artifacts_path.mkdir(parents=True, exist_ok=True)

        stdout_path = artifacts_path / "stdout.log"
        stderr_path = artifacts_path / "stderr.log"

        if language == "py":
            command = ["python", script_path.name]
        elif language == "js":
            command = ["node", script_path.name]
        else:
            raise ValueError(f"Unsupported language: {language}")

        process = subprocess.Popen(
            command,
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        queue: "Queue[str]" = Queue()
        handle = RunHandle(
            run_id=run_id,
            process=process,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            artifacts_path=artifacts_path,
            queue=queue,
        )

        with self._lock:
            self._handles[run_id] = handle
            self._artifact_index[run_id] = artifacts_path

        threading.Thread(
            target=self._pump_stream,
            args=(process.stdout, stdout_path, queue, "stdout"),
            daemon=True,
        ).start()
        threading.Thread(
            target=self._pump_stream,
            args=(process.stderr, stderr_path, queue, "stderr"),
            daemon=True,
        ).start()
        threading.Thread(target=self._wait_for_completion, args=(handle,), daemon=True).start()

        return handle

    def _pump_stream(self, stream, log_path: Path, queue: "Queue[str]", stream_type: str) -> None:
        if stream is None:
            return
        with log_path.open("w", encoding="utf-8") as log_file:
            for line in stream:
                log_file.write(line)
                log_file.flush()
                payload = json.dumps({"type": stream_type, "data": line})
                queue.put(payload)
        queue.put(json.dumps({"type": f"{stream_type}_end"}))

    def _wait_for_completion(self, handle: RunHandle) -> None:
        process = handle.process
        return_code = process.wait()
        handle.status = "finished" if return_code == 0 else "failed"
        handle.queue.put(json.dumps({"type": "status", "data": handle.status, "code": return_code}))
        handle.queue.put("__COMPLETE__")
        if self.on_complete:
            try:
                self.on_complete(
                    {
                        "run_id": handle.run_id,
                        "status": handle.status,
                        "return_code": return_code,
                        "stdout_path": str(handle.stdout_path),
                        "stderr_path": str(handle.stderr_path),
                        "artifacts_path": str(handle.artifacts_path),
                    }
                )
            except Exception as exc:  # pragma: no cover - logging only
                print(f"[ScriptRunner] on_complete callback failed: {exc}")
        with self._lock:
            self._handles.pop(handle.run_id, None)
            if handle.run_id not in self._artifact_index:
                self._artifact_index[handle.run_id] = handle.artifacts_path

    def stop(self, run_id: str) -> bool:
        with self._lock:
            handle = self._handles.get(run_id)
        if not handle:
            return False
        process = handle.process
        if process.poll() is not None:
            return True
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        handle.queue.put(json.dumps({"type": "status", "data": "stopped"}))
        handle.queue.put("__COMPLETE__")
        with self._lock:
            self._artifact_index.setdefault(run_id, handle.artifacts_path)
        return True

    def stream_logs(self, run_id: str) -> Iterator[str]:
        while True:
            with self._lock:
                handle = self._handles.get(run_id)
            if handle:
                break
            time.sleep(0.1)
        queue = handle.queue
        while True:
            payload = queue.get()
            if payload == "__COMPLETE__":
                break
            yield payload

    def get_handle(self, run_id: str) -> Optional[RunHandle]:
        with self._lock:
            return self._handles.get(run_id)

    def list_artifacts(self, run_id: str) -> List[str]:
        with self._lock:
            artifacts_path = self._artifact_index.get(run_id)
        if artifacts_path is None:
            return []
        if not artifacts_path.exists():
            return []
        return [item.name for item in artifacts_path.iterdir() if item.is_file()]
