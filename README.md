# ai-agent-learning

Practice repo for a small **retrieval-augmented** workflow over public GitHub documentation: download markdown as zip archives, chunk it, rank passages with **BM25**, and optionally turn the top hits into an answer with the **OpenAI** API.

## What is in this repository

| Path | Purpose |
|------|---------|
| [`aihero/course/`](aihero/course/) | Python project: ingest, chunking, BM25 index, CLI (`stats` / `ask`) |
| [`aihero/course/README.md`](aihero/course/README.md) | Setup, environment variables, and command-line reference |

**Requirements:** Python 3.11+

**Quick start** (from the course directory):

```bash
cd aihero/course
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python main.py stats
python main.py ask "What is Evidently?" --no-llm
```

Corpora are fixed in code to [DataTalksClub/faq](https://github.com/DataTalksClub/faq) and [evidentlyai/docs](https://github.com/evidentlyai/docs). Each run fetches the latest `main` (or `master`) zip from GitHub; nothing is persisted locally except what you pipe or save yourself.
