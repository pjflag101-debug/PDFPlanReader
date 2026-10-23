"""Print lists of rows as neat text tables in the terminal, and save them as CSV."""

from __future__ import annotations

import csv
from pathlib import Path


def format_table(headers: list[str], rows: list[list], title: str | None = None) -> str:
    """Return a boxed text table, e.g.

    +------+-----------+
    | Page | Type      |
    +------+-----------+
    |    1 | drawing   |
    +------+-----------+
    """
    cells = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in cells:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(v))

    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def fmt(row, header=False):
        out = []
        for i, v in enumerate(row):
            numeric = not header and v.replace(".", "", 1).isdigit()
            out.append(f" {v.rjust(widths[i]) if numeric else v.ljust(widths[i])} ")
        return "|" + "|".join(out) + "|"

    parts = []
    if title:
        parts.append(title)
    parts += [line, fmt(headers, header=True), line]
    parts += [fmt(r) for r in cells] or ["| " + "(none found)".ljust(len(line) - 4) + " |"]
    parts.append(line)
    return "\n".join(parts)


def save_csv(path: str | Path, headers: list[str], rows: list[list]) -> None:
    """Save rows as a CSV file that opens in Excel."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
