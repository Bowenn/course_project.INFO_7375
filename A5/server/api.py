"""FastAPI endpoints for StageChat."""

from fastapi import FastAPI

app = FastAPI(title="StageChat API", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness check used by the frontend and by `make check`."""
    return {"status": "ok"}
