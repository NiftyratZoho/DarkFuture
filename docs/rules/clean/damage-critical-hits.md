# Damage and Critical Hits

> Status: cleaned implementation draft  
> Owner: Damage Agent  
> Source files: `docs/rules/core/05-damage.md`, `docs/rules/core/06-passive-damage.md`, `docs/rules/core/07-critical-hits.md`, `docs/rules/white-line-fever/04-new-equipment.md`  
> Source pages: Dark Future Rulebook pp. 28-35; White Line Fever pp. 17-18, 22-31

## Scope

This section defines vehicle damage rolls, armour subtraction, damage increments, passive damage effects, target facing, target matrices, critical hit results, and terminal damage. It does not define firing legality, fire corridors, ram damage generation, crash damage generation, hazard roll result tables, vehicle design costs, or UI presentation.

## Core Damage Roll

Every damage source is treated as a `hit`. A hit may come from weapons, passive markers, collisions, crashes, explosions, or equipment failures.

Resolve ordinary damage as:

1. Roll 1d6.
2. Add the hit's `damageModifier`.
3. Subtract the target armour that applies to the hit's facing and ammunition type.
4. If the total is positive, subtract that many points from the vehicle's current damage total.
5. If the total is zero or lower, no ordinary damage is applied.

The damage die is also checked before modifiers. A natural 6 causes a `criticalHit` even when armour prevents ordinary damage. Armour never cancels a critical hit caused by a natural 6.

For crash and collision sources, the modifier is supplied by the Rams and Crashes Agent. For crashes, the core rule says the modifier equals the crashing vehicle's `speedFactor`.

## Vehicle Damage Characteristics and Armour

Core starting values:

- Renegade: 18 damage, 3 armour.
- Interceptor: 24 damage, 4 armour.
- Bike: 9 damage, 2 armour.

White Line Fever allows armour to vary by facing and material. Damage resolution must therefore request armour by `facing`, not by vehicle type alone.

Supported armour concepts:

- `carbonSteel`: normal armour. Subtracted normally unless AP rules override it.
- `carbonPlastic`: lightweight armour. Subtracted normally and also fully applies against AP hits.
- `none`: no armour contribution.

No car facing may exceed 6 armour. Bikes have lower facing caps: sides 4, roof 3, front/rear/floor 6.

## Damage Increments

When a vehicle falls below a listed `damageIncrement` threshold, apply one incremental damage step immediately. The starting damage total is not itself an increment threshold, so a vehicle does not suffer incremental damage just because it has taken its first point of damage.

Each incremental step applies:

- maximum speed -10 mph;
- acceleration -3 mph;
- handling -1.

Core thresholds:

- Interceptor: 18, 12, 6.
- Renegade: 12, 8, 4.
- Bike: 6, 3.

Implementation behaviour:

- A single hit may cross more than one threshold. Apply each newly crossed threshold once.
- Track applied thresholds in state so later hits do not reapply the same threshold.
- Apply ordinary damage and increments before resolving critical hits, terminal damage, or hazard rolls for that hit.

## Multiple Damage and Multiple Hits

A single hit can cause ordinary damage, a critical hit, terminal damage, and hazard rolls. Resolve those stages in this order:

1. Ordinary damage, including newly crossed damage increments.
2. Critical hits.
3. Terminal damage.
4. Hazard rolls.

When a vehicle takes multiple hits, resolve the full sequence for each hit before resolving the next hit.

If the vehicle has already reached zero damage, later hits do not apply ordinary damage, but their natural damage die still matters for critical hits. Terminal explosion checks may also still happen until the vehicle has exploded once.

## HE Hits

Hits whose damage notation ends in `HE` resolve ordinary damage normally. HE may additionally require hazard rolls. The Hazard Agent owns the hazard roll calculation and results.

Data must mark HE hits with `tags: ["HE"]` so the damage system can emit the right post-damage event for the Hazard Agent.

## Passive Damage Effects

Passive markers are deployed by the Shooting Agent and encountered through Movement/Track Geometry. This section defines their damage-side effects after a passive marker is hit.

### Oil

Oil causes no ordinary damage. Each oil hit reduces handling by 1, up to a maximum of 2 handling lost from oil over the engagement. The vehicle may also need a hazard roll.

Oil hazard timing is unusual: if another hazard roll is caused by the same move, resolve oil last. If another hazard roll forces panic braking, the oil hazard uses the lower 30 mph safety limit.

### Pattern Mines

A pattern mine hit causes one +3 ordinary damage hit. A vehicle travelling faster than 50 mph must also take a hazard roll. The marker is removed after the hit.

### Smoke

Smoke does not cause ordinary damage. It affects shooting modifiers and can force hazard rolls. A vehicle entering smoke faster than 60 mph must take a hazard roll. Shooting through smoke is owned by the Shooting Agent.

### Spikes

At 20 mph or less, spikes have no effect. Above 20 mph, the deploying player rolls 1d6. On 1-5 the spikes do nothing. On 6 they cause a wheel critical at 0 damage. This critical should target the `wheels` table directly rather than going through the target matrix.

### Double Passive Hits

If a straight-ahead move hits two identical passive markers:

- Oil: treat as two oil hits.
- Pattern mines: roll damage for both patterns in sequence. Make one hazard roll for both, using a 30 mph safety limit.
- Smoke: make one normal smoke hazard roll. If the car fires out from the smoke while both markers are underneath it, the shooting penalty is -1 for those two markers.
- Spikes: treat as one spike hit.

If the two passive markers are different, resolve each hit separately.

## Target Facing

Critical hits need a target `facing` before the target matrix is rolled.

Facing values:

- `front`
- `rear`
- `side`
- `floor`
- `roof`

Common facing rules:

- Most direct shots hit the target's front or rear based on relative positions.
- If both cars are on straights and share at least one lane, facing remains front or rear.
- If the target is at an oblique angle, on or firing from a corner, or in a different pair of lanes, roll 1d6: even hits front/rear, odd hits side.
- A vehicle spun to 90 degrees uses side facing.
- Passive weapon criticals use floor facing.
- Rolling uses roof facing.
- Crash critical facing is random: 1-2 roof, 3 left side, 4 right side, 5-6 front.

Track Geometry and Shooting must provide enough positional context to choose between front, rear, side, and oblique. This section only owns the final facing/matrix lookup.

## Target Matrix

After facing is known, roll 1d6 on that facing's target matrix. Some results request one additional roll to select a subtarget.

Important behaviours:

- Make only one primary matrix roll per critical hit.
- If the result names a system that is not fitted, already disabled, or already destroyed, the critical hit is wasted unless another rule redirects it.
- Weapon subtargets such as wings, sides, and passives require a left/right roll where odd is left and even is right.
- Renegades have one central passive station. Any `passives` result against a Renegade automatically targets that station.
- Side-facing `sideWeapon` subresults hit the side nearest the firer and do not need a left/right roll.

The machine-readable matrix is in `data/rules/target-matrices.json`.

## Critical Hit Result Tables

After the matrix selects a component, roll 1d6 on that component's critical result table.

Tables owned here:

- `driver`
- `engine`
- `wheels`
- `bodywork`
- `weapons`
- `fuel`
- `tailGunner` from White Line Fever

The result data is stored in `data/rules/damage-tables.json`. Effects are represented as structured ids and compact parameters, not as engine code.

## No Driver

Some driver criticals cause `noDriver`.

Required state effects:

- Vehicle automatically loses control.
- Driver drive skill is reduced to zero.
- Control loss tests receive +2.
- Vehicle speed drops by 5 mph after each move until it halts or crashes.
- If a no-driver vehicle ends any move on a curved track section, it automatically crashes.

Hazards/Control Loss and Rams/Crashes own the detailed resolution of the control loss and crash steps.

## Disabled Engine

When the engine is disabled:

- acceleration becomes zero;
- the vehicle automatically loses 5 mph after each completed move;
- lasers may take one last shot this turn if they have not already fired this turn;
- after that final stored-power shot, lasers stop working;
- turrets and missile guidance stop working immediately.

White Line Fever equipment can also disable or explode engines. Nox explosion uses the engine-explosion critical effect and disables the engine regardless of whether the critical would otherwise do so.

## Terminal Damage

When a hit removes the final damage point:

- engine is disabled;
- all weapons stop working;
- handling is reduced to zero.

For the hit that caused terminal damage and for later hits, make a terminal explosion check until the vehicle has exploded once:

- roll 1d6;
- on 1, the vehicle explodes and causes a driver critical;
- on 2-6, no explosion.

After the vehicle has exploded once, further ordinary damage is wasted. Critical checks from later natural 6 damage dice can still be represented as events if the Rules Lead decides post-explosion criticals remain relevant, but the core text says additional damage after the explosion is effectively wasted.

## White Line Fever Damage-Side Additions

### Armour Piercing

AP hits use special armour handling.

- If the AP damage rating is greater than or equal to the target's carbon steel armour on that facing, carbon steel armour is ignored.
- If the target's total armour is greater than the AP damage rating, carbon steel armour counts at half value, rounded down.
- Carbon plastic armour always applies at full value against AP.

### Depleted Uranium

Depleted uranium ammunition creates AP variants:

- Autocannon: +3AP.
- Minigun: +5AP.
- Chain gun: +6AP.

### Shaped Plastic

Shaped plastic ammunition is available for 40mm grenade launchers and 40mm RAG launchers. It changes damage to +6AP.

### Phosphor

Phosphor rounds cause no ordinary damage. They place persistent smoke. Damage should return a no-damage result and emit marker-placement data for Shooting/Track Geometry if that subsystem asks damage to classify the shot.

### Missile Damage

White Line Fever missile types add or modify damage:

- Cannister: no hit roll; vehicles on the target section take one or two +3 hits; facing is roof.
- High explosive missile: +8HE.
- HiVAP: AP damage equal to range in spaces, maximum +15; beyond 25 spaces reduce by 1 per space; cannot hit at 40 or more spaces.
- Shaped plastic missile: +6AP.
- Smoke missile: no ordinary damage; creates persistent smoke.
- TGSM: parent hit determines submunition count; each submunition is +4HE. Each submunition also has a facing roll: 1 front/forward armour, 2-3 side armour, 4-5 rear armour, 6 roof/superstructure bypassing standard facing armour.

### Reinforced Tyres

If a vehicle with reinforced tyres takes a wheel critical, roll 1d6. Even results cancel the wheel critical; odd results allow it to resolve normally.

### Rocket Booster Critical

If a rocket booster suffers a critical and explodes, it causes an additional +8HE hit and forces a 30 mph hazard roll. If one booster in a linked twin system is disabled, the other can no longer operate.

### Tail Gunners

Tail gunner mounts interact with critical hits:

- A roof/turret critical on a vehicle with a tail gun position is split by die roll: odd hits the gunner, even hits the weapon.
- A driver critical on a vehicle with a tail gunner is split by die roll: odd hits the driver, even hits the tail gunner.
- If the tail gunner is hit, use the tail gunner critical table.
- Vehicles with tail gunners count as two-seaters for critical-hit purposes.

## Required Engine Behaviours

- Accept a `hit` object with damage modifier, tags, facing, source, and optional ammunition/material metadata.
- Request/inject all dice rolls.
- Calculate ordinary damage before criticals, terminal damage, and hazard events.
- Detect natural 6 on the damage die before modifiers.
- Apply armour by facing and ammunition type.
- Apply damage increments exactly once per crossed threshold.
- Resolve multiple hits sequentially.
- Preserve critical and terminal damage log events even if ordinary damage is zero.
- Represent hazard triggers as structured events for the Hazard Agent.
- Represent component damage as state changes plus log entries, not prose-only messages.

## Data Extracted

- Core vehicle damage, armour, damage increment thresholds, and weapon damage characteristics: `data/rules/damage-tables.json`.
- Passive marker damage effects: `data/rules/damage-tables.json`.
- Critical hit result tables: `data/rules/damage-tables.json`.
- White Line Fever AP, armour, reinforced tyre, tail gunner, missile, and special ammunition effects: `data/rules/damage-tables.json`.
- Target facing rules and target matrices: `data/rules/target-matrices.json`.

## Ambiguities and OCR Notes

- Dark Future p. 28: The core OCR misreads Renegade armour as 8 in one place; the page image confirms Renegade armour is 3.
- Dark Future p. 33: OCR collapses the side, floor, and roof target matrices. The data file is based on the page image `df-33.jpg`.
- Dark Future p. 34: The engine table says brake cylinder reduces braking to 5 mph. OCR sometimes reads this as `Smph`.
- Dark Future p. 34: Tyre destroyed says maximum speed becomes 10 mph lower or 60 mph, whichever is slowest. Page-image proofread confirms this means the lower maximum speed.
- Dark Future p. 35: Terminal damage says the first terminal hit and later hits can trigger explosion checks, but also says a car can explode in this way only once. The data models a `terminalExplosionCheckedUntilExploded` event, not one check total.
- White Line Fever p. 24: Core rulebook gives Renegade armour 3. The WLF OCR says standard Renegades have 3 and Interceptors 4, matching the page image/core values.
- White Line Fever pp. 28-29: Cannister missile and TGSM rules depend on area targeting and missile hit resolution owned by Shooting. Damage only records resulting hit count, damage, and facing.
- White Line Fever p. 30: AP text says armour is ignored if armour is equal to or less than the weapon damage rating. The implementation rule is therefore `damageRating >= carbonSteelArmour`.

## Candidate Tests

### Ordinary Damage

- A +3 hit against 4 armour with damage die 2 causes 1 ordinary damage.
- A +1 hit against 4 armour with damage die 2 causes no ordinary damage.
- A natural 6 against armour high enough to stop ordinary damage still creates one critical hit.
- A non-natural modified 6 does not create a critical hit unless another rule says so.

### Damage Increments

- An Interceptor dropping from 19 to 17 damage applies the 18 threshold once.
- An Interceptor dropping from 19 to 5 damage applies the 18, 12, and 6 thresholds once each.
- A Renegade taking its first damage does not apply an increment at 18, because 18 is the starting total.

### Multiple Hits

- Two pattern mine hits resolve in sequence and can apply different increments.
- A vehicle already at zero damage ignores ordinary damage from later hits but still checks a natural 6 for critical.

### Passive Damage

- Oil reduces handling by 1 on the first two oil hits and not on the third.
- Pattern mine creates a +3 hit and removes its marker.
- Spikes at 20 mph do nothing.
- Spikes above 20 mph with die 6 create a wheel critical at 0 damage.
- Two straight-ahead pattern mine hits roll ordinary damage twice and request one hazard roll at 30 mph.

### Target Matrix

- Front-facing matrix roll 4 then subroll 3 selects side weapons.
- Rear-facing matrix roll 5 then subroll 4 selects fuel.
- Side-facing matrix roll 3 then subroll 5 selects rear wheels.
- Floor-facing matrix roll 6 then subroll 1 selects weapons, then side/passive subroll selects the component.
- Roof-facing matrix roll 6 then subroll 1 selects engine.

### Critical Results

- Driver roll 6 creates no-driver state.
- Engine roll 6 disables the engine, creates a +2HE side-facing hit, and requests a 50 mph hazard event.
- Wheel roll 5 reduces handling by 2, reduces max speed, and requests a 20 mph hazard event.
- Weapon roll 5 on an HE weapon requests an explosion die; odd creates a +8HE hit.
- Fuel roll 4 creates an immediate +8HE rear-facing hit and disables the engine.

### Terminal Damage

- A hit reducing a vehicle to zero disables the engine, stops weapons, reduces handling to zero, and requests a terminal explosion check.
- A terminal explosion die of 1 creates a driver critical and marks the vehicle as already exploded.
- Later damage after the vehicle has already exploded produces no further ordinary damage.

### White Line Fever

- +8AP against 6 carbon steel ignores carbon steel armour.
- +4AP against 4 carbon steel plus 2 carbon plastic applies 2 carbon steel and 2 carbon plastic armour.
- Reinforced tyres cancel a wheel critical on an even roll.
- Cannister missile odd target roll creates one +3 roof-facing hit.
- TGSM submunition count roll 5 creates six +4HE hits.
