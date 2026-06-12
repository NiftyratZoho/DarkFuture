# Track Geometry

> Status: cleaned implementation summary, not engine code.
> Owned data draft: `data/rules/track-pieces-draft.json`.
> Primary sources: `docs/rules/core/03-movement.md`, `docs/rules/core/09-rams-and-crashes.md`, `docs/rules/core/11-track-generation.md`, verified against `_analysis/ocr_pages/dark_future/page-10.png`, `page-13.png`, `page-14.png`, `page-15.png`, `page-52.png`, `page-53.png`, `page-54.png`, `page-55.png`, and `page-74.png` through `page-79.png`.

## Scope

This section defines the track geometry rules needed by movement, rams/crashes, hazards, firing corridors, and track generation. It does not implement movement, rams, hazards, shooting, or UI.

The track system must be represented as explicit `trackSpace` data. Rendering may use simple boxes, but legal movement and contact checks must not be inferred from pixels.

## Core Model

### Track sections

The core rulebook uses three section classes:

- `straight`: straight road section.
- `broadCurve`: 60-degree bend.
- `tightCorner`: 90-degree corner.

Curves exist in left-hand and right-hand forms. A right-hand curve should be a mirror of the matching left-hand curve once the left-hand graph is verified.

Source pages:

- Movement grid and curve grid: core pp.10, 13-15.
- Track generation curve types: core pp.74-76.

### Lanes and spaces

Straight sections are divided into lanes across the road and regular spaces along the road. A car occupies two adjacent lanes in one space. The initial OCR-derived pass assumed six lanes, but the user-provided track definitions supersede that: the playable implementation now uses eight lanes.

- straight sections have 3 spaces along their length;
- the road has 8 lanes across;
- a normal car position is a two-lane pair, giving possible lane pairs `1-2` through `7-8`.

The user-provided curve definitions add two curve profiles:

- `curve30to60`: tight 90-degree corner, lane speed limits from 30 mph on inner lanes to 60 mph on outer lanes.
- `curve50to80`: broader 60-degree bend, lane speed limits from 50 mph on inner lanes to 80 mph on outer lanes.

Curve sections also use lanes, but their spaces are irregular. The rulebook says curve sections have 2-5 spaces for road-hazard placement. The exact number depends on which side of the curve is being followed; this must be captured in the curve atlas rather than normalised away.

Source pages:

- Straight grid, lane/space terminology, car occupies two lanes: core p.10.
- Road hazards: straight sections have 3 spaces; curves have 2-5 spaces: core p.78.

## Curve Geometry

### Even and uneven lane pairs

Curve spaces are not regular rectangles. A vehicle still occupies two lanes, but the divider marks between spaces may not line up across all lanes.

The rulebook distinguishes:

- `even` lane pairs: the pair's space position is unambiguous.
- `uneven` lane pairs: position and moves are judged by the space divider on the outside of the bend.

Implementation consequence:

- Each curve `trackSpace` must carry whether its two-lane pair is `even` or `uneven`.
- Each curve `trackSpace` must store the outside divider it is aligned to, or an equivalent ordinal such as `outsideDividerIndex`.
- The `forward` link must be explicit. Do not calculate it from render coordinates.

Source pages:

- Even/uneven curve lanes and outside divider rule: core pp.10, 13.
- Contact zones on uneven curve lanes: core p.53.

### Forward movement on curves

On straight sections, the forward move stays in the same lane pair and advances one space.

On curves, the forward move still follows the same logical lane pair, but if the current or destination pair is uneven the next position is determined by the outside divider. The diagrams show that a vehicle may appear to move a different physical distance depending on where the dividers fall.

Implementation consequence:

- Each curve `trackSpace` needs a single normal `forward` target for each direction of travel.
- The target should be traced from the printed curve board, using the outside divider rule.
- A position may be visually staggered relative to adjacent lane pairs. That stagger matters for sideswipes and contact zones.

Source pages:

- Moving onto uneven lanes: core p.10.
- Moving on uneven lanes: core p.13.

### Drift on curves

A drift is declared before the forward move, then applied after that forward move while staying in the resulting space.

On curves:

- A voluntary drift while still on a curve is only allowed toward the outside of the bend.
- If drifting into an uneven pair, final position is aligned using the outside divider.
- A car that starts on a curve or bend but moves onto a straight section may drift in either direction after entering the straight.
- A drift from an even pair to an uneven pair may make the apparent forward movement shorter than staying in the same lanes. This is an expected result, not a bug.

Implementation consequence:

- Curve `trackSpace` data needs `driftOutward` links.
- `driftInward` should be absent or marked illegal while the final position remains on a curve.
- Boundary spaces that move from curve to straight need normal left/right drift links after the forward target is on the straight.

Source pages:

- Drift timing and outside-only curve drift: core p.13.
- Even-to-uneven and uneven-to-even drift examples: core p.14.
- Drift inward after leaving a curve: core p.14.

### U-turns around curves

U-turns are normally not allowed on curved track. Exceptions:

- A vehicle on the edge of a curve may U-turn across a straight section.
- A vehicle on a straight next to a curve may U-turn across the curve.
- Reversing vehicles follow the same curve-edge restrictions.
- The U-turn contact zone is six lanes wide.

Implementation consequence:

- Track spaces at curve/straight boundaries need `uTurnAcrossEdge` metadata.
- A U-turn legality check needs the six-lane contact zone, obstacles, and vehicles from the target area.

Source pages:

- U-turn contact zone: core p.14.
- U-turns on curve edges and across curve edge: core p.15.

## Contact Zones

### General rule

A collision occurs when a moving vehicle's contact zone overlaps another vehicle's contact zone. A crash occurs when the moving vehicle's contact zone extends off the road surface or hits an obstacle.

For implementation, a vehicle's intended move should be checked before the model is moved. If the move would collide, the rammer remains in the starting position while the ram sequence resolves.

Source pages:

- Contact-zone collision/crash rule: core p.10.
- Ram sequence: core p.52.

### Straight movement contact zones

The diagrams define different zones for:

- straight-ahead move;
- drift manoeuvre;
- U-turn manoeuvre;
- spin move;
- stationary vehicle at an angle.

Implementation consequence:

- Contact zones should be generated from `movementKind`, `fromTrackSpace`, `toTrackSpace`, and `vehicleOrientationState`.
- The track atlas must expose enough neighbouring spaces for these calculations.
- Straight movement contact zones can likely be represented as sets of lane-pair/space ids after the straight section's 6-by-3 grid is formalised.

Source pages:

- Common contact zones: core p.52.
- Spinning and stationary angled contact zones: core p.53.

### Curve contact zones

On curves, the track grid, not the miniature or rendered car box, determines contact. For even lane pairs, contact zones are judged directly from the curve space. For uneven lane pairs, contact zones are judged by the outside lane's space dividers.

Implementation consequence:

- Each curve `trackSpace` must include a `contactAnchor` tied to the outside divider.
- Contact zones for curve positions need explicit or derivable `contactZone` sets.
- Render overlap is irrelevant. Two rendered car boxes touching should not imply collision unless their rule contact zones overlap.

Source pages:

- Even/uneven contact zones on curves: core p.53.

### Sideswipes on curves

Sideswipe legality on curves depends on staggered positions:

- Cars on curves can be offset by roughly half a space.
- A sideswipe is allowed only if the front of the rammer is behind the front of the target.
- Sideswipes cannot be made with rear ends.
- Sideswipes are not limited by the normal drift restriction; an outer-lane car may sideswipe an inner-lane target.

Implementation consequence:

- Curve spaces need a `frontOrdinal` or equivalent along-lane progress value.
- Adjacent lane-pair spaces need comparable front positions.
- Sideswipe legality must use these ordinals, not rendered x/y overlap.

Source pages:

- Sideswipe on curves and legal inward sideswipe: core p.55.

### Head-on and shunt classification on curves

Head-on and shunt rams can occur on curves. For head-on rams on curves, lane markings determine whether vehicles are treated as head-on, not the angle of the car art. Shunts can also occur on curves if vehicles have one or both lanes in common and are moving in the same direction.

Implementation consequence:

- Each track position needs a logical travel direction along the lane pair.
- Ram classification should compare logical direction and lane overlap, not sprite angle.

Source pages:

- Head-on rams on curves: core p.54.
- Shunts on curves: core p.54.

## Track Generation

### Initial generation

Initial setup:

- Place three straight sections end to end.
- Generate further sections until ten sections are in play.
- For each generated section, roll once:
  - 1-4: straight.
  - 5-6: curve.
- If a curve is generated, roll for curve type:
  - 1-4: broad bend.
  - 5-6: tight corner.
- Roll for direction:
  - odd: left.
  - even: right.
- The section after every curve is automatically a straight.

Source pages:

- Initial generation and curve rolls: core p.74.

### Limited component availability

If the generated curve type is unavailable because all pieces of that type are already in use, switch to the other curve type. If a straight is required and no straights remain, generation ends and the finish is where the track stopped.

Source page:

- Component availability fallback: core p.75.

### 180-degree rule

If two consecutive generated curves go in the same direction, the next curve must go in the opposite direction. This prevents the road turning back on itself.

Source page:

- 180-degree rule: core p.75.

### Continuous generation

Continuous generation uses a seven-section rolling track:

- Start with three straights.
- Generate ahead to the lead driver's line of sight.
- The lead car's driver rolls for new track.
- A straight allows generation until there are three sections after the section occupied by the lead car, or until a curve blocks line of sight.
- A curve blocks line of sight. The mandatory straight after a curve is not placed until the lead vehicle moves onto the curve.
- Extra track after a curve is generated only after a car has moved off the curve and into the mandatory straight.
- There may never be more than seven sections in play. When adding a section would exceed seven, remove sections from the rear.
- Vehicles or passive markers on removed sections leave play without damage and cannot re-enter.

Source pages:

- Continuous generation and line of sight: core pp.75-76.
- Removing track: core pp.76-77.

### Direction of play

If vehicles travel in opposite directions, generation follows the lead car in the current direction of play. Direction of play is determined by the majority of vehicles; ties keep the previous direction. Vehicles going opposite to direction of play can drive off the board and leave play. If direction of play changes, generate a new stretch using the normal rules rather than preserving the old removed road.

Source page:

- Changing directions: core p.77.

## Road Hazards On Track Sections

This belongs partly to the Hazards Agent, but track geometry must provide placement locations.

Random road hazards are placed on newly generated sections on a roll of 1. Hazards occupy three lanes in one space on the left or right edge of the road. Types are sand, debris, and obstacles. Straights have 3 spaces; curves have 2-5 spaces. If more markers are generated than fit on the current side of the current section, overflow continues onto the next section.

Railroad crossings are special hazards. On straight sections they are placed across central spaces. On curves they are placed on end spaces.

Implementation consequence:

- Every track piece needs ordered edge placement slots for `left` and `right`.
- Slots must be ordered from the start of the section forward in direction of play.
- Each slot must know the three lanes it covers.
- Curve pieces need explicit `endSpace` slots for railroad crossings.

Source pages:

- Hazard generation and placement: core p.78.
- Hazard effects and railroad placement: core p.79.

## Required Track Atlas Work

The implementation cannot be faithful until the printed curve layouts are converted into explicit graphs. The remaining exact curve-layout work is:

1. Confirm the physical track-piece inventory from component pages or scans: number of straights, broad bends, and tight corners.
2. Trace straight section spaces as `spaceIndex` 1-3 by lane pair.
3. Trace left broad curve:
   - all valid two-lane positions;
   - whether each is even or uneven;
   - outside divider index for each uneven position;
   - forward links;
   - outward drift links;
   - curve-to-straight boundary links;
   - edge spaces where U-turns are legal.
4. Mirror the left broad curve into right broad curve, then verify against diagrams.
5. Trace left tight corner with the same data.
6. Mirror the left tight corner into right tight corner, then verify.
7. Add contact-zone sets or contact anchors for:
   - straight-ahead move;
   - drift;
   - U-turn;
   - curve even-lane positions;
   - curve uneven-lane positions;
   - angled/spinning vehicles.
8. Add `frontOrdinal` values for curve positions so staggered sideswipe legality can be tested.
9. Add road-hazard placement slots for all pieces.
10. Build diagram-based tests from pp.10, 13, 14, 15, 52, 53, 54, and 55.

## Ambiguities And OCR Doubts

### Exact curve graph is not text-defined

The OCR text gives the rule for outside dividers, but not a machine-readable map. The curve atlas must be traced from diagrams or component scans. This is the critical unresolved work.

Source pages: core pp.10, 13-15, 52-55.

### Number and shape of component pieces

The rules clearly use straights, broad bends, and tight corners, but this pass did not verify the physical board-piece inventory from component pages. The draft assumes four curve variants by mirroring: broad left/right and tight left/right.

Source pages: core pp.74-75. Needs component verification.

### Lane numbering convention

This spec numbers lanes left-to-right from the driver's point of view while entering a section, but the rulebook does not define numeric lane ids. The Rules Lead should approve this convention before implementation data is finalised.

Source pages: core pp.10, 13.

### Curve "2-5 spaces" needs per-piece confirmation

Road hazard rules say curves have 2-5 spaces. That likely reflects different counts along inside and outside lanes. Each curve piece needs ordered placement slots traced from the actual curve art.

Source page: core p.78.

### Contact zone set versus contact anchor

The diagrams show shaded zones, but this pass does not fully enumerate every affected `trackSpace`. A faithful engine can either store full contact-zone sets per position or store anchors plus a deterministic contact-zone generator. For curves, full explicit sets may be safer.

Source pages: core pp.52-53.

### Sideswipe "front behind front" requires a comparable measure

The curve sideswipe rule depends on front-of-car ordering where cars are staggered. The atlas needs an ordinal that can compare adjacent lane-pair positions. The exact ordinal values must be derived from the curve divider layout.

Source page: core p.55.

## Candidate Tests

- Straight section has 6 lanes, 3 spaces, and valid two-lane car positions only.
- Straight forward move preserves lane pair and increments space.
- Moving onto an uneven curve lane uses the outside divider target from p.10.
- Moving along uneven curve lanes follows outside divider targets from p.13.
- Curve drift only allows outward drift while the final position remains on the curve.
- Curve-to-straight drift allows either direction after the forward move enters the straight.
- Even-to-uneven curve drift matches the shorter apparent forward movement shown on p.14.
- Curve-edge U-turns are legal only for spaces marked as edge/across-straight.
- U-turn contact zone is six lanes wide.
- Curve contact checks use track grid/contact anchors, not render overlap.
- Head-on curve rams classify by lane markings/logical direction, not model art angle.
- Curve sideswipe is illegal if the rammer's front is not behind the target's front.
- Outer-to-inner sideswipe on a curve is legal when other sideswipe requirements are met.
- Track generation starts with three straights and builds to ten sections for initial generation.
- Every generated curve is followed by an automatic straight.
- After two same-direction curves, the next curve direction is forced opposite.
- Continuous generation stops line of sight at a curve.
- Continuous generation never leaves more than seven sections in play.
- Removed rear sections remove vehicles and passive markers from play without damage.
- Random road-hazard placement uses ordered left/right edge slots and overflows to following sections.
