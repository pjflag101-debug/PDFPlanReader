"""Project-specific legend/context records.

The semantic meaning is project-independent; its visual representation is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Evidence, ReviewStatus
from .semantics import SemanticClass


@dataclass
class LegendMapping:
    semantic_class: SemanticClass
    project_id: str | None = None
    floor_id: str | None = None
    evidence: Evidence = field(default_factory=Evidence)
    review_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED

    def __post_init__(self) -> None:
        if self.semantic_class is SemanticClass.IGNORE:
            raise ValueError("IGNORE is not a project legend meaning")
