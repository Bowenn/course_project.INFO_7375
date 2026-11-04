"""Export JSON Schemas generated from the Pydantic models.

The frontend's TypeScript types are generated from these files (`npm run gen:types`), so the
Pydantic models stay the single source of truth.

Usage (from the repository root):
    python tools/export_schemas.py          # write the schema files
    python tools/export_schemas.py --check  # exit 1 if a committed file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import BaseModel

from server.scene.schema import Scene

ROOT = Path(__file__).resolve().parents[1]

SCHEMAS: dict[Path, type[BaseModel]] = {
    ROOT / "server/scene/scene.schema.json": Scene,
}


def render(model: type[BaseModel]) -> str:
    # Serialization mode describes the JSON the backend emits, which is what the frontend reads.
    schema = model.model_json_schema(mode="serialization")
    document = {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a schema file is stale")
    args = parser.parse_args(argv)

    stale = []
    for path, model in SCHEMAS.items():
        text = render(model)
        relative = path.relative_to(ROOT)
        if args.check:
            if not path.exists() or path.read_text() != text:
                stale.append(relative)
        else:
            path.write_text(text)
            print(f"wrote {relative}")

    if stale:
        names = ", ".join(str(p) for p in stale)
        print(f"stale schema file(s): {names}. Run `make schemas`.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
