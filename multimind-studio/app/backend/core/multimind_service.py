from __future__ import annotations

import json
from typing import Dict, Iterable, Iterator, List, Optional

from .models import AppConfig, ChatMessage

try:  # pragma: no cover - optional dependency behaviour
    from multimind import MultiMind
    from multimind.models import OpenAIModel
except Exception:  # pragma: no cover - degrade gracefully if SDK missing
    MultiMind = None  # type: ignore
    OpenAIModel = None  # type: ignore


class MultiMindService:
    """Wrapper that exposes a streaming chat API using the MultiMind SDK."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._client = None
        if MultiMind and OpenAIModel:
            try:
                self._client = MultiMind(
                    models={"gpt": OpenAIModel(model=config.model_name)},
                    auto_select=True,
                )
            except Exception as exc:
                print(f"[MultiMind] Failed to initialise SDK: {exc}")
                self._client = None

    def get_models(self) -> List[Dict[str, str]]:
        if self._client:
            return [{"id": "gpt", "label": self.config.model_name}]
        return [{"id": "stub", "label": "Stub Model"}]

    def get_router(self) -> Dict[str, str]:
        return {"strategy": "auto", "default_model": self.config.model_name}

    def stream_chat(
        self,
        messages: Iterable[ChatMessage],
        model: Optional[str] = None,
    ) -> Iterator[str]:
        """Yield chat response chunks suitable for SSE."""

        prepared = [message.model_dump() for message in messages]
        if self._client is None:
            # Fallback stub that echoes last user message token by token.
            last_user = next((m["content"] for m in reversed(prepared) if m["role"] == "user"), "")
            for token in last_user.split():
                yield token + " "
            return

        target_model = model or self.config.model_name
        try:
            stream = self._client.stream_chat(messages=prepared, model=target_model)
        except AttributeError:
            # Older SDKs might expose a different API; fall back to non-streaming call.
            response = self._client.chat(messages=prepared, model=target_model)
            content = response.get("content") if isinstance(response, dict) else str(response)
            yield content
            return

        for chunk in stream:
            if isinstance(chunk, dict):
                text = chunk.get("content") or chunk.get("delta") or json.dumps(chunk)
            else:
                text = str(chunk)
            if text:
                yield text
