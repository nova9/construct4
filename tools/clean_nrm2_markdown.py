from __future__ import annotations

import re
import unicodedata
from pathlib import Path


SOURCE = Path("NRN2 document text extracted.txt")
OUTPUT = Path("NRM2-detailed-measurement-clean.md")

RUNNING_LINES = {
    "IP",
    "NRM 2: DETAILED MEASUREMENT FOR BUILDING WORKS",
    "RETURN TO WORK SECTIONS CONTENTS",
}

SECTION_LABELS = {
    "In this work section:",
    "Drawings that should accompany this section of measurement:",
    "Information that should be provided:",
    "Minimum information that should be shown on the drawings that accompany this section of measurement:",
    "Works and materials are included:",
    "Notes:",
}

ATOMIC_HEADINGS = {
    "Acknowledgements",
    "Contents",
    "Glossary",
    "Introduction",
    "Introduction to NRM",
    "RICS professional standards and guidance",
}


def clean_line(line: str) -> str:
    line = unicodedata.normalize("NFKC", line)
    line = line.replace("\x08", "")
    line = re.sub(r"\ufffd{2,}", " — ", line)
    line = line.replace("\ufffd", "")
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()


def page_label(lines: list[str]) -> tuple[str | None, list[str]]:
    while lines and not lines[0]:
        lines.pop(0)
    if lines and lines[0] == "IP":
        lines.pop(0)
    while lines and not lines[0]:
        lines.pop(0)

    if lines and re.fullmatch(r"(?:[ivxlcdm]+|\d+)", lines[0], re.I):
        return lines.pop(0), lines
    return None, lines


def remove_running_matter(lines: list[str]) -> list[str]:
    return [line for line in lines if line not in RUNNING_LINES]


def join_wrapped_work_section_titles(lines: list[str]) -> list[str]:
    joined: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if re.match(r"^Work section \d+:", line):
            parts = [line]
            lookahead = index + 1
            while (
                lookahead < len(lines)
                and lines[lookahead]
                and re.match(r"^[a-z]", lines[lookahead])
            ):
                parts.append(lines[lookahead])
                lookahead += 1
            joined.append(" ".join(parts))
            index = lookahead
            continue
        joined.append(line)
        index += 1
    return joined


def is_table_page(lines: list[str]) -> bool:
    joined = "\n".join(lines)
    measurement_headers = sum(
        marker in joined
        for marker in ("Unit", "Level one", "Level two", "Level three", "Notes")
    )
    pricing_headers = sum(
        marker in joined
        for marker in ("Item", "Subitem", "Description", "Included", "Pricing method", "Excluded")
    )
    return (
        ("Item or work to" in joined and measurement_headers >= 3)
        or pricing_headers >= 5
        or ("Cost centre" in joined and "Total charges" in joined)
    )


def blocks_from_lines(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append(" ".join(current))
            current = []

    for line in lines:
        if not line:
            flush()
            continue
        if line == "•" or line in ATOMIC_HEADINGS or line in SECTION_LABELS:
            flush()
            blocks.append(line)
            continue
        if re.match(r"^Work section \d+:", line):
            flush()
            blocks.append(line)
            continue
        current.append(line)
    flush()
    return blocks


def combine_list_blocks(blocks: list[str]) -> list[str]:
    result: list[str] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if block == "•" and index + 1 < len(blocks):
            result.append(f"- {blocks[index + 1]}")
            index += 2
            continue
        if re.fullmatch(r"\d+", block) and index + 1 < len(blocks):
            following = blocks[index + 1]
            if not re.fullmatch(r"\d+", following):
                result.append(f"{block}. {following}")
                index += 2
                continue
        if re.fullmatch(r"\d+\.\d+(?:\.\d+)*", block) and index + 1 < len(blocks):
            result.append(f"{block} {blocks[index + 1]}")
            index += 2
            continue
        result.append(block)
        index += 1
    return result


def heading_level(block: str) -> int | None:
    if re.match(r"^Work section \d+:", block):
        return 1
    if re.match(r"^Appendix [A-Z](?::|\b)", block):
        return 1
    if re.match(
        r"^[123] (?:General|Detailed measurement of building works|Rules of measurement for building works)$",
        block,
    ):
        return 1
    if re.match(r"^[A-Z]\d+\s+", block):
        return 2
    if re.match(r"^\d+\.\d+(?:\.\d+)*\s+", block):
        return 2
    if block in ATOMIC_HEADINGS:
        return 1
    if block.rstrip(":") + ":" in SECTION_LABELS:
        return 3
    if re.match(r"^(Figure|Table) [A-Z0-9.]+:", block):
        return 4
    return None


def prose_markdown(
    lines: list[str],
    page_reference: str,
    seen_passages: dict[str, str],
) -> list[str]:
    blocks = combine_list_blocks(blocks_from_lines(lines))
    output: list[str] = []
    for block in blocks:
        block = re.sub(r"\s+", " ", block).strip()
        if not block:
            continue
        level = heading_level(block)
        if level:
            output.append(f"{'#' * level} {block.rstrip(':')}")
        else:
            duplicate_key = block.casefold()
            should_deduplicate = (
                len(block) >= 160
                and not block.startswith(("- ", "> "))
                and not re.match(r"^\d+[.)]\s", block)
            )
            if should_deduplicate and duplicate_key in seen_passages:
                original_page = seen_passages[duplicate_key]
                output.append(
                    f"> Exact duplicate passage omitted; see source page {original_page}."
                )
                continue
            if should_deduplicate:
                seen_passages[duplicate_key] = page_reference
            output.append(block)
    return output


def table_markdown(lines: list[str]) -> list[str]:
    compact = [line for line in lines if line]
    return ["### Source-layout table", "```text", *compact, "```"]


def convert(source: str) -> str:
    rendered: list[str] = [
        "---",
        'title: "NRM 2: Detailed Measurement for Building Works"',
        'edition: "2nd edition UK"',
        'publication_date: "October 2021"',
        'effective_date: "1 December 2021"',
        'source_format: "OCR-derived plain text"',
        "---",
        "",
        "# NRM 2: Detailed Measurement for Building Works",
        "",
        "> Cleaned Markdown derived from the supplied text extraction. Source-page markers are preserved. Tables remain in source-layout text blocks where the OCR does not establish column relationships reliably.",
        "> Exact repeated prose is retained at its first occurrence and replaced later by a source-page cross-reference. Repeated headings and table labels are preserved where they provide structure.",
        "> The duplicated cover and table-of-contents pages are omitted; publication metadata is recorded above.",
        "",
    ]

    seen_passages: dict[str, str] = {}

    for page_index, raw_page in enumerate(source.split("\f"), start=1):
        lines = [clean_line(line) for line in raw_page.splitlines()]
        label, lines = page_label(lines)
        if page_index == 1 or label in {"iv", "v", "vi"}:
            continue
        lines = remove_running_matter(lines)
        lines = join_wrapped_work_section_titles(lines)
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        if not lines:
            continue

        rendered.extend(["---", ""])
        if label:
            rendered.append(f"<!-- Source page: {label}; extracted page: {page_index} -->")
        else:
            rendered.append(f"<!-- Extracted page: {page_index} -->")
        rendered.append("")

        page_reference = label or f"extracted-{page_index}"
        if is_table_page(lines):
            rendered.extend(table_markdown(lines))
            rendered.append("")
        else:
            for item in prose_markdown(lines, page_reference, seen_passages):
                rendered.extend([item, ""])

    return "\n".join(rendered).rstrip() + "\n"


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    OUTPUT.write_text(convert(source), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
