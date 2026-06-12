# Shooting

> Status: cleaned implementation draft, not engine code.  
> Owner: Shooting Agent  
> Source files: `docs/rules/core/04-shooting.md`, `docs/rules/core/06-passive-damage.md`, `docs/rules/white-line-fever/03-advanced-shooting.md`, `docs/rules/white-line-fever/04-new-equipment.md`  
> Source pages: Dark Future Rulebook pp. 22-27, 30-31; White Line Fever pp. 12-15, 18, 20, 27-36

## Scope

This section defines shooting action timing, direct-fire eligibility, passive weapon deployment, fire corridors, target selection, range, hit rolls, ordinary tactical factors, turrets, White Line Fever rear/side fire corridors, rear-facing weapons, outrigger mounts, linked weapons, and fire control computers.

This section does not resolve damage after a hit, passive damage effects, hazard roll results, vehicle design costs, mount capacity validation beyond shooting-specific legality, or campaign consequences.

## Core Concepts

- A `shoot` action is the phase action used to fire one direct-fire weapon, a linked group, a pair of turret-mounted weapons, or to deploy/use a passive weapon.
- A driver may shoot only if the phase action has not already been spent and the driver has not panic braked or lost control during the same phase.
- A driver may shoot in a phase even when the vehicle does not move in that phase, subject to the Turn Sequence restrictions for non-moving and stationary vehicles.
- A direct-fire shot is committed once the player checks `fireCorridor` or range.
- A passive deployment is resolved after the vehicle's move and after movement-linked hazard/control-loss tests.
- Damage and hazard results from passive hits can prevent a later direct-fire shot in the same phase.

Source pages: core pp. 22-25.

## Action Timing

### Declaring a shoot action

When a moving driver declares a shoot action before movement, the declaration must identify the weapon, linked group, turret pair, passive weapon, or fire-control-computer mode change that will use the action.

For direct fire, the driver may still cancel after movement and before checking range or `fireCorridor`. Once either check begins, the action is committed and ammunition is expended even if the target is out of range or otherwise illegal.

For passive deployment, the driver must complete the intended move and pass relevant hazard/control-loss tests before placing the marker. If the driver panic brakes or loses control, the marker is not deployed unless a locked-on system has a specific exception.

Source pages: core pp. 23-25.

### Non-moving and stationary vehicles

Drivers in vehicles that are not eligible to move in the current phase may still use direct-fire shooting or deploy smoke, matching the Turn Sequence section. Other passive deployments require a phase in which the vehicle actually moves.

Oil layers on stationary vehicles automatically switch off. Stationary vehicles and vehicles without a move may deploy smoke.

Source pages: core pp. 23-24.

## Passive Weapons

### Passive weapon types

Core passive marker types:

- `spikes`
- `oil`
- `patternMines`
- `smoke`
- `dummy`

Only vehicles with an appropriate passive mount may deploy passive weapons or dummies. Vehicles without passive weapons may not deploy dummy markers.

Source page: core p. 23.

### Deployment placement

A passive marker normally occupies the two lanes immediately behind the deploying vehicle.

Marker facing/state:

- oil, pattern mines, spikes, and dummies are placed face down;
- smoke is placed face up;
- face-down markers are revealed only when overlapped by a vehicle contact zone;
- dummies and pattern mine markers are removed when revealed or triggered as specified by passive damage rules;
- oil and normal smoke remain persistent after contact.

On curves, passive marker placement must be derived from the curve atlas. The marker is placed directly behind the vehicle and then adjusted to occupy exactly two legal curve spaces. This requires explicit per-curve passive-placement slots.

Source pages: core pp. 23-24.

### Tailgating

A vehicle is tailgated when another vehicle is in the space directly behind it. A tailgated vehicle can still deploy passives.

For non-smoke passive deployment while tailgated:

- request one d6;
- odd roll: deployment fails and no marker is placed;
- even roll: marker is placed normally, including under the tailgating vehicle if necessary.

Smoke ignores this tailgating failure rule and is always deployable.

If a marker is placed under a tailgating vehicle, that vehicle resolves the normal passive damage and hazard effects immediately after its next move. This is an exception to the usual passive-hit timing, which normally tests for moving onto a marker rather than off it.

Source page: core p. 24.

### Locked-on oil and smoke

Oil and smoke layers can be locked on by a shoot action. Once locked on, the system deploys after each qualifying move without spending another action.

Switching off a locked-on oil or smoke layer requires a shoot action declared at the start of the move. The switch-off succeeds only if the driver completes the move without losing control. A successful switch-off places no marker and uses no ammunition.

If a locked-on oil or smoke system would deploy while the vehicle is spinning, the marker is dispersed and not placed, but ammunition is still reduced.

Source page: core p. 24.

### Passive hits

A vehicle hits a passive marker when the marker is anywhere in that vehicle's `contactZone`. The vehicle completes its intended move first, then resolves passive damage and then passive hazard rolls.

The Damage Agent owns:

- oil handling reduction;
- spike wheel-critical checks;
- pattern mine damage;
- smoke hazard effects;
- double-hit resolution.

The Shooting Agent owns only the marker deployment, reveal, and contact-trigger timing.

Source pages: core pp. 24, 30-31.

## Direct Fire

### Eligible targets

A target is a vehicle. A shot cannot be aimed at a passive marker or a selected component/location on a vehicle.

A fixed-mount weapon can fire only at a vehicle at least partially inside that weapon's `fireCorridor`. A vehicle's rendered model position is used for fire-corridor inclusion, not its contact zone. This is especially important for curves and spun vehicles.

If multiple vehicles are in the same fire corridor, the shot must target the closest vehicle in that corridor. Friendly vehicles can block shots by being closer inside the corridor.

Fire corridors cannot be extended off the road/track sections.

Source pages: core pp. 25-26.

### Range

Range is measured in spaces. Count the target's occupied space, but not the firer's occupied space.

For non-straight shots, turret shots, or shots involving curves/spun vehicles, range is measured with the range/movement ruler from the firing weapon to the closest point of the target. A partial space counts as a full extra space.

For hit-number purposes, a target beyond six spaces but still within the weapon's maximum range counts as range 6. The shot still must be within the weapon's maximum range.

Source pages: core pp. 25-27.

### Hit roll sequence

For each fired weapon:

1. Determine legal target and measured range.
2. If the target is beyond weapon maximum range, the committed shot misses and ammunition is spent.
3. Request one d6 hit roll.
4. If the natural roll is 1, the shot misses regardless of modifiers.
5. Add weapon accuracy.
6. Add or subtract tactical factors.
7. If the modified total is equal to or greater than the capped range number, the shot hits.
8. If the total is lower, the shot misses.

Damage after a hit is delegated to the Damage Agent.

Source page: core p. 27.

## Fire Corridors And Mounts

### Core fixed fire corridor

Core fixed mounts use the ordinary forward corridor shown in the rulebook. The current draft treats this as a two-lane-wide corridor extending forward from the weapon's mounting/facing direction. Exact lane offsets must be encoded by the Track Geometry and Vehicle Design data.

On curves, fire corridors must be resolved with the range/movement ruler aligned to the space divider in front of the firing vehicle. Targets on curves are checked by extending the corridor over the curve geometry, not by rectangular grid shortcuts.

Source page: core p. 25.

### White Line Fever side and wing corridors

Wing-mounted and side-mounted weapons shift the ordinary corridor one lane toward the side on which the weapon is mounted.

Central hard points, including hood, roof, and tailgate, use the central corridor for their firing direction.

Source page: WLF p. 12.

### Rear hard points

Renegades and Interceptors add three rear hard points:

- rear-left wing;
- rear-centre tailgate;
- rear-right wing.

Each rear hard point may mount one medium or heavy weapon.

Renegade rear-wing mounts are rear-facing only. Interceptor rear-wing mounts may be forward-facing or rear-facing. Tailgate hard points are rear-facing only.

Source page: WLF p. 12.

### Rear-facing weapons

Roof, side, rear-wing, and tailgate hard points can support rear-facing weapons where vehicle-design legality allows it.

Restrictions:

- a vehicle with a tailgate gun cannot also have a rear-facing roof gun;
- if a hard point mounts two medium weapons, both must face the same direction;
- front-facing and rear-facing weapons cannot be linked together.

Rear-facing hit penalties:

- roof or tailgate rear-facing weapon: `-1`;
- side or wing rear-facing weapon: `-2`.

Rear-facing central weapons use the central corridor extending behind the vehicle. Rear-facing side/wing weapons use the side-shifted corridor extending behind the vehicle.

Source page: WLF p. 13.

### Interceptor turret blind spot with tailgate weapons

An Interceptor with a tailgate-mounted weapon and a turret, cupola, or pintle mount has a restricted rear blind spot. The turret/cupola/pintle cannot engage targets directly behind the vehicle in the blocked arc. The restriction does not apply to Renegades.

The exact blind-spot geometry must be traced from the WLF diagram before final implementation.

Source page: WLF p. 13.

## Turrets

### Core turret targeting

Turret-mounted weapons use normal hit roll rules but do not use fixed forward fire corridors. A turret may fire in any direction through a full 360-degree arc unless another rule restricts it.

Turrets select the nearest available enemy target. Friendly vehicles are vehicles that started the game on the same side and are ignored as targets by turret selection.

Tie handling:

- if equal-range targets include rear targets, the turret selects a rear target;
- if multiple equal-range rear targets exist, the player chooses between them without spending an extra action;
- if there are no rear equal-range targets but multiple equal-range front targets, the player chooses between them without spending an extra action.

The driver still spends a shoot action to fire turret weapons unless a fire control computer is firing automatically.

Source page: core p. 27.

### Pair of turret-mounted weapons

The core rules refer to a shoot action covering a pair of turret-mounted weapons. The exact pairing and ammunition handling should be confirmed against the vehicle/hardware section before final coding.

Source page: core p. 23.

## Linked Weapons

Only identical weapons facing the same direction may be linked. Different weapon types cannot be linked, and forward-facing weapons cannot be linked with rear-facing weapons.

Linked weapons may be on different hard points. When the linked group fires:

- one shoot action fires the whole linked group;
- the link cannot be partially bypassed;
- all linked weapons expend ammunition, even if a weapon has no target in its own corridor;
- each linked weapon uses its own fire corridor;
- each linked weapon targets the closest target in its own corridor;
- each firing weapon makes its own hit roll;
- different linked weapons can engage different targets without a hit penalty.

If linked weapon corridors include both friendly and enemy vehicles, the driver must pass a cool test against `driveSkill` before firing. The OCR indicates success requires a die roll lower than the driver's drive skill; however, the example says a roll of 3 passes against skill 4. Treat this as `roll < driveSkill` until proofread. If the test fails, the driver loses the shoot action and does not fire.

Source pages: WLF pp. 14-15.

## Outrigger Mounts

Bikes may take a pair of outrigger mounts in the advanced rules. This section records only shooting behaviour; design legality and damage vulnerability belong to Bikes/Three-Wheelers, Vehicle Design, and Damage.

Shooting rules:

- outrigger mounts may carry lightweight or medium weapons;
- both mounts must carry identical weapons;
- the outrigger weapons must be forward-firing;
- the outrigger weapons must be linked;
- outrigger-mounted weapons use the normal two-lane bike fire corridor;
- each outrigger may carry two 50mm missile tubes as a specific exception;
- medium weapons on outriggers may not be double-loaded;
- lightweight weapons on outriggers may be double-loaded if otherwise legal.

If one outrigger is disabled, firing the weapon on the remaining outrigger automatically fails a control-loss test. The Hazards Agent owns the consequence of that failed control-loss test.

Source page: WLF p. 14.

## Fire Control Computers

Fire control computers are automated systems that can fire a weapon or linked group at the end of each phase. They operate by mode. A computer starts in standby. Changing mode requires a shoot action and the computer cannot engage a target in the same phase in which its mode changes.

A natural hit roll of 1 still misses.

Fire control computers treat vehicles other than wrecks as possible targets. Hostile bikes are treated like cars. Friendly bikes do not block a fire-control-computer-controlled weapon's fire corridor even though their contact zone is car-sized.

Source page: WLF p. 34.

### Turret fire computer

A turret fire computer controls turret-mounted or cupola-mounted non-missile weapons. It cannot control pintle mounts. Turret-mounted missile pods need a missile fire computer instead.

Hit modifiers:

- `+1` to hit at ranges 1-6;
- `+2` to hit at ranges over 6;
- smoke penalty is capped at `-1` instead of the normal `-3`.

Modes:

- `standby`: no effect;
- `engagement`: automatically fires once per phase at the nearest available target;
- `designation`: records one enemy target and fires at it whenever possible, otherwise behaves as engagement mode. Changing the designated target requires selecting designation mode again with a shoot action.

Cupola-controlled weapons must be operated by the gunner rather than the driver.

Source page: WLF p. 34.

### Missile fire computer

A missile fire computer can control missile pods, including turret-mounted missile pods. It gives guided missiles a broader fire corridor, target selection, smoke mitigation, and range-based accuracy bonuses.

General rules:

- missiles controlled by a missile fire computer use a four-lane-wide fire corridor;
- the corridor applies regardless of where the missile pod is mounted;
- targets with only one lane inside the corridor are eligible;
- missiles cannot engage targets inside the two-space minimum range;
- if a spun/corner target has any part within one space of the front of the firing vehicle, the computer will not select it;
- friendly vehicles are ignored as targets;
- friendly vehicles can be steered around and do not block the usual way;
- the corridor is blocked only by a vehicle completely blocking both lanes to the target;
- a target cannot be engaged if another vehicle blocks the target lane in either of the two spaces immediately behind the target;
- smoke penalty is capped at `-1`;
- missile computer hit bonus is `+1` at range 5-6, `+2` at range 7-8, and `+3` at range 9 or more.

Modes:

- `standby`: no effect;
- `lockOn`: locks onto the closest target. One shoot action can fire any missile in any pod linked to the computer, bypassing normal strict loading order;
- `salvo`: locks the available arsenal onto the nearest target outside the minimum range. The driver may fire one missile or all available missiles with one shoot action;
- `engagement`: automatically launches one missile per phase at the nearest available target until missiles are expended or mode changes. It fires the lowest numbered available chamber; if two chambers share the same number, the player chooses. Smoke missiles are ignored and treated as empty in this mode;
- `designation`: records one enemy target. If that target is in the computer corridor, use it; otherwise lock onto the nearest enemy as in salvo mode. Changing the target requires another shoot action.

Source pages: WLF pp. 35-36.

## Special Shooting-Related Equipment

### Oil injection

Oil injection works like a smoke layer but does not occupy a passive weapon space and has effectively unlimited shots. It can be switched on/off with a shoot action and can be locked on like a smoke layer.

Oil-injection smoke is not persistent:

- car trail maximum: three markers;
- bike trail maximum: two markers;
- when the trail is full, the rear marker moves to the front each time the vehicle moves;
- when switched off, remove the rear-most marker immediately, then remove one remaining marker at the end of each further phase until none remain.

Its smoke has the same shooting obstruction and safety-limit effects as ordinary smoke.

Source page: WLF p. 18.

### Drag chutes

Releasing a drag chute is a shoot action. The driver rolls one d6; on `1`, the chute fails to open and is jettisoned.

An open drag chute places a marker behind the vehicle. For shooting, a drag chute marker penalizes hit rolls like smoke, but at `-2` per chute marker. Chute and smoke penalties combine, still capped at `-3`.

Source page: WLF p. 20.

### Missiles and missile smoke

Missile pods have minimum range 2. A missile inside minimum range does not arm and has no effect.

Smoke missiles use a four-lane-wide, six-space-long smoke corridor. Without a missile fire computer, the corridor begins six spaces from the firing vehicle. With a missile fire computer, the driver may choose the start range, but not below the two-space minimum. Smoke from smoke missiles is persistent.

Cannister missiles do not use ordinary hit rolls. They nominate a target track section within range and line of sight. The Damage Agent owns the per-vehicle hit/damage resolution, but Shooting owns the targeting restriction. Cannister missiles cannot be fired after a move in which the firer manoeuvred, used any action other than shoot, or was forced to take a hazard roll.

TGSM missiles make a standard missile accuracy check first and add `+4` accuracy. After a hit, they resolve submunitions, each at `+4` HE damage, using the WLF p. 29 submunition count and hit-location tables. Those p. 29 tables still need extraction before faithful tactical TGSM resolution can be implemented.

Phosphor ammunition creates persistent smoke markers in a six-marker trail beginning six spaces from the firer. Phosphor shots are high-trajectory and are not blocked by vehicles in the fire corridor. On curves, marker placement must use the range template and curve geometry.

Source pages: WLF pp. 27-31.

## Required Engine Behaviours

- Generate legal direct-fire actions only when the driver has an available action and is not barred by panic braking/control loss.
- Distinguish declared shooting from committed shooting.
- Commit a shot once range or fire corridor is checked.
- Spend ammunition for committed shots even when later found out of range.
- Resolve passive deployment after movement and movement-linked hazard/control-loss tests.
- Resolve passive hit timing after the target completes its intended move.
- Ask Track Geometry for fire-corridor inclusion, curve corridor overlays, range ruler measurement, and passive placement slots.
- Apply closest-target blocking for fixed weapons.
- Select turret targets by nearest enemy and rear-preference tie rules.
- Apply natural-1 automatic miss before modifiers.
- Cap normal range target number at 6 while still enforcing weapon maximum range.
- Apply ordinary tactical factors and WLF rear-facing/computer modifiers as structured modifier entries.
- For linked weapons, resolve each weapon's corridor and closest target independently.
- Request a cool test before firing linked weapons when friendly and enemy targets are both in linked corridors.
- Schedule fire-control-computer automatic attacks at end of phase.
- Prevent a fire-control computer from firing in the same phase its mode changes.
- Keep fire-control-computer target selection inside legal action/target APIs so AI and UI cannot bypass legality.

## Data Extracted

- Draft weapon accuracy and shooting traits: `data/rules/weapons-draft.json`.
- Draft shooting modifiers and modifier caps: `data/rules/shooting-modifiers.json`.

## Ambiguities And OCR Doubts

### Core fixed fire corridor dimensions

The OCR text preserves the rule but not the diagram precisely. The current draft treats normal fixed fire corridors as two lanes wide, but final geometry must be traced from the page image and coordinated with Track Geometry.

Source page: core p. 25.

### Passive marker placement on curves

The curve passive placement diagrams are not recoverable from OCR. The curve atlas needs explicit passive placement slots before faithful implementation.

Source page: core p. 24.

### Missile pod accuracy

Core OCR reads missile pod accuracy as `42`, which is almost certainly `+2` based on the weapon table pattern and WLF missile entries. The data marks this as `needsProofread`.

Source page: core p. 27.

### Linked weapon cool test comparator

WLF OCR says the roll must be less than drive skill, and the example roll of 3 against skill 4 passes. This draft uses `roll < driveSkill`. Confirm whether equality is failure.

Source page: WLF p. 15.

### Turret pair firing

Core shooting says a shoot action can cover a pair of turret-mounted weapons, but this needs confirmation from the hardware section before final ammunition and targeting rules are coded.

Source page: core p. 23.

### Interceptor rear blind spot

The turret/cupola/pintle blind spot with a tailgate weapon is diagram-defined. The exact arc must be traced before implementation.

Source page: WLF p. 13.

### Fire computer timing

WLF says computer firing is adjudicated at the end of each phase. Turn Sequence needs to confirm whether this happens after all ordinary driver activations and after all end-phase hazard/equipment effects.

Source page: WLF p. 34.

## Candidate Tests

### Action Timing

- A driver who used the phase action to U-turn cannot shoot in that phase.
- A driver who declared shoot before movement can cancel before checking range or `fireCorridor`.
- A driver who checks range for an out-of-range target spends ammunition and misses.
- A driver forced to panic brake before the shooting step cannot fire.
- A stationary vehicle in phase 1 can fire a direct-fire weapon.
- A non-moving vehicle in a later phase can fire direct-fire weapons but cannot deploy oil.

### Passive Deployment

- A moving vehicle that declares `shootPassive` places the marker only after completing movement and passing hazard/control-loss checks.
- Oil, mines, spikes, and dummy markers are face down; smoke is face up.
- A passive marker under a tailgating vehicle resolves after that vehicle's next move, not immediately.
- Tailgated non-smoke passive deployment fails on an odd d6 and succeeds on an even d6.
- Tailgated smoke deployment always succeeds.
- Locked-on oil deploys after each qualifying move without spending another action.
- Switching off locked-on oil succeeds only if the driver completes the move without losing control.
- Locked-on smoke in a spinning car spends ammunition but places no marker.

### Fire Corridors And Range

- A fixed weapon cannot target a vehicle outside its fire corridor.
- A vehicle partially inside a fire corridor is an eligible target.
- A closer friendly vehicle in the corridor blocks a farther enemy target.
- A fire corridor cannot extend off the track.
- Range counts the target space but not the firing vehicle's space.
- A measured range of 8 within weapon maximum uses target number 6 for the hit roll.
- A curved fire corridor asks Track Geometry/ruler logic rather than rectangular grid logic.

### Hit Rolls

- Natural roll 1 misses even when modifiers would otherwise hit.
- A 4.2mm MG at range 3 with accuracy +2 hits on natural 1? No: natural 1 still misses.
- A 4.2mm MG at range 3 with natural 2 and no modifiers hits after accuracy.
- A hood-mounted weapon adds +1.
- A turret-mounted weapon adds +1.
- Four smoke markers in the corridor apply only the maximum normal smoke penalty of -3.
- Firer at 81 mph applies -1.
- Target at 81 mph applies -1.

### Turrets

- A turret can select targets outside the normal fixed fire corridor.
- A turret ignores friendly vehicles as targets.
- A turret selects the nearest enemy target.
- Equal range targets prefer a rear target over a front target.
- Multiple equal rear targets allow player choice without spending another action.
- Interceptor with tailgate weapon and turret cannot target directly behind inside the traced blind spot.

### White Line Fever Mounts

- A left-wing forward weapon uses a one-lane-left shifted corridor.
- A right-side rear-facing weapon uses a one-lane-right rear corridor.
- A roof rear-facing weapon applies -1 to hit.
- A side rear-facing weapon applies -2 to hit.
- A Renegade rear-wing weapon cannot be forward-facing.
- An Interceptor rear-wing weapon can be forward-facing or rear-facing.
- A tailgate weapon can only be rear-facing.

### Linked Weapons

- Linked weapons require identical weapon ids and matching facing.
- Linked front and rear weapons are rejected.
- Firing a linked group expends ammunition from all linked weapons.
- Linked weapons with different corridors can hit different closest targets.
- A linked weapon with no target still expends ammunition when the group fires.
- Friendly and enemy targets in linked corridors request a cool test.
- Cool test roll 3 with drive skill 4 passes under the current provisional rule.
- Failed cool test spends the action and fires no weapons.

### Fire Control Computers

- A fire control computer starts in standby.
- Changing fire-control mode spends a shoot action.
- A computer does not fire in the same phase its mode changes.
- A turret fire computer in engagement mode fires once at the end of a phase.
- Turret fire computer smoke penalty is capped at -1.
- Turret fire computer gives +1 at range 6 and +2 at range 7.
- Missile fire computer rejects targets within two spaces.
- Missile fire computer ignores friendly targets and can steer around friendly blockers.
- Missile fire computer is blocked by a vehicle completely blocking both lanes to the target.
- Missile fire computer gives +1 at range 5-6, +2 at 7-8, and +3 at 9+.
- Missile fire computer engagement mode skips smoke missiles.

## Dependencies

- Turn Sequence Agent: action availability, phase timing, end-phase computer firing hook.
- Movement Agent: whether the vehicle actually moved, manoeuvre status, spun state.
- Track Geometry Agent: fire corridors, range ruler, curve fire geometry, passive placement slots.
- Hazards Agent: panic brake/control loss state and failed control-loss test consequences.
- Damage Agent: direct-fire damage, passive damage, target matrices, critical hits.
- Vehicle Design Agent: legal mounts, hard point capacity, linked group construction, ammunition loads.
- Bikes and Three-Wheelers Agent: bike corridors, outrigger damage, outrigger control-loss consequences.
