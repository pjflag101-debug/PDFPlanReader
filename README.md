# PDFPlanReader

An AI assistant for reading RAM Concept engineering PDFs (calculation reports and plan plots).

What it does so far:

1. **Reads a PDF**: pulls out the text and tables from every page, can save a picture of each page,
   and flags pages that are drawings rather than text.
2. **Finds the slab thickness**: the typical thickness (e.g. "220 POST TENSIONED SLAB MINIMUM U.N.O.")
   and every local thickness tag on the plan, with its grid location. Results are shown as a table
   and saved as a CSV you can open in Excel.

---

## How to use it (step by step)

These steps are for macOS. You only need to do steps 1–4 once.

### 1. Check you have Python and Git

Open **Terminal** and run:

```bash
python3 --version
git --version
```

You need Python **3.10 or newer**. If either command is not found, install Python from
<https://www.python.org/downloads/> and run `xcode-select --install` to get Git.

### 2. Download the code

```bash
cd ~/Documents
git clone -b Misa-branch https://github.com/pjflag101-debug/PDFPlanReader.git
cd PDFPlanReader
```

(If the branch has not been renamed yet, use `ram-concept-pdf-reader` instead of `Misa-branch`.)

### 3. Create a virtual environment

This keeps the project's packages separate from the rest of your computer.

```bash
python3 -m venv .venv
```

### 4. Install the project

```bash
.venv/bin/pip install -e ".[dev]"
```

This installs PyMuPDF (the PDF library), pytest, and the `ramread` command.

### 5. Check it works

```bash
.venv/bin/pytest
```

You should see `7 passed`.

### 6. Add your PDF

Make a `samples` folder and copy your RAM Concept PDF into it:

```bash
mkdir -p samples
cp ~/Downloads/your_report.pdf samples/
```

PDFs in `samples/` are ignored by Git, so client files won't be uploaded to GitHub by accident.

### 7. Read the PDF

```bash
PYTHONPATH=src .venv/bin/python -m ramconcept_ai samples/your_report.pdf
```

(`.venv/bin/ramread samples/your_report.pdf` does the same thing if it works on your computer.
On some Macs it fails with `No module named 'ramconcept_ai'`, so the command above is the safe one.)

Terminal prints two tables and a one-line summary, for example:

```
your_report.pdf: 1 page(s)
+------+---------+------------+--------+-------------------------+
| Page | Type    | Characters | Tables | Starts with             |
+------+---------+------------+--------+-------------------------+
|    1 | drawing |      42082 |      0 | Regulated Design Record |
+------+---------+------------+--------+-------------------------+

Slab thickness
+----------------+----------------------+-----------+---------------------------------+---------------------+------+
| Thickness (mm) | Where                | Grid      | Notes                           | Slab type           | Page |
+----------------+----------------------+-----------+---------------------------------+---------------------+------+
|            220 | Everywhere (typical) | -         | minimum, unless noted otherwise | post-tensioned      |    1 |
|            200 | Local tag on plan    | 5-6 / B-C | minimum                         | reinforced concrete |    1 |
|            250 | Local tag on plan    | 6-7 / B-C | minimum                         | -                   |    1 |
+----------------+----------------------+-----------+---------------------------------+---------------------+------+

Summary: the slab is 220 mm minimum post-tensioned unless noted otherwise.
         200 mm minimum reinforced concrete at grid 5-6 / B-C.
         250 mm minimum at grid 6-7 / B-C.
```

If the table wraps onto two lines, make the Terminal window wider.

### 8. Look at the results

Everything goes into the `output/` folder:

| File | What's in it |
|------|--------------|
| `output/<name>_thickness.csv` | The slab thickness table: **open this in Excel** |
| `output/<name>.txt` | All the text, split by page |
| `output/<name>.json` | Text, tables, slab thicknesses and PDF details for each page |
| `output/images/<name>_p001.png` … | One picture per page (only with `--images`) |

Open the folder in Finder with:

```bash
open output
```

### How slab thickness is found

| Kind | What it looks for | Example on the drawing |
|------|-------------------|------------------------|
| **Typical** (applies everywhere unless shown otherwise) | A sentence with a number followed by "SLAB" | `ROOF LEVEL SLAB PLAN - 220 POST TENSIONED SLAB MINIMUM U.N.O.` |
| **Local tag** | A number inside a small box (the legend's `THK` symbol), plus nearby words like `MIN`, `RC`, `PT` | `[200] MIN RC` |

- **Grid** is worked out from the grid bubbles (1, 2, 3 … and A, B, C …) around the plan.
  `5-6 / B-C` means between grid lines 5 and 6, and between B and C.
- Numbers **without** a box (step heights, dimensions such as `300`) are ignored.
- Always check the result against the drawing. This is step one, and new drawing styles may need new rules.

### Options

```bash
PYTHONPATH=src .venv/bin/python -m ramconcept_ai samples/your_report.pdf --images            # also save each page as a PNG
PYTHONPATH=src .venv/bin/python -m ramconcept_ai samples/your_report.pdf --images --dpi 300  # sharper images (default 150)
PYTHONPATH=src .venv/bin/python -m ramconcept_ai samples/your_report.pdf --no-tables         # skip table search (faster)
PYTHONPATH=src .venv/bin/python -m ramconcept_ai samples/your_report.pdf -o results          # save to results/ instead of output/
PYTHONPATH=src .venv/bin/python -m ramconcept_ai --help                                      # list all options
```

### Next time

You don't need to install again. Just go to the folder and run it:

```bash
cd ~/Documents/PDFPlanReader
git pull                                   # get the latest changes
PYTHONPATH=src .venv/bin/python -m ramconcept_ai samples/your_report.pdf
```

---

## Using it from Python

```python
from ramconcept_ai import read_pdf

doc = read_pdf("samples/your_report.pdf")
print(doc.page_count, doc.metadata)
for page in doc.pages:
    print(page.number, page.likely_drawing, len(page.tables))
    for table in page.tables:
        for row in table:
            print(row)          # e.g. ['CS-1', '152.3', 'OK']
```

Slab thickness only:

```python
from ramconcept_ai import find_slab_thicknesses

for t in find_slab_thicknesses("samples/your_report.pdf"):
    print(t.thickness_mm, t.kind, t.grid, t.description)
# 220 typical None 220 mm minimum post-tensioned
# 200 local 5-6 / B-C 200 mm minimum reinforced concrete
```

`read_pdf` options: `extract_tables=False` to skip tables, `image_dir="output/images"` to save page
images, `dpi=150` to set image resolution. `doc.save_json("out.json")` saves everything to a file.

---

## Saving your changes to GitHub

```bash
git status                       # see what changed
git add .
git commit -m "Describe your change"
git push
```

---

## Troubleshooting

- **`command not found: python3`**: install Python from python.org (step 1).
- **`No module named 'ramconcept_ai'`**: use the `PYTHONPATH=src .venv/bin/python -m ramconcept_ai ...`
  command instead of `ramread`. Run it from inside the project folder.
- **A command runs forever with no output**: press **Control + C** to stop it. If the project is in
  an iCloud-synced folder (Documents, Desktop), moving it to a folder iCloud doesn't sync can help.
- **`No such file or directory: .venv/bin/ramread`**: you're not in the project folder, or step 4
  wasn't run. Run `cd ~/Documents/PDFPlanReader`, then repeat steps 3–4.
- **`FileNotFoundError`**: check the PDF path. Drag the PDF into Terminal to paste its full path.
- **`password protected`**: the PDF is locked. Save an unlocked copy first.
- **A page says `drawing?` but it has text**: the text is probably part of an image (scanned). Use
  `--images` and look at the PNG.

---

## Roadmap

1. ~~Basic PDF reading: text, tables, page images~~
2. ~~Slab thickness: typical thickness and local thickness tags with grid location~~
3. More slab plan details, one at a time: steps in slab, penetrations/voids, concrete strength, cover
4. Identify RAM Concept page types (material properties, load cases, design strips, punching shear, deflection plots)
5. Parse those sections into structured data (e.g. design strip moments, punching shear ratios)
6. Ask questions with an AI model: send text and tables (plus page images for plots) to an LLM
7. Automated checks: flag failing strips, high punching shear ratios, deflection limit breaches
