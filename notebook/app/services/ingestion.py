"""
Ingestion : fichier brut -> texte -> chunks.

Étape 1 (extract_text) : chaque format a son propre parseur, on normalise
tout en texte brut.
Étape 2 (split_into_chunks) : on découpe en morceaux qui se chevauchent
légèrement (chunk_overlap) pour ne jamais couper une idée en plein milieu
et perdre le contexte nécessaire à la génération de réponse.
"""
from io import BytesIO

from pypdf import PdfReader
import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt", "md"}


def get_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Format '.{ext}' non supporté. Formats acceptés : {sorted(SUPPORTED_EXTENSIONS)}"
        )
    return ext


def extract_text(file_bytes: bytes, extension: str) -> str:
    """Extrait le texte brut d'un fichier selon son extension."""
    if extension == "pdf":
        return _extract_pdf(file_bytes)
    if extension == "docx":
        return _extract_docx(file_bytes)
    if extension in ("txt", "md"):
        return file_bytes.decode("utf-8", errors="ignore")
    raise ValueError(f"Extension non gérée : {extension}")


def _extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    return "\n\n".join(pages_text)


def _extract_docx(file_bytes: bytes) -> str:
    document = docx.Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def split_into_chunks(text: str) -> list[str]:
    """
    Découpe le texte en chunks avec chevauchement.
    RecursiveCharacterTextSplitter essaie de couper aux frontières naturelles
    (paragraphe > phrase > mot) plutôt qu'à un nombre de caractères brut.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    # on jette les chunks vides ou quasi vides (ex: pages blanches de PDF scannés)
    return [c.strip() for c in chunks if len(c.strip()) > 20]
