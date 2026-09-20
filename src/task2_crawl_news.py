"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"
API_BASE_URL = "https://public.vietnamtourism.gov.vn/post"
REQUEST_TIMEOUT_SECONDS = 30


# Avoid UnicodeEncodeError when Vietnamese titles are printed on Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARTICLE_URLS = [
    "https://vietnamtourism.gov.vn/post/63518",
    "https://vietnamtourism.gov.vn/post/61973",
    "https://vietnamtourism.gov.vn/post/39869",
    "https://vietnamtourism.gov.vn/post/54044",
    "https://vietnamtourism.gov.vn/post/44034",
]


def _post_id_from_url(url: str) -> str:
    """Extract and validate the numeric post ID from an official article URL."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "vietnamtourism.gov.vn":
        raise ValueError(f"Unsupported article URL: {url}")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2 or path_parts[0] != "post" or not path_parts[1].isdigit():
        raise ValueError(f"Invalid Vietnam Tourism post URL: {url}")
    return path_parts[1]


def _html_to_markdown(raw_html: str) -> str:
    """Remove non-content tags and convert article HTML to clean Markdown."""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    result = markdownify(str(soup), heading_style="ATX", bullets="-")
    lines = [line.rstrip() for line in result.splitlines()]
    return "\n".join(lines).strip()


def _fetch_article(url: str) -> dict[str, str]:
    """Fetch one post from the public API used by the official website."""
    post_id = _post_id_from_url(url)
    response = requests.get(
        f"{API_BASE_URL}/{post_id}",
        headers={
            "Accept": "application/json",
            "User-Agent": "K4-RAG-Pipeline/1.0 (educational crawler)",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("API response must be a JSON object")

    title = BeautifulSoup(html.unescape(str(payload.get("title") or "")), "html.parser").get_text(
        " ", strip=True
    )
    content = _html_to_markdown(str(payload.get("content") or ""))
    summary = _html_to_markdown(str(payload.get("summary") or ""))
    if summary and summary not in content:
        content = f"{summary}\n\n{content}".strip()

    if not title:
        raise ValueError(f"Post {post_id} has no title")
    if len(content) < 200:
        raise ValueError(f"Post {post_id} has insufficient content ({len(content)} characters)")

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": content,
    }


async def crawl_article(url: str) -> dict[str, str]:
    """Crawl without blocking the asyncio event loop."""
    return await asyncio.to_thread(_fetch_article, url)


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output.name} — {article['title']}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
