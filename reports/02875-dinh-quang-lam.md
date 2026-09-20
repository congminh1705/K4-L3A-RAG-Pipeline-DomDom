# Individual contribution report

## Thông tin

- Họ và tên: Đinh Quang Lâm
- Mã học viên: 02875
- Nhóm: DomDom
- Repository/branch: `https://github.com/congminh1705/K4-L3A-RAG-Pipeline-DomDom.git` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Module Contracts & Schema Validation | Thiết kế hệ thống type annotations (`TypedDict`) cho Document, Chunk, SearchResult, GenerationResult; hiện thực các hàm runtime validation (`validate_document`, `validate_search_results`, `validate_generation_result`) nhằm đảm bảo tính toàn vẹn dữ liệu, kiểm tra tính duy nhất của ID, thứ tự sắp xếp score giảm dần và chặn schema drift giữa 10 tasks. | `src/contracts.py` | Done |
| Bộ chỉ mục Lexical Search (BM25) | Tự triển khai thuật toán Okapi BM25 (`BM25Index`) chạy độc lập (zero-dependency) với chuẩn hóa Unicode NFC và tokenization tiếng Việt; tính toán IDF có smoothing, chuẩn hóa độ dài văn bản; đảm bảo kết quả tìm kiếm tuân thủ contract `SearchResult` và sắp xếp score giảm dần. | `src/task6_lexical_search.py` | Done |
| Thuật toán Reranking (RRF) | Hiện thực thuật toán Reciprocal Rank Fusion ($k=60$, 1-based indexing) kết hợp đa nguồn xếp hạng (Dense + BM25); xử lý deduplication chunk trong từng list; xây dựng cơ chế sắp xếp đa tiêu chí (-score, best_rank, item_id) chống tie-break không xác định; gắn nhãn `retrieval_method="hybrid"`. | `src/task7_reranking.py` | Done |
| Vectorless Fallback Search | Xây dựng bộ tìm kiếm dự phòng không dùng vector (`pageindex_search`): phân đoạn văn bản thô theo section 1.400 ký tự (overlap 150), băm SHA-256 lưu cache document IDs (`pageindex_doc_ids.json`); chấm điểm theo độ phủ từ khóa (token coverage) kết hợp cộng điểm khớp chính xác cụm từ (+0.25 phrase bonus). | `src/task8_pageindex_vectorless.py` | Done |
| Retrieval Pipeline Orchestration | Xây dựng pipeline tích hợp đa tầng: điều phối Dense Search + BM25, hợp nhất RRF đúng 1 lần; so sánh cosine score gốc của dense với ngưỡng `SCORE_THRESHOLD=0.30` để kích hoạt fallback; cài đặt cơ chế fault-tolerance (bọc `try/except`) để lỗi từ BM25 hay PageIndex không làm sập pipeline. | `src/task9_retrieval_pipeline.py` | Done |
| Tối ưu Context & Hallucination Guard | Hiện thực hàm `reorder_for_llm` phân bổ lại vị trí chunk (đưa chunk điểm cao về 2 đầu context) nhằm giải quyết hiện tượng "lost-in-the-middle" của LLM; xây dựng hàm kiểm tra bằng chứng `_has_sufficient_evidence` (lọc stopword tiếng Việt, ngưỡng phủ 40%) để kích hoạt `SAFE_REFUSAL` sớm trước khi gọi model sinh câu trả lời. | `src/task10_generation.py` (`reorder_for_llm`, `_has_sufficient_evidence`, `format_context`) | Done |
| Bộ kiểm thử Contracts (Unit Testing) | Viết toàn bộ test suite kiểm thử hợp đồng dữ liệu: kiểm tra chữ ký hàm của toàn bộ 10 tasks, mock ChromaDB và Lexical corpus, xác minh thứ tự và tính duy nhất của search result, kiểm tra tính bất biến (non-mutating) của context reordering, kiểm thử các kịch bản fallback và lỗi provider. | `tests/test_contracts.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng Cosine Similarity score gốc từ Dense Retrieval làm điều kiện kích hoạt Fallback PageIndex, tuyệt đối không dùng điểm số RRF.

   **Lý do/evidence:** Điểm số RRF thực chất là tổng nghịch đảo thứ hạng ($\sum \frac{1}{k + rank}$), chỉ mang ý nghĩa thứ tự tương đối giữa các ứng viên trong cùng một lượt truy vấn và bị phụ thuộc vào tham số $k$ cũng như số lượng danh sách xếp hạng tham gia fusion. Ngược lại, Cosine score đo trực tiếp khoảng cách vector trong không gian ngữ nghĩa, cho phép hiệu chuẩn một ngưỡng tin cậy khách quan (`SCORE_THRESHOLD = 0.30`) để phân định rõ ràng giữa truy vấn nội domain (đo được $0.351 - 0.494$) và truy vấn lạc đề/ngoài domain (đo được $0.155 - 0.192$).

   **Trade-off:** Phải lưu vết và truyền điểm số dense score cao nhất xuyên suốt pipeline trước khi gộp bảng xếp hạng, và ngưỡng cutoff này cần được hiệu chuẩn thực nghiệm trên từng bộ dữ liệu cụ thể.

2. **Quyết định:** Tự xây dựng module Okapi BM25 (`BM25Index`) và tokenizer tiếng Việt thuần bằng chuẩn Unicode NFC thay vì sử dụng thư viện bên ngoài (như `rank_bm25` hay `Whoosh`).

   **Lý do/evidence:** Giảm thiểu tối đa phụ thuộc ngoài (dependency-free), ngăn ngừa hoàn toàn các lỗi tương thích môi trường trên Windows (đặc biệt khi chạy với Python 3.13 hoặc lỗi bảng mã `cp1252`). Đồng thời, việc chuẩn hóa Unicode NFC trực tiếp giúp giải quyết triệt để sự không đồng nhất giữa bộ gõ tiếng Việt tổ hợp và dựng sẵn trong dữ liệu văn bản pháp luật và báo chí.

   **Trade-off:** Tokenizer hiện tại là word-boundary regex cơ bản, chưa có từ điển tách từ ghép tiếng Việt chuyên sâu (compound words như "lữ hành", "di sản"), nhưng hoàn toàn đáp ứng tốt bài toán tra cứu từ khóa chính xác và số hiệu văn bản pháp quy.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: 
  - Chạy bộ kiểm thử tự động: `pytest tests/test_contracts.py -v` (11/11 tests pass).
  - Kiểm thử ngưỡng fallback với query in-domain: "Điều kiện kinh doanh dịch vụ lữ hành nội địa" (dense score $\approx 0.48 \ge 0.30 \rightarrow$ chạy Hybrid RRF).
  - Kiểm thử query out-of-domain: "Cách làm visa đi Pháp tự túc 2024" (dense score $\approx 0.18 < 0.30 \rightarrow$ tự động kích hoạt PageIndex fallback).
  - Kiểm thử query phá hoại / không có căn cứ: "Quy định đánh thuế tài sản ảo tại Việt Nam" $\rightarrow$ `_has_sufficient_evidence` trả về `False`, trả ngay `SAFE_REFUSAL` mà không lãng phí token LLM.
- Kết quả trước/sau nếu có:
  - Trước khi có contract test: Các module có nguy cơ trả về sai schema (ví dụ thiếu trường `chunk_index`, ID bị trùng lặp, hoặc score không được sắp xếp giảm dần) làm module sau bị crash.
  - Sau khi chuẩn hóa: Toàn bộ pipeline đạt tính nhất quán 100%, bảo đảm không có duplicate ID, thứ hạng search luôn giảm dần, và pipeline vẫn hoạt động an toàn ngay cả khi PageIndex hoặc BM25 gặp sự cố.
- Lỗi đã phát hiện và cách xử lý:
  - Phát hiện lỗi cộng dồn điểm sai trong RRF khi một tài liệu xuất hiện lặp lại trong cùng một danh sách kết quả $\rightarrow$ khắc phục bằng cách bổ sung tập `seen_in_list` để deduplicate trước khi tính nghịch đảo rank.
  - Phát hiện hàm `reorder_for_llm` có nguy cơ làm đột biến (mutate) danh sách chunks gốc $\rightarrow$ chuyển sang sao chép danh sách (`list(chunks)`) và viết test kiểm tra tính bất biến (`original_ids == [item["id"] for item in chunks]`).

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Module tìm kiếm vectorless (PageIndex fallback) hiện đang sử dụng thuật toán tính token coverage cục bộ dựa trên file cache tĩnh, chưa kết nối trực tiếp đến API đám mây chính thức của PageIndex do giới hạn về API quota.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Tích hợp thư viện tách từ tiếng Việt chuyên dụng (như `underthesea` hoặc `pyvi`) vào BM25 tokenizer để hỗ trợ n-gram/từ ghép, và thay thế RRF heuristic bằng một Cross-Encoder Reranker (như `bge-reranker-base`) có so sánh A/B thực nghiệm.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Đinh Quang Lâm
