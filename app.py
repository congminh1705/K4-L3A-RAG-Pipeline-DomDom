"""Streamlit UI for the Vietnam tourism and heritage RAG assistant."""

from __future__ import annotations

from html import escape

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import SAFE_REFUSAL, generate_with_citation

load_dotenv()

VIDEO = "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260912_104036_bd6924f6-3c8e-417e-8465-6d03c8c2e9e6.mp4"
POSTER = "https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/82e7eb75-c65f-490a-99b5-f3d1cad54200.webp"
SUGGESTIONS = (
    "Di sản văn hóa phi vật thể là gì?",
    "Điều kiện kinh doanh dịch vụ lữ hành nội địa gồm những gì?",
    "Phú Quốc có những điều kiện nào để phát triển du lịch?",
)

st.set_page_config(
    page_title="VietHeritage — Trợ lý Du lịch & Di sản",
    page_icon="🇻🇳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


def inject_design() -> None:
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;800&display=swap');
:root{{--ink:#fff;--muted:rgba(255,255,255,.66);--violet:#a78bfa;--panel:rgba(9,8,15,.76);--line:rgba(255,255,255,.11)}}
*{{box-sizing:border-box}} html,body,[class*="css"]{{font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
html,body{{background:#020104}} body{{color:var(--ink);-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}}
#MainMenu,footer,header[data-testid="stHeader"]{{visibility:hidden}}
[data-testid="stAppViewContainer"]{{background:transparent}} [data-testid="stMain"]{{position:relative;z-index:2}}
.stMainBlockContainer{{max-width:1120px;padding:0 28px 118px}}
.video-stage{{position:fixed;inset:0;overflow:hidden;z-index:0;background:#020104 url('{POSTER}') center/cover no-repeat}}
.video-stage video{{width:100%;height:100%;object-fit:cover;object-position:51% 8%;opacity:.76}}
.video-stage:after{{content:"";position:absolute;inset:0;background:radial-gradient(circle at 50% 42%,transparent 5%,rgba(1,0,5,.18) 56%,#020104 100%),linear-gradient(180deg,rgba(0,0,0,.08),rgba(2,1,5,.48))}}
.top-nav{{height:74px;display:flex;align-items:center;justify-content:space-between;position:relative;z-index:3}}
.brand{{color:#fff;font-size:21px;font-weight:800;letter-spacing:-.6px}} .brand span{{color:#b6a0ff}}
.nav-meta{{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:12px}} .nav-dot{{width:7px;height:7px;border-radius:50%;background:#6ee7b7;box-shadow:0 0 12px #6ee7b7}}
.hero-copy{{min-height:51vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:62px 0 42px;animation:heroIn .9s cubic-bezier(.16,1,.3,1) both}}
.hero-copy.compact{{min-height:0;padding:44px 0 18px}} .eyebrow{{padding:8px 13px;border:1px solid var(--line);border-radius:999px;background:rgba(7,5,13,.55);backdrop-filter:blur(12px);color:#e9e4ff;font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase}}
.hero-copy h1{{margin:20px 0 0;color:#fff;font-size:clamp(48px,7.3vw,92px);line-height:.99;letter-spacing:-.055em;font-weight:500}}
.hero-copy.compact h1{{font-size:clamp(34px,5vw,58px)}} .hero-copy h1 span{{display:block;color:#c4b5fd}}
.hero-copy p{{max-width:690px;margin:24px auto 0;color:rgba(255,255,255,.76);font-size:clamp(15px,1.45vw,18px);line-height:1.75;font-weight:300}} .hero-copy.compact p{{display:none}}
[data-testid="stButton"] button{{min-height:44px;border-radius:999px;border:1px solid var(--line);background:rgba(8,7,13,.72);color:#f4f1ff;font-weight:500;backdrop-filter:blur(14px);transition:.18s ease}}
[data-testid="stButton"] button:hover{{border-color:rgba(196,181,253,.7);color:#fff;background:rgba(71,50,120,.58);transform:translateY(-1px)}}
.section-label{{color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.11em;font-size:10px;font-weight:600;margin:4px 0 10px}}
[data-testid="stChatMessage"]{{border:1px solid var(--line);border-radius:22px;padding:14px 17px;margin:10px 0;background:rgba(8,7,13,.72);backdrop-filter:blur(18px);box-shadow:0 18px 50px rgba(0,0,0,.16)}}
[data-testid="stChatMessage"] p{{line-height:1.7}} [data-testid="stChatMessageAvatarUser"]{{background:#f7f5ff;color:#09070f}} [data-testid="stChatMessageAvatarAssistant"]{{background:#7251c7}}
[data-testid="stChatInput"]{{border:1px solid rgba(255,255,255,.16);border-radius:999px;background:rgba(9,8,15,.88);backdrop-filter:blur(22px);box-shadow:0 20px 60px rgba(0,0,0,.45)}}
[data-testid="stChatInput"] textarea{{color:#fff!important}} [data-testid="stBottomBlockContainer"]{{background:linear-gradient(180deg,transparent,#020104 60%)}}
[data-testid="stExpander"]{{border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.035);overflow:hidden}}
.source-card{{padding:10px 2px 12px;border-bottom:1px solid rgba(255,255,255,.07)}} .source-card:last-child{{border-bottom:0}}
.source-title{{color:#fff;font-size:13px;font-weight:600}} .source-meta{{color:rgba(255,255,255,.55);font-size:11px;margin-top:5px;word-break:break-word}}
.source-badge{{display:inline-block;padding:3px 7px;margin-right:5px;border-radius:99px;background:rgba(167,139,250,.14);color:#d8ccff;font-size:10px;border:1px solid rgba(167,139,250,.2)}}
[data-testid="stSidebar"]{{background:#09080f;border-right:1px solid var(--line)}} [data-testid="stSidebar"] *{{color:#f4f1ff}}
.empty-note{{text-align:center;color:rgba(255,255,255,.48);font-size:12px;margin:12px 0 20px}}
@keyframes heroIn{{from{{opacity:0;transform:translateY(24px);filter:blur(5px)}}to{{opacity:1;transform:none;filter:none}}}}
@media(max-width:700px){{.stMainBlockContainer{{padding-left:18px;padding-right:18px}}.top-nav{{height:62px}}.hero-copy{{min-height:44vh;padding-top:38px}}.hero-copy h1{{font-size:clamp(43px,14vw,68px)}}.nav-meta span:last-child{{display:none}}}}
@media(prefers-reduced-motion:reduce){{*,*:before,*:after{{animation:none!important;transition:none!important}}.video-stage video{{display:none}}}}
</style>
<div class="video-stage" aria-hidden="true"><video autoplay muted loop playsinline preload="auto" poster="{POSTER}"><source src="{VIDEO}" type="video/mp4"></video></div>
""",
        unsafe_allow_html=True,
    )


def render_sources(sources: list[dict], retrieval_source: str | None) -> None:
    if not sources:
        return
    route = "PageIndex fallback" if retrieval_source == "pageindex" else "Hybrid · Dense + BM25 + RRF"
    with st.expander(f"{len(sources)} nguồn đã sử dụng · {route}"):
        for index, source in enumerate(sources, 1):
            metadata = source.get("metadata", {})
            title = escape(str(metadata.get("title", "Không có tiêu đề")))
            location = escape(str(metadata.get("url") or metadata.get("source", "Không rõ nguồn")))
            method = escape(str(source.get("retrieval_method", "retrieval")))
            score = float(source.get("score", 0.0))
            raw = " ".join(str(source.get("content", "")).split())
            excerpt = escape(raw[:220] + ("…" if len(raw) > 220 else ""))
            st.markdown(
                f'<div class="source-card"><div class="source-title">[S{index}] {title}</div>'
                f'<div class="source-meta"><span class="source-badge">{method}</span>'
                f'<span class="source-badge">{score:.4f}</span><br>{location}<br><br>{excerpt}</div></div>',
                unsafe_allow_html=True,
            )


def queue_question(question: str) -> None:
    st.session_state.pending_query = question


inject_design()

with st.sidebar:
    st.markdown("## Cấu hình truy xuất")
    st.caption("Điều chỉnh số đoạn văn đưa vào mô hình tạo câu trả lời.")
    top_k = st.slider("Số chunks", 3, 10, 5)
    st.markdown("---")
    st.markdown("**Pipeline đang sử dụng**")
    st.caption("Dense + BM25 → RRF → PageIndex fallback → LLM với citation")
    st.markdown("**Corpus**")
    st.caption("3 tài liệu pháp lý · 5 bài viết · 986 chunks")
    if st.button("Xóa cuộc trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()

st.markdown('<div class="top-nav"><div class="brand">Viet<span>Heritage</span></div><div class="nav-meta"><i class="nav-dot"></i><span>RAG pipeline sẵn sàng</span></div></div>', unsafe_allow_html=True)
compact = " compact" if st.session_state.messages else ""
st.markdown(
    f'<section class="hero-copy{compact}"><div class="eyebrow">AI grounded in verified sources</div>'
    '<h1>Khám phá Việt Nam<span>qua từng di sản.</span></h1>'
    '<p>Hỏi đáp về di sản văn hóa, quy định du lịch và điều kiện phát triển du lịch Phú Quốc — mọi câu trả lời đều được đối chiếu với nguồn.</p></section>',
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown('<div class="section-label">Bắt đầu với một câu hỏi</div>', unsafe_allow_html=True)
    for column, question in zip(st.columns(3), SUGGESTIONS):
        with column:
            st.button(question, key=f"suggestion-{question}", use_container_width=True, on_click=queue_question, args=(question,))
    st.markdown('<div class="empty-note">Câu trả lời chỉ sử dụng dữ liệu trong corpus của dự án.</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        render_sources(message.get("sources", []), message.get("retrieval_source"))

typed_query = st.chat_input("Hỏi về du lịch và di sản Việt Nam…")
query = st.session_state.pop("pending_query", None) or typed_query

if query and query.strip():
    query = query.strip()
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Đang truy xuất và đối chiếu nguồn…"):
            try:
                result = generate_with_citation(query, top_k=top_k)
            except Exception:
                result = {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
        st.markdown(result["answer"])
        render_sources(result["sources"], result["retrieval_source"])
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "retrieval_source": result["retrieval_source"],
    })
    st.rerun()
