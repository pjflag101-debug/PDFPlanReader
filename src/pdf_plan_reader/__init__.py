"""Public API for PDFPlanReader."""

from .engineering_rules import (
    ThicknessDecision,
    WetAreaDecision,
    design_thickness_from_range,
    design_wet_area_thickness,
)
from .models import DesignRegion, DrawingMetadata, Evidence, ReviewStatus
from .pdf_reader import PdfDocument, PdfPage, PdfWord, read_pdf
from .semantics import SemanticClass

__all__ = [
    "DesignRegion",
    "DrawingMetadata",
    "Evidence",
    "PdfDocument",
    "PdfPage",
    "PdfWord",
    "ReviewStatus",
    "SemanticClass",
    "ThicknessDecision",
    "WetAreaDecision",
    "design_thickness_from_range",
    "design_wet_area_thickness",
    "read_pdf",
]
