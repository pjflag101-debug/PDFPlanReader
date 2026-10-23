import pymupdf
import pytest

from ramconcept_ai import read_pdf


@pytest.fixture
def sample_pdf(tmp_path):
    """A two-page PDF: a report page with a table, and a near-empty 'drawing' page."""
    path = tmp_path / "sample.pdf"
    doc = pymupdf.open()

    page = doc.new_page()
    page.insert_text((72, 72), "RAM Concept Calculation Report - Level 2 Slab", fontsize=12)
    page.insert_text((72, 90), "Concrete f'c = 40 MPa. Slab thickness = 250 mm. " * 3, fontsize=8)
    # simple ruled 3x3 table
    x0, y0, w, h = 72, 140, 120, 20
    rows = [["Strip", "Mu (kNm)", "Status"], ["CS-1", "152.3", "OK"], ["MS-1", "98.7", "OK"]]
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            rect = pymupdf.Rect(x0 + c * w, y0 + r * h, x0 + (c + 1) * w, y0 + (r + 1) * h)
            page.draw_rect(rect, color=(0, 0, 0), width=0.8)
            page.insert_text((rect.x0 + 4, rect.y1 - 6), cell, fontsize=9)

    drawing = doc.new_page()
    drawing.draw_line((50, 50), (500, 700))
    drawing.insert_text((60, 760), "Plan", fontsize=10)

    doc.save(path)
    doc.close()
    return path


def test_reads_text_and_tables(sample_pdf):
    doc = read_pdf(sample_pdf)
    assert doc.page_count == 2
    assert "Calculation Report" in doc.pages[0].text
    assert not doc.pages[0].likely_drawing
    assert doc.pages[0].tables, "table should be detected"
    assert ["CS-1", "152.3", "OK"] in doc.pages[0].tables[0]


def test_flags_drawing_pages(sample_pdf):
    assert read_pdf(sample_pdf).pages[1].likely_drawing


def test_renders_images(sample_pdf, tmp_path):
    doc = read_pdf(sample_pdf, image_dir=tmp_path / "img", dpi=72)
    assert all(p.image_path and (tmp_path / "img").joinpath(p.image_path.split("/")[-1]).exists() for p in doc.pages)


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        read_pdf("does_not_exist.pdf")
