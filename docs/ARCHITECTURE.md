# PDFPlanReader architecture

## Governing principle

**PDF/AI determines WHAT the drawing means.**

Exact CAD coordinates and RAM Concept generation are intentionally outside this repository's first scope.

## Pipeline

1. **PDF native reader**
   - page metadata
   - text
   - PDF-native word/glyph bounds
   - rendered images
2. **Legend / note reader**
   - project-specific hatch, symbol and text conventions
   - no global colour/hatch assumptions
3. **Visual region detector**
   - `BASE_SLAB`
   - `LOCAL_PROPERTY_REGION`
   - `LOCAL_WET_AREA_OVERRIDE`
   - background / uncertain regions
4. **Semantic resolver**
   - associate regions with source-supported notes and legend evidence
   - distinguish voids and material-only properties
5. **Engineering interpreter**
   - base thickness / U.N.O.
   - explicit thickness ranges -> minimum design thickness
   - wet-area setdown + maximum fall -> critical-low-point design thickness
6. **Engineer review gate**
   - accepted / rejected / review required
7. **Design-ready JSON**

## Segmentation model boundary

A visual model such as SegFormer is only a **region detector**. It must not silently become the text reader, legend resolver or engineering rule engine.

## Data handling

This repository is public. Client drawings, proprietary training patches, checkpoints and project datasets must remain outside the repository unless explicitly approved for public release.
