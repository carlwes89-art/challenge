"""
Le pipeline RAG, explicite (pas caché derrière une chaîne LangChain opaque) :

1. RETRIEVE : on cherche les chunks les plus proches sémantiquement de la question
   dans la collection Chroma du notebook.
2. AUGMENT  : on construit un prompt qui contient ces chunks numérotés comme
   "sources" et on instruit le modèle à ne répondre qu'à partir d'elles.
3. GENERATE : le LLM répond en citant les sources par leur numéro [1], [2]...
4. On remappe ces numéros vers les vraies références (fichier, chunk) pour
   renvoyer des citations exploitables au client (comme NotebookLM qui affiche
   la source cliquable à côté de chaque affirmation).

Si aucun chunk pertinent n'est trouvé (notebook vide, ou question hors sujet),
on le dit explicitement plutôt que de laisser le LLM halluciner une réponse.
"""
import re
import time

from app.config import settings
from app.services import vectorstore, llm
from app.schemas import SourceChunk

SYSTEM_PROMPT = """Tu es un assistant qui répond UNIQUEMENT à partir des sources fournies.

Règles strictes :
- N'utilise que les informations présentes dans les sources ci-dessous.
- Si la réponse ne se trouve pas dans les sources, dis clairement que tu ne peux pas répondre avec les documents fournis. N'invente jamais.
- Cite systématiquement tes affirmations avec le numéro de la source entre crochets, par exemple [1] ou [2].
- Réponds dans la langue de la question."""


def _build_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        blocks.append(f"[{i}] (source: {hit['filename']})\n{hit['text']}")
    return "\n\n".join(blocks)


def _build_history_block(history: list[dict] | None) -> str:
    if not history:
        return ""
    lines = [f"{'Utilisateur' if m['role'] == 'user' else 'Assistant'} : {m['content']}" for m in history]
    return "Historique de la conversation :\n" + "\n".join(lines) + "\n\n"


def answer_question(
    notebook_id: str,
    question: str,
    history: list[dict] | None = None,
    provider_override: str | None = None,
) -> dict:
    """
    Retourne toujours la même forme de dict (answer, sources, provider,
    retrieval_ms, generation_ms), y compris quand aucune source n'est trouvée,
    pour que l'appelant (router chat, outil de comparaison, logging des stats)
    n'ait jamais de cas particulier à gérer.
    """
    provider = provider_override or settings.llm_provider

    t0 = time.perf_counter()
    hits = vectorstore.query(notebook_id, question)
    retrieval_ms = (time.perf_counter() - t0) * 1000

    if not hits:
        return {
            "answer": "Je n'ai trouvé aucune source pertinente dans ce notebook pour répondre à "
                      "cette question. Ajoute des documents ou reformule ta question.",
            "sources": [],
            "provider": provider,
            "retrieval_ms": retrieval_ms,
            "generation_ms": 0.0,
        }

    context = _build_context(hits)
    history_block = _build_history_block(history)
    user_prompt = (
        f"{history_block}Sources disponibles :\n\n{context}\n\n"
        f"Question : {question}\n\n"
        "Réponds en citant les sources utilisées avec [numéro]."
    )

    t1 = time.perf_counter()
    raw_answer = llm.generate(SYSTEM_PROMPT, user_prompt, provider_override=provider_override)
    generation_ms = (time.perf_counter() - t1) * 1000

    # On ne garde dans les citations retournées que les sources réellement
    # référencées par le modèle dans sa réponse (ex: [1], [3])
    cited_indices = {int(n) for n in re.findall(r"\[(\d+)\]", raw_answer)}
    sources = []
    for i, hit in enumerate(hits, start=1):
        if not cited_indices or i in cited_indices:
            sources.append(
                SourceChunk(
                    document_id=hit["document_id"],
                    filename=hit["filename"],
                    chunk_index=hit["chunk_index"],
                    excerpt=hit["text"][:280] + ("..." if len(hit["text"]) > 280 else ""),
                )
            )

    return {
        "answer": raw_answer,
        "sources": sources,
        "provider": provider,
        "retrieval_ms": retrieval_ms,
        "generation_ms": generation_ms,
    }


def compare_providers(notebook_id: str, question: str, history: list[dict] | None = None) -> list[dict]:
    """
    Exécute la même question sur tous les providers disponibles (Ollama,
    et Anthropic si une clé API est configurée), pour l'outil de comparaison
    de l'espace développeur. Un échec sur un provider n'empêche pas les autres
    de répondre.
    """
    results = []
    for provider in llm.available_providers():
        try:
            result = answer_question(notebook_id, question, history=history, provider_override=provider)
            result["error"] = None
            results.append(result)
        except Exception as e:
            results.append(
                {
                    "provider": provider,
                    "answer": None,
                    "sources": [],
                    "retrieval_ms": 0.0,
                    "generation_ms": 0.0,
                    "error": str(e),
                }
            )
    return results
