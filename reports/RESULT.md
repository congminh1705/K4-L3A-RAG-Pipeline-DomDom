# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-20 |
| Framework and version | Evaluator offline tại `src.evaluate`; token-overlap proxy metrics v1 |
| Evaluator model | Không dùng LLM; đánh giá tất định để có thể tái lập |
| Generator model | Gemini `gemini-3.6-flash` cho runtime; không gọi trong A/B offline |
| Embedding model | Local feature hashing 1024 chiều, chuẩn hóa cosine |
| Corpus version/commit | Working tree: 3 legal + 5 news, 986 chunks |
| Golden dataset size | 15 câu grounded |
| `top_k` | 5 |
| Fallback threshold and calibration | 0.30; in-domain 0.351–0.494, out-of-domain 0.155–0.192 trên 3 query mỗi nhóm |

Các metric dưới đây là proxy dựa trên token overlap, không phải điểm Ragas/LLM judge.
`Faithfulness` đo tỷ lệ token của câu trả lời trích xuất có trong context;
`answer relevance` là token-F1 với đáp án kỳ vọng; `context recall` đo độ phủ
expected context; `context precision` là tỷ lệ chunk đạt ngưỡng phủ 0.2.

## Configurations

- **Config A — dense-only:** cosine search trên ChromaDB với embedding hashing, lấy 5 chunks.
- **Config B — hybrid + RRF:** lấy 10 dense và 10 BM25 candidates, RRF với `k=60`, trả 5 chunks.

Hai cấu hình dùng cùng golden dataset, evaluator, chunking và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric | Config A | Config B | Delta B−A |
| --- | ---: | ---: | ---: |
| Faithfulness | 1.0000 | 1.0000 | +0.0000 |
| Answer relevance | 0.3421 | 0.3593 | +0.0172 |
| Context recall | 0.8123 | 0.9072 | +0.0949 |
| Context precision | 0.9067 | 0.9200 | +0.0133 |
| **Average** | **0.7653** | **0.7966** | **+0.0313** |

## A/B comparison

- Cấu hình tốt hơn: hybrid + RRF, với average tăng 0.0313.
- Evidence: context recall tăng 0.0949; query về danh hiệu du lịch Việt Nam tăng recall từ 0.4815 lên 1.0000 và query về di sản, làng nghề Hà Nội tăng từ 0.4848 lên 1.0000.
- Trade-off về latency/cost: hybrid chạy thêm BM25 và RRF nên tốn CPU hơn dense-only, nhưng không phát sinh API cost. Trong lần đo này, answer relevance proxy cũng tăng 0.0172.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Điều kiện kinh doanh dịch vụ lữ hành nội địa gồm những gì? | dense | 1.0000 | 0.1026 | 1.0000 | 1.0000 | generation proxy | Context đúng nhưng câu trích xuất dài hơn đáp án chuẩn, làm giảm token-F1 |
| 2 | Theo Luật Di sản văn hóa, di sản văn hóa phi vật thể là gì? | dense | 1.0000 | 0.1463 | 0.5946 | 1.0000 | generation proxy | Câu trích xuất chứa nhiều nội dung hơn đáp án chuẩn, làm giảm token-F1 |
| 3 | Luật Di sản văn hóa định nghĩa danh lam thắng cảnh như thế nào? | dense | 1.0000 | 0.1622 | 0.7200 | 1.0000 | generation proxy | Chunk đúng nhưng câu trả lời trích xuất chưa cô đọng theo định nghĩa |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| ---: | --- | --- | --- | --- |
| 1 | Thay hashing bằng embedding đa ngôn ngữ như BGE-M3 khi có tài nguyên | Dense bỏ sót một phần context ở các câu hỏi tin tức và di sản | Tăng semantic recall cho câu hỏi diễn đạt khác văn bản | Chạy lại `python -m src.evaluate` và so context recall |
| 2 | Bổ sung heading-aware chunking cho văn bản pháp luật | PDF có nhiều điều khoản và chú thích lặp | Giảm nhiễu, tăng context precision | A/B recursive hiện tại với chunk theo Điều/Chương |
| 3 | Rút gọn prompt và yêu cầu trả lời theo đúng phạm vi câu hỏi | Relevance proxy thấp dù context đúng | Câu trả lời ngắn và sát expected answer hơn | Chấm lại bằng Ragas/LLM judge trên cùng 15 câu |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | ---: | ---: | --- |
| Chưa chạy reranker nâng cao | Hybrid + RRF | 0.0000 | 0 | Giữ RRF làm baseline tái lập; chỉ thêm reranker khi có A/B thực đo |
