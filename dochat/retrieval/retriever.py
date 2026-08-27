import numpy as np


class Retriever:

    def __init__(self, vector_store, embedding_model):

        self.vector_store = vector_store
        self.embedding_model = embedding_model


    # ========================================================
    # EMBEDDING DE LA QUESTION
    # ========================================================

    def embed_query(self, question):

        embedding = self.embedding_model.encode(
            question,
            convert_to_numpy=True
        )

        return embedding


    # ========================================================
    # RECHERCHE
    # ========================================================

    def retrieve(
        self,
        question,
        k=5,
        score_threshold=None
    ):

        # ----------------------------------------------------
        # 1. Transformer la question en vecteur
        # ----------------------------------------------------

        query_embedding = self.embed_query(
            question
        )


        # ----------------------------------------------------
        # 2. Recherche FAISS
        # ----------------------------------------------------

        results = self.vector_store.search(
            query_embedding,
            k=k
        )


        # ----------------------------------------------------
        # 3. Filtrage par score
        # ----------------------------------------------------

        if score_threshold is not None:

            results = [
                result
                for result in results
                if result["score"] >= score_threshold
            ]


        return results


    # ========================================================
    # AFFICHAGE
    # ========================================================

    def display_results(self, results):

        print()
        print("=" * 60)
        print("RETRIEVAL")
        print("=" * 60)

        for i, result in enumerate(results):

            print(
                f"\nRESULTAT {i + 1}"
            )

            print(
                "SCORE :",
                result["score"]
            )

            chunk = result["chunk"]

            print(
                "SOURCE :",
                chunk.get(
                    "metadata",
                    {}
                ).get(
                    "source",
                    "unknown"
                )
            )

            metadata = chunk.get(
                "metadata",
                {}
            )

            if "page" in metadata:

                print(
                    "PAGE :",
                    metadata["page"]
                )

            print(
                "\nTEXT :"
            )

            print(
                chunk["text"]
            )

            print(
                "-" * 60
            )