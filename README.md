# PDFPlanReader

An AI assistant for reading RAM Concept engineering PDFs (calculation reports and plan plots).

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
from ramconcept_ai import read_pdf

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
