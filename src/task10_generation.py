"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os
import re
import unicodedata

from dotenv import load_dotenv

from .contracts import validate_generation_result
from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ các tài liệu hiện có."

SYSTEM_PROMPT = """Bạn là trợ lý hỏi đáp về du lịch và di sản Việt Nam.
Chỉ trả lời từ context được cung cấp, không dùng kiến thức bên ngoài.
Trích dẫn mỗi khẳng định bằng nhãn nguồn [S1], [S2] tương ứng trong context.
Nếu context không đủ bằng chứng, trả lời đúng câu: "Tôi không thể xác minh thông tin này từ các tài liệu hiện có."
Trả lời bằng tiếng Việt, rõ ràng và ngắn gọn."""


def _has_sufficient_evidence(query: str, chunks: list[dict]) -> bool:
    stopwords = {"là", "có", "và", "của", "cho", "về", "theo", "những", "nào", "gì"}
    normalize = lambda text: {
        token
        for token in re.findall(
            r"[^\W_]+", unicodedata.normalize("NFC", text.lower()), flags=re.UNICODE
        )
        if len(token) > 1 and token not in stopwords
    }
    query_tokens = normalize(query)
    context_tokens = normalize(" ".join(chunk["content"] for chunk in chunks))
    return bool(query_tokens) and len(query_tokens & context_tokens) / len(query_tokens) >= 0.4


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)
    front = list(chunks[::2])
    back = list(chunks[1::2])
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        citation_label = metadata.get("citation_label", f"S{index}")
        source = metadata["source"]
        url_line = f"\nURL: {metadata['url']}" if metadata.get("url") else ""
        parts.append(
            f"[{citation_label}] Title: {metadata['title']}\n"
            f"Source: {source}{url_line}\n"
            f"Content:\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured")
        response = OpenAI().responses.create(
            model=LLM_MODEL or "gpt-5-mini",
            instructions=system_prompt,
            input=user_message,
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.output_text.strip()

    if LLM_PROVIDER == "gemini":
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=LLM_MODEL or "gemini-3.6-flash",
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                ),
            )
            answer = response.text
        finally:
            client.close()
        if not answer:
            raise RuntimeError("Gemini returned an empty response")
        return answer.strip()

    if LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic

        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        response = Anthropic().messages.create(
            model=LLM_MODEL or "claude-sonnet-4-5",
            max_tokens=1200,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text")).strip()

    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    try:
        chunks = retrieve(query.strip(), top_k=top_k)
    except Exception as error:
        print(f"Retrieval failed: {error}")
        chunks = []
    if not chunks:
        result = {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
        validate_generation_result(result)
        return result
    if not _has_sufficient_evidence(query, chunks):
        result = {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
        validate_generation_result(result)
        return result

    labeled_chunks = [
        {**chunk, "metadata": {**chunk["metadata"], "citation_label": f"S{index}"}}
        for index, chunk in enumerate(chunks, 1)
    ]
    reordered = reorder_for_llm(labeled_chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query.strip()}"
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as error:
        print(f"Generation provider unavailable: {error}")
        result = {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
        validate_generation_result(result)
        return result

    method = chunks[0]["retrieval_method"]
    retrieval_source = "pageindex" if method == "pageindex" else "hybrid"
    result = {
        "answer": answer or SAFE_REFUSAL,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }
    validate_generation_result(result)
    return result


if __name__ == "__main__":
    print(generate_with_citation("test query"))
