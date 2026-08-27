"""
Modèles ORM SQLAlchemy = les tables de métadonnées.
Un Notebook regroupe des Documents (ses "sources") et des ChatMessages (l'historique).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Notebook(Base):
    __tablename__ = "notebooks"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    created_at = Column(DateTime, default=_now)

    documents = relationship("Document", back_populates="notebook", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="notebook", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    notebook_id = Column(String, ForeignKey("notebooks.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)          # pdf / docx / txt / md
    status = Column(String, default="processing")        # processing / ready / error
    num_chunks = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=_now)

    notebook = relationship("Notebook", back_populates="documents")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=_uuid)
    notebook_id = Column(String, ForeignKey("notebooks.id"), nullable=False)
    role = Column(String, nullable=False)                 # "user" / "assistant"
    content = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)             # citations, stockées en JSON
    created_at = Column(DateTime, default=_now)

    notebook = relationship("Notebook", back_populates="messages")


class QueryLog(Base):
    """
    Une ligne par exécution du pipeline RAG (question posée), qu'elle vienne
    du chat normal ou de l'outil de comparaison dev. Sert de base à toutes
    les statistiques de l'espace développeur (latences, usage par provider...).
    """
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=_uuid)
    notebook_id = Column(String, ForeignKey("notebooks.id"), nullable=False)
    question = Column(Text, nullable=False)
    provider = Column(String, nullable=False)             # "ollama" / "anthropic"
    retrieval_ms = Column(Float, default=0.0)
    generation_ms = Column(Float, default=0.0)
    total_ms = Column(Float, default=0.0)
    num_sources = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)
