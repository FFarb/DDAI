from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field as PydanticField
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field, SQLModel


class AppConfig(BaseSettings):
    """Application level configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: Optional[str] = PydanticField(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = PydanticField(default=None, alias="ANTHROPIC_API_KEY")
    mistral_api_key: Optional[str] = PydanticField(default=None, alias="MISTRAL_API_KEY")
    model_name: str = PydanticField(default="gpt-4o-mini", alias="MODEL_NAME")
    workspace_dir: str = PydanticField(default="./workspace", alias="WORKSPACE_DIR")
    vectorstore_dir: str = PydanticField(default="./vectorstore", alias="VECTORSTORE_DIR")
    database_url: str = PydanticField(default="sqlite:///./app.db", alias="DATABASE_URL")

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace_dir).resolve()

    @property
    def vectorstore_path(self) -> Path:
        return Path(self.vectorstore_dir).resolve()


class Script(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    language: str = Field(default="py")
    path: str
    tags: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScriptRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True, unique=True)
    script_id: Optional[int] = Field(default=None, foreign_key="script.id")
    script_name: Optional[str] = Field(default=None)
    status: str = Field(default="pending")
    stdout_path: Optional[str] = Field(default=None)
    stderr_path: Optional[str] = Field(default=None)
    artifacts_path: Optional[str] = Field(default=None)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = Field(default=None)


class AppSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str


class ScriptBase(BaseModel):
    name: str
    language: str = "py"
    path: str
    tags: List[str] = PydanticField(default_factory=list)


class ScriptCreate(ScriptBase):
    content: str = ""


class ScriptUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    path: Optional[str] = None
    tags: Optional[List[str]] = None
    content: Optional[str] = None


class ScriptRead(ScriptBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ScriptRunRead(BaseModel):
    run_id: str
    script_id: Optional[int]
    script_name: Optional[str]
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    stdout_path: Optional[str]
    stderr_path: Optional[str]
    artifacts_path: Optional[str]


class SettingsPayload(BaseModel):
    data: Dict[str, Any]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    system_prompt: Optional[str] = None


class RagQuery(BaseModel):
    query: str
    collection_id: str
    top_k: int = 3


class RagQueryResponse(BaseModel):
    contexts: List[str]
    answer: str


def ensure_directories(config: AppConfig) -> None:
    config.workspace_path.mkdir(parents=True, exist_ok=True)
    (config.workspace_path / "uploads").mkdir(parents=True, exist_ok=True)
    config.vectorstore_path.mkdir(parents=True, exist_ok=True)
