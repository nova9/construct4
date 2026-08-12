from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TypeAlias

from openai.lib._pydantic import to_strict_json_schema
from pydantic import BaseModel

from pipeline.schemas.first_pass import DrawingExtraction
from pipeline.schemas.second_pass import SecondPassResult
from pipeline.schemas.third_pass import ThirdPassResult


SchemaModel: TypeAlias = type[BaseModel]
MODELS: dict[str, SchemaModel] = {
    "first": DrawingExtraction,
    "second": SecondPassResult,
    "third": ThirdPassResult,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a strict pass JSON Schema.")
    parser.add_argument("pass_name", choices=MODELS)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    schema = to_strict_json_schema(MODELS[args.pass_name])
    args.output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
