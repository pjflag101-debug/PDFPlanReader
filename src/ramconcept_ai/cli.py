"""Command line entry point: python -m ramconcept_ai.cli <file.pdf> [options]"""

from __future__ import annotations

import argparse
from pathlib import Path

from ramconcept_ai.pdf_reader import read_pdf


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Read a RAM Concept PDF (text, tables, page images).")
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

    stem = args.pdf.stem
    (args.out / f"{stem}.txt").write_text(doc.full_text)
    doc.save_json(args.out / f"{stem}.json")

    print(f"{args.pdf.name}: {doc.page_count} pages")
    for p in doc.pages:
        kind = "drawing?" if p.likely_drawing else "text"
        first_line = p.text.splitlines()[0][:60] if p.text else ""
        print(f"  p{p.number:>3}  {kind:<8}  {len(p.text):>6} chars  {len(p.tables)} tables  {first_line}")
    print(f"Saved to {args.out}/{stem}.txt and {stem}.json")


if __name__ == "__main__":
    main()
