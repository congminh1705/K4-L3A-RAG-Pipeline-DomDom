"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import math
import re
import unicodedata
from collections import Counter

from .contracts import validate_search_results


CORPUS: list[dict] = []


def _tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    return re.findall(r"[^\W_]+", text, flags=re.UNICODE)


class BM25Index:
    """Small dependency-free BM25 implementation for a reproducible local index."""

    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.documents = [Counter(tokens) for tokens in tokenized_corpus]
        self.lengths = [len(tokens) for tokens in tokenized_corpus]
        self.average_length = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        self.k1 = k1
        self.b = b
        document_frequency: Counter[str] = Counter()
        for terms in self.documents:
            document_frequency.update(terms.keys())
        count = len(self.documents)
        self.idf = {
            term: math.log(1.0 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores: list[float] = []
        for terms, length in zip(self.documents, self.lengths):
            score = 0.0
            norm = self.k1 * (
                1.0 - self.b + self.b * length / (self.average_length or 1.0)
            )
            for token in query_tokens:
                frequency = terms.get(token, 0)
                if frequency:
                    score += self.idf.get(token, 0.0) * (
                        frequency * (self.k1 + 1.0) / (frequency + norm)
                    )
            scores.append(score)
        return scores


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    return BM25Index([_tokenize(item["content"]) for item in corpus])


def _get_corpus() -> list[dict]:
    global CORPUS
    if not CORPUS:
        from .task4_chunking_indexing import chunk_documents, load_documents

        CORPUS = chunk_documents(load_documents())
    return CORPUS


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    corpus = _get_corpus()
    if not corpus:
        return []
    bm25 = build_bm25_index(corpus)
    scores = bm25.get_scores(_tokenize(query))
    ranked_indices = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
    results = []
    for index in ranked_indices:
        if scores[index] <= 0 or len(results) >= top_k:
            break
        item = corpus[index]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": dict(item["metadata"]),
            "retrieval_method": "bm25",
        })
    validate_search_results(results, top_k=top_k, expected_method="bm25")
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
