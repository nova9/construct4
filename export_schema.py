"""Export an OpenAI strict JSON Schema for ``codex exec --output-schema``."""

from __future__ import annotations

import json
from pathlib import Path

from openai.lib._pydantic import to_strict_json_schema

from schema import DrawingExtraction

OUTPUT_PATH = Path("result.schema.json")


def main() -> None:
    schema = to_strict_json_schema(DrawingExtraction)
    OUTPUT_PATH.write_text(
        json.dumps(schema, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
