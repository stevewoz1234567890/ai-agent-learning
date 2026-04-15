# Documentation RAG (course)

End-to-end flow: **fetch** markdown from two GitHub repos → **parse** front matter → **chunk** by paragraph size → **retrieve** with BM25 → **answer** with an LLM or print context only.

## Corpora

| Slug (for `--repos`) | Repository |
|----------------------|------------|
| `faq` | [DataTalksClub/faq](https://github.com/DataTalksClub/faq) |
| `docs` | [evidentlyai/docs](https://github.com/evidentlyai/docs) |

Zip URLs use `refs/heads/main`, then `refs/heads/master` if needed.

## Layout

| Module | Role |
|--------|------|
| `ingest.py` | Download repo zip, extract `.md` / `.mdx`, `python-frontmatter` |
| `chunking.py` | Merge paragraphs into chunks (default max 2500 characters) |
| `rag.py` | `rank_bm25` index, context formatting, optional OpenAI chat |
| `main.py` | `stats` and `ask` subcommands |

## Setup

```bash
cd aihero/course
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

With [uv](https://github.com/astral-sh/uv):

```bash
cd aihero/course
uv sync
uv run python main.py stats
```

Dependencies are listed in `pyproject.toml` (`requests`, `python-frontmatter`, `rank-bm25`, `openai`). Lockfile: `uv.lock`.

## Environment variables (LLM path)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Required for synthesized answers (omit and use `--no-llm` for retrieval-only). |
| `OPENAI_MODEL` | Chat model (default: `gpt-4o-mini`). |
| `OPENAI_BASE_URL` | Optional; use for OpenAI-compatible proxies or local servers. |

If `ask` runs without a key and without `--no-llm`, the tool falls back to printing the retrieved context (same as `--no-llm`).

## CLI

### `stats`

Downloads each configured repo and prints how many markdown files were found.

```bash
python main.py stats
```

### `ask`

Loads the corpus (optionally filtered), builds chunks and a BM25 index, retrieves top passages, then either calls the chat API or prints context.

```bash
python main.py ask "YOUR QUESTION"
python main.py ask "YOUR QUESTION" --no-llm
python main.py ask "YOUR QUESTION" --repos faq
python main.py ask "YOUR QUESTION" --repos faq,docs --top-k 10 -v
```

| Option | Description |
|--------|-------------|
| `question` | Positional: natural-language query. |
| `--repos` | Comma-separated filter: match repo **name** or last path segment (e.g. `faq`, `docs`). Omit to use both corpora. |
| `--top-k` | Number of chunks to retrieve (default: 8). |
| `--max-chunk-chars` | Maximum characters per chunk before splitting (default: 2500). |
| `--no-llm` | Skip the API; print ranked context blocks only. |
| `-v`, `--verbose` | On stderr, list retrieval scores and source paths. |

Example with API:

```bash
export OPENAI_API_KEY=sk-...
python main.py ask "How do I monitor data drift with Evidently?"
```

## Help

```bash
python main.py -h
python main.py ask -h
```
