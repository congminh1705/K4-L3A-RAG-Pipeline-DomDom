import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="Trợ lý Du lịch và Di sản Việt Nam",
    page_icon="🇻🇳",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("Thông tin truy xuất")
    st.caption("Hybrid retrieval: dense + BM25 + RRF, có fallback vectorless")
    top_k = st.slider("Số chunks", 3, 10, 5)
    st.info("Câu trả lời chỉ dựa trên 3 tài liệu và 5 bài viết trong corpus.")

st.title("Trợ lý Du lịch và Di sản Việt Nam")
st.caption("Hỏi về di sản văn hóa, quy định du lịch và điều kiện phát triển du lịch Phú Quốc.")


def show_sources(sources: list[dict], retrieval_source: str | None = None) -> None:
    if not sources:
        return
    label = f"Nguồn tham khảo · {retrieval_source or 'retrieval'}"
    with st.expander(label):
        for index, source in enumerate(sources, 1):
            metadata = source["metadata"]
            location = metadata.get("url") or metadata["source"]
            st.markdown(
                f"**[S{index}] {metadata['title']}**  \n"
                f"Nguồn: {location}  \n"
                f"Điểm: `{source['score']:.4f}` · Phương thức: `{source['retrieval_method']}`"
            )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        show_sources(message.get("sources", []), message.get("retrieval_source"))

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm tài liệu và tạo câu trả lời..."):
            result = generate_with_citation(query, top_k=top_k)
        st.markdown(result["answer"])
        show_sources(result["sources"], result["retrieval_source"])

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "retrieval_source": result["retrieval_source"],
    })
