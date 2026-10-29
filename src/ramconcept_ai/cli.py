"""Command line entry point.

    ramread <file.pdf> [options]
    python -m ramconcept_ai <file.pdf> [options]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ramconcept_ai.pdf_reader import read_pdf
from ramconcept_ai.table import format_table, save_csv
from ramconcept_ai.thickness import find_slab_thicknesses

THICKNESS_HEADERS = ["Thickness (mm)", "Where", "Grid", "Notes", "Slab type", "Page", "Found as"]


def _thickness_rows(found) -> list[list]:
    rows = []
    for t in found:
        where = "Everywhere (typical)" if t.kind == "typical" else "Local tag on plan"
        notes = ", ".join(
            {"MIN": "minimum", "U.N.O.": "unless noted otherwise", "TYP": "typical"}.get(q, q)
            for q in t.qualifiers
            if q not in ("RC", "PT")
        )
        rows.append([t.thickness_mm, where, t.grid or "-", notes or "-", t.slab_type or "-", t.page, t.source])
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Read a RAM Concept / structural slab PDF.")
    parser.add_argument("pdf", type=Path, help="PDF file to read")
    parser.add_argument("-o", "--out", type=Path, default=Path("output"), help="output folder (default: output/)")
    parser.add_argument("--images", action="store_true", help="also render each page to PNG")
    parser.add_argument("--dpi", type=int, default=150, help="image resolution (default: 150)")
    parser.add_argument("--no-tables", action="store_true", help="skip table detection (faster)")
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    doc = read_pdf(
        args.pdf,
        extract_tables=not args.no_tables,
        image_dir=args.out / "images" if args.images else None,
        dpi=args.dpi,
    )
    thicknesses = find_slab_thicknesses(args.pdf)

    stem = args.pdf.stem
    (args.out / f"{stem}.txt").write_text(doc.full_text)
    data = doc.to_dict()
    data["slab_thicknesses"] = [t.to_dict() for t in thicknesses]
    (args.out / f"{stem}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    rows = _thickness_rows(thicknesses)
    save_csv(args.out / f"{stem}_thickness.csv", THICKNESS_HEADERS, rows)

    # ---- what you see in the terminal
    print()
    page_rows = []
    for p in doc.pages:
        kind = "drawing" if p.likely_drawing else "text"
        first_line = (p.text.splitlines()[0].strip()[:45] if p.text else "")
        page_rows.append([p.number, kind, len(p.text), len(p.tables), first_line])
    print(format_table(["Page", "Type", "Characters", "Tables", "Starts with"], page_rows, title=f"{args.pdf.name}: {doc.page_count} page(s)"))
    print()
    print(format_table(THICKNESS_HEADERS[:6], [r[:6] for r in rows], title="Slab thickness"))

    typical = [t for t in thicknesses if t.kind == "typical"]
    local = [t for t in thicknesses if t.kind == "local"]
    if typical or local:
        print()
        if typical:
            print(f"Summary: the slab is {typical[0].description} unless noted otherwise.")
        for t in local:
            print(f"         {t.description} at grid {t.grid or '?'}.")

    print()
    print(f"Saved to {args.out}/: {stem}.txt, {stem}.json, {stem}_thickness.csv" + (", images/" if args.images else ""))


if __name__ == "__main__":
    main()
