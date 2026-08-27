from pypdf import PdfReader
from sentence_transformers import SentenceTransformer, CrossEncoder
import os
import re
import math
import ollama


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_PATH = "./documents/POWER - Les 48 lois de pouvoir - Robert Greene.pdf"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

RETRIEVAL_K = 10
FINAL_K = 3

FAITHFULNESS_THRESHOLD = 0.75

LLM_MODEL = "llama3.2:3b"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# ============================================================
# 1. CHARGEMENT DU DOCUMENT
# ============================================================

def load_document(path):

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Document introuvable : {path}"
        )

    extension = os.path.splitext(path)[1].lower()

    if extension == ".pdf":

        pdf = PdfReader(path)

        print(
            "Nombre de pages :",
            len(pdf.pages)
        )

        text_full = ""

        for page in pdf.pages:

            text = page.extract_text()

            if text:
                text_full += text + "\n"

        return text_full

    else:

        raise ValueError(
            "Format non supporté pour le moment. "
            "Utilise un PDF."
        )


# ============================================================
# 2. NETTOYAGE DU TEXTE
# ============================================================

def clean_text(text):

    # Supprimer les espaces multiples
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Réduire les retours à la ligne excessifs
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# 3. CHUNKING
# ============================================================

def split_text(text, max_size=500):

    separators = [
        "\n\n",
        "\n",
        ". ",
        "? ",
        "! ",
        "; "
    ]

    if len(text) <= max_size:
        return [text.strip()]

    for separator in separators:

        if separator not in text:
            continue

        parts = text.split(separator)

        smaller_parts = []

        for part in parts:

            part = part.strip()

            if not part:
                continue

            if len(part) <= max_size:

                smaller_parts.append(part)

            else:

                smaller_parts.extend(
                    split_text(
                        part,
                        max_size
                    )
                )

        return merge_parts(
            smaller_parts,
            max_size
        )

    # Dernier recours :
    # découpage par caractères

    return [
        text[i:i + max_size].strip()
        for i in range(
            0,
            len(text),
            max_size
        )
    ]


def merge_parts(parts, max_size=500):

    chunks = []

    current = ""

    for part in parts:

        if not current:

            current = part

        elif len(current) + len(part) + 1 <= max_size:

            current += "\n" + part

        else:

            chunks.append(
                current.strip()
            )

            current = part

    if current:

        chunks.append(
            current.strip()
        )

    return chunks


# ============================================================
# 4. OVERLAP
# ============================================================

def add_overlap(chunks, overlap=100):

    if overlap <= 0:
        return chunks

    final_chunks = []

    for i, chunk in enumerate(chunks):

        if i == 0:

            final_chunks.append(chunk)

            continue

        previous = chunks[i - 1]

        overlap_text = previous[-overlap:]

        new_chunk = (
            overlap_text +
            "\n" +
            chunk
        )

        final_chunks.append(
            new_chunk
        )

    return final_chunks


# ============================================================
# 5. EMBEDDINGS
# ============================================================

model = SentenceTransformer(
    EMBEDDING_MODEL
)


# ============================================================
# 6. COSINE SIMILARITY FROM SCRATCH
# ============================================================

def cosine_similarity(A, B):

    dot_product = 0

    for i in range(len(A)):

        dot_product += (
            A[i] * B[i]
        )

    norm_A = math.sqrt(
        sum(
            x ** 2
            for x in A
        )
    )

    norm_B = math.sqrt(
        sum(
            x ** 2
            for x in B
        )
    )

    if norm_A == 0 or norm_B == 0:
        return 0

    return dot_product / (
        norm_A * norm_B
    )


# ============================================================
# 7. CONSTRUCTION DE LA VECTOR DB
# ============================================================

def build_vector_db(chunks):

    embeddings = model.encode(
        chunks
    )

    vector_db = []

    for i, chunk in enumerate(chunks):

        vector_db.append({

            "id": i,

            "text": chunk,

            "embedding": embeddings[i]

        })

    return vector_db


# ============================================================
# 8. RETRIEVAL
# ============================================================

def retrieve(
    question,
    vector_db,
    k=10
):

    question_embedding = model.encode(
        question
    )

    scores = []

    for item in vector_db:

        score = cosine_similarity(
            question_embedding,
            item["embedding"]
        )

        scores.append(
            (item, score)
        )

    scores.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return scores[:k]


# ============================================================
# 9. RERANKING
# ============================================================

reranker = CrossEncoder(
    RERANKER_MODEL
)


def rerank(
    question,
    retrieved,
    k=3
):

    pairs = []

    for item, embedding_score in retrieved:

        pairs.append([
            question,
            item["text"]
        ])

    rerank_scores = reranker.predict(
        pairs
    )

    ranked = []

    for i in range(
        len(retrieved)
    ):

        item, embedding_score = retrieved[i]

        ranked.append(
            (
                item,
                rerank_scores[i]
            )
        )

    ranked.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return ranked[:k]


# ============================================================
# 10. CONSTRUCTION DU CONTEXTE
# ============================================================

def build_context(results):

    context = ""

    for item, score in results:

        context += (
            item["text"] +
            "\n\n"
        )

    return context.strip()


# ============================================================
# 11. GÉNÉRATION DE LA RÉPONSE
# ============================================================

def generate_answer(
    question,
    context
):

    prompt = f"""
Tu es un assistant RAG.

Tu dois répondre uniquement à partir
du contexte fourni.

Si la réponse n'est pas présente dans
le contexte, dis clairement que
l'information n'est pas disponible.

Ne crée aucune information.

CONTEXTE :
{context}

QUESTION :
{question}

RÉPONSE :
"""

    response = ollama.chat(

        model=LLM_MODEL,

        messages=[

            {
                "role": "user",
                "content": prompt
            }

        ]
    )

    return response[
        "message"
    ]["content"]


# ============================================================
# 12. EXTRACTION DES CLAIMS
# ============================================================

def extract_claims(answer):

    claims = re.split(
        r"[.!?]\s+",
        answer
    )

    return [
        claim.strip()
        for claim in claims
        if claim.strip()
    ]


def split_context(context):
    """
    Transforme un contexte RAG en passages.
    Fonctionne quel que soit le type de document
    tant que le texte a été correctement extrait.
    """

    if not context:
        return []

    # Nettoyage des retours à la ligne
    context = context.replace("\r\n", "\n")

    # Séparation par blocs
    passages = re.split(r"\n\s*\n|\n", context)

    passages = [
        passage.strip()
        for passage in passages
        if passage.strip()
    ]

    return passages

# ============================================================
# 13. VÉRIFICATION D'UNE CLAIM
# ============================================================

def verify_claim(claim, context, threshold=0.75):

    claim_embedding = model.encode(claim)

    passages = split_context(context)

    best_score = 0
    best_passage = ""

    for passage in passages:

        passage_embedding = model.encode(passage)

        score = cosine_similarity(
            claim_embedding,
            passage_embedding
        )

        if score > best_score:
            best_score = score
            best_passage = passage

    supported = best_score >= threshold

    return {
        "claim": claim,
        "score": best_score,
        "supported": supported,
        "best_passage": best_passage
    }


# ============================================================
# 14. ÉVALUATION DE LA FIDÉLITÉ
# ============================================================

def evaluate_faithfulness(answer, context, threshold=0.75):

    claims = extract_claims(answer)

    if not claims:
        return 0

    supported_count = 0

    print("=" * 60)
    print("FAITHFULNESS")
    print("=" * 60)

    for claim in claims:

        result = verify_claim(
            claim,
            context,
            threshold
        )

        print("CLAIM :", result["claim"])
        print("BEST PASSAGE :", result["best_passage"])
        print("SCORE :", result["score"])
        print("SUPPORTED :", result["supported"])
        print("=" * 60)

        if result["supported"]:
            supported_count += 1

    faithfulness = supported_count / len(claims)

    print("FAITHFULNESS :", faithfulness)

    return faithfulness


# ============================================================
# 15. PIPELINE COMPLET
# ============================================================

def build_rag(path):

    print("=" * 60)
    print("CHARGEMENT DU DOCUMENT")
    print("=" * 60)

    text = load_document(
        path
    )

    text = clean_text(
        text
    )

    print(
        "Nombre de caractères :",
        len(text)
    )


    print("\n" + "=" * 60)
    print("CHUNKING")
    print("=" * 60)

    chunks = split_text(
        text,
        CHUNK_SIZE
    )

    chunks = add_overlap(
        chunks,
        CHUNK_OVERLAP
    )

    print(
        "Nombre de chunks :",
        len(chunks)
    )


    print("\n" + "=" * 60)
    print("VECTOR DATABASE")
    print("=" * 60)

    vector_db = build_vector_db(
        chunks
    )

    print(
        "Vector DB créée avec",
        len(vector_db),
        "chunks"
    )

    return vector_db


# ============================================================
# 16. QUESTION AU RAG
# ============================================================

def ask_rag(
    question,
    vector_db
):

    print("\n")
    print("=" * 60)
    print("QUESTION")
    print("=" * 60)

    print(question)


    # --------------------------------------------
    # Retrieval
    # --------------------------------------------

    retrieved = retrieve(
        question,
        vector_db,
        RETRIEVAL_K
    )


    print("\n")
    print("=" * 60)
    print("RETRIEVAL")
    print("=" * 60)

    for item, score in retrieved:

        print(
            "SCORE :",
            score
        )

        print(
            item["text"]
        )

        print(
            "-" * 60
        )


    # --------------------------------------------
    # Reranking
    # --------------------------------------------

    reranked = rerank(
        question,
        retrieved,
        FINAL_K
    )


    print("\n")
    print("=" * 60)
    print("RERANKING")
    print("=" * 60)

    for item, score in reranked:

        print(
            "RERANK SCORE :",
            score
        )

        print(
            item["text"]
        )

        print(
            "-" * 60
        )


    # --------------------------------------------
    # Context
    # --------------------------------------------

    context = build_context(
        reranked
    )


    # --------------------------------------------
    # LLM
    # --------------------------------------------

    answer = generate_answer(
        question,
        context
    )


    print("\n")
    print("=" * 60)
    print("RÉPONSE")
    print("=" * 60)

    print(answer)


    # --------------------------------------------
    # Faithfulness
    # --------------------------------------------

    print("\n")
    print("=" * 60)
    print("FAITHFULNESS")
    print("=" * 60)

    faithfulness = (
        evaluate_faithfulness(
            answer,
            context
        )
    )

    print(
        "FAITHFULNESS :",
        faithfulness
    )

    return answer


# ============================================================
# 17. INITIALISATION
# ============================================================

vector_db = build_rag(
    DOCUMENT_PATH
)


# ============================================================
# 18. INTERFACE QUESTIONS
# ============================================================

while True:

    question = input(
        "\nPose ta question "
        "(ou 'exit' pour quitter) : "
    )

    if question.lower() == "exit":
        break

    ask_rag(
        question,
        vector_db
    )