#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

import fitz


PDF_PATH = Path("plan.pdf")
FIRST_PASS_PATH = Path("first_pass_result.json")
OUTPUT_DIR = Path("second_pass")

DPI = 500
PADDING = 0.03


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    first_pass = json.loads(
        FIRST_PASS_PATH.read_text(encoding="utf-8")
    )

    requests = first_pass["verification_requests"]
    elements = first_pass["elements"]

    elements_by_key = {
        element["key"]: element
        for element in elements
    }

    document = fitz.open(PDF_PATH)

    for index, request in enumerate(requests, start=1):
        page_number = request["page"]
        bbox = request["bbox"]

        left = clamp(bbox["left"] - PADDING)
        top = clamp(bbox["top"] - PADDING)
        right = clamp(bbox["right"] + PADDING)
        bottom = clamp(bbox["bottom"] + PADDING)

        page = document[page_number - 1]
        rect = page.rect

        clip = fitz.Rect(
            rect.x0 + left * rect.width,
            rect.y0 + top * rect.height,
            rect.x0 + right * rect.width,
            rect.y0 + bottom * rect.height,
        )

        pixmap = page.get_pixmap(
            clip=clip,
            dpi=DPI,
            alpha=False,
        )

        name = f"request-{index:03d}"

        image_path = OUTPUT_DIR / f"{name}.png"
        context_path = OUTPUT_DIR / f"{name}.json"

        pixmap.save(image_path)

        required_for = request["required_for"]

        relevant_elements = [
            elements_by_key[key]
            for key in required_for
            if key in elements_by_key
        ]

        context = {
            "request_index": index,
            "source_page": page_number,
            "purpose": request["purpose"],
            "reason": request["reason"],
            "required_for": required_for,
            "first_pass_elements": relevant_elements,
        }

        context_path.write_text(
            json.dumps(context, indent=2) + "\n",
            encoding="utf-8",
        )

        print(
            f"Prepared {name}: "
            f"page {page_number}, "
            f"{len(required_for)} element(s)"
        )

    document.close()


if __name__ == "__main__":
    main()