"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

import sys
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Validate the documents collected manually by the group."""
    documents = sorted(
        path for path in DATA_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".doc", ".docx"}
    )
    if len(documents) < 3:
        raise RuntimeError(
            f"Cần ít nhất 3 PDF/DOCX trong {DATA_DIR}; hiện có {len(documents)}."
        )
    for path in documents:
        if path.stat().st_size <= 1024:
            raise RuntimeError(f"Tài liệu quá nhỏ hoặc rỗng: {path.name}")
        print(f"Ready: {path.name}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
