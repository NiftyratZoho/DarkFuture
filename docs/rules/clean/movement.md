# Movement

> Status: cleaned implementation summary, not engine code.  
> Owner: Movement Agent  
> Source files: `docs/rules/core/03-movement.md`, `docs/rules/white-line-fever/01-advanced-manoeuvres.md`  
> Cross-section contracts read: `docs/rules/clean/turn-sequence.md`, `docs/rules/clean/track-geometry.md`  
> Draft data: `data/rules/movement-actions.json`

## Scope

This section defines movement action legality and movement-side effects for cars and, where stated, bikes. It covers speed calculation dependencies, ordinary forward moves, acceleration, braking, drift, U-turns, reverse, regain control, and White Line Fever advanced manoeuvres.

This section does not own:

- phase activation tables, except for movement interactions with double moves;
- track-space graph layout, curve links, or contact-zone geometry;
- hazard roll resolution;
- control-loss test resolution;
- ram classification or damage;
- shooting resolution.

Movement rules consume those systems through explicit state, legal action queries, and rule events.

## Required State Inputs

A movement legality check needs at least:

- current `turn` and `phase`;
- whether this is the first or second move in a White Line Fever double-move phase;
- vehicle `mph`, `speedFactor`, maximum speed, acceleration, braking, and control state;
- vehicle type, especially car versus bike;
- current `trackSpace`, facing, direction of travel, and whether the vehicle is reversing;
- track geometry links for forward, reverse, drift, swerve, U-turn, curve-edge U-turns, and contact zones;
- current vehicles, obstacles, edge of road, and passive markers in relevant contact zones;
- pending automatic movement requirements from control loss or failed bootlegger results.

`speedFactor` calculation itself belongs to the turn sequence contract: current `mph` divided by 20 and rounded up. Movement changes `mph`; the turn system recalculates or reads `speedFactor` after speed changes.

## Ordinary Forward Move

If a non-stationary vehicle is fast enough to move in the current phase, it must make a forward move unless a specific rule replaces or interrupts that move.

On a straight section, a forward move keeps the same lane pair and advances to the next forward `trackSpace`.

On curves, forward movement follows the explicit `forward` link supplied by the Track Geometry Agent. Uneven curve lanes must use the outside-divider mapping already captured by track geometry. Movement code must not infer this from render coordinates.

Before applying a move, the engine must ask track geometry for the relevant movement contact zone. If the contact zone overlaps another vehicle, obstacle, or road edge, the move is blocked or converted into the appropriate ram/crash workflow. Rams and crashes own the final result.

## Action Declaration

Most movement actions are declared before the model moves. A declared action must include all rule-relevant parameters:

- accelerate/brake amount in `mph`;
- drift direction;
- U-turn direction or target, if needed by geometry;
- bootlegger direction;
- swerve direction;
- dual-action components and their order.

If no action is declared, the vehicle performs its compulsory forward move at steady speed.

Vehicles that are not fast enough to move in the current phase cannot use movement actions, except for stationary phase-1 moving off and reverse as described below.

## Acceleration

Acceleration increases speed by up to the vehicle's current acceleration characteristic. The amount is declared before movement.

Core timing:

1. declare acceleration amount and resulting speed;
2. perform the forward move;
3. apply the new `mph`.

An acceleration action can only be used by a vehicle that is actually moving in the current phase, except that a vehicle stationary at the start of phase 1 may move off.

Acceleration cannot raise a vehicle above its current maximum speed. If damage or critical hits have reduced maximum speed below the vehicle's current speed, the vehicle cannot accelerate until its speed is no longer above that maximum.

If a vehicle's acceleration characteristic is reduced to zero, it automatically loses 5 mph immediately after each move unless it uses a brake action to reduce speed by more, within its current braking allowance.

If an accelerating vehicle must take a hazard roll in the same move, use the new, faster speed for that hazard calculation.

Source pages: core pp. 11, 15-16.

## Moving Off From Stationary

A vehicle stationary at the beginning of phase 1 may accelerate and move after all other vehicles in that phase.

If multiple vehicles move off in the same phase, the one declaring the highest acceleration amount moves first. Tie handling is not fully recovered from OCR and should be reviewed against the page image.

When moving off, the vehicle may combine the acceleration/move-off with either a drift or a U-turn. The core rules call this the only basic-game exception allowing two actions in one phase. White Line Fever dual actions later generalise some combinations; the engine should still preserve `movingOff` as a distinct exception because it applies only from stationary phase 1.

Source page: core p. 16.

## Braking

Braking reduces speed by up to the vehicle's current braking characteristic. Braking is declared before movement and speed is adjusted immediately after the forward move.

The vehicle still makes the move required for the phase even if the brake reduces its speed below the phase threshold. Phase order for the current phase also remains fixed under the Turn Sequence contract.

A brake action can only be used by a vehicle that is actually moving in the current phase. A driver cannot wait until a later phase in which the vehicle is no longer eligible to move and then brake.

A vehicle's braking characteristic can be reduced by damage or critical hits, but the OCR indicates it cannot fall below 5 mph.

If a braking vehicle must take a hazard roll in the same phase, use the new, slower speed.

Source pages: core pp. 11, 16.

## Drift

A core drift is a manoeuvre action. It is declared before the forward move.

Core timing:

1. declare drift direction;
2. perform the forward move;
3. shift one lane left or right while staying in the resulting space, using track geometry's drift link.

A vehicle may not drift if it is not moving in the current phase.

The manoeuvre cannot be attempted if the manoeuvre contact zone contains another vehicle, the road edge, or an obstacle. The exception is White Line Fever swerve handling, which has its own danger hierarchy.

Core curve rule:

- on a curve, voluntary drift is only outward while the final position remains on the curve;
- a vehicle starting on a curve but moving onto a straight may drift either direction after entering the straight;
- if drifting into an uneven curve lane, final alignment uses the outside-divider convention supplied by track geometry.

Core safety limit:

- drifts are automatic at up to 80 mph;
- above 80 mph, the manoeuvre is completed but triggers a hazard roll.

White Line Fever modifies curve drifting:

- outward curve drift uses the drift safety limit, not the printed curve lane limit;
- inward curve drift becomes legal under advanced rules and uses the final position's outer-lane printed safety limit instead of the 80 mph drift limit.

Source pages: core pp. 13-14; WLF pp. 6-7.

## Cutting Up

The core drift rules allow a moving car to drift from beside another vehicle into a position ahead of it, but with restrictions.

A driver cannot use a drift to cut up a vehicle that has not yet moved in the current phase, unless the target is stationary and its declared action will not cause a collision with the drifting vehicle.

When a player tries to cut up a stationary vehicle, the stationary vehicle's action must be declared immediately. If that vehicle is moving off, the cut-up is not allowed.

A drift cannot be used to move next to a car and then across into contact. That is handled as a sideswipe by Rams and Crashes.

Source page: core p. 14.

## U-Turn

A U-turn is a manoeuvre action that turns the vehicle around and leaves it facing the opposite direction.

A U-turn cannot be used to ram. It cannot be attempted if another vehicle, obstacle, or the road edge is inside the U-turn contact zone.

Core curve restrictions:

- U-turns are normally prohibited on curved track;
- a vehicle on the edge of a curve may U-turn across an adjacent straight;
- a vehicle on a straight next to a curve may U-turn across the curve;
- reversing vehicles follow the same curve-edge restrictions;
- the U-turn contact zone is six lanes wide.

Core safety limits:

- at up to 10 mph, a U-turn is automatic;
- from 11 to 30 mph, the manoeuvre triggers a hazard roll;
- at 31 mph or more, the driver loses control before executing the U-turn and must take an immediate control-loss test instead.

Source pages: core pp. 14-15.

## Reverse

Reverse is an action, not a free forward move. Bikes cannot reverse.

Only a vehicle stationary at the start of phase 1 may make a reverse move. It is treated as moving backwards at 10 mph for the reverse move.

Reverse prevents the driver from shooting, braking, or accelerating in that phase. A reversing driver may include a drift or U-turn as part of the reverse action, but not while reversing on curved track.

Reversing is allowed on curved track, but a reversing vehicle on a curve may not drift or U-turn.

Reverse moves ignore hazard rolls. At the end of the reverse move, the vehicle speed returns to 0 mph. On the following turn, the vehicle may either accelerate and move forward or reverse again if still stationary at the start of phase 1.

Source page: core p. 17.

## Regain Control

The detailed control-loss test belongs to the Hazards Agent. Movement only defines the action dependency.

A driver who has lost control must take a control-loss test at the start of each move. If that test is passed, the driver is forced to use the `regainControl` action and cannot use another action in that phase.

Drivers who have lost control cannot choose ordinary actions while out of control.

Source pages: core pp. 11, 17; detailed dependency core p. 42.

## White Line Fever: Double Move Interactions

White Line Fever allows speed factors above 6. The exact phase/move counts are owned by `data/rules/speed-phases.json`.

In a double-move phase:

- the vehicle makes two moves;
- the driver has only one action total;
- the action may be assigned to either the first move or the second move;
- if more than one vehicle double moves, all first moves are resolved by descending speed before any second moves.

Movement action data must therefore include `actionTiming` with allowed values `firstMove`, `secondMove`, and, for automatic no-action moves, `none`.

Open implementation point: acceleration and braking speed changes happen immediately after the move on which the action is used. If used on the first move of a double-move phase, the changed `mph` should affect hazard speed and possibly later phase eligibility, but the current phase's activation order is already fixed by Turn Sequence. Whether the second move in the same phase uses the changed speed for hazard thresholds is inferred as yes, because the speed change has already occurred; this needs Rules Lead confirmation.

Source page: WLF p. 4.

## White Line Fever: Swerve

A swerve is an advanced manoeuvre and is effectively a two-lane drift in one direction, split around a forward move.

Swerve sequence:

1. shift one lane left or right;
2. make the forward move;
3. shift one lane again in the same direction.

The second shift is mandatory unless prevented by control loss. The driver cannot voluntarily stop after the first shift or after the forward move.

A swerve can only be used when moving onto, along, or off straight sections. It cannot be used while on curves.

Passive-weapon damage and hazard rolls caused by each stage are resolved immediately before moving to the next stage. If the vehicle loses control after the first shift or forward move, it does not make the final shift.

Swerve safety limit:

- the driver must take a hazard roll after completing the manoeuvre;
- separate hazard rolls are not taken merely for each lane shift, aside from hazards/passives encountered during the staged movement.

Swerves can be allowed even when the contact zone contains a vehicle, road edge, obstacle, or passive marker, but only to avoid a worse accident. The WLF danger hierarchy, least to most dangerous, is:

1. smoke;
2. sand;
3. debris;
4. spikes;
5. mines;
6. shunts;
7. sideswipes;
8. crashes;
9. head-on rams.

A swerve cannot replace an imminent danger with an equal or more dangerous result. Friend/enemy ownership is ignored for this comparison.

If a bike sideswipes during a swerve, it automatically goes out of control. Bike-specific consequences are owned by Bikes and Hazards.

Source pages: WLF pp. 6-7.

## White Line Fever: Bootlegger Turn

A bootlegger turn is an advanced car-only manoeuvre for rapidly reversing direction. Bikes cannot attempt it.

Prerequisites:

- car only;
- straight track section only;
- speed must be 31-60 mph to attempt normally;
- the bootlegger contact zone must be clear of vehicles and road edge;
- passive markers in the contact zone do not prohibit the attempt, but are resolved after the move.

The driver declares left or right before testing. A left bootlegger mirrors the right bootlegger geometry.

The special bootlegger test is made before moving the model. OCR indicates:

- roll one D6;
- subtract the vehicle's adverse control value;
- add +1 for each oil or mine marker in the contact zone;
- add +1 if debris is in the contact zone;
- add +1 if sand is in the contact zone.

Bootlegger test result draft:

- 1 or less: success; move to intended position and reduce speed to 0 mph;
- 2-3: failure; roll D6 and use the direction-specific failure diagram for final position;
- 4 or more: oversteer/control-loss result; exact table text is OCR-damaged and must be proofread from the page image.

Safety limits:

- below 31 mph: bootlegger cannot be attempted;
- at 61 mph or faster, the driver automatically loses control before the bootlegger and makes a control-loss test instead.

On a failed result in the 2-3 band, OCR indicates the car remains moving at speed factor 1, suffers a tyre critical at 0 damage, and on its next move must make an automatic straight-ahead reverse move in the same direction it was travelling before the bootlegger. That next move happens in phase 1 of the next turn, needs no control-loss test, and is treated as moving backwards at 10 mph. This needs proofread because the diagram and table are noisy.

Passive markers in the bootlegger contact zone are resolved after the move. If multiple passive weapons are present, resolve damage for all, then hazard rolls from lowest safety limit upward; oil is tested last against its lower safety limit. Shooting/Damage/Hazards own the exact passive resolution.

Source page: WLF p. 5.

## White Line Fever: Bulldozer Move

A bulldozer move lets a slow car push a stationary, off-grid or angled car out of the path and align it with the grid.

Prerequisites:

- rammer must be a car; bikes cannot bulldoze;
- target must be stationary;
- target must be angled to the grid, not aligned normally;
- rammer must hit left or right of the target's centre, according to the diagram;
- rammer must be travelling at 20 mph or slower, including reverse movement.

If the target is aligned on the grid, use ordinary shunt or head-on ram handling. If the target is moving, treat the collision as a ram. If the rammer hits the centre rather than the required offset, treat it as a head-on ram. If the rammer is at 21 mph or faster, treat the collision as a head-on ram.

The OCR indicates both vehicles suffer a single low-damage hit and critical hits are ignored, but exact damage wording belongs to Rams/Damage and should be proofread.

Source page: WLF p. 8.

## White Line Fever: Dual Actions

White Line Fever permits these dual actions:

- drift and shoot;
- accelerate and drift;
- brake and drift;
- accelerate and shoot;
- brake and shoot.

Each component has its normal effect. The order is the order named by the action:

- `brakeAndShoot`: speed is adjusted before shooting;
- `accelerateAndDrift`: drift hazard speed is checked after acceleration;
- `brakeAndDrift`: drift hazard speed is checked after braking.

When shooting is combined with accelerate, brake, or drift, apply a -1 hit-roll penalty. This applies even if the shot uses or is made automatically by fire-control equipment.

Any hazard roll in a phase where the driver performed a dual action suffers a -1 penalty.

Dual actions are still one phase action for action-count purposes. In a double-move phase, the dual action should be assigned to either the first or second move, not split across both moves, unless Rules Lead later approves otherwise.

Source page: WLF p. 8.

## Required Engine Behaviours

- Expose movement actions only when phase/action eligibility allows them.
- Distinguish move eligibility from action eligibility.
- Resolve contact-zone checks before changing vehicle position.
- Use track geometry links for forward, reverse, drift, swerve, U-turn, and curve-edge exceptions.
- Emit movement events for Hazards, Rams/Crashes, Damage, and Shooting rather than resolving those systems here.
- Apply acceleration/braking timing after the movement step on which the action was used.
- Recalculate or expose changed `mph` and `speedFactor` after speed changes.
- Preserve current phase activation order despite speed changes.
- In double-move phases, enforce one action across both moves and record which move received it.
- Represent forced actions such as `regainControl` and automatic failed-bootlegger reverse moves explicitly.

## Data Extracted

- Movement action draft definitions: `data/rules/movement-actions.json`.
- Speed factor phase tables remain in `data/rules/speed-phases.json` and are not duplicated here.
- Exact curve and contact-zone links remain in track geometry data and are not duplicated here.

## Ambiguities and OCR Doubts

### Page 15-16 OCR column mixing

Core pp. 15-16 have severe column mixing between U-turn, acceleration, moving off, braking, and maximum speed. The cleaned rules above are recoverable, but values such as core vehicle max speeds and exact tie handling for multiple moving-off vehicles need proofread from page images or vehicle data.

### Moving-off tie handling

Core p. 16 says multiple vehicles moving off are ordered by highest acceleration amount. The OCR does not clearly state tie handling after equal declared acceleration.

### Bootlegger result table and diagrams

WLF p. 5 has damaged OCR around the bootlegger failure table and final-position diagrams. The success row and parts of the failure rows are recoverable, but the exact final positions and oversteer/control-loss row require diagram tracing.

### Swerve diagram geometry

WLF pp. 6-7 explain the three-stage sequence and danger hierarchy, but exact contact zones and illegal example geometry must be represented by track geometry/contact-zone data.

### Inward curve drift diagrams

WLF p. 7 explains inward drift on curves, but exact even/uneven movement amounts are diagram-dependent. Track Geometry must supply final links and safety-limit metadata.

### Bulldozer damage text

WLF p. 8 OCR mixes bulldozer result text with the dual-action column. The movement legality is clear enough, but exact damage and target displacement geometry need Rams/Damage and diagram proofread.

### Dual action and double move interaction

WLF p. 4 says one action may be used on either move of a double move. WLF p. 8 says dual actions are an action combining two named effects. This pass assumes a dual action must occur wholly on one of the two moves, not split across first and second moves.

## Candidate Tests

### Forward Movement

- A vehicle at a phase-eligible speed with no action moves one forward `trackSpace`.
- A straight forward move preserves lane pair and advances one space.
- A curve forward move uses the `forward` graph link and never render coordinates.
- A phase-eligible moving vehicle cannot choose to remain still unless another rule forces or replaces movement.

### Acceleration

- A moving vehicle can accelerate by any amount from 0 up to current acceleration.
- Acceleration cannot exceed current maximum speed.
- A vehicle above its reduced maximum speed cannot accelerate.
- Acceleration speed change is applied after the forward move.
- Hazard speed after acceleration uses the new speed.
- A vehicle with zero acceleration loses 5 mph after each move unless braking reduces speed by more.

### Moving Off

- A vehicle stationary at the start of phase 1 may accelerate and move off after ordinary moving vehicles.
- A stationary phase-1 move-off may combine with drift.
- A stationary phase-1 move-off may combine with U-turn if contact-zone and speed rules allow it.
- A stationary vehicle cannot move off in phase 2 or later.

### Braking

- A moving vehicle can brake by any amount from 0 up to current braking.
- Braking speed change is applied after the forward move.
- A vehicle braking from 25 mph to 10 mph in phase 2 still completes its phase-2 move.
- A vehicle not eligible to move in the current phase cannot brake.
- Hazard speed after braking uses the new speed.
- Braking characteristic never validates below 5 mph after damage adjustments.

### Drift

- A core drift performs forward move then one-lane shift.
- A drift over 80 mph requests a hazard roll.
- A drift at 80 mph or less does not request a drift-speed hazard roll.
- A curve drift inward is illegal under core rules while the final position remains on the curve.
- A curve drift outward uses track geometry's outward link.
- A curve-to-straight drift may go either direction once the forward move enters a straight.
- A cut-up drift against a not-yet-moved vehicle is illegal unless the target is stationary and not moving off.
- A drift cannot create a sideswipe; that action must be routed to Rams/Crashes.

### U-Turn

- A U-turn at 10 mph or less completes without a U-turn speed hazard roll.
- A U-turn at 11-30 mph requests a hazard roll.
- A U-turn at 31 mph or more triggers immediate control loss instead of moving.
- U-turn is illegal when its contact zone contains a vehicle, obstacle, or road edge.
- U-turn is illegal on ordinary curve spaces.
- U-turn is legal only on curve-edge spaces marked by track geometry.

### Reverse

- A car stationary at the start of phase 1 may reverse at 10 mph.
- A bike cannot reverse.
- Reverse consumes the phase action and blocks shooting, braking, and accelerating.
- Reverse may include drift or U-turn on straight track.
- Reverse on curved track allows no drift or U-turn.
- Reverse ignores hazard rolls and returns speed to 0 mph at the end of the move.

### Regain Control

- A driver who passes a start-of-move control-loss test is forced into `regainControl`.
- A driver out of control cannot declare ordinary movement actions.

### Double Moves

- In a double-move phase, a vehicle can assign acceleration to the first move or second move, but not both.
- If acceleration is assigned to the first move, the second move happens after the speed change while the phase order remains fixed.
- A dual action in a double-move phase is consumed wholly on one move.

### Swerve

- A swerve shifts one lane, moves forward, then shifts one more lane in the same direction.
- A swerve cannot be voluntarily stopped after stage one or two.
- Passive marker effects are requested after each swerve stage before the next stage.
- If control loss occurs before the final shift, the final shift is skipped.
- A swerve on a curve is illegal.
- A swerve replacing a head-on ram with a crash is legal.
- A swerve replacing a shunt with another shunt is illegal.
- A swerve replacing mines with a crash is illegal.

### Bootlegger

- A bike cannot bootlegger.
- A bootlegger below 31 mph is illegal.
- A bootlegger at 31-60 mph requests a bootlegger test.
- A bootlegger at 61 mph or faster triggers immediate control loss instead.
- A successful bootlegger moves to the intended position and reduces speed to 0 mph.
- Passive markers in the bootlegger contact zone are resolved after movement.
- Failed-bootlegger final positions match traced WLF p. 5 diagrams once available.

### Bulldozer

- A car at 20 mph or less can bulldoze a stationary angled target when it hits the permitted offset.
- A bike cannot bulldoze.
- A bulldozer attempt against a moving target is treated as a ram.
- A bulldozer attempt against a normally aligned target is treated as ordinary ram handling.
- A bulldozer attempt at 21 mph or faster is treated as a head-on ram.

### Dual Actions

- `accelerateAndDrift` applies acceleration before checking drift hazard speed.
- `brakeAndDrift` applies braking before checking drift hazard speed.
- `brakeAndShoot` adjusts speed before shooting.
- A shoot dual action applies a -1 hit-roll penalty.
- Any hazard roll in a phase after a dual action applies a -1 hazard penalty.

## Dependencies

- Turn Sequence: phase eligibility, double-move scheduling, action timing, activation order stability.
- Track Geometry: forward links, curve links, drift links, swerve links, U-turn edge permissions, contact zones, printed curve safety limits.
- Hazards: hazard roll calculation, control-loss tests, panic braking, out-of-control movement.
- Rams and Crashes: collisions, sideswipes, bulldozer result, crash/head-on/shunt classification.
- Shooting: shoot component of dual actions and hit-roll penalty handling.
- Damage: passive marker damage, bootlegger tyre critical, bulldozer low-damage hit.
- Bikes and Three-Wheelers: bike exceptions and bike-specific control-loss consequences.
