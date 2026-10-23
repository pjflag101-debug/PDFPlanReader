"""Basic PDF reading for RAM Concept reports and drawings.

Extracts, per page:
  - plain text
  - tables (as lists of rows)
  - an optional rendered PNG image (useful later for vision models on plan plots)

RAM Concept output is usually a mix of calculation reports (text + tables:
loads, design strips, punching shear checks) and plan plots (mostly graphics).
Pages with very little text are flagged as likely drawings.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pymupdf

# Pages with fewer characters than this are probably drawings/plots, not text reports.
DRAWING_TEXT_THRESHOLD = 200


@dataclass
class PageContent:
    number: int  # 1-based
    text: str
    tables: list[list[list[str | None]]] = field(default_factory=list)
    image_path: str | None = None
    likely_drawing: bool = False


@dataclass
class PdfDocument:
    path: str
    page_count: int
    metadata: dict
    pages: list[PageContent]

    @property
    def full_text(self) -> str:
        return "\n\n".join(f"--- Page {p.number} ---\n{p.text}" for p in self.pages)

    def to_dict(self) -> dict:
        return asdict(self)

    def save_json(self, out_path: str | Path) -> None:
        Path(out_path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))


def read_pdf(
    pdf_path: str | Path,
    *,
    extract_tables: bool = True,
    image_dir: str | Path | None = None,
    dpi: int = 150,
) -> PdfDocument:
    """Read a PDF and return its text, tables and (optionally) page images."""
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    if image_dir is not None:
        image_dir = Path(image_dir)
        image_dir.mkdir(parents=True, exist_ok=True)

    pages: list[PageContent] = []
    with pymupdf.open(pdf_path) as doc:
        if doc.needs_pass:
            raise ValueError(f"{pdf_path} is password protected")

        for page in doc:
            text = page.get_text("text", sort=True).strip()

            tables = []
            if extract_tables:
                for table in page.find_tables().tables:
                    # Read each cell from its bounding box: table.extract() in PyMuPDF 2.0
                    # drops spaces and splits punctuation ("152.3" -> "1523\n.").
                    tables.append(
                        [
                            [page.get_textbox(pymupdf.Rect(cell)).strip() if cell else None for cell in row.cells]
                            for row in table.rows
                        ]
                    )

            image_path = None
            if image_dir is not None:
                out = image_dir / f"{pdf_path.stem}_p{page.number + 1:03d}.png"
                page.get_pixmap(dpi=dpi).save(out)
                image_path = str(out)

            pages.append(
                PageContent(
                    number=page.number + 1,
                    text=text,
                    tables=tables,
                    image_path=image_path,
                    likely_drawing=len(text) < DRAWING_TEXT_THRESHOLD,
                )
            )

        return PdfDocument(
            path=str(pdf_path),
            page_count=doc.page_count,
            metadata={k: v for k, v in (doc.metadata or {}).items() if v},
            pages=pages,
        )
