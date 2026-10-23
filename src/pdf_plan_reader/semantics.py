"""Project-independent semantic classes used by the design plan reader."""

from __future__ import annotations

from enum import Enum


class SemanticClass(str, Enum):
    """Engineering meaning, independent of a project's visual convention."""

    BACKGROUND_STRONG = "BACKGROUND_STRONG"
    BASE_SLAB = "BASE_SLAB"
    LOCAL_PROPERTY_REGION = "LOCAL_PROPERTY_REGION"
    LOCAL_WET_AREA_OVERRIDE = "LOCAL_WET_AREA_OVERRIDE"
    VOID_PENETRATION = "VOID_PENETRATION"
    MATERIAL_PROPERTY = "MATERIAL_PROPERTY"
    IGNORE = "IGNORE"
