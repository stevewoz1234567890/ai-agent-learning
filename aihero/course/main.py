"""CLI: ingest GitHub markdown corpora and run BM25 + optional LLM Q&A."""

from __future__ import annotations

import argparse
import sys
import time

from chunking import chunk_documents
from ingest import read_repo_data
from rag import DocumentIndex, answer


REPOS: tuple[tuple[str, str, str], ...] = (
    ("DataTalksClub", "faq", "DataTalksClub/faq"),
    ("evidentlyai", "docs", "evidentlyai/docs"),
)


def load_corpus(only: set[str] | None = None) -> list[dict]:
    """Load configured repos; optionally restrict by slug (e.g. faq, docs)."""
    all_docs: list[dict] = []
    for owner, name, slug in REPOS:
        key = name.lower()
        if only is not None and key not in only and slug.split("/")[-1].lower() not in only:
            continue
        t0 = time.perf_counter()
        docs = read_repo_data(owner, name)
        for d in docs:
            d["source_repo"] = slug
        elapsed = time.perf_counter() - t0
        print(f"Loaded {len(docs)} documents from {slug} in {elapsed:.1f}s", file=sys.stderr)
        all_docs.extend(docs)
    return all_docs


def cmd_stats(_: argparse.Namespace) -> int:
    for owner, name, slug in REPOS:
        docs = read_repo_data(owner, name)
        print(f"{slug}: {len(docs)} markdown files")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    only = None
    if args.repos:
        only = {x.strip().lower() for x in args.repos.split(",") if x.strip()}
    docs = load_corpus(only=only)
    chunks = chunk_documents(docs, max_chars=args.max_chunk_chars)
    print(f"Indexed {len(chunks)} chunks", file=sys.stderr)
    index = DocumentIndex(chunks)
    text, hits = answer(
        index,
        args.question,
        top_k=args.top_k,
        use_llm=not args.no_llm,
    )
    print(text)
    if args.verbose and hits:
        print("\n--- Retrieval ---", file=sys.stderr)
        for h in hits:
            print(f"  score={h.score:.3f} {h.source_repo} {h.filename}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Documentation RAG: BM25 retrieval over FAQ + Evidently docs; optional OpenAI synthesis."
    )
    sub = p.add_subparsers(dest="command", required=True)

    st = sub.add_parser("stats", help="Count markdown files in each configured repo")
    st.set_defaults(func=cmd_stats)

    ask = sub.add_parser("ask", help="Answer a question using retrieved context")
    ask.add_argument("question", help="Natural language question")
    ask.add_argument(
        "--repos",
        help="Comma-separated filter: short names from configured list (e.g. faq,docs)",
        default=None,
    )
    ask.add_argument("--top-k", type=int, default=8, dest="top_k")
    ask.add_argument("--max-chunk-chars", type=int, default=2500, dest="max_chunk_chars")
    ask.add_argument(
        "--no-llm",
        action="store_true",
        help="Print retrieved context only (no OPENAI_API_KEY required)",
    )
    ask.add_argument("-v", "--verbose", action="store_true")
    ask.set_defaults(func=cmd_ask)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
