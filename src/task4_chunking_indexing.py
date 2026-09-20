"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import hashlib
import math
import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

from .contracts import validate_document


load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip().lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip() or "BAAI/bge-m3"
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"

_EMBEDDING_MODEL_INSTANCE = None


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFC", text.lower())
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


def _hash_embeddings(texts: list[str]) -> list[list[float]]:
    """Dependency-free fallback that produces stable normalized dense vectors."""
    vectors: list[list[float]] = []
    for text in texts:
        vector = [0.0] * EMBEDDING_DIM
        tokens = _tokens(text)
        features = tokens + [f"{a}::{b}" for a, b in zip(tokens, tokens[1:])]
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % EMBEDDING_DIM
            vector[index] += 1.0 if value & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        vectors.append([value / norm for value in vector])
    return vectors


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed text with the configured provider and a deterministic local fallback."""
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("All texts must be non-empty strings")

    if EMBEDDING_PROVIDER in {"hashing", "local_hashing"}:
        return _hash_embeddings(texts)

    if EMBEDDING_PROVIDER == "sentence_transformers":
        try:
            from sentence_transformers import SentenceTransformer

            global _EMBEDDING_MODEL_INSTANCE
            if _EMBEDDING_MODEL_INSTANCE is None:
                _EMBEDDING_MODEL_INSTANCE = SentenceTransformer(EMBEDDING_MODEL)
            vectors = _EMBEDDING_MODEL_INSTANCE.encode(
                texts,
                batch_size=32,
                normalize_embeddings=True,
                show_progress_bar=len(texts) > 64,
            )
            return vectors.tolist()
        except (ImportError, OSError, RuntimeError) as error:
            if os.getenv("ALLOW_HASH_EMBEDDING_FALLBACK", "1") == "1":
                print(f"Embedding fallback to local hashing: {error}")
                return _hash_embeddings(texts)
            raise

    if EMBEDDING_PROVIDER == "openai":
        from openai import OpenAI

        model = EMBEDDING_MODEL if EMBEDDING_MODEL != "BAAI/bge-m3" else "text-embedding-3-small"
        response = OpenAI().embeddings.create(model=model, input=texts)
        return [item.embedding for item in response.data]

    if EMBEDDING_PROVIDER == "gemini":
        from google import genai

        model = EMBEDDING_MODEL if EMBEDDING_MODEL != "BAAI/bge-m3" else "gemini-embedding-001"
        response = genai.Client(api_key=os.getenv("GEMINI_API_KEY")).models.embed_content(
            model=model,
            contents=texts,
        )
        return [list(item.values) for item in response.embeddings]

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    try:
        import chromadb
    except ImportError as error:
        raise RuntimeError("ChromaDB is required: python -m pip install chromadb") from error

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _extract_metadata(path: Path, content: str) -> dict:
    title_match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    source_match = re.search(r"^\*\*Source:\*\*\s*(.+)$", content, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    source_value = source_match.group(1).strip() if source_match else path.name
    is_url = source_value.startswith(("http://", "https://"))
    return {
        "source": source_value if is_url else path.name,
        "title": title,
        "doc_type": "legal" if "legal" in path.parts else "news",
        "url": source_value if is_url else None,
    }


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents: list[dict] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        document = {
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": _extract_metadata(path, content),
        }
        validate_document(document)
        documents.append(document)
    return documents


def _split_text(text: str) -> list[str]:
    """Paragraph-aware character splitter with deterministic overlap."""
    text = re.sub(r"[ \t]+", " ", text).strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        hard_end = min(start + CHUNK_SIZE, len(text))
        end = hard_end
        if hard_end < len(text):
            search_from = start + int(CHUNK_SIZE * 0.7)
            candidates = [
                text.rfind("\n\n", search_from, hard_end),
                text.rfind("\n", search_from, hard_end),
                text.rfind(". ", search_from, hard_end),
                text.rfind(" ", search_from, hard_end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (2 if text[boundary:boundary + 2] == ". " else 0)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    chunks: list[dict] = []
    for document in documents:
        validate_document(document)
        for index, text in enumerate(_split_text(document["content"])):
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []
    vectors: list[list[float]] = []
    for start in range(0, len(chunks), 64):
        vectors.extend(embed_texts([chunk["content"] for chunk in chunks[start:start + 64]]))
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding provider returned an unexpected vector count")
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    collection = get_collection()
    current_ids = set(collection.get(include=[]).get("ids", []))
    desired_ids = {chunk["id"] for chunk in chunks}
    stale_ids = sorted(current_ids - desired_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)

    for start in range(0, len(chunks), 100):
        batch = chunks[start:start + 100]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[
                {key: ("" if value is None else value) for key, value in chunk["metadata"].items()}
                for chunk in batch
            ],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
