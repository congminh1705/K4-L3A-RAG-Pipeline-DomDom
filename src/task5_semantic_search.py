"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection
from .contracts import validate_search_results


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    collection = get_collection()
    available = collection.count() if hasattr(collection, "count") else top_k
    if available <= 0:
        return []
    query_vector = embed_texts([query.strip()])[0]
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, available),
        include=["documents", "metadatas", "distances"],
    )
    results = []
    for item_id, content, metadata, distance in zip(
        response.get("ids", [[]])[0],
        response.get("documents", [[]])[0],
        response.get("metadatas", [[]])[0],
        response.get("distances", [[]])[0],
    ):
        normalized_metadata = dict(metadata or {})
        normalized_metadata["url"] = normalized_metadata.get("url") or None
        results.append({
            "id": item_id,
            "content": content,
            "score": max(0.0, 1.0 - float(distance)),
            "metadata": normalized_metadata,
            "retrieval_method": "dense",
        })
    output = sorted(results, key=lambda item: (-item["score"], item["id"]))[:top_k]
    validate_search_results(output, top_k=top_k, expected_method="dense")
    return output


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
