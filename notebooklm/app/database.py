"""
Connexion SQLAlchemy (SQLite).
SQLite est largement suffisant ici : on ne stocke que les métadonnées
(notebooks, documents, messages). Le contenu vectorisé vit dans ChromaDB.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

os.makedirs(settings.data_dir, exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.sqlite_path}",
    connect_args={"check_same_thread": False},  # nécessaire pour SQLite + FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency FastAPI : une session DB par requête, fermée proprement à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import db_models  # noqa: F401  (assure l'enregistrement des modèles)
    Base.metadata.create_all(bind=engine)
