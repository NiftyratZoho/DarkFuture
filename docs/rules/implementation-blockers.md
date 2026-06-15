# Implementation Blockers

> Purpose: this is the working checklist for rulebook proofread notes that are still blocking a faithful implementation. Add comments under `User notes` as you verify the books, then update the relevant JSON or clean rules file.
>
> Status values:
> - `blocked`: cannot implement faithfully without the missing rule/table/diagram.
> - `partial`: playable behaviour exists, but the listed rule detail is not faithful yet.
> - `data-ready`: proofread data exists but still needs code integration.
> - `resolved`: no longer blocking.
>
> Blocker types:
> - Rule unclear/readability issue: the source wording is ambiguous, damaged, or needs a rules decision before transcription or coding.
> - Structured transcription needed: the rule text/table is readable, but it still needs to be converted into structured rows or clean-rule procedure.
> - Diagram/grid tracing needed: the prose is readable, but exact visual geometry, layouts, cells, or templates must be traced from diagrams or track pieces.
> - Code implementation missing: the rule/data is clear enough for implementation, but engine/campaign/tactical code still needs to consume it.

## Vehicle Design and Equipment

### VD-001 Rear hardpoint cost/weight rows

- Status: `resolved`
- Source to check: White Line Fever pp. 12 and 43.
- Data rows: `data/rules/equipment.json` mount upgrades `rearLeftWing`, `tailgate`, `rearRightWing`.
- Missing information: none. User proofread confirmed rear hard points have no cost or weight.
- Blocks implementation: no longer blocks vehicle design or campaign purchase/fitting for these mounts.
- Current code behaviour: rear hardpoints are zero-cost/zero-weight campaign items.
- User notes: hard points have no costs or weights for cars there are 3 one on the rear left, one on the rear right and one in the centre. 
- Implementation notes: updated `data/rules/equipment.json`; campaign purchase and fit tests now cover `tailgate`.

### VD-002 Rear hardpoint mount rules

- Status: `resolved`
- Source to check: White Line Fever pp. 12-13.
- Data rows: same as VD-001, plus `docs/rules/clean/shooting.md` rear fire corridors.
- Missing information: none for design legality. Interceptor turret/cupola/pintle blind-spot geometry is tracked separately in VD-006/SH notes.
- Blocks implementation: no longer blocks vehicle design or linked weapon validation.
- Current code behaviour: rear hardpoint upgrades install as one-weapon ordinary mounts. Each accepts one medium or heavy weapon; car lightweight weapons still count as medium. Renegade rear wings are rear-facing only; Interceptor rear wings can face front or rear; tailgate is rear-facing only.
- User notes:all of these can take on heavy or one medium weapon. Note that renegades are all rear facing for interceptor the rear left and rear right wing mounts can be forward or rear facing.  as per page 13 the text contains hit roll penalties on tailgate or roof -1 on side or wing mounted weapons -2 to hit
- Implementation notes: updated `data/rules/equipment.json`, `dark_future/vehicle_design.py`, and vehicle design tests. The shooting modifier rows already contain the `-1` and `-2` penalties.

### VD-003 Missile ammunition proofread

- Status: `resolved`
- Source to check: White Line Fever pp. 28-29 and 43.
- Data rows: `data/rules/equipment.json` ammunition types `missile.cannister`, `missile.smoke`, `missile.tgsm`; `missile.shapedPlastic` is cost/weight-present but still marked for proofread.
- Blocker type: none.
- Missing information: none for missile ammunition tables listed here.
- Blocks implementation: no longer blocked.
- Current code behaviour: missile shaped plastic, cannister, smoke, and TGSM all have proofread cost/weight rows for loadout design. TGSM now stores and exposes the D6 submunition-count table plus D6 hit-location table for tactical resolution after a successful standard missile accuracy check.
- User notes: Cannister  cannot be fired in a turn after a hazard roll or manoeuver. hits an entire track section automaticallly damaghe +3 and damage is on roof. cost $10k and weighs 30.  Shaped plastic is weight 30 and cost 5,000 per missile. smoke lands on  the 6th space away from the firer and fills 6 spaces and 4 lanes wide. its persistant and doesnt clear. if a missile fire computer is used it is any space at least 2 spaces away up to the 6th at the choice of the firer. , cost 2000, weight 30. TGSM cost 12,500 and weight 30 with +4 asccuracy and +4 damaHE for each sub munitioion which there is a table to determine the number after it hgas already gone through a standard accuracy check for a missile. with a dice roll to determine where it hits in a specific table on page 29 of the rules.
- Implementation notes: updated `data/rules/equipment.json`; missile reload tests cover cannister, smoke, and TGSM design loadout.

### VD-004 Minigun identity and double-load weight

- Status: `partial`
- Source to check: White Line Fever p. 43.
- Data rows: `data/rules/equipment.json` `minigun62mm`; `data/rules/wlf-vehicle-tables-proofread.json` `minigun7_62mm`.
- Blocker type: rule unclear/readability issue limited to name/calibre/id confirmation.
- Missing information: confirm weapon name/calibre/id alignment only.
- Blocks implementation: no longer blocks minigun purchase, ammo, or double-load facility in the current backend.
- Current code behaviour: minigun double-load uses +75 added weight.
- User notes:  +75 weight
- Implementation notes: updated `data/rules/equipment.json`, `data/rules/wlf-vehicle-tables-proofread.json`, and vehicle design tests.

### VD-005 Rocket booster critical and damage effects

- Status: `resolved`
- Source to check: White Line Fever pp. 22-23 and 42.
- Data rows: `rocketBoosterSingle`, `rocketBoosterTwin`.
- Missing information: none for passive-space targeting or booster critical effects.
- Blocks implementation: no longer blocks rocket booster tactical/damage integration at current engine fidelity.
- Current code behaviour: pulse/cruise/off tactical actions are implemented from WLF p. 22, including the pulse table, 24-shot single boosters, 36-shot twin boosters, shot expenditure, cruise minimum, cruise speed lock, acceleration/braking lockout, and 5 mph per phase decay after boosters turn off above normal max. Booster criticals disable the passive-space booster system; linked Interceptor twin boosters disable as a pair; exploding boosters apply an additional +8HE hit and a 30 mph hazard roll.
- User notes: rocket boosters replace passive weapons in a vehicle and should be hit when the damage roll is the same as it would be for a passive weapon.
- Implementation notes: WLF p.22 page image is readable. Updated `data/rules/equipment.json`, `dark_future/engine.py`, and tests.

### VD-006 Cupola/pintle detailed behaviour

- Status: `partial`
- Source to check: White Line Fever pp. 34 and 43.
- Data rows: `cupola`, `pintle`, `turretFireComputer`.
- Blocker type: diagram/grid tracing needed for the Interceptor blind spot.
- Missing information: none for text rules. The Interceptor tailgate/turret/cupola/pintle blind spot is diagram-defined and needs grid-cell encoding.
- Blocks implementation: final Interceptor blind-spot grid integration.
- Current code behaviour: proofread cost/weight and $5,000 extra crewman data are available; basic design mount support exists; turret fire computers are restricted to turret/cupola non-missile weapons and excluded from pintles; cupola fire-computer operation is recorded as tail-gunner operated.
- Implementation notes: WLF p.34 confirms turret fire computers can control cupola-mounted weapons but not pintle-mounted weapons; when controlling a cupola-mounted weapon, it must be operated by the gunner, not the driver. Turret-mounted missile pods require missile fire computers. WLF p.43 confirms cupola cars-only `$10,000`/200, pintle `$6,000`/100, and that mount weight includes the tail gunner while the additional crewman costs `$5,000`. WLF p.13 gives the Interceptor blind-spot diagram for tailgate weapon plus turret/cupola/pintle; implement as a diagram-derived grid mask.
- User notes:

## Track Geometry and Movement

### TG-001 Curve lane-link atlas

- Status: `partial`
- Source to check: physical track pieces, trace images, Dark Future pp. 13-14.
- Data rows/docs: `docs/rules/clean/curve-atlas-trace-plan.md`, `docs/rules/clean/track-geometry.md`.
- Blocker type: diagram/grid tracing needed.
- Missing information: exact curve contact zones, edge contacts, lateral sideswipe zones, and U-turn sweep cells for each lane/space on 90-degree corners and 60-degree bends. Ordinary forward movement and outward-drift lane links are no longer blocked.
- Blocks implementation: exact curve contact, sideswipe, crash, and U-turn edge checks.
- Current code behaviour: procedural 90-degree and 60-degree curves preserve lane count/section counts/speed limits. Curve forward movement follows the lane pair. Voluntary curve drift is outward only while staying on the curve; the drift resolves after the forward move onto the next outward space line. Curve-to-straight drift may go either way after entering the straight. Contact-zone geometry remains conservative.
- User notes: Curve movement is rules-derived: drift outward only while on curves, drift either way after moving from curve to straight, and drifting into another car is a ram/sideswipe rather than legal passage.

### TG-002 U-turn contact template near curves

- Status: `partial`
- Source to check: Dark Future pp. 13-14 and U-turn diagrams.
- Blocker type: diagram/grid tracing needed.
- Missing information: exact six-lane swept contact cells when a vehicle starts or ends a U-turn on/near a curve. The six-lane width and curve-edge legality are readable; exact cells depend on the curve atlas.
- Blocks implementation: curve-edge U-turn resolution.
- Current code behaviour: curve-edge/adjacent-to-curve U-turns are rejected rather than guessed.
- User notes:

### MV-001 Bootlegger reverse failure result

- Status: `partial`
- Source to check: Dark Future movement table/diagram around bootlegger reverse.
- Blocker type: diagram/grid tracing needed for final positions.
- Missing information: final-position diagram coordinates. The 2-3 failure aftermath, forced next phase-1 reverse move, tyre critical at 0 damage, and collision wording are readable.
- Blocks implementation: faithful bootlegger failure chain.
- Current code behaviour: only non-ambiguous manoeuvre/hazard effects are implemented.
- User notes:

### MV-002 Bulldozer result and displacement

- Status: `resolved`
- Source to check: White Line Fever p. 8.
- Blocker type: none.
- Missing information: none for the implemented text rule.
- Blocks implementation: no longer blocked.
- Current code behaviour: bulldozer is available to cars at 20 mph or less when the next space contains a stationary unaligned vehicle; the target is displaced two lane pairs, aligned to the grid, and both vehicles take a single low-damage hit with no critical roll.
- Implementation notes: WLF p.8 is readable. Implement prerequisites, target alignment, two-lane push, single -1 damage hit to both vehicles, ignore criticals, and fallback to ram/head-on cases.
- User notes:

## Hazards and Control Loss

### HZ-001 Safety-limit summary table

- Status: `data-ready`
- Source to check: Dark Future p. 38.
- Data rows: `data/rules/hazard-results.json` rows marked `needsProofread`.
- Blocker type: code implementation missing for systems that do not yet consume the confirmed thresholds.
- Missing information: none for the reviewed table values.
- Blocks implementation: final hazard thresholds for systems not yet wired into gameplay.
- Current code behaviour: page image review confirmed debris 10 mph, U-turn 10 mph, bike overlap/dodge values, and broken axle 40 mph. Data rows updated where present.
- User notes:

### HZ-002 U-turn lower safety limit

- Status: `resolved`
- Source to check: Dark Future pp. 38 and 40.
- Missing information: none.
- Blocks implementation: no longer blocked.
- Current code behaviour: 0-10 mph safe, 11-30 mph completes with hazard roll, above 30 mph causes control-loss handling.
- Implementation notes: DF p.38 table confirms 10 mph safety limit; DF p.40 confirms 31+ immediate control-loss test.
- User notes:

### HZ-003 Skid and spin templates

- Status: `partial`
- Source to check: Dark Future skid/spin result diagrams.
- Blocker type: diagram/grid tracing needed.
- Missing information: exact spin-template result positions/speed reductions and realignment coordinates. Skid procedure, spin process, collision handling, rolling, and re-alignment text are readable.
- Blocks implementation: faithful control-loss movement.
- Current code behaviour: playable control-loss effects exist, but exact skid/spin templates are not traced.
- User notes:

### HZ-004 Passive marker exception

- Status: `resolved`
- Source to check: Dark Future passive hazard text.
- Missing information: none. It is not a specific passive weapon type; the exception is a passive marker dropped directly under a tailgating pursuer.
- Blocks implementation: no longer blocks passive marker lifecycle at current engine fidelity.
- Current code behaviour: passive markers test on entry. If a passive marker is dropped directly under a tailgating pursuer, the marker records that vehicle and resolves when that specific vehicle moves off the marker space.
- Implementation notes: updated `PassiveMarker` state, drop-marker tailgater detection, move-off marker checks, save/load compatibility, and engine regression tests.
- User notes:

## Shooting and Weapons

### SH-001 Missile pod accuracy

- Status: `resolved`
- Source to check: Dark Future p. 27 weapon table.
- Data rows: `data/rules/weapons-draft.json` `missile-pod`.
- Missing information: none.
- Blocks implementation: no longer blocked.
- Current code behaviour: missile pod accuracy is marked proofread as `+2`.
- Implementation notes: DF p.27 page image is readable; updated `data/rules/weapons-draft.json`.
- User notes:

### SH-002 Fire corridor diagrams on curves

- Status: `partial`
- Source to check: Dark Future shooting diagrams and curve track diagrams.
- Blocker type: diagram/grid tracing needed.
- Missing information: exact line/corridor projection across curve geometry, including phosphor and missile smoke templates.
- Blocks implementation: faithful shooting on curves and persistent smoke corridors.
- Current code behaviour: straight/adjacent corridor and smoke blocking are playable; curve template placement is not final.
- User notes:

### SH-003 Linked-weapon cool test wording

- Status: `resolved`
- Source to check: Shooting linked weapons section.
- Data rows: `data/rules/shooting-modifiers.json` linked weapon cool test.
- Missing information: none.
- Blocks implementation: no longer blocked.
- Current code behaviour: data uses `roll < driveSkill`; equality fails.
- Implementation notes: WLF p.15 is readable; updated `data/rules/shooting-modifiers.json`.
- User notes:

## Rams, Crashes, and Damage

### RC-001 Sideswipe draw hazard handling

- Status: `blocked`
- Source to check: Dark Future rams/crashes sideswipe text.
- Data rows: `data/rules/ram-types.json`.
- Blocker type: rule unclear/readability issue requiring a rules decision.
- Missing information: damage-on-draw wording is readable, but hazard-on-draw timing remains under-specified and needs a rules decision before exact implementation.
- Blocks implementation: exact sideswipe aftermath.
- Current code behaviour: conservative/playable ram handling is implemented.
- User notes:

### RC-002 Ram damage facing mapping

- Status: `partial`
- Source to check: Rams/crashes damage text and target matrices.
- Blocker type: structured transcription needed for ram-facing mapping.
- Missing information: crash facing is readable; ram facing still needs final mapping for head-on, shunt, sideswipe, and T-bone damage requests.
- Blocks implementation: faithful armour-facing damage from rams.
- Current code behaviour: ram damage exists, but final facing-specific mapping needs proofread.
- User notes:

### DM-001 Tyre destroyed maximum-speed wording

- Status: `resolved`
- Source to check: Dark Future p. 34.
- Missing information: none.
- Blocks implementation: no longer blocked.
- Current code behaviour: tyre destroyed applies handling -2, caps maximum speed to the slower of current max minus 10 mph and 60 mph, and reduces current mph to the new cap.
- User notes:

## Campaign and Scenarios

### CP-001 Campaign starting funds and outlaw setup

- Status: `resolved`
- Source to check: White Dwarf 124 p. 18.
- Missing information: none for starting funds/free driver setup.
- Blocks implementation: no longer blocks campaign creation data.
- Current code behaviour: data now records `$100,000` starting funds, free first drive-skill 2 Op driver, free first two drive-skill 2 outlaw drivers, and vehicles/equipment bought from funds.
- User notes:

### CP-002 Approach and encounter tables

- Status: `partial`
- Source to check: White Dwarf 124 pp. 20-22.
- Data rows: `data/rules/campaign-sequence.json`, `data/rules/scenarios.json`.
- Blocker type: structured transcription needed.
- Missing information: page images are readable enough for extraction, but drive-skill bonus threshold/table, approach result bands, intercept/pursuit/ambush setup details, and exception wording for failed objectives still need structured transcription.
- Blocks implementation: faithful campaign-to-tactical contract generation.
- Current code behaviour: scenario cycling and settlement exist as playable approximations.
- User notes:

### CP-003 Loot and bounty table proofread

- Status: `partial`
- Source to check: White Dwarf 124 pp. 26 and 29.
- Blocker type: structured transcription needed.
- Missing information: page images are readable enough for extraction, but loot success number/restrictions and leader modifier table still need structured transcription.
- Blocks implementation: final loot phase.
- Current code behaviour: bounty table is implemented from OCR-marked data; loot is simplified.
- User notes:

### CP-004 Disorders, eccentricity, and psychosis tables

- Status: `partial`
- Source to check: White Dwarf 124 pp. 30-31 and White Dwarf 125 p. 69.
- Blocker type: structured transcription needed.
- Missing information: page images are readable enough for extraction, but disorder rows, eccentricity rows, recovery clauses, and exact psychosis point effects need structured table transcription.
- Blocks implementation: full driver long-term campaign state.
- Current code behaviour: driver state fields exist, but random disorder/eccentricity generation is not implemented.
- User notes:

### CP-005 Agency formation and driver generation

- Status: `partial`
- Source to check: White Dwarf 125 p. 72.
- Blocker type: structured transcription needed for driver generation rows.
- Missing information: agency formation cost is resolved as `$10,000`; driver generation table rows still need structured transcription.
- Blocks implementation: full agency upgrade/recruitment workflow.
- Current code behaviour: campaign sequence data records the agency formation cost; novice and experienced-driver stubs exist.
- User notes:

### CP-006 Hacking and system hostility

- Status: `resolved`
- Source to check: White Dwarf 125 p. 75.
- Blocker type: none.
- Missing information: none for the hostile-system summary now captured.
- Blocks implementation: no longer blocked.
- Current code behaviour: tactical hostile-system effects are data-driven from `data/rules/campaign-sequence.json`; hostile robotic/computer drive changes handling, acceleration, and braking, and hostile missile/turret fire computers force friendly-only targeting.
- User notes:

### SC-001 Scenario diagram setup

- Status: `partial`
- Source to check: Dark Future core scenarios pp. 86-89 and WLF scenario diagrams.
- Data rows: `data/rules/scenarios.json`.
- Blocker type: structured transcription needed for setup rows; diagram/grid tracing needed for deployment sections and track layouts.
- Missing information: many setup diagrams are readable from page images, but shaded deployment sections, exact diagram track layouts, and setup rows still need structured scenario transcription.
- Blocks implementation: faithful scenario-specific tactical start layouts.
- Current code behaviour: intercept, ambush, and pursuit have playable setup patterns.
- User notes:

### SC-002 Outdistancing victory rule

- Status: `blocked`
- Source to check: Dark Future core p. 89.
- Blocker type: rule unclear/readability issue.
- Missing information: numeric distance/exit rule for outdistancing.
- Blocks implementation: faithful scenario victory in the relevant core scenario.
- Current code behaviour: pursuit/outlaw escape uses current playable convention.
- User notes:

## Bikes and Three-Wheelers

### BK-001 Lightweight RAG accuracy

- Status: `resolved`
- Source to check: White Line Fever bike/weapon tables.
- Data rows: `data/rules/bikes-three-wheelers.json`.
- Missing information: none.
- Blocks implementation: no longer blocked.
- Current code behaviour: 40mm RAG launcher tube is range 12, accuracy 0.
- User notes:

### BK-002 Trike and sidecar target matrices

- Status: `resolved`
- Source to check: White Line Fever three-wheeler target matrix tables.
- Data rows: `data/rules/bikes-three-wheelers.json`.
- Blocker type: none.
- Missing information: none for the supplied trike and motorcycle-combination target matrices.
- Blocks implementation: no longer blocked.
- Current code behaviour: trike and motorcycle-combination target matrices are structured by attack arc and D6 component ranges.
- User notes:

## Resolved In This Pass

- Status: `resolved`
- Source: `data/rules/wlf-vehicle-tables-proofread.json`.
- Items unblocked and pushed into `data/rules/equipment.json`:
  - `twoWheelDrive`: cost 3000, weight 0.
  - `computerDrive`: cost 2000, weight 0.
  - `rocketBoosterSingle`: cost 30000, weight 150.
  - `rocketBoosterTwin`: cost 45000, weight 225.
  - `crashBars`: cost 500, weight 0.
  - `crashSuppressionSystem`: cost 5000, weight 10.
  - `cupola`: cost 10000, weight 200.
  - `pintle`: cost 6000, weight 100.
  - `outrigger`: cost 5000, weight 0.
  - Rocket booster pulse/cruise/off tactical effects from WLF p. 22.
  - Rocket booster ammunition ratings: single 24 shots, twin 36 shots.
  - Rocket booster passive-space targeting, disabled-pair behaviour, exploding +8HE hit, and 30 mph hazard roll.
  - `rearLeftWing`, `tailgate`, `rearRightWing`: cost 0, weight 0, one medium/heavy weapon with proofread facings.
  - `missile.shapedPlastic`: cost 5000, weight 30.
  - `missile.cannister`: cost 10000, weight 30, automatic track-section roof hit data captured.
  - `missile.smoke`: cost 2000, weight 30, persistent 6-space/4-lane smoke corridor data captured.
  - `missile.tgsm`: cost 12500, weight 30, +4 accuracy and +4 HE per submunition recorded; p. 29 submunition tables still outstanding.
  - `minigun62mm` double-load additional weight: 75.
  - Missile pod accuracy: +2.
  - Linked-weapon cool test: d6 roll must be lower than drive skill.
  - U-turn safety limit: 10 mph; 31+ mph causes immediate control-loss test.
  - Hazard safety limit rows: debris 10 mph; bike overlap/dodge rows confirmed from DF p.38.
  - Tyre destroyed max speed: lower of current maximum minus 10 mph and 60 mph.
  - Campaign start data: `$100,000`, Op first driver free, outlaw first two drivers free, drive skill 2.
  - Agency formation cost: `$10,000`.
  - Hacking hostility summary: robotic drive, computer drive, missile fire computer, and turret fire computer.
  - Bike 40mm RAG launcher tube accuracy: 0.
