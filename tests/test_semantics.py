from pdf_plan_reader import SemanticClass
from pdf_plan_reader.legend import LegendMapping
from pdf_plan_reader.models import Evidence


def test_wet_area_is_semantic_not_colour_rule():
    mapping = LegendMapping(
        semantic_class=SemanticClass.LOCAL_WET_AREA_OVERRIDE,
        project_id="example-project",
        evidence=Evidence(
            legend_text="WET AREA SETDOWN",
            visual_description="project-specific triangular hatch",
        ),
    )
    assert mapping.semantic_class is SemanticClass.LOCAL_WET_AREA_OVERRIDE
    assert "blue" not in (mapping.evidence.legend_text or "").lower()
