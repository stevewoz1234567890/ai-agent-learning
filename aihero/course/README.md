# Course: documentation RAG

Loads markdown from the DataTalks Club FAQ and Evidently docs GitHub repos, chunks it, retrieves with BM25, and optionally synthesizes an answer with the OpenAI API.

## Setup

```bash
cd aihero/course
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
python main.py stats
python main.py ask "What is Evidently?" --no-llm
python main.py ask "What courses does DataTalks Club offer?" --repos faq --verbose
```

With an API key (and optional `OPENAI_MODEL`, `OPENAI_BASE_URL`):

```bash
export OPENAI_API_KEY=sk-...
python main.py ask "How do I monitor data drift with Evidently?"
```
