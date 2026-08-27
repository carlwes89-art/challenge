"""
Le chat garde la mémoire de la conversation par notebook (comme NotebookLM
qui permet des questions de suivi du type "et pour le deuxième point ?").
On repasse les derniers échanges au LLM pour qu'il ait le contexte.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import db_models, schemas
from app.services import rag

router = APIRouter(prefix="/notebooks/{notebook_id}/chat", tags=["chat"])

MAX_HISTORY_MESSAGES = 6  # on ne garde que les derniers échanges pour ne pas exploser le contexte


def _get_notebook_or_404(notebook_id: str, db: Session) -> db_models.Notebook:
    notebook = db.get(db_models.Notebook, notebook_id)
    if not notebook:
        raise HTTPException(404, "Notebook introuvable")
    return notebook


def _log_query(db: Session, notebook_id: str, question: str, result: dict) -> None:
    """Trace chaque exécution du pipeline RAG pour alimenter les stats de l'espace dev."""
    db.add(
        db_models.QueryLog(
            notebook_id=notebook_id,
            question=question,
            provider=result["provider"],
            retrieval_ms=result["retrieval_ms"],
            generation_ms=result["generation_ms"],
            total_ms=result["retrieval_ms"] + result["generation_ms"],
            num_sources=len(result["sources"]),
        )
    )


@router.post("", response_model=schemas.ChatResponse)
def ask_question(notebook_id: str, payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    _get_notebook_or_404(notebook_id, db)

    past_messages = (
        db.query(db_models.ChatMessage)
        .filter(db_models.ChatMessage.notebook_id == notebook_id)
        .order_by(db_models.ChatMessage.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(past_messages)]

    try:
        result = rag.answer_question(notebook_id, payload.question, history=history)
    except Exception as e:
        # Convertie en HTTPException : ce chemin passe par le gestionnaire
        # d'erreurs standard de Starlette, qui applique bien les en-têtes CORS
        # (contrairement à une exception non gérée qui remonterait brute et
        # ferait échouer la requête côté navigateur avec un NetworkError).
        raise HTTPException(502, f"Le moteur LLM a échoué : {e}")

    # on sauvegarde les deux messages (question + réponse) pour l'historique
    user_msg = db_models.ChatMessage(
        notebook_id=notebook_id, role="user", content=payload.question
    )
    assistant_msg = db_models.ChatMessage(
        notebook_id=notebook_id,
        role="assistant",
        content=result["answer"],
        sources_json=json.dumps([s.model_dump() for s in result["sources"]]),
    )
    db.add_all([user_msg, assistant_msg])
    _log_query(db, notebook_id, payload.question, result)
    db.commit()

    return schemas.ChatResponse(answer=result["answer"], sources=result["sources"])


@router.post("/compare", response_model=schemas.CompareResponse)
def compare_providers(notebook_id: str, payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Outil pour l'espace développeur : exécute la même question sur tous les
    moteurs LLM disponibles et renvoie les réponses côte à côte avec leurs
    latences. Ne touche PAS à l'historique de conversation affiché à
    l'utilisateur final (c'est un outil d'inspection, pas une vraie question
    dans le notebook) mais les exécutions réussies sont quand même tracées
    dans QueryLog pour les statistiques.
    """
    _get_notebook_or_404(notebook_id, db)

    raw_results = rag.compare_providers(notebook_id, payload.question)

    provider_results = []
    for r in raw_results:
        if r.get("error"):
            provider_results.append(schemas.ProviderResult(provider=r["provider"], error=r["error"]))
        else:
            provider_results.append(
                schemas.ProviderResult(
                    provider=r["provider"],
                    answer=r["answer"],
                    sources=r["sources"],
                    retrieval_ms=r["retrieval_ms"],
                    generation_ms=r["generation_ms"],
                )
            )
            _log_query(db, notebook_id, payload.question, r)

    db.commit()
    return schemas.CompareResponse(results=provider_results)


@router.get("", response_model=list[schemas.ChatMessageOut])
def get_history(notebook_id: str, db: Session = Depends(get_db)):
    _get_notebook_or_404(notebook_id, db)
    messages = (
        db.query(db_models.ChatMessage)
        .filter(db_models.ChatMessage.notebook_id == notebook_id)
        .order_by(db_models.ChatMessage.created_at.asc())
        .all()
    )
    out = []
    for m in messages:
        sources = json.loads(m.sources_json) if m.sources_json else []
        out.append(
            schemas.ChatMessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=sources,
                created_at=m.created_at,
            )
        )
    return out
