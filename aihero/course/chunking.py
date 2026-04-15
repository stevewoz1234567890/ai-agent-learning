"""Split document bodies into retrieval-sized chunks."""

from __future__ import annotations


def _body(doc: dict) -> str:
    text = doc.get("content")
    if text is None:
        return ""
    return str(text).strip()


def chunk_documents(
    docs: list[dict],
    *,
    max_chars: int = 2500,
    source_repo: str | None = None,
) -> list[dict]:
    """
    Split each document into paragraph-merged chunks up to max_chars.

    Each output chunk has: text, filename, source_repo, chunk_index (within doc).
    """
    chunks: list[dict] = []
    default_repo = source_repo

    for doc in docs:
        filename = doc.get("filename", "unknown")
        src = doc.get("source_repo") or default_repo or "unknown"
        body = _body(doc)
        if not body:
            continue
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        buf: list[str] = []
        size = 0
        chunk_idx = 0

        def flush():
            nonlocal buf, size, chunk_idx
            if not buf:
                return
            text = "\n\n".join(buf)
            chunks.append(
                {
                    "text": text,
                    "filename": filename,
                    "source_repo": src,
                    "chunk_index": chunk_idx,
                }
            )
            chunk_idx += 1
            buf = []
            size = 0

        for p in paragraphs:
            add = len(p) + (2 if buf else 0)
            if size + add > max_chars and buf:
                flush()
            if len(p) > max_chars:
                flush()
                for start in range(0, len(p), max_chars):
                    piece = p[start : start + max_chars]
                    chunks.append(
                        {
                            "text": piece,
                            "filename": filename,
                            "source_repo": src,
                            "chunk_index": chunk_idx,
                        }
                    )
                    chunk_idx += 1
                continue
            buf.append(p)
            size += add
        flush()

    return chunks
