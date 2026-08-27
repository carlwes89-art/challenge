"""
Wrapper autour de ChromaDB.

Choix clé : une collection Chroma PAR notebook (préfixée "notebook_<id>").
Ça isole complètement les sources d'un notebook par rapport aux autres,
exactement comme NotebookLM ne mélange jamais les sources entre projets.

Les embeddings sont calculés localement avec sentence-transformers
(aucun appel API, aucun coût, fonctionne offline).
"""
import chromadb
from chromadb.utils import embedding_functions

from app.config import settings

_client = None
_embedding_fn = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_dir)
    return _client


def get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        # Charge le modèle sentence-transformers une seule fois (coûteux au 1er appel)
        model_name = settings.embedding_model.split("/")[-1]
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=f"sentence-transformers/{model_name}"
        )
    return _embedding_fn


def _collection_name(notebook_id: str) -> str:
    return f"notebook_{notebook_id}"


def get_collection(notebook_id: str):
    return get_client().get_or_create_collection(
        name=_collection_name(notebook_id),
        embedding_function=get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def _collection_exists(notebook_id: str) -> bool:
    existing = {c.name for c in get_client().list_collections()}
    return _collection_name(notebook_id) in existing


def add_chunks(notebook_id: str, document_id: str, filename: str, chunks: list[str]) -> int:
    """Ajoute les chunks d'un document dans la collection du notebook. Retourne le nombre ajouté."""
    if not chunks:
        return 0
    collection = get_collection(notebook_id)
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "filename": filename, "chunk_index": i}
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def query(notebook_id: str, question: str, top_k: int | None = None) -> list[dict]:
    """Retourne les top_k chunks les plus pertinents pour la question, tous documents confondus."""
    # Court-circuit AVANT de charger le modèle d'embeddings (coûteux) si le
    # notebook n'a encore aucun document indexé -> pas de collection créée.
    if not _collection_exists(notebook_id):
        return []

    collection = get_collection(notebook_id)
    if collection.count() == 0:
        return []
    k = min(top_k or settings.top_k, collection.count())
    results = collection.query(query_texts=[question], n_results=k)

    hits = []
    for text, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append(
            {
                "text": text,
                "document_id": meta["document_id"],
                "filename": meta["filename"],
                "chunk_index": meta["chunk_index"],
                "distance": distance,
            }
        )
    return hits


def delete_document(notebook_id: str, document_id: str) -> None:
    collection = get_collection(notebook_id)
    collection.delete(where={"document_id": document_id})


def delete_notebook_collection(notebook_id: str) -> None:
    try:
        get_client().delete_collection(name=_collection_name(notebook_id))
    except Exception:
        pass  # collection jamais créée (notebook sans documents) -> pas grave
