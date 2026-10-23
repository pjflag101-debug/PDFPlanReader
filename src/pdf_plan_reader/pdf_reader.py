"""PDF-native extraction for structural plan drawings.

Coordinates are kept in PDF page space. Text locations come from PDF glyph/word
bounds, not CAD insertion points, so note-to-region alignment remains auditable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class PdfWord:
    text: str
    bbox: tuple[float, float, float, float]
    block_no: int
    line_no: int
    word_no: int


@dataclass
class PdfPage:
    number: int
    width: float
    height: float
    text: str
    words: list[PdfWord] = field(default_factory=list)
    image_path: str | None = None


@dataclass
class PdfDocument:
    path: str
    page_count: int
    metadata: dict[str, str]
    pages: list[PdfPage]

    def to_dict(self) -> dict:
        return asdict(self)

    def save_json(self, out_path: str | Path) -> None:
        Path(out_path).write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )


def read_pdf(
    pdf_path: str | Path,
    *,
    image_dir: str | Path | None = None,
    dpi: int = 150,
) -> PdfDocument:
    """Extract page text, PDF-native word boxes and optional rendered PNGs."""
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    image_root: Path | None = None
    if image_dir is not None:
        image_root = Path(image_dir)
        image_root.mkdir(parents=True, exist_ok=True)

    pages: list[PdfPage] = []
    with pymupdf.open(pdf_path) as doc:
        if doc.needs_pass:
            raise ValueError(f"{pdf_path} is password protected")

        for page in doc:
            words = [
                PdfWord(
                    text=item[4],
                    bbox=(float(item[0]), float(item[1]), float(item[2]), float(item[3])),
                    block_no=int(item[5]),
                    line_no=int(item[6]),
                    word_no=int(item[7]),
                )
                for item in page.get_text("words", sort=True)
            ]

            image_path = None
            if image_root is not None:
                out = image_root / f"{pdf_path.stem}_p{page.number + 1:03d}.png"
                page.get_pixmap(dpi=dpi, alpha=False).save(out)
                image_path = str(out)

            rect = page.rect
            pages.append(
                PdfPage(
                    number=page.number + 1,
                    width=float(rect.width),
                    height=float(rect.height),
                    text=page.get_text("text", sort=True).strip(),
                    words=words,
                    image_path=image_path,
                )
            )

        metadata = {k: str(v) for k, v in (doc.metadata or {}).items() if v}
        page_count = doc.page_count

    return PdfDocument(
        path=str(pdf_path),
        page_count=page_count,
        metadata=metadata,
        pages=pages,
    )
