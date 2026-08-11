from __future__ import annotations

import json
from pathlib import Path

from openai.lib._pydantic import to_strict_json_schema

from second_pass_schema import SecondPassResult

OUTPUT_PATH = Path("second_pass_result.schema.json")


def main() -> None:
    schema = to_strict_json_schema(SecondPassResult)

    OUTPUT_PATH.write_text(
        json.dumps(schema, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
