import re

import pymupdf
import pytest

from ramconcept_ai import find_slab_thicknesses
from ramconcept_ai.cli import main


@pytest.fixture
def slab_plan(tmp_path):
    """A small A1-style slab plan: grid bubbles, a title with the typical thickness,
    two boxed thickness tags, and an unboxed step height that must be ignored."""
    path = tmp_path / "plan.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=2384, height=1684)

    # grid: columns 1-3 printed top and bottom, rows A-B printed left and right
    for label, x in [("1", 600), ("2", 900), ("3", 1200)]:
        for y in (300, 950):
            page.insert_text((x, y), label, fontsize=14)
    for label, y in [("A", 450), ("B", 750)]:
        for x in (450, 1400):
            page.insert_text((x, y), label, fontsize=14)

    page.insert_text((700, 1100), "LEVEL 2 SLAB PLAN - 220 POST TENSIONED SLAB MINIMUM U.N.O.", fontsize=14)

    def tag(x, y, value, *words):
        page.insert_text((x, y), value, fontsize=12)
        w = pymupdf.get_text_length(value, fontsize=12)
        page.draw_rect(pymupdf.Rect(x - 4, y - 13, x + w + 4, y + 4), color=(0, 0, 0), width=0.8)
        for i, word in enumerate(words):
            page.insert_text((x + w + 8, y + i * 14), word, fontsize=10)

    tag(700, 600, "200", "MIN", "RC")  # between grids 1-2 and A-B
    tag(1000, 600, "250", "MIN")  # between grids 2-3 and A-B
    page.insert_text((1050, 700), "300", fontsize=12)  # step height: no box
    page.draw_line((1040, 703), (1080, 703))

    doc.save(path)
    doc.close()
    return path


def test_typical_thickness_from_title(slab_plan):
    typical = [t for t in find_slab_thicknesses(slab_plan) if t.kind == "typical"]
    assert len(typical) == 1
    t = typical[0]
    assert t.thickness_mm == 220
    assert t.slab_type == "post-tensioned"
    assert "MIN" in t.qualifiers and "U.N.O." in t.qualifiers


def test_boxed_tags_with_grid(slab_plan):
    local = {t.thickness_mm: t for t in find_slab_thicknesses(slab_plan) if t.kind == "local"}
    assert set(local) == {200, 250}, "300 has no box and is a step height, not a thickness"
    assert local[200].qualifiers == ["MIN", "RC"]
    assert local[200].slab_type == "reinforced concrete"
    assert local[200].grid == "1-2 / A-B"
    assert local[250].grid == "2-3 / A-B"


def test_cli_prints_table_and_saves_csv(slab_plan, tmp_path, capsys):
    out = tmp_path / "out"
    main([str(slab_plan), "-o", str(out), "--no-tables"])
    printed = capsys.readouterr().out
    assert "Slab thickness" in printed
    assert re.search(r"\|\s+220 \| Everywhere \(typical\)", printed)
    csv_text = (out / "plan_thickness.csv").read_text(encoding="utf-8-sig")
    assert csv_text.splitlines()[0].startswith("Thickness (mm),Where,Grid")
    assert "200,Local tag on plan,1-2 / A-B" in csv_text
