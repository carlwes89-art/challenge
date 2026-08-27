import pytest

from app.services import ingestion


def test_get_extension_valid():
    assert ingestion.get_extension("cours.pdf") == "pdf"
    assert ingestion.get_extension("notes.MD") == "md"


def test_get_extension_invalid_raises():
    with pytest.raises(ValueError):
        ingestion.get_extension("archive.zip")


def test_extract_text_txt():
    text = ingestion.extract_text("Bonjour le monde".encode("utf-8"), "txt")
    assert text == "Bonjour le monde"


def test_split_into_chunks_respects_overlap_and_size():
    long_text = "Phrase de test. " * 500
    chunks = ingestion.split_into_chunks(long_text)
    assert len(chunks) > 1
    assert all(len(c) > 0 for c in chunks)


def test_split_into_chunks_drops_tiny_fragments():
    chunks = ingestion.split_into_chunks("court")
    assert chunks == []  # trop court pour être un chunk exploitable
