"""Lexical retrieval (BM25) and optional LLM answer synthesis."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from openai import OpenAI
from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


@dataclass
class RetrievalHit:
    chunk_index: int
    score: float
    text: str
    filename: str
    source_repo: str


class DocumentIndex:
    def __init__(self, chunks: list[dict]):
        chunks = [c for c in chunks if (c.get("text") or "").strip()]
        if not chunks:
            raise ValueError("chunks must be non-empty")
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        tokenized = [_tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 8) -> list[RetrievalHit]:
        q = _tokenize(query)
        if not q:
            return []
        scores = self._bm25.get_scores(q)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        hits: list[RetrievalHit] = []
        for i, score in ranked[:top_k]:
            if score <= 0:
                continue
            ch = self.chunks[i]
            hits.append(
                RetrievalHit(
                    chunk_index=i,
                    score=float(score),
                    text=ch["text"],
                    filename=ch.get("filename", "unknown"),
                    source_repo=ch.get("source_repo", "unknown"),
                )
            )
        return hits


def format_context(hits: list[RetrievalHit]) -> str:
    parts = []
    for h in hits:
        parts.append(
            f"---\nSource: {h.source_repo} / {h.filename}\n{h.text}"
        )
    return "\n".join(parts)


def synthesize_answer(
    query: str,
    context_block: str,
    *,
    model: str | None = None,
    client: OpenAI | None = None,
) -> str:
    """Call the chat API. Uses OPENAI_API_KEY and optional OPENAI_BASE_URL."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set; use retrieval-only mode or export the key."
        )
    c = client or OpenAI()
    m = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    system = (
        "You are a careful assistant. Answer using ONLY the provided context. "
        "If the context does not contain enough information, say you do not know. "
        "When stating facts, mention the source path (filename) they came from."
    )
    user = f"Context:\n{context_block}\n\nQuestion: {query}"
    resp = c.chat.completions.create(
        model=m,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    choice = resp.choices[0].message
    return (choice.content or "").strip()


def answer(
    index: DocumentIndex,
    query: str,
    *,
    top_k: int = 8,
    use_llm: bool = True,
) -> tuple[str, list[RetrievalHit]]:
    hits = index.search(query, top_k=top_k)
    if not hits:
        return "No relevant passages found in the indexed documentation.", []
    ctx = format_context(hits)
    if not use_llm:
        return ctx, hits
    try:
        return synthesize_answer(query, ctx), hits
    except RuntimeError as e:
        if "OPENAI_API_KEY" in str(e):
            return ctx, hits
        raise
