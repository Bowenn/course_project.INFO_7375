# StageChat

**StageChat** is a domain-specific chatbot for conversational 3D room staging. Describe a room in plain language — *"a 4 × 5 m Scandinavian living room for a family with a cat, window on the north wall"* — and StageChat plans a furniture layout, retrieves matching 3D models from a curated asset catalog, places them with a constraint solver, and renders the room in your browser. Then keep talking: *"move the sofa under the window"*, *"swap the coffee table for a round one"*, *"make the armchair dark green"*. Under the hood, a tool-using LLM agent edits a hierarchical scene graph, and a verifier checks every edit for collisions, out-of-bounds objects, and blocked paths before it reaches the screen.

*Built as the final project for INFO 7375 (Semantic Intelligence in LLM) at Northeastern University, Fall 2026.*

> Status: early development. The pieces below are being built sprint by sprint.

## Setup

Requirements: [conda](https://docs.conda.io/) (Miniconda is enough) and Node.js 22.18 or newer.

```bash
conda env create -f environment.yml   # Python 3.11 + backend deps (editable install)
conda activate stagechat
cp .env.example .env                  # then add your own API keys
cd apps/web && npm install && cd ../..
```

## Commands

Run these from the repository root with the `stagechat` env active.

| Command | What it does |
|---|---|
| `make check` | Backend tests, ruff lint + format check, frontend lint + build |
| `make api` | Backend at http://localhost:8000 (auto-reload) |
| `make web` | Frontend dev server at http://localhost:5173 |
| `make format` | Auto-format and auto-fix Python code |

## Layout

```text
apps/web/     React + Vite + TypeScript viewer and chat UI
server/       FastAPI backend: agent loop, LLM adapters, scene schema/solver/verifier, retrieval
tests/        Backend tests (pytest)
assets/       Asset catalog; raw downloads and processed GLBs are git-ignored
tools/        Asset and schema scripts
eval/         Benchmark prompts, edit dialogues, splits, metrics
```

## License

Code: [MIT](LICENSE). Third-party assets keep their own licenses; see [CREDITS.md](CREDITS.md).
