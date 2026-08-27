"""
Point d'entrée. Lance avec :
    uvicorn app.main:app --reload

Documentation interactive auto-générée disponible sur /docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import notebooks, documents, chat, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Chatbot RAG sur documents (façon NotebookLM) — upload de documents, "
                 "questions/réponses avec citations des sources.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS ouvert : pas de frontend dédié pour l'instant, on garde la porte ouverte
# pour tester depuis un client HTTP ou un futur frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Filet de sécurité : une exception vraiment non gérée (bug, service externe
    en panne...) serait normalement interceptée par le middleware d'erreurs
    de Starlette, qui répond AVANT le middleware CORS — le navigateur reçoit
    alors une réponse sans en-têtes CORS et l'affiche comme un échec réseau
    générique, masquant la vraie cause. Ce handler renvoie une erreur 500
    propre qui passe par le pipeline normal (CORS inclus).
    """
    return JSONResponse(status_code=500, content={"detail": f"Erreur interne : {exc}"})


app.include_router(notebooks.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(stats.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.app_name, "llm_provider": settings.llm_provider}
