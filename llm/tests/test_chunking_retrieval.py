import pytest

from app.chunking import chunk_pages
from app.retrieval import BM25Index


def test_chunks_respect_size_and_keep_pages():
    pages = ["word " * 600, "short page text"]
    chunks = chunk_pages(pages, size=200, overlap=40)
    assert all(len(c.text) <= 200 for c in chunks)
    assert chunks[-1].page == 2
    assert [c.id for c in chunks] == list(range(len(chunks)))


def test_chunks_overlap():
    text = " ".join(f"w{i}" for i in range(300))
    chunks = chunk_pages([text], size=200, overlap=50)
    assert len(chunks) > 2
    first_tail = set(chunks[0].text.split()[-5:])
    assert first_tail & set(chunks[1].text.split())


def test_invalid_overlap_rejected():
    with pytest.raises(ValueError):
        chunk_pages(["x"], size=100, overlap=80)


def test_empty_pages_produce_no_chunks():
    assert chunk_pages(["", "   "]) == []


def test_bm25_ranks_relevant_chunk_first():
    chunks = chunk_pages(
        [
            "The grace period for premium payment is thirty days.",
            "Maternity expenses are covered after twenty four months.",
            "Cataract surgery has a waiting period of two years.",
        ],
        size=200,
        overlap=20,
    )
    index = BM25Index(chunks)
    assert "maternity" in index.search("Is maternity covered?", 1)[0].text.lower()
    assert "grace" in index.search("grace period payment", 1)[0].text.lower()
    assert index.search("zzzz qqqq", 3) == []
