# Dark Future Rules Extraction

This directory contains the rules extraction pass for a faithful, turn-based Dark Future adaptation.

The current files are OCR-based Markdown generated from local scanned PDFs. They are not proofread yet. Treat them as the extraction corpus to clean and verify before implementation planning.

## Sources

- `G:\archive\books and things\warhammer\Dark Future - Rulebook.pdf`
- `G:\archive\books and things\warhammer\whitelinefever.pdf`
- `G:\archive\games stuff\Icewinddale\pics\other\WHITE DWARF\White Dwarf 124.pdf` pages 18-31
- `G:\archive\games stuff\Icewinddale\pics\other\WHITE DWARF\White Dwarf 125.pdf` pages 68-76

## Current Outputs

- `raw/dark-future-rulebook-ocr.md` - full core rulebook OCR with page markers.
- `raw/white-line-fever-ocr.md` - full White Line Fever OCR with page markers.
- `raw/dead-mans-curve-ocr.md` - Dead Man's Curve campaign rules OCR with issue/page markers.
- `core/` - core rulebook split by rules chapter.
- `white-line-fever/` - White Line Fever split by rules chapter.
- `dead-mans-curve/` - Dead Man's Curve split by White Dwarf issue and page range.

## Workflow

1. Extract all rules into Markdown.
2. Proofread and correct OCR chapter by chapter against the page images.
3. Convert tables and track geometry into structured data.
4. Only then plan implementation.

## Notes

- OCR page images are in `_analysis/ocr_pages/`.
- Raw OCR page text is in `_analysis/ocr_raw/`.
- The curve and track-piece rules should be treated as a dedicated extraction pass because the layout diagrams define movement geometry, not just visual art.
- The Dead Man's Curve text in White Dwarf 125 refers to rules published in White Dwarf 123. For this project, treat that as a publication-delay typo: the relevant first part is White Dwarf 124 pages 18-31.
