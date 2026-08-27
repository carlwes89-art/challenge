"""
Schémas Pydantic : ce que l'API reçoit et renvoie.
Séparés des modèles ORM (app/db_models.py) pour ne jamais exposer la DB directement.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ---------- Notebooks ----------

class NotebookCreate(BaseModel):
    name: str
    description: str = ""


class NotebookOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    document_count: int = 0

    model_config = {"from_attributes": True}


# ---------- Documents ----------

class DocumentOut(BaseModel):
    id: str
    notebook_id: str
    filename: str
    file_type: str
    status: str
    num_chunks: int
    error_message: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ---------- Chat ----------

class ChatRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list[SourceChunk] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Comparaison de providers (outil dev) ----------

class ProviderResult(BaseModel):
    provider: str
    answer: Optional[str] = None
    sources: list[SourceChunk] = []
    retrieval_ms: float = 0.0
    generation_ms: float = 0.0
    error: Optional[str] = None


class CompareResponse(BaseModel):
    results: list[ProviderResult]


# ---------- Statistiques (espace développeur) ----------

class StatsOverview(BaseModel):
    notebooks_count: int
    documents_count: int
    documents_ready: int
    documents_error: int
    total_chunks: int
    total_queries: int
    avg_retrieval_ms: float
    avg_generation_ms: float
    active_provider: str
    anthropic_configured: bool


class QueryLogOut(BaseModel):
    id: str
    notebook_id: str
    question: str
    provider: str
    retrieval_ms: float
    generation_ms: float
    total_ms: float
    num_sources: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProviderStat(BaseModel):
    provider: str
    count: int
    avg_retrieval_ms: float
    avg_generation_ms: float
    avg_total_ms: float


class NotebookStats(BaseModel):
    id: str
    name: str
    document_count: int
    chunk_count: int
    query_count: int
