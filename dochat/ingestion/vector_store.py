import faiss
import numpy as np
import json
from pathlib import Path


class VectorStore:

    def __init__(self, dimension):

        self.dimension = dimension

        # Index FAISS pour cosine similarity
        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.metadata = []


    # ========================================================
    # AJOUTER DES EMBEDDINGS
    # ========================================================

    def add(self, embeddings, chunks):

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        # Normalisation
        faiss.normalize_L2(
            embeddings
        )

        self.index.add(
            embeddings
        )

        self.metadata.extend(
            chunks
        )


    # ========================================================
    # RECHERCHE
    # ========================================================

    def search(self, query_embedding, k=5):

        query_embedding = np.asarray(
            [query_embedding],
            dtype="float32"
        )

        faiss.normalize_L2(
            query_embedding
        )

        scores, ids = self.index.search(
            query_embedding,
            k
        )

        results = []

        for score, idx in zip(
            scores[0],
            ids[0]
        ):

            if idx == -1:
                continue

            results.append({
                "score": float(score),

                "chunk": self.metadata[idx]
            })

        return results


    # ========================================================
    # SAUVEGARDE
    # ========================================================

    def save(self, directory):

        directory = Path(directory)

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            str(
                directory / "index.faiss"
            )
        )

        with open(
            directory / "metadata.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.metadata,
                file,
                ensure_ascii=False,
                indent=2
            )


    # ========================================================
    # CHARGEMENT
    # ========================================================

    @classmethod
    def load(cls, directory):

        directory = Path(directory)

        index = faiss.read_index(
            str(
                directory / "index.faiss"
            )
        )

        with open(
            directory / "metadata.json",
            "r",
            encoding="utf-8"
        ) as file:

            metadata = json.load(
                file
            )

        store = cls(
            index.d
        )

        store.index = index

        store.metadata = metadata

        return store