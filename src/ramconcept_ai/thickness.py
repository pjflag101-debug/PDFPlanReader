"""Find slab thicknesses on structural slab plan PDFs.

Two kinds of thickness are found:

  typical  The thickness that applies everywhere unless shown otherwise, usually in the
           drawing title or notes, e.g. "ROOF LEVEL SLAB PLAN - 220 POST TENSIONED SLAB
           MINIMUM U.N.O."  (U.N.O. = unless noted otherwise)

  local    A thickness tag on the plan: a number drawn inside a small box (the legend's
           "THK - DENOTES SLAB THICKNESS" symbol), often with a word next to it such as
           MIN or RC.  Plain numbers without a box (step heights, dimensions) are ignored.

Each local tag also gets a grid reference (e.g. "5-6 / B-C") worked out from the
grid bubbles printed around the plan.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pymupdf

# Plausible slab thicknesses in mm.
MIN_MM, MAX_MM = 80, 1500

# Words next to a tag that describe it.
QUALIFIERS = {"MIN", "MIN.", "MAX", "MAX.", "RC", "PT", "P.T.", "TYP", "TYP.", "THK", "MM"}

SLAB_TYPES = {
    "POST TENSIONED": "post-tensioned",
    "POST-TENSIONED": "post-tensioned",
    "PT": "post-tensioned",
    "P.T.": "post-tensioned",
    "RC": "reinforced concrete",
    "REINFORCED CONCRETE": "reinforced concrete",
}

# "220 POST TENSIONED SLAB MINIMUM U.N.O.", "200mm THK RC SLAB", "250 THICK SLAB TYP."
TYPICAL_RE = re.compile(
    r"\b(?P<mm>\d{2,4})\s*(?:MM)?\s*(?:THK|THICK)?\.?\s*"
    r"(?P<type>POST[- ]TENSIONED|P\.?T\.?|RC|REINFORCED CONCRETE)?\s*"
    r"(?:SUSPENDED\s+|TRANSFER\s+|GROUND\s+)?SLAB\b(?P<rest>[^\n]*)",
    re.IGNORECASE,
)
# "200 THK" / "200mm THK" anywhere in the text
THK_RE = re.compile(r"\b(?P<mm>\d{2,4})\s*(?:MM)?\s*(?:THK|THICK)\b", re.IGNORECASE)


@dataclass
class SlabThickness:
    thickness_mm: int
    kind: str  # "typical" or "local"
    page: int
    qualifiers: list[str] = field(default_factory=list)  # e.g. ["MIN", "RC"]
    slab_type: str | None = None  # "post-tensioned", "reinforced concrete", ...
    grid: str | None = None  # e.g. "5-6 / B-C"
    source: str = ""  # the text it came from
    bbox: tuple[float, float, float, float] | None = None  # position on the page (points)

    @property
    def description(self) -> str:
        parts = [f"{self.thickness_mm} mm"]
        if any(q.startswith("MIN") for q in self.qualifiers):
            parts.append("minimum")
        if self.slab_type:
            parts.append(self.slab_type)
        return " ".join(parts)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["description"] = self.description
        return d


def _slab_type(words: list[str] | str | None) -> str | None:
    if not words:
        return None
    text = " ".join(words) if isinstance(words, list) else words
    text = text.upper().strip()
    for key, value in SLAB_TYPES.items():
        if re.search(rf"(?<![A-Z]){re.escape(key)}(?![A-Z])", text):
            return value
    return None


def _in_range(mm: int) -> bool:
    return MIN_MM <= mm <= MAX_MM


# --------------------------------------------------------------------------- typical


def find_typical(page: pymupdf.Page) -> list[SlabThickness]:
    """Thicknesses written as sentences, e.g. in the drawing title or notes."""
    found: list[SlabThickness] = []
    seen: set[tuple[int, str]] = set()
    text = page.get_text("text", sort=True)
    for line in text.splitlines():
        line = " ".join(line.split())  # collapse the big gaps PDFs leave between words
        for m in TYPICAL_RE.finditer(line):
            mm = int(m["mm"])
            if not _in_range(mm):
                continue
            rest = m["rest"].upper()
            quals = []
            if re.search(r"\bMIN(IMUM)?\b", rest):
                quals.append("MIN")
            if "U.N.O" in rest or "UNO" in rest.split():
                quals.append("U.N.O.")
            if re.search(r"\bTYP(ICAL)?\b", rest):
                quals.append("TYP")
            key = (mm, m.group(0))
            if key in seen:
                continue
            seen.add(key)
            found.append(
                SlabThickness(
                    thickness_mm=mm,
                    kind="typical",
                    page=page.number + 1,
                    qualifiers=quals,
                    slab_type=_slab_type(m["type"]),
                    source=m.group(0).strip(),
                )
            )
    return found


# --------------------------------------------------------------------------- local tags


def _segments(page: pymupdf.Page) -> tuple[list, list]:
    """All short horizontal and vertical line segments on the page."""
    horiz, vert = [], []
    for path in page.get_drawings():
        for item in path["items"]:
            if item[0] == "l":
                a, b = item[1], item[2]
                if abs(a.y - b.y) < 0.5:
                    horiz.append((min(a.x, b.x), max(a.x, b.x), a.y))
                elif abs(a.x - b.x) < 0.5:
                    vert.append((min(a.y, b.y), max(a.y, b.y), a.x))
            elif item[0] == "re":
                r = item[1]
                horiz += [(r.x0, r.x1, r.y0), (r.x0, r.x1, r.y1)]
                vert += [(r.y0, r.y1, r.x0), (r.y0, r.y1, r.x1)]
    return horiz, vert


def _box_around(word: pymupdf.Rect, horiz: list, vert: list) -> pymupdf.Rect | None:
    """Return the box drawn tightly around a word, or None if there isn't one."""
    w, h = word.width, word.height
    pad = max(h, 6) * 0.9  # how far the box may sit from the text
    max_len_h, max_len_v = w * 4 + 2 * pad, h * 3 + 2 * pad  # sides of a *small* box only

    def spans_x(seg):
        return seg[0] <= word.x0 + 1 and seg[1] >= word.x1 - 1 and seg[1] - seg[0] <= max_len_h

    def spans_y(seg):
        return seg[0] <= word.y0 + 1 and seg[1] >= word.y1 - 1 and seg[1] - seg[0] <= max_len_v

    tops = [s[2] for s in horiz if spans_x(s) and word.y0 - pad <= s[2] <= word.y0 + 1.5]
    bottoms = [s[2] for s in horiz if spans_x(s) and word.y1 - 1.5 <= s[2] <= word.y1 + pad]
    lefts = [s[2] for s in vert if spans_y(s) and word.x0 - pad <= s[2] <= word.x0 + 1]
    rights = [s[2] for s in vert if spans_y(s) and word.x1 - 1 <= s[2] <= word.x1 + pad]
    if not (tops and bottoms and lefts and rights):
        return None
    return pymupdf.Rect(max(lefts), max(tops), min(rights), min(bottoms))


def _grid(page: pymupdf.Page, words: list) -> tuple[list, list]:
    """Grid bubbles: labels printed twice on the same line (top+bottom, or left+right).

    Returns (columns, rows) as sorted lists of (position, label)."""
    labels: dict[str, list[pymupdf.Rect]] = {}
    for x0, y0, x1, y1, s, *_ in words:
        if re.fullmatch(r"[A-Z]{1,2}|\d{1,2}", s) and (y1 - y0) >= 8:
            labels.setdefault(s, []).append(pymupdf.Rect(x0, y0, x1, y1))
    cols, rows = [], []
    for label, rects in labels.items():
        for i, a in enumerate(rects):
            for b in rects[i + 1 :]:
                ac, bc = (a.tl + a.br) / 2, (b.tl + b.br) / 2
                if abs(ac.x - bc.x) < 3 and abs(ac.y - bc.y) > 200:
                    cols.append(((ac.x + bc.x) / 2, label))
                elif abs(ac.y - bc.y) < 3 and abs(ac.x - bc.x) > 200:
                    rows.append(((ac.y + bc.y) / 2, label))
    # keep one entry per label
    cols = sorted({lbl: pos for pos, lbl in cols}.items(), key=lambda kv: kv[1])
    rows = sorted({lbl: pos for pos, lbl in rows}.items(), key=lambda kv: kv[1])
    return [(p, l) for l, p in cols], [(p, l) for l, p in rows]


def _between(value: float, lines: list[tuple[float, str]]) -> str | None:
    if len(lines) < 2:
        return None
    for (p0, l0), (p1, l1) in zip(lines, lines[1:]):
        if abs(value - p0) < 3:
            return l0
        if p0 < value < p1:
            return f"{l0}-{l1}"
    if abs(value - lines[-1][0]) < 3:
        return lines[-1][1]
    return f"outside {lines[0][1]}-{lines[-1][1]}"


def find_local_tags(page: pymupdf.Page) -> list[SlabThickness]:
    """Boxed thickness tags on the plan, e.g. [200] MIN RC."""
    words = page.get_text("words")
    horiz, vert = _segments(page)
    cols, rows = _grid(page, words)
    found = []
    for x0, y0, x1, y1, s, *_ in words:
        if not re.fullmatch(r"\d{2,4}", s) or not _in_range(int(s)):
            continue
        rect = pymupdf.Rect(x0, y0, x1, y1)
        box = _box_around(rect, horiz, vert)
        if box is None:
            continue

        # words just to the right of, or just under, the box
        near = box + (-box.height, -box.height * 0.3, box.width * 1.2, box.height * 1.6)
        quals = []
        for wx0, wy0, wx1, wy1, ws, *_ in words:
            wr = pymupdf.Rect(wx0, wy0, wx1, wy1)
            if wr == rect or not near.intersects(wr):
                continue
            if ws.upper() in QUALIFIERS:
                quals.append(ws.upper().rstrip("."))

        center = (box.tl + box.br) / 2
        col, row = _between(center.x, cols), _between(center.y, rows)
        grid = " / ".join(g for g in (col, row) if g) or None
        found.append(
            SlabThickness(
                thickness_mm=int(s),
                kind="local",
                page=page.number + 1,
                qualifiers=quals,
                slab_type=_slab_type(quals),
                grid=grid,
                source=" ".join([s] + quals),
                bbox=tuple(round(v, 1) for v in box),
            )
        )
    return found


def _find_thk_text(page: pymupdf.Page, already: list[SlabThickness]) -> list[SlabThickness]:
    """Unboxed "200 THK" style labels not already found."""
    known = {t.thickness_mm for t in already}
    out = []
    for line in page.get_text("text", sort=True).splitlines():
        line = " ".join(line.split())
        if "DENOTES" in line.upper():  # legend line
            continue
        for m in THK_RE.finditer(line):
            mm = int(m["mm"])
            if _in_range(mm) and mm not in known:
                known.add(mm)
                out.append(SlabThickness(mm, "local", page.number + 1, ["THK"], source=m.group(0)))
    return out


# --------------------------------------------------------------------------- public


def find_slab_thicknesses(pdf: str | Path | pymupdf.Document) -> list[SlabThickness]:
    """Find every slab thickness in a PDF: typical first, then local tags, page by page."""
    doc = pymupdf.open(pdf) if not isinstance(pdf, pymupdf.Document) else pdf
    try:
        results: list[SlabThickness] = []
        for page in doc:
            typical = find_typical(page)
            local = find_local_tags(page)
            results += typical + local + _find_thk_text(page, typical + local)
        return results
    finally:
        if doc is not pdf:
            doc.close()
