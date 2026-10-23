from pathlib import Path

import pymupdf
import pytest

from pdf_plan_reader import read_pdf


@pytest.fixture
def sample_plan(tmp_path: Path) -> Path:
    path = tmp_path / "plan.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595)
    page.insert_text((100, 100), "LEVEL 1 SLAB PROFILE - 230 U.N.O.", fontsize=10)
    page.insert_text((250, 250), "260-230", fontsize=9)
    page.draw_rect(pymupdf.Rect(80, 80, 700, 500), width=0.8)
    doc.save(path)
    doc.close()
    return path


def test_reads_pdf_native_word_bounds(sample_plan: Path):
    doc = read_pdf(sample_plan)
    assert doc.page_count == 1
    words = {word.text: word for word in doc.pages[0].words}
    assert "260-230" in words
    box = words["260-230"].bbox
    assert box[2] > box[0]
    assert box[3] > box[1]


def test_renders_plan_image(sample_plan: Path, tmp_path: Path):
    image_dir = tmp_path / "images"
    doc = read_pdf(sample_plan, image_dir=image_dir, dpi=90)
    assert doc.pages[0].image_path is not None
    assert Path(doc.pages[0].image_path).exists()


def test_missing_pdf_raises():
    with pytest.raises(FileNotFoundError):
        read_pdf("missing-plan.pdf")
