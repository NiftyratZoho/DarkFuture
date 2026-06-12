# Track Piece Photo Review

> Status: photo evidence review.
> Source image: `D:/Users/Niftyrat/Desktop/s-l1600.jpg`.

## What The Photo Confirms

The image shows physical Dark Future road sections with the printed lane/grid markings visible enough to confirm the component families used by the extracted rules:

- straight road sections;
- broad curve/bend sections;
- tight corner sections;
- printed speed/safety-limit markings around curve edges;
- eight-lane road layout with car positions occupying two adjacent lanes, per the later user-provided track definitions;
- irregular curve dividers, confirming that curve movement must be traced as a graph rather than inferred from screen coordinates.

## Visible Inventory

The photo visibly contains:

- 7 straight sections:
  - 4 short rectangular sections in the middle column;
  - 3 longer rectangular sections on the right.
- 6 curved sections:
  - multiple broad/bend-like sections;
  - multiple tighter corner-like sections.

Because the photo is angled and pieces overlap visually, the exact broad-vs-tight count should still be treated as `needsOrthographicConfirmation`.

## What Can Be Used Immediately

The implementation may now treat the physical component inventory as at least:

- `straight`: 7 visible sections;
- `curve`: 6 visible sections across broad and tight variants;
- `curveDirections`: left/right can be produced by physical rotation/mirroring.
- `lanes`: 8, with legal two-lane vehicle lane pairs 1-2 through 7-8.

The current game can safely use this for:

- track generation inventory limits;
- UI/debug labels;
- choosing provisional curve section types;
- validating that curves are not an abstract invention.

## What This Photo Cannot Safely Provide

This single photo is not sufficient for final faithful curve atlas data because:

- perspective distortion changes divider spacing;
- pieces are rotated differently;
- some grid intersections are partially hidden by glare;
- edges are not square to the camera;
- broad and tight curve identity is visible but not reliably separable for every piece;
- exact lane-pair forward links and contact anchors need pixel-level tracing from a square-on image.

## Required Follow-Up Images

For final curve atlas extraction, take or source one square-on image per piece type:

1. One straight section.
2. One broad left/right bend, photographed flat and square to the camera.
3. One tight left/right corner, photographed flat and square to the camera.

Photo requirements:

- camera directly above the piece;
- full piece visible with all edges;
- no glare over grid intersections;
- at least 1600 px across the piece;
- one piece per image;
- include a ruler or known straight-edge if possible.

## Implementation Consequence

The code may use provisional curve safety-limit sections now, but final faithful curve movement still requires a traced `trackSpace` graph with:

- all legal two-lane positions;
- even/uneven lane-pair classification;
- outside-divider index;
- forward links;
- outward drift links;
- contact anchors;
- front ordinals for sideswipe comparison;
- ordered hazard-placement slots.
