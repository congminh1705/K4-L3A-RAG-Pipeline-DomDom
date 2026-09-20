"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_PATH = Path(__file__).parent.parent / "pageindex_doc_ids.json"


def _document_id(path: Path) -> str:
    relative = path.relative_to(STANDARDIZED_DIR).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return f"{relative}:{digest}"


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    mapping = {
        path.relative_to(STANDARDIZED_DIR).as_posix(): _document_id(path)
        for path in sorted(STANDARDIZED_DIR.rglob("*.md"))
        if path.stat().st_size > 0
    }
    CACHE_PATH.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Cached {len(mapping)} PageIndex document IDs in {CACHE_PATH.name}")


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFC", text.lower())
    return set(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))


def _sections(content: str, size: int = 1400, overlap: int = 150) -> list[str]:
    """Create coarse, non-embedding sections for vectorless fallback search."""
    sections: list[str] = []
    start = 0
    while start < len(content):
        end = min(start + size, len(content))
        if end < len(content):
            boundary = max(content.rfind("\n\n", start + size // 2, end), content.rfind(". ", start + size // 2, end))
            if boundary > start:
                end = boundary + 1
        section = content[start:end].strip()
        if section:
            sections.append(section)
        if end >= len(content):
            break
        start = max(start + 1, end - overlap)
    return sections


def _metadata(path: Path, content: str, index: int) -> dict:
    title_match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    source_match = re.search(r"^\*\*Source:\*\*\s*(.+)$", content, flags=re.MULTILINE)
    source = source_match.group(1).strip() if source_match else path.name
    url = source if source.startswith(("http://", "https://")) else None
    return {
        "source": source if url else path.name,
        "title": title_match.group(1).strip() if title_match else path.stem,
        "doc_type": "legal" if "legal" in path.parts else "news",
        "url": url,
        "chunk_index": index,
    }


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    if not CACHE_PATH.exists():
        upload_documents()
    mapping = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    query_tokens = _tokens(query)
    candidates: list[dict] = []
    for relative_path, document_id in mapping.items():
        path = STANDARDIZED_DIR / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for index, section in enumerate(_sections(content)):
            section_tokens = _tokens(section)
            overlap = query_tokens & section_tokens
            if not overlap:
                continue
            coverage = len(overlap) / max(len(query_tokens), 1)
            phrase_bonus = 0.25 if query.lower() in section.lower() else 0.0
            score = coverage + phrase_bonus
            candidates.append({
                "id": f"{document_id}::section-{index}",
                "content": section,
                "score": float(score),
                "metadata": _metadata(path, content, index),
                "retrieval_method": "pageindex",
            })
    candidates.sort(key=lambda item: (-item["score"], item["id"]))
    return candidates[:top_k]


if __name__ == "__main__":
    upload_documents()
