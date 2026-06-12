# Track Geometry Helper Notes

## Scope

`dark_future.track` is a data-backed helper layer over `data/rules/track-definitions.json`.
It does not integrate with `dark_future.engine` yet and does not attempt to trace exact printed curve
forward links, contact zones, or staggered uneven-lane positions.

The helpers cover the canonical draft data currently available:

- 8 total lanes.
- 2-lane vehicle width.
- legal vehicle lane pairs `1` through `7`.
- 3 straight spaces per lane.
- `curve30to60` and `curve50to80` speed limits by lane.
- curve section counts by lane.
- occupied lane-pair section count using the larger of the two lanes.
- occupied lane-pair safety limit using the lower of the two lanes.

## Position Conventions

Track-piece indexes are zero based when moving across a layout. Spaces are one based within each
track piece. Lane and lane-pair numbers are also one based.

Curves use the JSON convention that lane 1 is the inside lane and lane 8 is the outside lane. The
current helper therefore treats outward curve drift as `lane_pair + 1` and inward curve drift as
`lane_pair - 1`.

## Forward Movement

`forward_position()` advances within the current track piece until the occupied lane pair's section
count is exhausted. On curves, that count is the larger section count of the two occupied lanes, so
outer-lane pairs can remain on a curve longer than inner-lane pairs.

When a move crosses a piece boundary, forward travel enters space `1` of the next piece. Reverse
travel enters the last valid occupied lane-pair space of the previous piece.

## Drift Constraints

Straight drift accepts `left` and `right` directions and clamps legality through lane-pair bounds.

Curve drift accepts `outward` and `inward`. Core rules only allow outward voluntary curve drift while
the final position remains on the curve, so inward curve drift is rejected unless callers opt into
`allow_inward_curve_drift=True` for later White Line Fever or boundary-specific handling.

## Render Grid Data

`render_grid_data()` returns simple rectangular grid metadata for a piece:

- lane count;
- maximum rendered spaces;
- cell validity by lane and space;
- lane speed limits;
- lane-pair section counts and safety limits.

This is display/debug data only. Future tactical movement and collision checks should use explicit
track-space graph data once the printed curve atlas is traced.

## Remaining Atlas Work

The helper layer intentionally does not infer diagram-specific curve links from render coordinates.
The exact curve atlas still needs traced data for:

- uneven lane outside-divider alignment;
- explicit forward and drift links;
- curve-to-straight boundary drift exceptions;
- contact anchors and contact zones;
- front ordinals for curve sideswipes;
- U-turn edge metadata;
- road-hazard placement slots.
