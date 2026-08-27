"""
Endpoints purement analytiques : rien ici ne modifie l'état de l'application,
tout est calculé à la volée à partir de SQLite (métadonnées + QueryLog).
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import db_models, schemas

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=schemas.StatsOverview)
def overview(db: Session = Depends(get_db)):
    documents_count = db.query(db_models.Document).count()
    documents_ready = (
        db.query(db_models.Document).filter(db_models.Document.status == "ready").count()
    )
    documents_error = (
        db.query(db_models.Document).filter(db_models.Document.status == "error").count()
    )
    total_chunks = db.query(func.sum(db_models.Document.num_chunks)).scalar() or 0
    total_queries = db.query(db_models.QueryLog).count()
    avg_retrieval = db.query(func.avg(db_models.QueryLog.retrieval_ms)).scalar() or 0.0
    avg_generation = db.query(func.avg(db_models.QueryLog.generation_ms)).scalar() or 0.0

    return schemas.StatsOverview(
        notebooks_count=db.query(db_models.Notebook).count(),
        documents_count=documents_count,
        documents_ready=documents_ready,
        documents_error=documents_error,
        total_chunks=int(total_chunks),
        total_queries=total_queries,
        avg_retrieval_ms=round(avg_retrieval, 1),
        avg_generation_ms=round(avg_generation, 1),
        active_provider=settings.llm_provider,
        anthropic_configured=bool(settings.anthropic_api_key),
    )


@router.get("/queries", response_model=list[schemas.QueryLogOut])
def recent_queries(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(db_models.QueryLog)
        .order_by(db_models.QueryLog.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/providers", response_model=list[schemas.ProviderStat])
def provider_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(
            db_models.QueryLog.provider,
            func.count(db_models.QueryLog.id),
            func.avg(db_models.QueryLog.retrieval_ms),
            func.avg(db_models.QueryLog.generation_ms),
            func.avg(db_models.QueryLog.total_ms),
        )
        .group_by(db_models.QueryLog.provider)
        .all()
    )
    return [
        schemas.ProviderStat(
            provider=provider,
            count=count,
            avg_retrieval_ms=round(avg_retrieval or 0.0, 1),
            avg_generation_ms=round(avg_generation or 0.0, 1),
            avg_total_ms=round(avg_total or 0.0, 1),
        )
        for provider, count, avg_retrieval, avg_generation, avg_total in rows
    ]


@router.get("/notebooks", response_model=list[schemas.NotebookStats])
def notebook_stats(db: Session = Depends(get_db)):
    notebooks = db.query(db_models.Notebook).all()
    out = []
    for nb in notebooks:
        query_count = (
            db.query(db_models.QueryLog).filter(db_models.QueryLog.notebook_id == nb.id).count()
        )
        out.append(
            schemas.NotebookStats(
                id=nb.id,
                name=nb.name,
                document_count=len(nb.documents),
                chunk_count=sum(d.num_chunks for d in nb.documents),
                query_count=query_count,
            )
        )
    return out
