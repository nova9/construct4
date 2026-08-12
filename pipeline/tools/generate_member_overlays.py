from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from pipeline.schemas.second_pass import Beam, Column, SecondPassResult
from pipeline.schemas.third_pass import (
    MemberPosition,
    ThirdPassResult,
    validate_against_second_pass,
)


Member = Beam | Column
COLORS = {
    "beam": {"stroke": "#1769e0", "fill": "rgba(23,105,224,0.18)"},
    "column": {"stroke": "#d58400", "fill": "rgba(213,132,0,0.22)"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render one full-page PNG per beam or column, with only that "
            "member's normalized third-pass position overlaid."
        )
    )
    parser.add_argument("--pdf", type=Path, default=Path("data/input/plan.pdf"))
    parser.add_argument(
        "--result", type=Path, default=Path("data/results/second_pass.json")
    )
    parser.add_argument(
        "--positions", type=Path, default=Path("data/results/third_pass.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output/member-overlays")
    )
    parser.add_argument("--dpi", type=int, default=150)
    return parser.parse_args()


def run(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "unknown command error").strip()
        raise SystemExit(f"Command failed: {' '.join(command[:2])}\n{detail}") from error
    return completed.stdout.strip()


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(
            f"Required command '{name}' was not found. "
            "Install Poppler and ImageMagick, then rerun this script."
        )


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return cleaned or "unnamed-member"


def image_size(path: Path) -> tuple[int, int]:
    raw = run(["magick", "identify", "-format", "%w %h", str(path)])
    width, height = raw.split()
    return int(width), int(height)


def label_font() -> str:
    candidates = (
        Path("/System/Library/Fonts/HelveticaNeue.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise SystemExit("No suitable label font was found for ImageMagick.")


def render_page(pdf: Path, page: int, dpi: int, output: Path) -> None:
    prefix = output.with_suffix("")
    run(
        [
            "pdftoppm",
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            "-r",
            str(dpi),
            "-png",
            str(pdf),
            str(prefix),
        ]
    )


def draw_member(
    source_page: Path,
    output: Path,
    member: Member,
    position_record: MemberPosition,
    kind: str,
    font: str,
) -> dict[str, object]:
    if position_record.position is None:
        raise ValueError(f"{member.key} has no position")

    width, height = image_size(source_page)
    position = position_record.position
    x1 = round(position.left * width)
    y1 = round(position.top * height)
    x2 = round(position.right * width)
    y2 = round(position.bottom * height)

    line_width = max(5, round(min(width, height) / 330))
    handle = line_width * 2
    point_size = max(20, round(min(width, height) / 85))
    label = f"{kind.upper()} | {member.drawing_id or 'UNLABELLED'} | {member.key}"
    label_width = min(width - 16, round(len(label) * point_size * 0.62 + 24))
    label_height = point_size + 18
    label_x = min(max(8, x1), max(8, width - label_width - 8))
    label_y = y1 - label_height - 8
    if label_y < 8:
        label_y = min(height - label_height - 8, y2 + 8)

    color = COLORS[kind]
    rectangles = [
        (x1 - handle, y1 - handle, x1 + handle, y1 + handle),
        (x2 - handle, y1 - handle, x2 + handle, y1 + handle),
        (x1 - handle, y2 - handle, x1 + handle, y2 + handle),
        (x2 - handle, y2 - handle, x2 + handle, y2 + handle),
    ]
    draw_commands = [
        f"fill {color['fill']} stroke {color['stroke']} "
        f"stroke-width {line_width} rectangle {x1},{y1} {x2},{y2}",
        f"fill {color['stroke']} stroke none rectangle "
        f"{label_x},{label_y} {label_x + label_width},{label_y + label_height}",
    ]
    draw_commands.extend(
        f"fill {color['stroke']} stroke white stroke-width 2 rectangle {a},{b} {c},{d}"
        for a, b, c, d in rectangles
    )

    escaped_label = label.replace("\\", "\\\\").replace("'", "\\'")
    command = ["magick", str(source_page)]
    for draw_command in draw_commands:
        command.extend(["-draw", draw_command])
    command.extend(
        [
            "-font",
            font,
            "-pointsize",
            str(point_size),
            "-fill",
            "white",
            "-stroke",
            "none",
            "-draw",
            f"text {label_x + 12},{label_y + point_size + 4} '{escaped_label}'",
            "-strip",
            str(output),
        ]
    )
    run(command)

    return {
        "key": member.key,
        "drawing_id": member.drawing_id,
        "kind": kind,
        "page": member.page,
        "location": member.location,
        "normalized_position": position.model_dump(),
        "pixel_position": {"left": x1, "top": y1, "right": x2, "bottom": y2},
        "image_size": {"width": width, "height": height},
        "image": output.as_posix(),
    }


def main() -> None:
    args = parse_args()
    require_command("pdftoppm")
    require_command("magick")

    if args.dpi <= 0:
        raise SystemExit("--dpi must be greater than zero")
    if not args.pdf.is_file():
        raise SystemExit(f"PDF not found: {args.pdf}")
    if not args.result.is_file():
        raise SystemExit(f"Second-pass result not found: {args.result}")
    if not args.positions.is_file():
        raise SystemExit(f"Third-pass positions not found: {args.positions}")

    result = SecondPassResult.model_validate_json(args.result.read_text())
    positions = ThirdPassResult.model_validate_json(args.positions.read_text())
    validate_against_second_pass(positions, result)
    font = label_font()
    position_maps = {
        "beam": {record.key: record for record in positions.beams},
        "column": {record.key: record for record in positions.columns},
    }
    members: list[tuple[str, Member, MemberPosition]] = [
        *(("beam", member, position_maps["beam"][member.key]) for member in result.beams),
        *(("column", member, position_maps["column"][member.key]) for member in result.columns),
    ]
    positioned = [
        (kind, member, record)
        for kind, member, record in members
        if record.position
    ]
    skipped = [
        member.key for _, member, record in members if record.position is None
    ]

    args.output.mkdir(parents=True, exist_ok=True)
    for kind in COLORS:
        kind_output = args.output / kind
        kind_output.mkdir(exist_ok=True)
        for old_image in kind_output.glob("*.png"):
            old_image.unlink()

    manifest: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="member-overlay-pages-") as temp_dir:
        temp_root = Path(temp_dir)
        rendered_pages: dict[int, Path] = {}
        for page in sorted({member.page for _, member, _ in positioned}):
            rendered = temp_root / f"page-{page}.png"
            render_page(args.pdf, page, args.dpi, rendered)
            rendered_pages[page] = rendered

        for kind, member, position_record in positioned:
            filename = (
                f"page-{member.page:02d}__{kind}__{safe_filename(member.key)}.png"
            )
            output = args.output / kind / filename
            manifest.append(
                draw_member(
                    rendered_pages[member.page],
                    output,
                    member,
                    position_record,
                    kind,
                    font,
                )
            )

    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "source_pdf": args.pdf.as_posix(),
                "source_result": args.result.as_posix(),
                "source_positions": args.positions.as_posix(),
                "dpi": args.dpi,
                "generated_images": len(manifest),
                "skipped_without_position": skipped,
                "members": manifest,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"Generated {len(manifest)} member overlay images in {args.output} "
        f"({len(skipped)} skipped without a position)."
    )
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
