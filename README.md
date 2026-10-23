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

## Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -e ".[dev]"

# macOS/Linux
.venv/bin/pip install -e ".[dev]"
```

## Basic PDF extraction

```bash
pdfplan read path/to/plan.pdf --images
```

The command writes structured JSON plus optional page PNGs. Text extraction includes PDF-native bounding boxes so later note-to-region alignment uses the PDF itself rather than CAD text insertion points.

## Python

```python
from pdf_plan_reader import read_pdf

pdf = read_pdf("plan.pdf")
for page in pdf.pages:
    print(page.number, len(page.words), page.image_path)
```

## Tests

```bash
pytest
```

## Data and models

This public repository must not contain client drawings or proprietary project data. Training datasets, PDFs, checkpoints and review artifacts should remain in approved private/local storage. Only reusable code, schemas and non-sensitive metadata belong here.
