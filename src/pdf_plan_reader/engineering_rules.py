"""Explicit, auditable engineering interpretation rules.

These functions never infer missing drawing evidence silently.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import ReviewStatus


@dataclass(frozen=True)
class ThicknessDecision:
    source_thickness_range_mm: tuple[float, float]
    minimum_thickness_mm: float
    maximum_thickness_mm: float
    design_thickness_mm: float
    design_basis: str = "MINIMUM_DRAWING_THICKNESS"
    review_status: ReviewStatus = ReviewStatus.ACCEPTED


@dataclass(frozen=True)
class WetAreaDecision:
    parent_slab_thickness_mm: float | None
    step_or_setdown_mm: float | None
    maximum_fall_mm: float | None
    design_reduction_mm: float | None
    design_thickness_mm: float | None
    review_status: ReviewStatus
    design_basis: str = "CRITICAL_LOW_POINT"


def design_thickness_from_range(value_a_mm: float, value_b_mm: float) -> ThicknessDecision:
    """Use the minimum of an explicitly stated slab-thickness range for design."""
    minimum = min(value_a_mm, value_b_mm)
    maximum = max(value_a_mm, value_b_mm)
    return ThicknessDecision(
        source_thickness_range_mm=(value_a_mm, value_b_mm),
        minimum_thickness_mm=minimum,
        maximum_thickness_mm=maximum,
        design_thickness_mm=minimum,
    )


def design_wet_area_thickness(
    *,
    parent_slab_thickness_mm: float | None,
    step_or_setdown_mm: float | None,
    maximum_fall_mm: float | None,
) -> WetAreaDecision:
    """Return design thickness at the critical low point of a wet area.

    All three values must be explicit drawing evidence. Missing evidence is
    returned as REVIEW_REQUIRED rather than guessed.
    """
    if (
        parent_slab_thickness_mm is None
        or step_or_setdown_mm is None
        or maximum_fall_mm is None
    ):
        return WetAreaDecision(
            parent_slab_thickness_mm=parent_slab_thickness_mm,
            step_or_setdown_mm=step_or_setdown_mm,
            maximum_fall_mm=maximum_fall_mm,
            design_reduction_mm=None,
            design_thickness_mm=None,
            review_status=ReviewStatus.REVIEW_REQUIRED,
        )

    reduction = step_or_setdown_mm + maximum_fall_mm
    return WetAreaDecision(
        parent_slab_thickness_mm=parent_slab_thickness_mm,
        step_or_setdown_mm=step_or_setdown_mm,
        maximum_fall_mm=maximum_fall_mm,
        design_reduction_mm=reduction,
        design_thickness_mm=parent_slab_thickness_mm - reduction,
        review_status=ReviewStatus.ACCEPTED,
    )
