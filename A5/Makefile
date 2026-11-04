# StageChat developer commands. Run from this folder with the `stagechat` conda env active.

WEB := apps/web

.PHONY: check test lint format schemas schemas-check api web env-check

# Everything that must pass before a commit
check: test lint schemas-check
	cd $(WEB) && npm run lint && npm run build

test: env-check
	python -m pytest -q

lint: env-check
	python -m ruff check .
	python -m ruff format --check .

format: env-check
	python -m ruff format .
	python -m ruff check --fix .

# Regenerate the JSON Schema from the Pydantic models, then the TypeScript types from it
schemas: env-check
	python tools/export_schemas.py
	cd $(WEB) && npm run gen:types

# Fail if a generated schema or type file is out of date
schemas-check: env-check
	python tools/export_schemas.py --check
	cd $(WEB) && npm run check:types

api: env-check
	python -m uvicorn server.api:app --reload --reload-dir server --port 8000

web:
	cd $(WEB) && npm run dev

env-check:
	@python -c "import fastapi, pytest" 2>/dev/null || \
	    (echo "Backend packages not found. Run: conda activate stagechat" && exit 1)
