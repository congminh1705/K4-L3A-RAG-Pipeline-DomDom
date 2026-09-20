"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
import sys
from pathlib import Path
from typing import Any


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


# Windows terminals may otherwise default to cp1252 and fail on Vietnamese names.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _write_markdown(path: Path, content: str) -> bool:
    """Write non-empty Markdown using a stable output path for safe re-runs."""
    content = content.strip()
    if not content:
        print(f"Skipped empty document: {path.name}")
        return False
    path.write_text(f"{content}\n", encoding="utf-8")
    return True


def convert_legal_docs() -> int:
    """Convert every PDF/DOC/DOCX policy document to Markdown."""
    try:
        from markitdown import MarkItDown
    except ImportError as error:
        raise RuntimeError("MarkItDown is required. Run: python -m pip install -e '.[dev]'") from error

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()
    converted = 0

    for source_path in sorted(legal_dir.iterdir() if legal_dir.exists() else []):
        if not source_path.is_file() or source_path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        try:
            text = converter.convert(str(source_path)).text_content
            if not text.strip():
                print(f"Skipped {source_path.name}: no extractable text (OCR may be required)")
                continue
            header = f"# {source_path.stem}\n\n**Source:** {source_path.name}\n\n---\n\n"
            if _write_markdown(output_dir / f"{source_path.stem}.md", header + text):
                converted += 1
                print(f"Converted: {source_path.name}")
        except Exception as error:
            print(f"Failed to convert {source_path.name}: {error}")
    return converted


def _required_article_fields(data: dict[str, Any], source_path: Path) -> tuple[str, str, str, str]:
    """Validate crawler output before it becomes part of the RAG corpus."""
    fields = ("url", "title", "date_crawled", "content_markdown")
    missing = [field for field in fields if not isinstance(data.get(field), str) or not data[field].strip()]
    if missing:
        raise ValueError(f"missing or empty fields: {', '.join(missing)} in {source_path.name}")
    return tuple(data[field].strip() for field in fields)  # type: ignore[return-value]


def convert_news_articles() -> int:
    """Convert crawler JSON files to Markdown while preserving source metadata."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    converted = 0

    for source_path in sorted(news_dir.glob("*.json")) if news_dir.exists() else []:
        try:
            data = json.loads(source_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(f"JSON root must be an object in {source_path.name}")
            url, title, date_crawled, content = _required_article_fields(data, source_path)
            markdown = (
                f"# {title}\n\n**Source:** {url}\n\n"
                f"**Crawled:** {date_crawled}\n\n---\n\n{content}"
            )
            if _write_markdown(output_dir / f"{source_path.stem}.md", markdown):
                converted += 1
                print(f"Converted: {source_path.name}")
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"Skipped {source_path.name}: {error}")
    return converted


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    legal_count = convert_legal_docs()
    news_count = convert_news_articles()
    print(f"Saved {legal_count} legal and {news_count} news Markdown files to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
