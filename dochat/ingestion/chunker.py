import re


"""def clean_text(text):

    # Normalise les retours à la ligne
    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # Supprime les espaces multiples
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Supprime les lignes vides excessives
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def split_sentences(text):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def chunk_text(
    text,
    chunk_size=500,
    overlap=100
):

    text = clean_text(text)

    if len(text) <= chunk_size:

        return [text]

    paragraphs = re.split(
        r"\n\s*\n",
        text
    )

    chunks = []

    current = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # Le paragraphe rentre
        if len(current) + len(paragraph) + 1 <= chunk_size:

            if current:
                current += "\n"

            current += paragraph

        else:

            # Sauvegarde du chunk actuel
            if current:

                chunks.append(
                    current.strip()
                )

            # Nouveau chunk
            current = paragraph

    if current:

        chunks.append(
            current.strip()
        )

    # Si certains chunks sont trop grands,
    # on les découpe par phrases.
    final_chunks = []

    for chunk in chunks:

        if len(chunk) <= chunk_size:

            final_chunks.append(chunk)

        else:

            sentences = split_sentences(
                chunk
            )

            current = ""

            for sentence in sentences:

                if (
                    len(current)
                    + len(sentence)
                    + 1
                    <= chunk_size
                ):

                    if current:
                        current += " "

                    current += sentence

                else:

                    if current:
                        final_chunks.append(
                            current.strip()
                        )

                    current = sentence

            if current:

                final_chunks.append(
                    current.strip()
                )

    return final_chunks


def create_chunks(documents):

    chunks = []

    chunk_id = 0

    for document in documents:

        text = document["text"]

        metadata = document["metadata"]

        document_chunks = chunk_text(
            text
        )

        for chunk in document_chunks:

            chunks.append({

                "id": chunk_id,

                "text": chunk,

                "metadata": metadata.copy()

            })

            chunk_id += 1

    return chunks"""

def smart_chunk(
    text,
    max_size=800,
    overlap=100
):

    # --------------------------------------------------
    # Nettoyage
    # --------------------------------------------------

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    text = text.strip()


    # --------------------------------------------------
    # Découpage par paragraphes
    # --------------------------------------------------

    paragraphs = re.split(
        r"\n\s*\n",
        text
    )

    paragraphs = [
        p.strip()
        for p in paragraphs
        if p.strip()
    ]


    chunks = []

    current = ""


    # --------------------------------------------------
    # Construction des chunks
    # --------------------------------------------------

    for paragraph in paragraphs:

        # Le paragraphe tient encore
        if len(current) + len(paragraph) <= max_size:

            if current:

                current += "\n\n"

            current += paragraph

        else:

            # Sauvegarder le chunk actuel
            if current:

                chunks.append(
                    current.strip()
                )


            # Si le paragraphe est trop gros
            if len(paragraph) > max_size:

                sentences = re.split(
                    r"(?<=[.!?])\s+",
                    paragraph
                )

                current = ""

                for sentence in sentences:

                    if (
                        len(current)
                        + len(sentence)
                        <= max_size
                    ):

                        if current:
                            current += " "

                        current += sentence

                    else:

                        if current:

                            chunks.append(
                                current.strip()
                            )

                        current = sentence

            else:

                current = paragraph


    # --------------------------------------------------
    # Dernier chunk
    # --------------------------------------------------

    if current:

        chunks.append(
            current.strip()
        )


    return chunks