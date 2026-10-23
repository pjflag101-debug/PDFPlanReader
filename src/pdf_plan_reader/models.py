"""Core data contracts for PDF-first structural plan understanding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .semantics import SemanticClass


class ReviewStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Evidence:
    source_page: int | None = None
    source_text: str | None = None
    source_bbox: tuple[float, float, float, float] | None = None
    legend_text: str | None = None
    visual_description: str | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class DrawingMetadata:
    drawing_number: str | None = None
    title: str | None = None
    level: str | None = None
    revision: str | None = None


@dataclass
class DesignRegion:
    semantic_class: SemanticClass
    region_id: str | None = None
    parent_region_id: str | None = None
    polygon_pdf: list[tuple[float, float]] | None = None
    parent_slab_thickness_mm: float | None = None
    design_thickness_mm: float | None = None
    source_thickness_range_mm: tuple[float, float] | None = None
    step_or_setdown_mm: float | None = None
    maximum_fall_mm: float | None = None
    evidence: list[Evidence] = field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["semantic_class"] = self.semantic_class.value
        data["review_status"] = self.review_status.value
        return data
