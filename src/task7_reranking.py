"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""

from .contracts import validate_search_results


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    if top_k <= 0:
        return []
    if k < 0:
        raise ValueError("k must be non-negative")

    scores: dict[str, float] = {}
    best_rank: dict[str, int] = {}
    items: dict[str, dict] = {}
    for ranked_list in ranked_lists:
        seen_in_list: set[str] = set()
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            if item_id in seen_in_list:
                continue
            seen_in_list.add(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            best_rank[item_id] = min(best_rank.get(item_id, rank), rank)
            items.setdefault(item_id, item)

    ranked_ids = sorted(
        scores,
        key=lambda item_id: (-scores[item_id], best_rank[item_id], item_id),
    )
    results = []
    for item_id in ranked_ids[:top_k]:
        result = {
            **items[item_id],
            "metadata": dict(items[item_id]["metadata"]),
            "score": scores[item_id],
            "retrieval_method": "hybrid",
        }
        results.append(result)
    validate_search_results(results, top_k=top_k, expected_method="hybrid")
    return results


if __name__ == "__main__":
    print("Implement rerank_rrf, then run contract tests.")
