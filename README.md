# PDFPlanReader

PDFPlanReader is a structural-design plan reader focused on understanding **issued engineering PDF drawings** before any CAD/RAM Concept automation.

The project is deliberately PDF-first:

> PDF/AI determines **what** the drawing means. Exact CAD geometry can be added later if required.

## V1 scope

The first version reads structural slab/profile plans and produces design-ready semantic data:

- drawing metadata (sheet, level, revision where available)
- PDF text and text bounding boxes
- rendered plan images for vision models
- `BASE_SLAB` regions
- `LOCAL_PROPERTY_REGION` regions
- `LOCAL_WET_AREA_OVERRIDE` regions
- void / penetration regions
- project-specific legend context
- slab thickness and thickness-range interpretation
- wet-area step/fall design interpretation
- explicit `REVIEW_REQUIRED` results when evidence is incomplete

It intentionally does **not** include DXF coordinate recovery, RAM Concept CPT creation, meshing, design strips, or RAM automation.

## Engineering principles

1. Read the project legend and notes before interpreting hatches or colours.
2. Never encode global rules such as `blue == wet area`.
3. Preserve source evidence and engineer-review status.
4. When a drawing explicitly gives a slab-thickness range such as `260-230`, preserve the range and use the **minimum** value for design (`230 mm`).
5. For an explicitly defined wet area, design thickness at the critical low point is:

   `parent thickness - step/setdown - maximum fall`

   Missing values are not guessed; they become `REVIEW_REQUIRED`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Step 1: Read a PDF

```bash
.venv/bin/ramread samples/your_report.pdf            # text + tables
.venv/bin/ramread samples/your_report.pdf --images   # also render every page to PNG
```

Writes `output/<name>.txt` (all text, by page) and `output/<name>.json` (text, tables,
metadata, and a `likely_drawing` flag for each page).

From Python:

```python
from pdf_plan_reader import read_pdf

doc = read_pdf("samples/your_report.pdf")
for page in doc.pages:
    print(page.number, page.likely_drawing, page.tables)
```

## Tests

```bash
.venv/bin/pytest
```

## Roadmap

1. ~~Basic PDF reading: text, tables, page images~~
2. Identify RAM Concept page types (material properties, load cases, design strips, punching shear, deflection plots)
3. Parse those sections into structured data (e.g. design strip moments, punching shear ratios)
4. Ask questions with an AI model: send text and tables (plus page images for plots) to an LLM
5. Automated checks: flag failing strips, high punching shear ratios, deflection limit breaches
