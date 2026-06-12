# Vehicle Design and Equipment

> Status: cleaned implementation draft, not engine code.  
> Owner: Vehicle Design Agent  
> Source files: `docs/rules/core/12-vehicle-design.md`, `docs/rules/core/13-vehicles-and-hardware.md`, `docs/rules/white-line-fever/04-new-equipment.md`, `docs/rules/white-line-fever/05-safety-devices.md`, `docs/rules/white-line-fever/07-design-section.md`  
> Source pages: Dark Future Rulebook pp. 81-86; White Line Fever pp. 16-37, 41-44

## Scope

This section defines vehicle templates, payload and advanced weight handling, ordinary and passive mounts, engine/chassis selection, add-on systems, armour, weapon-system installation, ammunition/reload bookkeeping, fire-control computer installation, safety devices, record-sheet fields, and campaign repair/re-equipment dependencies.

This section does not resolve movement, shooting, damage, hazard rolls, rams, bike-specific handling exceptions, scenario setup, campaign money awards, or UI rendering. It supplies legal vehicle records and equipment metadata for those agents.

## Design Modes

There are two supported design modes.

`corePayload` mode uses the core book payload limit. A vehicle has fixed movement characteristics, fixed armour, fixed damage, and a maximum payload of fitted items. Installed weapon and equipment weight must not exceed payload. This is the right mode for basic scenarios and early tactical implementation.

`advancedWeight` mode uses White Line Fever vehicle design. Start with a chassis/engine entry, add all systems, armour, weapons, ammunition, crewed mounts, and safety devices, then calculate total cost and total weight. Acceleration and maximum speed come from total weight and engine size. Braking and handling come from total weight and vehicle type. The WLF characteristic and equipment summary tables are represented in `data/rules/wlf-vehicle-tables-proofread.json`; unresolved cells are tracked in `docs/rules/implementation-blockers.md`.

Source pages: core pp. 81-83; WLF pp. 41-44.

## Core Vehicle Templates

Core vehicles:

- `renegade`: 18 damage, 3 armour, 100 mph max speed, 20 mph acceleration, 30 mph braking, handling 4, payload 650.
- `interceptor`: 24 damage, 4 armour, 120 mph max speed, 30 mph acceleration, 40 mph braking, handling 5, payload 850.
- `bike`: 9 damage, 2 armour, 110 mph max speed, 40 mph acceleration, 40 mph braking, handling 6, payload 300.

These values are stored in `data/rules/vehicles.json`.

Source pages: core pp. 81, 83.

## Mount Model

Vehicle templates must expose explicit mount ids rather than a count only. Shooting uses these ids for fire corridors and linked groups, Damage uses them for target-matrix component hits, and Campaign uses them for repair/re-equipment.

Mount fields:

- `id`: stable mount id.
- `kind`: `ordinary`, `passive`, `turret`, `cupola`, `pintle`, `outrigger`.
- `location`: physical/target location such as `hood`, `roof`, `leftWing`, `rightSide`, or `passiveLeft`.
- `allowedWeaponClasses`: weapon classes accepted by the mount.
- `allowedFacings`: normally `front`, with WLF rear-facing exceptions.
- `capacity`: one weapon unless the mount has a special rule.
- `fireCorridorProfile`: corridor profile consumed by Shooting.

Core mount rules:

- Bikes have left and right front fairing mounts plus one passive mount. Fairing mounts take lightweight weapons only.
- Lightweight weapons can be mounted on cars but count as medium weapons for car fitting.
- Renegades have hood, roof, left wing, right wing, and one passive mount.
- Interceptors have hood, roof, left wing, right wing, left side, right side, and two passive mounts.
- Passive mounts accept passive weapons only, one passive per mount.
- Cars may add one turret.
- A turret can hold one heavy weapon or two medium weapons.
- Heavy weapons fit only on hood, roof, turret, or side mounts. A Renegade has no side mounts, so heavy weapons on a Renegade are limited to hood, roof, or turret.
- Heavy weapons cannot be fitted to car wings.
- Fixed core weapons are forward firing.
- Turrets cannot mount missile launcher tubes in the core rules.

White Line Fever mount rules:

- Rear hard points add rear-left wing, rear-centre tailgate, and rear-right wing hard points to Renegades and Interceptors.
- Rear hard points have no cost or weight.
- Each rear hard point carries one medium or heavy weapon. Lightweight car weapons still count as medium for fitting.
- Renegade rear-wing hard points are rear-facing only.
- Interceptor rear-wing hard points can face front or rear.
- Tailgate hard points are rear-facing only.
- A tailgate gun cannot be combined with a rear-facing roof gun.
- If two medium weapons share a hard point, both face the same direction.
- Cupola and pintle mounts are crewed mount types. The proofread WLF table gives cupola cost 10000/weight 200 and pintle cost 6000/weight 100. Weight includes the tail gunner; the additional crewman costs 5000. Cupola is cars only. Turret fire computers can control turret or cupola non-missile weapons, but not pintle weapons; when a turret fire computer controls a cupola weapon, the gunner operates it rather than the driver. Turret-mounted missile pods require missile fire computers. The Interceptor tailgate-weapon blind spot for turret, cupola, and pintle mounts is diagram-defined and must be represented as grid geometry.
- Outrigger mounts are bike-only and conflict with crash bars.

Source pages: core pp. 81, 83; WLF pp. 12-14, 43.

## Linking Weapons

Linking is a design-time relation between installed weapons.

Rules:

- Linking has no cost.
- Linked weapons must be identical weapon ids.
- Linked weapons must face the same direction.
- Turret-mounted weapons cannot be linked with non-turret weapons.
- Front-facing and rear-facing weapons cannot be linked together.
- When a linked group fires, all weapons in the group fire and all spend ammunition as Shooting defines.
- There is no stated maximum linked-group size except mount availability and legality.

Source pages: core p. 81; WLF pp. 14-15.

## Weapons and Ammunition

Weapon data overlaps with Shooting and Damage. This section owns design/install metadata: cost, weight, class, reload costs, double-load facility, sanctioned/black-market flag, and ammo compatibility. `weapons-draft.json` owns hit accuracy/range/damage details until the Rules Lead merges them.

Core weapons include:

- Heavy: chain gun, 40mm grenade launcher, heavy laser, missile pod.
- Medium: 6mm machine gun, 15mm autocannon, 20mm grenade launcher, combat laser.
- Passive: spike layer, pattern mine layer, smoke layer, oil layer.
- Lightweight: 4.2mm machine gun, lightweight 20mm grenade launcher, lightweight combat laser, 40mm RAG launcher tube.
- Lightweight passives: spike layer, pattern mine layer, smoke layer, oil layer.

White Line Fever adds or changes:

- Minigun as a lightweight weapon.
- Special ammunition for eligible weapons.
- Missile types.
- Reload rows distinct from starting weapon cost.
- Outlaw black-market surcharge for sanctioned items.
- Double-load facilities for listed weapons only.

Proofread missile loadout rows:

- shaped plastic missile: cost 5000, weight 30.
- cannister missile: cost 10000, weight 30.
- smoke missile: cost 2000, weight 30.
- TGSM missile: cost 12500, weight 30.

A basic weapon purchase includes one single load of ordinary ammunition unless the weapon is a laser or another non-ammunition system. Reloads and special ammunition must be represented as ordered magazine entries. Every special shot loaded into a magazine replaces one ordinary shot; it does not increase capacity.

Source pages: core pp. 81, 84-85; WLF pp. 27-32, 43.

## Engines and Chassis

Advanced design cars choose a vehicle type and engine size:

- Renegade V6: cost 20000, weight 1000.
- Renegade V8: cost 35000, weight 1000.
- Renegade V12: cost 60000, weight 1000.
- Interceptor V6: cost 50000, weight 1000.
- Interceptor V8: cost 70000, weight 1000.
- Interceptor V12: cost 90000, weight 1000.

WLF text says engine/chassis weight remains 1000 regardless of engine size; power-to-weight tables determine final movement characteristics.

The WLF p. 17 OCR line for Interceptor V12 reads `vi2 $30,000`; the WLF p. 41 example and p. 42 summary indicate 90000. The data uses 90000 and marks the OCR conflict.

Source pages: WLF pp. 17, 41-42.

## Engine Add-Ons

### Charger

A charger may be fitted to any vehicle and any power plant. Only one charger may be fitted. It increases acceleration by 4 mph and maximum speed by 16 mph. It works with the engine and stops working if the engine is disabled.

Design data: cost 5000, weight 0.

Source page: WLF p. 17.

### Nox

Nox may be fitted to any vehicle. It is switched on using an accelerate action that cannot be part of a dual action. While active, acceleration is doubled and maximum speed is increased by 40 mph for cars or 10 mph for bikes. At the end of each phase in which it is used, roll 2d6 for explosion risk.

Base explosion rolls: 2 or 12. With a charger: 2, 11, or 12. With active oil injection smoke: 2, 3, or 12. With both: 2, 3, 11, or 12. On explosion, resolve the exploding-engine critical effect and disable the engine regardless of critical result.

It is switched off using a brake action that cannot be part of a dual action; the vehicle must reduce speed by at least 5 mph and no Nox explosion roll is made for that phase.

Design data: cost 2000, weight 0.

Source page: WLF p. 17.

### Oil Injection

Oil injection is an engine add-on that behaves like a smoke layer but does not use a passive mount and has effectively unlimited shots. It can be switched and locked on/off through Shooting. It reduces acceleration by 2 mph and maximum speed by 4 mph.

Design data: cost 2000, weight 0.

Source page: WLF p. 18.

## Driving Systems

### Active Suspension

Active suspension is car-only. It increases handling by 2. The bonus is lost if the system is disabled.

Design data:

- Renegade: cost 8000, weight 30.
- Interceptor: cost 12000, weight 40.

Source page: WLF p. 20.

### Robotic Drive

Robotic drive requires active suspension. It can be bought as a complete system including active suspension, or later as an upgrade. The final handling bonus is +3; the separate active suspension +2 is not added on top. It stops working if active suspension is disabled.

Design data:

- Renegade complete: cost 12000, weight 50.
- Renegade upgrade: cost 7000, added weight 20.
- Interceptor complete: cost 15000, weight 60.
- Interceptor upgrade: cost 10000, added weight 20.

Source page: WLF p. 20.

### Drag Chute

Drag chutes do not occupy passive mounts. Design data: any vehicle, cost 3000, weight 20.

Rules-side effects belong to Shooting/Hazards: released with a shoot action, may fail on a natural 1, decelerates by 30 mph per move down to 60 mph, remains represented by a marker, creates shooting penalties, and forces a hazard roll for vehicles colliding with it above a 10 mph safety limit.

Source page: WLF p. 20.

### Bike Drive Systems

WLF lists bike-specific systems:

- `twoWheelDrive`: handling +1, braking +10 mph.
- `computerDrive`: handling +1, acceleration +5 mph, braking +5 mph.

The proofread WLF table gives `twoWheelDrive` cost 3000/weight 0 and `computerDrive` cost 2000/weight 0.

Source page: WLF p. 42.

### Rocket Boosters

Rocket boosters are car equipment mounted in passive weapon spaces. Interceptors have two passive mounts and therefore use the twin-rocket system with 36 shots; Renegades have one passive mount and use a single booster with 24 shots. Bikes may not be fitted with rocket boosters. Boosters have cruise/pulse modes. They can exceed normal maximum speed temporarily; after use, speed decays back toward normal maximum at 5 mph per phase. If the booster passive-space system is critically hit, it is disabled; linked twin boosters are disabled as a pair, and an exploding booster applies an additional +8HE hit plus a 30 mph hazard roll.

Design summary rows:

- Single booster: cost 30000, weight 150.
- Twin booster: cost 45000, weight 225.

Engine owns pulse/cruise/off tactical actions from WLF p. 22. Damage Agent owns booster critical explosion effects and disabled twin-pair consequences.

Source pages: WLF pp. 22-23, 42.

## Armour

Core mode uses one armour value for all facings. Advanced mode records armour separately by facing and material.

Facings:

- `front`
- `rear`
- `leftSide`
- `rightSide`
- `floor`
- `roof`

Materials:

- `carbonSteel`
- `carbonPlastic`

Rules:

- Standard core armour is carbon steel unless converted.
- WLF permits adding, removing, and converting armour by facing.
- Car armour may not exceed 6 on any facing.
- Bikes have lower caps: side facings 4, roof 3, front/rear/floor 6.
- Carbon plastic is lighter and retains full value against AP hits.
- Damage owns AP armour handling.

Proofread status:

- WLF p. 42 armour cost/weight rows are captured in `data/rules/wlf-vehicle-tables-proofread.json`.
- The WLF p. 41 worked example confirms that adding 2 carbon-steel armour points to all Interceptor facings costs 16000 and weighs 320.

Source pages: WLF pp. 24-26, 41-42.

## Fire-Control Computers

Fire-control computers are design equipment with weight 0 and cost 10000.

Types:

- `turretFireComputer`: controls turret or cupola non-missile weapons; cannot control pintle weapons or turret-mounted missile pods.
- `missileFireComputer`: controls missile pods, including turret-mounted missile pods.

Shooting owns modes, targeting, timing, and hit modifiers. Vehicle Design owns installation, compatibility, and record-sheet fields for current mode/designated target.

Source pages: WLF pp. 34-36, 43.

## Safety Devices

### Crash Bars

Crash bars are bike-only and cannot be combined with outrigger mounts. They reduce side-hit damage from a bike roll, crash, or collision. They are the only safety device allowed on bikes.

Design data: cost 500, weight 0.

Source page: WLF p. 37.

### Crash Suppression System

Car-only safety system. It gives a saving throw against driver critical hits caused by crashes or rolls. The roll is 2d6 and succeeds if the total is equal to or greater than the vehicle's current speed factor. Passenger cages may also apply to the same driver critical when both are fitted.

Design data: cost 5000, weight 10.

Source page: WLF p. 37.

### Ejector Seat

Car-only safety device. It can be fired with a shoot action, and it is the only action allowed while the vehicle is out of control. Declare before moving the car and before control-loss tests. The driver escapes, the vehicle enters no-driver state, and later driver critical results are rerolled.

Design data: cost 7500, weight 30.

Source page: WLF p. 37.

### Passenger Cage

Car-only safety device. It gives a d6 save against any driver critical hit. Even rolls cancel the driver critical; odd rolls do not. If a crash suppression system is also fitted and the critical came from a crash or roll, both saving throws can apply.

Design data: cost 5000, weight 30.

Source page: WLF p. 37.

## Record Sheet Fields

Vehicle records need these fields:

- vehicle id, template/chassis id, vehicle type, owner side.
- engine size and active engine add-ons.
- total cost, total weight, design mode.
- damage max/current and applied damage increments.
- maximum speed, acceleration, braking.
- handling split into `nonHeHandling` and `heHandling` for WLF advanced rules.
- armour by facing and material.
- mounts with installed item ids, facing, linked group id, ammunition/magazine queue, current shots, disabled/destroyed state.
- passive mounts and markers supported by installed passives.
- fire-control computer modes and designated target.
- safety devices and one-use/jettisoned state.
- invisible notes such as reinforced tyres or computer-drive support.
- campaign state: damaged components, repair cost/time state, salvage flag, re-equipment eligibility, and post-engagement mileage/ownership.

Source pages: WLF pp. 41, 44; Dead Man's Curve dependencies in `docs/rules/clean/campaign.md`.

## Campaign Repair and Re-Equipment Dependencies

Campaign must be able to inspect installed equipment and component damage.

Required handoff fields:

- item cost for replacement and salvage valuation.
- item weight for revalidation after refit.
- whether the item is sanctioned/black-market.
- whether an Outlaw surcharge applies.
- whether item is destroyed, disabled, expended, jettisoned, or repairable.
- crew dependency for cupola/pintle/tail-gunner systems.
- ammunition inventory and magazine order.
- armour material and facing points after damage/repair.

Re-equipping a campaign vehicle must rerun vehicle design legality checks after each change.

## Required Engine Behaviours

- Validate installed item ids and mount ids against `vehicles.json` and `equipment.json`.
- Reject overweight core-payload designs.
- Reject advanced designs over the engine's maximum supported total weight.
- Reject heavy weapons on car wings.
- Reject ordinary weapons in passive mounts and passives in ordinary mounts.
- Reject non-lightweight weapons on bike fairing mounts unless a Bikes/Three-Wheelers rule explicitly permits otherwise.
- Reject missile pods in core turrets.
- Reject illegal rear-facing combinations and illegal linked groups.
- Apply car lightweight weapons as medium class for mount capacity.
- Calculate total cost and total weight from chassis, armour, systems, weapons, ammunition, mounts, and safety devices.
- Apply Outlaw surcharge to sanctioned items where campaign context requires it.
- Keep magazine order explicit for mixed ammunition loads.
- Preserve source references and `needsProofread` flags in validation messages.

## Data Extracted

- Vehicle templates, core stats, mounts, chassis/engine entries, design modes, and record fields: `data/rules/vehicles.json`.
- Engine add-ons, driving systems, mount upgrades, armour material metadata, weapons/install rows, ammunition, fire-control computers, safety devices, and double-load facilities: `data/rules/equipment.json`.

## Ambiguities and OCR Doubts

- Core p. 82 is mostly OCR noise and appears to be a record sheet or visual material. No mechanical rule was extracted from it.
- WLF p. 17 OCR reads Interceptor V12 as `$30,000`; WLF p. 41 example and p. 42 table support `$90,000`.
- Remaining vehicle-design blockers are maintained in `docs/rules/implementation-blockers.md`: minigun identity/calibre alignment, TGSM tactical submunition tables, and detailed cupola/pintle behaviour.
- WLF p. 43 several weapon/reload rows are OCR-damaged. Confirm against page image before final economy/campaign coding.

## Candidate Tests

### Core Templates

- Renegade template loads with damage 18, armour 3, max speed 100, acceleration 20, braking 30, handling 4, payload 650.
- Interceptor template loads with six ordinary mounts and two passive mounts.
- Bike template loads with two lightweight fairing mounts and one passive mount.

### Payload and Weight

- A core Interceptor design at exactly 850 fitted weight is legal.
- A core Interceptor design above 850 fitted weight is rejected.
- In advanced mode, chassis weight is included in total weight.
- The WLF p. 41 Odyssey 4 example totals 143500 cost and 2080 weight with the extracted rows.

### Mount Legality

- A heavy weapon on an Interceptor side mount is legal.
- A heavy weapon on an Interceptor wing mount is rejected.
- A heavy weapon on a Renegade roof mount is legal.
- A passive in an ordinary mount is rejected.
- An ordinary weapon in a passive mount is rejected.
- A missile pod in a core turret is rejected.
- A bike fairing rejects medium and heavy weapons.

### Linking

- Identical forward-facing wing autocannons can be linked.
- Different weapon ids cannot be linked.
- Front-facing and rear-facing weapons cannot be linked.
- A turret weapon cannot be linked to a fixed weapon.

### Add-Ons and Systems

- Only one charger can be installed.
- Charger adds +4 acceleration and +16 maximum speed while engine is functional.
- Nox doubles acceleration and adds the correct max-speed bonus while active.
- Nox plus charger expands explosion rolls to 2, 11, 12.
- Oil injection reduces acceleration by 2 and max speed by 4.
- Robotic drive as an upgrade requires active suspension.
- Robotic drive final handling bonus is +3, not active suspension +2 plus +3.

### Armour

- A car facing cannot exceed armour 6.
- Bike side armour above 4 is rejected.
- Armour by facing is recorded with material.
- Carbon plastic armour is flagged for Damage AP handling.

### Ammunition

- A basic non-laser weapon purchase includes one normal load.
- A special ammunition shot replaces one GP shot in magazine order.
- A mixed magazine keeps ordered entries.
- A weapon not listed in double-load data cannot receive a double-load facility.
- Double-load facility cost does not include extra reload cost.

### Safety Devices

- Crash bars are bike-only.
- Crash bars and outriggers cannot both be fitted.
- Ejector seats are car-only.
- Ejector seat use creates no-driver vehicle state.
- Passenger cage saves a driver critical on even d6.
- Crash suppression save succeeds when 2d6 is equal to or greater than current speed factor.

### Campaign

- Re-equipping after a campaign engagement reruns mount and weight validation.
- Destroyed installed equipment keeps original cost and weight for repair/salvage calculations.
- Outlaw purchase of a sanctioned item applies the configured surcharge.
