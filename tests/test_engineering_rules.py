from pdf_plan_reader import ReviewStatus, design_thickness_from_range, design_wet_area_thickness


def test_explicit_thickness_range_uses_minimum_for_design():
    decision = design_thickness_from_range(260, 230)
    assert decision.source_thickness_range_mm == (260, 230)
    assert decision.maximum_thickness_mm == 260
    assert decision.minimum_thickness_mm == 230
    assert decision.design_thickness_mm == 230
    assert decision.design_basis == "MINIMUM_DRAWING_THICKNESS"


def test_wet_area_uses_step_plus_maximum_fall_at_critical_low_point():
    decision = design_wet_area_thickness(
        parent_slab_thickness_mm=230,
        step_or_setdown_mm=10,
        maximum_fall_mm=20,
    )
    assert decision.design_reduction_mm == 30
    assert decision.design_thickness_mm == 200
    assert decision.review_status is ReviewStatus.ACCEPTED


def test_wet_area_missing_evidence_requires_review():
    decision = design_wet_area_thickness(
        parent_slab_thickness_mm=230,
        step_or_setdown_mm=10,
        maximum_fall_mm=None,
    )
    assert decision.design_thickness_mm is None
    assert decision.review_status is ReviewStatus.REVIEW_REQUIRED
