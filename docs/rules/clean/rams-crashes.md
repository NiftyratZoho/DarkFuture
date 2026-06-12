# Rams and Crashes

> Status: cleaned implementation draft, not engine code.  
> Owner: Rams and Crashes Agent  
> Source file: `docs/rules/core/09-rams-and-crashes.md`  
> Source pages: Dark Future Rulebook pp. 52-58  
> Data file: `data/rules/ram-types.json`

## Scope

This section defines how contact-zone overlaps become rams or crashes, how ram type is classified, how ram damage and speed adjustment are requested, and which post-ram hazard rolls are triggered.

This section does not own:

- movement legality before a contact-zone check;
- the exact `contactZone` sets for each track position or manoeuvre;
- curve lane graph layout;
- hazard-roll calculation;
- damage table lookup after ram/crash damage requests are emitted;
- bike-specific collision exceptions.

Rams and crashes consume movement intents, track geometry contact zones, vehicle state, and hazard/damage services through structured events.

## Required State Inputs

A ram/crash check needs at least:

- moving `vehicle` id, current `trackSpace`, intended movement stage, current `mph`, `speedFactor`, `facing`, direction of travel, and `controlState`;
- intended movement `contactZone` from Track Geometry;
- road-surface coverage for that contact zone;
- vehicles, wrecks, obstacles, and passive markers overlapping the contact zone;
- target vehicle `mph`, `speedFactor`, direction of travel, `facing`, whether it is stationary, whether it is wrecked, and whether it is angled to the road grid;
- curve metadata for lane overlap, same/opposite travel direction, inner/outer lane, and front-position ordering on staggered curve spaces.

## Contact-Zone Collision Checks

A ram occurs when the `contactZone` of a moving vehicle overlaps the `contactZone` of another vehicle. The vehicle executing the movement is the `rammer`; the other vehicle is the `target`.

A crash occurs when the moving vehicle's `contactZone` extends off the road surface or hits an obstacle rather than a vehicle.

The engine should check the intended movement before updating the rammer's position. If a ram or crash will occur:

- the rammer remains in its pre-move position while the event is resolved;
- the movement stage that caused contact ends immediately;
- the driver cannot perform any other action in the same phase as the ram.

Movement actions that are not allowed to ram, such as a U-turn, should ask Track Geometry for a blocking contact-zone check and reject the action before it becomes a ram event.

Source page: core p. 52.

## Ram Sequence

Rams resolve in this order:

1. Get the rammer's intended movement `contactZone`.
2. If that zone overlaps a vehicle, leave the rammer in its original position.
3. Classify the ram as `headOn`, `shunt`, `sideswipeNeckAndNeck`, or `sideswipeOpposed`.
4. If it is a sideswipe, resolve the sideswipe test before damage.
5. Emit ram damage requests.
6. Apply speed adjustment.
7. Emit post-ram hazard-roll requests for vehicles that are still moving and under control.
8. Continue any special after-ram movement sequence, such as the target moving after a shunt.

Source pages: core pp. 52, 55-57.

## Ram Type Classification

### Head-on

A `headOn` ram occurs when the rammer collides with a vehicle travelling in the opposite direction. It can happen when the vehicles share both lanes or only one lane.

Head-on rams can occur on straight or curved track. On curves, classification uses lane markings and logical direction of travel, not rendered model angle.

Special cases treated as `headOn`:

- any collision with a wreck;
- any collision with a stationary vehicle facing opposite the rammer's travel direction;
- any collision with a vehicle angled to the road grid;
- a bulldozer attempt that fails its offset/speed/alignment prerequisites, once White Line Fever bulldozer rules are integrated.

Source pages: core pp. 54, 57.

### Shunt

A `shunt` occurs when the rammer and target are travelling in the same direction and the rammer is faster than the target. It can happen when vehicles share one or both lanes.

Shunts can occur on straight or curved track. On curves, same direction and shared lane membership come from Track Geometry.

Special case: a collision with a stationary, non-wreck target facing the same direction as the rammer is treated as a shunt.

Source pages: core pp. 54, 57.

### Sideswipe

A sideswipe is a declared ram action made after a straight-ahead move. The rammer must end neck-and-neck with a target in adjacent lanes in the same square or equivalent curve position.

Sideswipes cannot be made after a drift because the drift has already used the phase action. A driver must have declared the ram action.

Sideswipe subtype:

- `sideswipeNeckAndNeck`: both vehicles are travelling in the same direction.
- `sideswipeOpposed`: the target is stationary or the vehicles are travelling in opposite directions.

On curves, vehicles may be staggered. A sideswipe is legal only if the front of the rammer is behind the front of the target. Sideswipes cannot be made with rear ends. This requires Track Geometry to expose comparable front-position ordinals.

Sideswipes on curves are not restricted by the normal drift rule that forbids inward curve drift. An outer-lane vehicle may sideswipe an inner-lane target when the other sideswipe requirements are met.

Source pages: core pp. 54-55.

## Sideswipe Test

Resolve a sideswipe test immediately on contact and before damage.

Each driver:

1. Rolls 1d6.
2. Adds `optimumControl` if the vehicle is under control.
3. Adds `adverseControl` instead if the vehicle is out of control.

The rammer adds an additional +1.

If totals are equal, the result is a draw. Otherwise, the higher total is the winner and the lower total is the loser.

The result controls which vehicle receives ram damage and which vehicles take hazard rolls.

Source page: core p. 55.

## Ram Damage

Ram damage is emitted as damage requests for the Damage Agent. Each request should specify target vehicle, facing if known, hit count, damage characteristic, source ram id, and whether critical hits are possible. Ram hits are then resolved using normal damage rules: roll damage, add damage characteristic, subtract relevant internal armour, and apply criticals on a natural six where normal damage rules allow.

### Relative speed-factor hit

A relative speed-factor hit is one hit. Its damage characteristic is:

```text
abs(faster.speedFactor - slower.speedFactor)
```

If both vehicles have the same `speedFactor`, the damage characteristic is zero and no damage is caused for relative speed-factor damage.

### Combined speed-factor hit

A combined speed-factor hit is one hit. Its damage characteristic is:

```text
rammer.speedFactor + target.speedFactor
```

### Relative speed-factor damage

Relative speed-factor damage uses the relative speed-factor value as both damage basis and damage request content for both vehicles involved in a shunt. The OCR wording distinguishes "hit" and "damage"; implementation should represent this as the shunt rule: both vehicles take one relative speed-factor hit only if the relative speed factor is greater than zero.

### Combined speed-factor damage

Combined speed-factor damage uses the combined speed factor as both hit count and damage characteristic:

```text
hitCount = rammer.speedFactor + target.speedFactor
damageCharacteristic = rammer.speedFactor + target.speedFactor
```

### Damage by ram type

- `headOn`: both vehicles take combined speed-factor damage.
- `shunt`: both vehicles take relative speed-factor damage; if `speedFactor`s are equal, no ram damage is caused, but post-ram hazard rolls still happen.
- `sideswipeNeckAndNeck`: the loser takes one relative speed-factor hit; on a draw, both vehicles take one relative speed-factor hit.
- `sideswipeOpposed`: the loser takes one combined speed-factor hit; on a draw, both vehicles take one combined speed-factor hit.

Source page: core p. 56.

## Speed Adjustment

### Head-on

After a head-on ram, both vehicles come to a halt.

```text
rammer.mph = 0
target.mph = 0
```

### Shunt

For a shunt, calculate the difference between the vehicles' speeds in mph, halve it, and round up. Add that amount to the target's speed and subtract it from the rammer's speed.

```text
delta = ceil(abs(rammer.mph - target.mph) / 2)
rammer.mph -= delta
target.mph += delta
```

This leaves both vehicles at the same speed or with the front vehicle slightly faster. When both vehicles are at the same speed, the one in front moves first.

### Sideswipe

For a neck-and-neck sideswipe, both vehicles lose 10 mph.

For an opposed sideswipe, both vehicles lose 20 mph.

Speed cannot fall below 0 mph.

Source page: core p. 57.

## Post-Ram Hazard Rolls

Only vehicles that are still moving and under control take post-ram hazard rolls.

Hazard requests:

- `shunt`: both vehicles test against 40 mph. The target of a shunt ignores panic-brake results, stays in control, and does not brake. The rammer resolves panic braking normally.
- `sideswipeNeckAndNeck`: only the loser tests, against 40 mph. If the sideswipe test was a draw, both vehicles should be treated as damage losers for damage; the OCR does not explicitly confirm whether both also take hazard rolls and needs proofread.
- `sideswipeOpposed`: the winner tests against 40 mph, and the loser tests against 20 mph.
- `headOn`: no post-ram hazard roll is required because both vehicles stop.

Drivers who lose control from a post-ram hazard roll take the normal control-loss test at the start of their next move.

Source pages: core pp. 52, 57.

## Moving After A Shunt

After a shunt, both vehicles remain in their original phase-start positions but with adjusted speeds. The target vehicle then takes its move.

If the target is under control, its driver may declare an action, move forward, and execute the action using the normal sequence. If the target is out of control, its move begins with the normal control-loss test.

After the target completes its move and action, the rammer may complete its own move but cannot perform any action. If either vehicle's later move creates another collision, resolve that new collision through the normal ram sequence.

Source page: core p. 57.

## Skids, Spins, And Rams

Vehicles that are skidding or spinning execute staged movement in strict order. Before each stage, the contact zone for that stage must be checked. If a collision occurs, the staged movement ends and the collision resolves immediately.

After a sideswipe causes control loss:

- a later skid after that sideswipe does not roll a random skid direction;
- on a straight, the skidding vehicle drift-skids outward away from the sideswipe;
- on a curve, a vehicle sideswiped from an inner lane drift-skids outward;
- on a curve, a vehicle sideswiped from an outer lane skids straight but still loses 10 mph as though it had drift-skidded.

If spin rotation would hit another vehicle, do not roll for further rotation. Leave the spinning vehicle in place and treat the collision as a sideswipe. If the spinning vehicle remains moving after that sideswipe, it remains spinning for subsequent moves.

After a shunt involving a skidding or spinning car, the car still takes its normal forward movement and then resolves its skid and/or spin stage.

If a rolling vehicle has one of its staged movements blocked by another vehicle, complete as many stages as possible, resolve the collision at the current speed, then the rolling car rolls and comes to a halt.

Source page: core p. 57.

## Crashes

A crash occurs immediately when a moving vehicle's contact zone leaves the road surface or hits an obstacle. A driver is not allowed to voluntarily choose a manoeuvre that would cause a crash. Under the core rules, ordinary crashes happen when a vehicle is out of control.

When a vehicle crashes:

- remove it from tactical play;
- if the scenario does not need campaign persistence, no crash damage roll is required;
- if the campaign or scenario tracks vehicle repair state, emit crash damage requests before removal is finalised for campaign records.

Crash damage uses speed-factor damage:

```text
hitCount = vehicle.speedFactor
damageCharacteristic = vehicle.speedFactor
```

Example preserved for tests: a vehicle crashing at 75 mph has `speedFactor` 4, so it takes four hits at +4.

Source page: core p. 58.

## Curve Crashes

Some curve crashes occur even when the contact zone does not leave the road surface:

- a vehicle that ends a move on curved track with no driver crashes immediately;
- in core rules, a vehicle forced to rotate on curved track because of a spin crashes immediately.

When a car crashes on a curve for these reasons, remove it immediately and ignore any collisions or passive-marker contacts that the rotation would otherwise have caused. Other vehicles nearby are not affected by that curve crash.

White Line Fever advanced spin rules may override the core "spin on curve crashes immediately" behaviour. The Hazards section records that advanced rules allow spinning on curves; Rules Lead must decide mode-specific behaviour before implementation.

Source page: core p. 58.

## Required Engine Behaviours

- Consume contact zones supplied by Track Geometry; never infer collisions from render overlap.
- Leave the rammer in its starting position when a ram or crash is detected before movement.
- Classify ram type from logical direction, lane overlap, target state, wreck state, and curve metadata.
- Reject voluntary manoeuvres that would crash before they are chosen.
- Enforce sideswipe declaration/action timing and curve front-position requirements.
- Request sideswipe dice rolls with structured modifiers and deterministic dice injection.
- Emit damage requests instead of applying damage tables locally.
- Apply speed adjustments after damage requests are created.
- Emit hazard-roll requests for shunts and sideswipes with special shunt-target panic-brake handling.
- Preserve structured logs for contact-zone checks, ram classification, sideswipe tests, damage requests, speed changes, and hazard requests.

## Data Extracted

- Ram type, damage, speed adjustment, and hazard request draft: `data/rules/ram-types.json`.

## Ambiguities And OCR Doubts

### Contact-zone diagrams require tracing

The page 52-53 diagrams define exact contact zones for straight-ahead movement, drift, U-turns, spins, stationary angled cars, and curve positions. The OCR cannot encode those diagrams. Track Geometry must trace them into explicit `contactZone` sets or generators before engine coding.

Source pages: core pp. 52-53.

### Sideswipe draw hazard handling

The damage rule says both vehicles take damage on a sideswipe-test draw. The hazard text says only the loser tests after a neck-and-neck sideswipe. Because a draw has no loser, Rules Lead must confirm whether both vehicles test, neither tests, or both are treated as losers for hazard purposes.

Source pages: core pp. 55-57.

### Shunt equal-speed edge case

The shunt definition says the rammer must be faster than the target, but the damage text discusses equal speed factors and still requires hazard rolls. Implementation should distinguish mph eligibility for the shunt from speed-factor equality for damage. Rules Lead should confirm no shunt is possible at equal mph.

Source pages: core pp. 54, 56.

### Stationary same-direction target speed after shunt

The shunt speed formula assumes two mph values. A stationary same-direction target starts at 0 mph, so the formula is straightforward, but the subsequent "target must now take its move" wording may be odd for a vehicle that was stationary and not otherwise phase-eligible. Treat it as requiring proofread during implementation.

Source page: core p. 57.

### Facing and damage target side

The ram section defines damage quantity but does not clearly state the facing used for damage requests in the OCR. Damage Agent owns target matrices; implementation needs proofread or cross-reference for whether head-on/shunt/sideswipe map to front/rear/side facings.

Source pages: core pp. 34, 56.

### Core versus White Line Fever curve spins

Core rules crash a car that rotates on a curve. White Line Fever allows advanced curve spin movement. Engine data should carry rule-mode metadata so the selected ruleset controls this behaviour.

Source page: core p. 58; WLF advanced hazards.

### Bulldozer damage and displacement

Movement notes White Line Fever bulldozer handling, but the exact damage and target displacement are not in this core extraction. Rams must revisit this after the WLF manoeuvre page is proofread.

Source: WLF p. 8 via Movement Agent dependency.

## Candidate Tests

### Contact And Blocking

- A forward move whose contact zone overlaps a vehicle creates a ram and leaves the rammer in its starting position.
- A move whose contact zone extends off-road creates a crash.
- A legal U-turn whose contact zone overlaps a vehicle is rejected rather than converted into a ram.
- Render overlap without `contactZone` overlap does not create a ram.

### Classification

- Opposite-direction vehicles with one shared lane classify as `headOn`.
- Opposite-direction vehicles with both lanes shared classify as `headOn`.
- Same-direction vehicles with the rammer faster than the target classify as `shunt`.
- Collision with a wreck always classifies as `headOn`.
- Collision with a stationary same-direction non-wreck classifies as `shunt`.
- Collision with a stationary opposite-direction vehicle classifies as `headOn`.
- Collision with an angled vehicle classifies as `headOn`.
- Curve head-on classification uses logical lane direction, not render angle.
- Curve shunt classification uses shared logical lanes and same travel direction.

### Sideswipes

- A declared sideswipe after a straight-ahead move is legal against an adjacent same-square target.
- A sideswipe after a drift is illegal.
- A sideswipe without a declared ram action is illegal.
- A curve sideswipe is illegal when the rammer's front is not behind the target's front.
- A curve outer-to-inner sideswipe is legal when front-position and adjacency requirements are met.
- Sideswipe test adds optimum control for under-control vehicles.
- Sideswipe test adds adverse control for out-of-control vehicles.
- Rammer receives +1 on the sideswipe test.
- Equal sideswipe totals produce a draw.

### Damage

- Head-on at speed factors 3 and 3 emits six hits at +6 against both vehicles.
- Shunt at speed factors 5 and 4 emits one +1 hit against both vehicles.
- Shunt at equal speed factors emits no damage but still emits hazard requests.
- Neck-and-neck sideswipe loser at speed factors 4 and 3 emits one +1 hit against the loser.
- Neck-and-neck sideswipe draw emits one relative speed-factor hit against both vehicles.
- Opposed sideswipe loser at speed factors 1 and 3 emits one +4 hit against the loser.
- Opposed sideswipe draw emits one combined speed-factor hit against both vehicles.

### Speed Adjustment

- Head-on sets both vehicles to 0 mph.
- Shunt from 60 mph into 40 mph adjusts both to 50 mph.
- Shunt from 65 mph into 40 mph uses rounded-up half difference.
- Neck-and-neck sideswipe reduces both vehicles by 10 mph.
- Opposed sideswipe reduces both vehicles by 20 mph.
- Speed adjustment never reduces mph below 0.

### Hazards And Continuation

- Shunt emits 40 mph hazard requests for both moving, under-control vehicles.
- Shunt target treats panic-brake result as no effect.
- Head-on emits no post-ram hazard requests.
- Neck-and-neck sideswipe emits a 40 mph hazard request for the loser.
- Opposed sideswipe emits 40 mph for the winner and 20 mph for the loser.
- A vehicle that loses control from a post-ram hazard waits until its next move for the control-loss test.
- After a shunt, the target completes its move before the rammer finishes its no-action move.

### Crashes

- Out-of-control vehicle whose contact zone leaves the road crashes immediately.
- Voluntary action that would crash is not offered as legal.
- Non-campaign crash removes the vehicle without crash damage rolls.
- Campaign crash at 75 mph emits four +4 crash hits before removal is recorded.
- No-driver vehicle ending on a curve crashes immediately.
- Core spin rotation on a curve crashes immediately and ignores adjacent collisions.
