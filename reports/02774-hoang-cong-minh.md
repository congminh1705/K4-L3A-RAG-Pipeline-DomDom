# Individual contribution report

## Thông tin

- Họ và tên: Hoàng Công Minh
- Mã học viên: 02774
- Nhóm: DomDom
- Repository/branch: `https://github.com/congminh1705/K4-L3A-RAG-Pipeline-DomDom.git` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập và chuẩn hóa dữ liệu | Crawl 5 bài Vietnam Tourism; chuyển PDF/JSON sang Markdown; loại tài liệu Phú Quốc không phù hợp và bổ sung bản Luật Du lịch từ Công báo Chính phủ. | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py`, `data/standardized/` | Done |
| Chunking và indexing | Tách đoạn theo paragraph, chunk 500 ký tự và overlap 50; tạo ID/metadata ổn định; lưu và đồng bộ index ChromaDB. | `src/task4_chunking_indexing.py`; kết quả: 986 chunks | Done |
| Retrieval và reranking | Hoàn thiện semantic search, BM25 tiếng Việt, RRF, score threshold và fallback vectorless kiểu PageIndex. | `src/task5_semantic_search.py` đến `src/task9_retrieval_pipeline.py` | Done |
| Generation và UI | Tích hợp Gemini, citation `[S1]`, kiểm tra evidence, safe refusal; sửa vòng đời Gemini client; hoàn thiện giao diện Streamlit. | `src/task10_generation.py`, `app.py` | Done |
| Evaluation và test | Tạo golden dataset 15 câu, evaluator A/B dense và hybrid; chạy contract, acceptance test và truy vấn Gemini thật. | `src/evaluate.py`, `group_project/evaluation/golden_dataset.json`, `reports/RESULT.md`, `tests/` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng local feature hashing 1.024 chiều làm embedding mặc định.

   **Lý do/evidence:** Pipeline có thể index, tìm kiếm và chạy test offline, không phụ thuộc tải model hoặc chi phí embedding API.

   **Trade-off:** Khả năng hiểu ngữ nghĩa tiếng Việt thấp hơn embedding đa ngôn ngữ; BM25 và RRF được dùng để cải thiện recall.

2. **Quyết định:** Kết hợp dense search và BM25 bằng Reciprocal Rank Fusion trước bước generation.

   **Lý do/evidence:** A/B evaluation cho thấy hybrid tăng context recall; truy vấn thực tế lấy đúng điều khoản Luật Du lịch và Gemini trả citation `[S1]`.

   **Trade-off:** Phải chạy hai retriever nên tốn CPU và có độ trễ cao hơn dense-only.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m pytest -q`; truy vấn Gemini “Điều kiện kinh doanh dịch vụ lữ hành nội địa là gì?”.
- Kết quả trước/sau nếu có: sau khi loại tài liệu Phú Quốc và thêm Luật Du lịch chính thức, corpus có 3 tài liệu pháp lý, 5 bài tin và 986 chunks; **20/20 test passed**. Hybrid retrieval tìm đúng `09-2017-qh14-congbao.md`, Gemini `gemini-3.6-flash` trả đủ ba điều kiện với citation `[S1]`.
- Lỗi đã phát hiện và cách xử lý: Python 3.14 không tương thích dependency nên chuyển sang Python 3.13; PDF scan không trích được chữ nên thay bằng bản Công báo có text layer; Gemini client bị đóng sớm nên giữ client đến khi đọc xong response và đóng trong `finally`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: embedding hashing chưa tối ưu cho câu hỏi diễn đạt khác văn bản; PageIndex hiện là fallback cục bộ và evaluation dùng token-overlap proxy.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: thử BGE-M3 và chunking theo `Chương/Điều`, sau đó đánh giá lại bằng Ragas hoặc LLM judge.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Hoàng Công Minh
