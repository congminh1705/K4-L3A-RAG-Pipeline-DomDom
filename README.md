# Day 8 — RAG Pipeline

## Mục tiêu

Mỗi nhóm xây dựng một chatbot RAG trả lời câu hỏi từ bộ tài liệu do nhóm thu thập. Sản phẩm phải có hybrid retrieval, citation, giao diện chat và báo cáo đánh giá.

Nhóm tự chọn bài toán và thu thập dữ liệu phù hợp; repo không cung cấp dữ liệu mẫu.

## Sản phẩm phải nộp

- Repository nhóm chạy được.
- Tối thiểu 3 tài liệu chính sách và 5 bài viết/page do nhóm tự thu thập.
- Pipeline: convert → chunk → index → dense + BM25 → RRF → fallback → generation có citation.
- Chatbot Streamlit hiển thị câu trả lời và nguồn đã dùng.
- Golden dataset tối thiểu 15 câu; đánh giá 4 metric và so sánh A/B.
- `group_project/evaluation/RESULT.md`.
- Mỗi thành viên nộp báo cáo cá nhân theo template trong `group_project/ịndividual/INDIVIDUAL_REPORT.md`.

## Quick start

Yêu cầu Python 3.10–3.13 (không dùng Python 3.14).

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
cp .env.example .env
```

Điền API key cần dùng trong `.env`; không commit file này.

Trên Windows PowerShell, có thể chạy trực tiếp bằng interpreter trong môi trường ảo:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m src.task4_chunking_indexing
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\streamlit.exe run app.py
```

```bash
# 1. Thu thập và chuẩn hoá
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Index và kiểm tra contract
python -m src.task4_chunking_indexing
pytest -q

# 3. Chạy sản phẩm
streamlit run app.py
```

## Cấu hình hiện tại

- Corpus du lịch và di sản Việt Nam: 3 tài liệu legal, 5 bài viết, 986 chunks.
- Chunking: paragraph-aware, 500 ký tự, overlap 50 ký tự.
- Dense retrieval: ChromaDB cosine với feature hashing 1024 chiều chạy offline.
- Lexical retrieval: BM25 cục bộ trên cùng corpus chunks.
- Fusion: Reciprocal Rank Fusion, `k=60`, chỉ chạy một lần.
- Fallback: tìm kiếm vectorless theo section, trả `retrieval_method="pageindex"`;
  lỗi fallback không làm pipeline crash.
- Generation: Gemini theo `LLM_PROVIDER` trong `.env`, citation `[S1]`, `[S2]`;
  OpenAI và Anthropic cũng được hỗ trợ.
- UI: Streamlit hiển thị câu trả lời, nguồn, score và retrieval method.

Embedding hashing giúp demo chạy không cần tải model lớn. Khi có đủ tài nguyên, đổi
`EMBEDDING_PROVIDER=sentence_transformers` và `EMBEDDING_MODEL=BAAI/bge-m3`, rồi
chạy lại Task 4 để tạo index mới.

## Evaluation

Golden dataset có 15 câu grounded. Chạy A/B dense-only và hybrid + RRF bằng:

```bash
python -m src.evaluate
```

Kết quả chi tiết được ghi tạm vào `.cache/evaluation_results.json`; báo cáo đã tổng
hợp tại `group_project/evaluation/RESULT.md`. Evaluator hiện dùng bốn token-overlap
proxy metrics chạy offline và ghi rõ giới hạn trong báo cáo.

## Lộ trình 3 giờ

| Mốc                  | Thời gian | Kết quả cần có                           |
| -------------------- | --------: | ---------------------------------------- |
| 0. Setup             |   10 phút | Môi trường và `.env` sẵn sàng            |
| 1. Data              |   25 phút | ≥3 legal, ≥5 news, Markdown đã chuẩn hoá |
| 2. Index & search    |   30 phút | ChromaDB, dense search và BM25 chạy được |
| 3. Fusion & fallback |   25 phút | RRF và fallback tuân thủ contract        |
| 4. Generation & UI   |   30 phút | Chatbot trả lời có citation              |
| 5. Evaluation        |   30 phút | 15+ Q&A, 4 metric, A/B comparison        |
| 6. Demo & handoff    |   30 phút | Test, report, demo và push repository    |

## Lưu ý quy tắc để có code quality tốt:

- Dense và BM25 nên cùng trả về `SearchResult` theo một schema.
- RRF chỉ nên dùng để gộp thứ hạng và chỉ chạy một lần.
- Fallback dùng cosine score gốc của dense retrieval.
- Threshold phải được hiệu chỉnh trên query in domain và out of domain, không có một con số đúng cho mọi corpus.

## Tài liệu

- [Module contracts](docs/MODULE_CONTRACTS.md): schema, interface và invariant mà code/test nên tuân theo.
- [Step-by-step guide](docs/STEP_BY_STEP.md): thứ tự triển khai và tiêu chí hoàn thành từng bước.
- [Grading rubric](docs/GRADING_RUBRIC.md): Rubric thang điểm.
- [Individual report](group_project/ịndividual/INDIVIDUAL_REPORT.md): template báo cáo cá nhân.
- [Suggested topics](docs/SUGGESTED_TOPICS.md): danh sách chủ đề tham khảo, không bắt buộc.

## Kiểm tra

```bash
# Contract tests
pytest tests/test_contracts.py -q

# Acceptance tests
pytest tests/test_acceptance.py -q

# Toàn bộ
pytest -q
```
