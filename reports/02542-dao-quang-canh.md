# Individual contribution report

## Thông tin

- Họ và tên: Đào Quang Cảnh
- Mã học viên: 02542
- Nhóm: DomDom
- Repository/branch: `https://github.com/congminh1705/K4-L3A-RAG-Pipeline-DomDom.git` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thiết kế lại giao diện Streamlit (UI/UX) | Viết lại toàn bộ `app.py` từ giao diện mặc định Streamlit (title/caption/sidebar cơ bản) sang một trang landing dạng "cinematic": video nền full-bleed, hero section với gradient/blur, top-nav thương hiệu "VietHeritage", bảng màu tối (dark, glassmorphism), font Google `Plus Jakarta Sans`. | `app.py` (hàm `inject_design`) | Done |
| Luồng tương tác (UX flow) | Thêm 3 nút gợi ý câu hỏi (`SUGGESTIONS`) để người dùng bắt đầu hội thoại bằng một click; dùng `pending_query` trong `session_state` + callback `queue_question` để nút gợi ý và ô chat cùng đẩy vào một pipeline xử lý câu hỏi duy nhất, tránh trùng lặp logic. Thêm trạng thái "compact" cho hero khi đã có hội thoại để nhường chỗ cho khung chat. | `app.py` (`queue_question`, khối `if not st.session_state.messages`) | Done |
| Hiển thị nguồn trích dẫn (source cards) | Thiết kế lại `show_sources` → `render_sources`: từ danh sách markdown thuần sang "source card" có badge phương thức truy xuất, badge điểm số, đoạn trích (excerpt) 220 ký tự đầu của nội dung chunk, và nhãn route truy xuất (`Hybrid · Dense + BM25 + RRF` hoặc `PageIndex fallback`) hiển thị ngay trên tiêu đề expander. | `app.py` (`render_sources`) | Done |
| Bảo mật đầu ra UI (XSS) | Toàn bộ nội dung động render bằng `unsafe_allow_html=True` (title, location, excerpt, method) được escape qua `html.escape` trước khi chèn vào HTML, tránh injection nếu metadata/nội dung tài liệu chứa ký tự HTML. | `app.py` (import `escape`, `render_sources`) | Done |
| Xử lý lỗi phía UI khi generation thất bại | Bọc lời gọi `generate_with_citation` trong `try/except`, khi lỗi (ví dụ Gemini client/API) trả về `SAFE_REFUSAL` thay vì crash toàn bộ ứng dụng Streamlit. | `app.py` (khối xử lý `query`) | Done |
| Sidebar cấu hình | Viết lại sidebar: thêm mô tả pipeline đang dùng, thống kê corpus (3 tài liệu pháp lý · 5 bài viết · 986 chunks), nút "Xóa cuộc trò chuyện" reset `messages`/`pending_query` và `st.rerun()`; đặt `initial_sidebar_state="collapsed"` để ưu tiên không gian cho hero/chat. | `app.py` (khối `with st.sidebar`) | Done |
| Responsive & accessibility | Thêm media query cho màn hình ≤700px (thu nhỏ hero, ẩn phần phụ của nav) và `@media (prefers-reduced-motion: reduce)` để tắt animation/video cho người dùng có nhu cầu giảm chuyển động. | `app.py` (CSS trong `inject_design`) | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng một biến trạng thái `pending_query` trong `st.session_state` để hợp nhất hai nguồn nhập câu hỏi (nút gợi ý và `st.chat_input`) thành một điểm xử lý duy nhất, thay vì gọi `generate_with_citation` riêng ở hai nơi.

   **Lý do/evidence:** Trước khi sửa, chỉ có `st.chat_input` — không có cách nào để một nút bấm tự động gửi câu hỏi vì Streamlit re-run toàn bộ script mỗi lần tương tác. Dùng callback (`on_click=queue_question`) ghi vào session_state rồi đọc lại (`pop`) ở đầu vòng xử lý giải quyết đúng mô hình re-run của Streamlit.

   **Trade-off:** Thêm một biến trạng thái cần quản lý vòng đời (phải `pop`/reset đúng chỗ, nếu không sẽ bị lặp lại câu hỏi cũ ở lần rerun kế tiếp).

2. **Quyết định:** Escape (`html.escape`) mọi giá trị động trước khi nội suy vào chuỗi HTML render qua `unsafe_allow_html=True`, thay vì tin tưởng dữ liệu từ metadata/nội dung tài liệu.

   **Lý do/evidence:** UI hiển thị `title`, `url/source`, `retrieval_method` và trích đoạn nội dung — các trường này đến từ dữ liệu đã crawl/convert, không đảm bảo sạch HTML. Vì các phần tử source-card được dựng thủ công bằng f-string thay vì `st.markdown` thường, cần tự escape để tránh HTML/script injection vào trang.

   **Trade-off:** Escape làm mất khả năng hiển thị định dạng phong phú (bold, link) nếu sau này muốn cho phép markdown trong excerpt; hiện chấp nhận vì ưu tiên an toàn hơn trình bày.

3. **Quyết định:** Bọc `generate_with_citation` trong `try/except` ở tầng UI và fallback về `SAFE_REFUSAL` thay vì để Streamlit hiển thị traceback.

   **Lý do/evidence:** Lỗi runtime (Gemini client, mạng, rate limit) không nên làm sập cả session chat của người dùng; người dùng cần một câu trả lời an toàn nhất quán với hành vi refusal đã định nghĩa ở tầng generation (`src/task10_generation.py`), thay vì một trang lỗi kỹ thuật.

   **Trade-off:** Bắt exception rộng (`except Exception`) có thể che giấu lỗi lập trình thực sự trong lúc phát triển; chấp nhận đánh đổi cho trải nghiệm người dùng cuối, lỗi vẫn có thể theo dõi qua log riêng nếu cần.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: chạy `streamlit run app.py` thủ công, thử luồng: (1) click từng nút gợi ý trong `SUGGESTIONS`, (2) gõ câu hỏi trực tiếp vào `st.chat_input`, (3) bấm "Xóa cuộc trò chuyện" giữa hội thoại, (4) thu nhỏ cửa sổ trình duyệt xuống dưới 700px để kiểm tra responsive, (5) bật "reduce motion" ở hệ điều hành để kiểm tra video/animation bị tắt.
- Kết quả trước/sau nếu có: trước khi sửa, giao diện chỉ có `st.title`/`st.caption`/sidebar mặc định, danh sách nguồn là markdown thuần không có excerpt; sau khi sửa, cả hai luồng nhập câu hỏi (nút gợi ý và chat input) đều chạy đúng một pipeline, source card hiển thị đủ tiêu đề/badge/excerpt, hero thu gọn đúng khi đã có tin nhắn, và ứng dụng không crash khi ép `generate_with_citation` ném lỗi giả lập.
- Lỗi đã phát hiện và cách xử lý: nút gợi ý ban đầu không tự gửi câu hỏi do Streamlit re-run lại script mỗi lần — xử lý bằng `pending_query` + callback như mô tả ở trên; nội dung excerpt hiển thị lỗi xuống dòng lộn xộn do chunk gốc chứa newline thô — xử lý bằng `" ".join(str(...).split())` để chuẩn hoá khoảng trắng trước khi escape/cắt 220 ký tự.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: chưa có test tự động (unit/UI test) cho `app.py` — toàn bộ kiểm thử hiện tại là thủ công qua trình duyệt; excerpt trong source-card cắt cứng theo ký tự (220) nên đôi khi cắt giữa câu.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: viết test cho `render_sources`/`queue_question` bằng `streamlit.testing.v1.AppTest`, và cắt excerpt theo ranh giới câu/từ thay vì theo số ký tự cố định.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Đào Quang Cảnh
