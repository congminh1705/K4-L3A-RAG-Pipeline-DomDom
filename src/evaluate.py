"""Reproducible offline A/B evaluation for dense versus hybrid retrieval.

The four scores are token-overlap proxies so the lab can be rerun without
paid evaluator calls. They are deliberately labelled as proxies in RESULT.md.
"""

import json
import re
import unicodedata
from pathlib import Path

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf


ROOT = Path(__file__).parent.parent
DATASET_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT_PATH = ROOT / ".cache" / "evaluation_results.json"
TOP_K = 5

STOPWORDS = {
    "và", "là", "có", "của", "cho", "được", "theo", "trong", "với", "những",
    "một", "các", "từ", "đến", "về", "thì", "nào", "bao", "gì", "khi", "tại",
}


def tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFC", text.lower())
    return {
        token for token in re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)
        if len(token) > 1 and token not in STOPWORDS
    }


def f1(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    precision = overlap / len(left)
    recall = overlap / len(right)
    return 2 * precision * recall / (precision + recall) if overlap else 0.0


def extractive_answer(question: str, results: list[dict]) -> str:
    query_tokens = tokens(question)
    sentences: list[tuple[float, str]] = []
    for result in results:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", result["content"]):
            sentence = sentence.strip()
            if len(sentence) < 25:
                continue
            score = len(tokens(sentence) & query_tokens) / max(len(query_tokens), 1)
            sentences.append((score, sentence))
    sentences.sort(key=lambda item: (-item[0], len(item[1])))
    return " ".join(sentence for _, sentence in sentences[:2])[:900]


def score_case(case: dict, results: list[dict]) -> dict[str, float]:
    combined_context = "\n".join(result["content"] for result in results)
    context_tokens = tokens(combined_context)
    expected_context_tokens = tokens(case["expected_context"])
    answer = extractive_answer(case["question"], results)
    answer_tokens = tokens(answer)
    expected_answer_tokens = tokens(case["expected_answer"])

    faithfulness = len(answer_tokens & context_tokens) / max(len(answer_tokens), 1)
    answer_relevance = f1(answer_tokens, expected_answer_tokens)
    context_recall = len(context_tokens & expected_context_tokens) / max(len(expected_context_tokens), 1)
    relevant_chunks = sum(
        len(tokens(result["content"]) & expected_context_tokens)
        / max(len(expected_context_tokens), 1) >= 0.2
        for result in results
    )
    context_precision = relevant_chunks / max(len(results), 1)
    return {
        "faithfulness": round(faithfulness, 4),
        "answer_relevance": round(answer_relevance, 4),
        "context_recall": round(context_recall, 4),
        "context_precision": round(context_precision, 4),
    }


def evaluate() -> dict:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    configurations = {"dense": [], "hybrid": []}
    details: list[dict] = []
    for case in dataset:
        dense_candidates = semantic_search(case["question"], top_k=TOP_K * 2)
        dense = dense_candidates[:TOP_K]
        sparse = lexical_search(case["question"], top_k=TOP_K * 2)
        hybrid = rerank_rrf([dense_candidates, sparse], top_k=TOP_K)
        row = {"question": case["question"]}
        for name, results in (("dense", dense), ("hybrid", hybrid)):
            scores = score_case(case, results)
            configurations[name].append(scores)
            row[name] = {
                **scores,
                "sources": [result["metadata"]["title"] for result in results],
            }
        details.append(row)

    summary: dict[str, dict[str, float]] = {}
    for name, rows in configurations.items():
        summary[name] = {
            metric: round(sum(row[metric] for row in rows) / len(rows), 4)
            for metric in rows[0]
        }
        summary[name]["average"] = round(sum(summary[name].values()) / 4, 4)

    output = {"top_k": TOP_K, "dataset_size": len(dataset), "summary": summary, "details": details}
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
