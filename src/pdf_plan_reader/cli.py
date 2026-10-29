"""Command-line interface for PDFPlanReader."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pdf_reader import read_pdf


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="pdfplan", description="Read a structural design-plan PDF")
    sub = parser.add_subparsers(dest="command", required=True)

    read_parser = sub.add_parser("read", help="extract PDF-native text, word boxes and page images")
    read_parser.add_argument("pdf", type=Path)
    read_parser.add_argument("-o", "--out", type=Path, default=Path("output"))
    read_parser.add_argument("--images", action="store_true")
    read_parser.add_argument("--dpi", type=int, default=150)

    args = parser.parse_args(argv)
    if args.command == "read":
        args.out.mkdir(parents=True, exist_ok=True)
        images = args.out / "images" if args.images else None
        doc = read_pdf(args.pdf, image_dir=images, dpi=args.dpi)
        out_json = args.out / f"{args.pdf.stem}.json"
        doc.save_json(out_json)
        print(f"Read {doc.page_count} page(s): {args.pdf}")
        print(f"Saved: {out_json}")


if __name__ == "__main__":
    main()
