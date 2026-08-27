"""
Un "notebook" = un espace de travail isolé, comme dans NotebookLM.
Chaque notebook a ses propres documents, sa propre collection vectorielle,
et son propre historique de conversation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import db_models, schemas
from app.services import vectorstore

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.post("", response_model=schemas.NotebookOut, status_code=201)
def create_notebook(payload: schemas.NotebookCreate, db: Session = Depends(get_db)):
    notebook = db_models.Notebook(name=payload.name, description=payload.description)
    db.add(notebook)
    db.commit()
    db.refresh(notebook)
    return schemas.NotebookOut(**notebook.__dict__, document_count=0)


@router.get("", response_model=list[schemas.NotebookOut])
def list_notebooks(db: Session = Depends(get_db)):
    notebooks = db.query(db_models.Notebook).all()
    return [
        schemas.NotebookOut(**nb.__dict__, document_count=len(nb.documents))
        for nb in notebooks
    ]


@router.get("/{notebook_id}", response_model=schemas.NotebookOut)
def get_notebook(notebook_id: str, db: Session = Depends(get_db)):
    notebook = db.get(db_models.Notebook, notebook_id)
    if not notebook:
        raise HTTPException(404, "Notebook introuvable")
    return schemas.NotebookOut(**notebook.__dict__, document_count=len(notebook.documents))


@router.delete("/{notebook_id}", status_code=204)
def delete_notebook(notebook_id: str, db: Session = Depends(get_db)):
    notebook = db.get(db_models.Notebook, notebook_id)
    if not notebook:
        raise HTTPException(404, "Notebook introuvable")
    vectorstore.delete_notebook_collection(notebook_id)  # nettoie aussi Chroma
    db.delete(notebook)
    db.commit()
