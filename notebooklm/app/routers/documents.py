"""
Pipeline complet déclenché à l'upload :
fichier -> extraction texte -> chunking -> embeddings -> stockage Chroma
                                                        -> métadonnées SQLite

Traitement synchrone volontairement (simple, prévisible, suffisant pour la
taille de documents d'un challenge). Pour passer à l'échelle en prod, cette
étape partirait en tâche de fond (Celery / BackgroundTasks FastAPI).
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app import db_models, schemas
from app.services import ingestion, vectorstore

router = APIRouter(prefix="/notebooks/{notebook_id}/documents", tags=["documents"])


def _get_notebook_or_404(notebook_id: str, db: Session) -> db_models.Notebook:
    notebook = db.get(db_models.Notebook, notebook_id)
    if not notebook:
        raise HTTPException(404, "Notebook introuvable")
    return notebook


@router.post("", response_model=schemas.DocumentOut, status_code=201)
async def upload_document(
    notebook_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    _get_notebook_or_404(notebook_id, db)

    try:
        extension = ingestion.get_extension(file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    document = db_models.Document(
        notebook_id=notebook_id,
        filename=file.filename,
        file_type=extension,
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        file_bytes = await file.read()
        text = ingestion.extract_text(file_bytes, extension)
        if not text.strip():
            raise ValueError("Aucun texte extractible (fichier vide, scanné sans OCR, etc.)")

        chunks = ingestion.split_into_chunks(text)
        num_added = vectorstore.add_chunks(notebook_id, document.id, file.filename, chunks)

        document.status = "ready"
        document.num_chunks = num_added
    except Exception as e:
        document.status = "error"
        document.error_message = str(e)

    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=list[schemas.DocumentOut])
def list_documents(notebook_id: str, db: Session = Depends(get_db)):
    _get_notebook_or_404(notebook_id, db)
    return (
        db.query(db_models.Document)
        .filter(db_models.Document.notebook_id == notebook_id)
        .all()
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(notebook_id: str, document_id: str, db: Session = Depends(get_db)):
    _get_notebook_or_404(notebook_id, db)
    document = db.get(db_models.Document, document_id)
    if not document or document.notebook_id != notebook_id:
        raise HTTPException(404, "Document introuvable")

    vectorstore.delete_document(notebook_id, document_id)
    db.delete(document)
    db.commit()
