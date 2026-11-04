# StageChat developer commands. Run from this folder with the `stagechat` conda env active.

WEB := apps/web

.PHONY: check test lint format api web env-check

# Everything that must pass before a commit
check: test lint
	cd $(WEB) && npm run lint && npm run build

test: env-check
	python -m pytest -q

lint: env-check
	python -m ruff check .
	python -m ruff format --check .

format: env-check
	python -m ruff format .
	python -m ruff check --fix .

api: env-check
	python -m uvicorn server.api:app --reload --reload-dir server --port 8000

web:
	cd $(WEB) && npm run dev

env-check:
	@python -c "import fastapi, pytest" 2>/dev/null || \
	    (echo "Backend packages not found. Run: conda activate stagechat" && exit 1)
