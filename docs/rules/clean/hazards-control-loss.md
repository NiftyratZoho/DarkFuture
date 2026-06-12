# Hazards and Control Loss

> Status: cleaned implementation draft  
> Owner: Hazards Agent  
> Source files: `docs/rules/core/08-hazards-control-loss-tests.md`, `docs/rules/white-line-fever/02-advanced-hazards.md`  
> Source pages: Dark Future Rulebook pp. 38-46; White Line Fever pp. 10-11

## Scope

This section defines when `hazardRoll`s are required, how hazard totals are calculated, what panic braking does, when `controlLoss` begins, how control-loss tests are resolved, and how skids, spins, and rolls are represented. It consumes movement, damage, passive weapon, and ram events; it does not own movement legality, damage resolution, passive-marker placement, or ram classification.

## Core Concepts

- A hazard is any event with a safety limit that may force a `hazardRoll`.
- A vehicle travelling at or below the applicable safety limit is safe from that hazard and does not roll.
- A vehicle travelling above the safety limit takes a `hazardRoll` unless it is already out of control.
- Vehicles that are out of control do not take further hazard rolls until they regain control.
- Hazard results can cause no effect, panic braking, or control loss.
- A vehicle that loses control keeps moving in the normal turn sequence but must resolve a `controlLoss` test before each subsequent move.
- Drivers of out-of-control vehicles cannot choose ordinary actions.

## Inputs From Other Sections

Hazard resolution needs these inputs from other agents:

- Turn Sequence: current `turn`, `phase`, activation order, and whether the vehicle has a move in the phase.
- Movement: current `mph`, `speedFactor`, braking already used this phase, declared manoeuvre, acceleration/braking changes, reverse movement, and whether the vehicle is on a curve.
- Track Geometry: curve safety limits, outside/inside lane for uneven curve spaces, contact zones, road-edge crash detection, and curve spin positioning.
- Shooting and Damage: passive hits, HE damage value, shattered screen, driver hurt/injured, tyre destruction, exploding weapon/engine/fuel tank, and any handling or driver skill changes before the hazard roll.
- Rams and Crashes: ram type, winner/loser where relevant, speed after impact, and post-ram hazard requirement.
- Vehicle Design: current handling, current braking, current driver drive skill, and vehicle type.

## Safety Limits

Each hazard source has a safety limit in mph. The engine should evaluate whether the vehicle's current `mph` exceeds the limit. Speeds exactly equal to the safety limit do not require a hazard roll.

Known safety-limit sources:

- Curves: use the printed safety limit for the curve lane. If a vehicle spans lanes with different curve limits, use the higher and therefore safer limit on the outside lane.
- Drift manoeuvre: hazard limit 80 mph.
- U-turn: U-turns at 0-10 mph are safe, 11-30 mph completes with a hazard roll, and above 30 mph automatically causes control loss before the U-turn move begins.
- Sideswipe:
  - neck-and-neck sideswipe: losers only test at 40 mph;
  - opposed sideswipe: winner tests at 40 mph, loser tests at 20 mph.
- Shunt: both vehicles test at 40 mph.
- Bike overlapping contact zones: neck-and-neck appears to use 80 mph; opposed appears to use 40 mph. Bike agent must confirm.
- Passive weapons:
  - oil on a straight-ahead move: 60 mph;
  - oil on any other move, including manoeuvres and curves: 30 mph;
  - pattern mines: 50 mph;
  - smoke: 60 mph.
- Random road hazards:
  - sand: 30 mph;
  - debris: 10 mph;
  - railroad crossing: 60 mph.
- HE and critical-hit hazards:
  - HE hit of +4 or less: 50 mph;
  - HE hit of +5 or more: 30 mph;
  - shattered screen: 30 mph;
  - tyre destroyed: 20 mph;
  - exploding weapon: 30 mph;
  - exploding engine: 50 mph;
  - exploding fuel tank: 30 mph;
  - driver hurt: 40 mph;
  - driver injured: 20 mph.

## Hazard Timing

Acceleration and braking actions change speed after the vehicle moves and before hazard rolls are made. Hazard rolls for curves, manoeuvres, and weapon hits are made just after each move, and their effects apply immediately.

Damage-triggered hazard rolls are made after damage is calculated and recorded. This means the roll can use reduced handling or reduced drive skill caused by the same hit.

Passive-weapon hazard rolls normally happen when the vehicle moves onto the passive marker. A vehicle does not retest simply for moving off that marker. One passive case is noted as an exception in the OCR, but the weapon identity is unclear and needs proofread.

Reverse moves ignore hazard rolls.

If a vehicle is hit during a phase in which it no longer has a move, any panic-brake result still changes speed immediately. The panic-braking allowance for those late-turn hits applies for the rest of the turn, not merely the current non-move activation.

## Multiple Hazard Rolls

A vehicle may encounter more than one hazard during the same move. Resolve required tests in descending safety-limit order. Oil tests are always resolved last.

After each panic-brake result, update `mph` immediately. If the speed reduction brings the vehicle to or below the safety limit for a later pending hazard, skip that later test.

If any hazard roll causes control loss, do not resolve further hazard rolls for that vehicle until the driver regains control.

## Optimum and Adverse Control

`optimumControl` is the higher of the vehicle's current handling and the driver's current drive skill.

`adverseControl` is the lower of the vehicle's current handling and the driver's current drive skill.

If handling is reduced to zero, the vehicle immediately loses control and adds +2 to later control-loss tests. A vehicle with no driver also immediately loses control and adds +2 to later control-loss tests. A vehicle with no driver cannot shoot.

The rulebook includes an advisory `optimumSpeed` concept: for a known safety limit and optimum control value, the safest aggressive speed is the highest speed where even a die roll of 6 still produces only a panic-brake result. This is useful for AI and UI previews, but it is derived from the hazard formula and does not need a separate rule table.

## Hazard Roll Procedure

To resolve a `hazardRoll`:

1. Roll 1d6.
2. Add `excessSpeedModifier`: +1 for each full or partial 10 mph by which `mph` exceeds the safety limit.
3. Subtract `optimumControl`.
4. Compare the final total to the hazard result table.

Hazard results:

- total 0 or less: no effect.
- total 1-4: panic brake.
- total 5 or more: control loss.

Example calculation to preserve as a test: a vehicle at 90 mph taking a +2 HE hit uses a 50 mph safety limit. With optimum control 4 and a die roll of 5, excess speed is +4, so the total is 5 and the vehicle loses control.

## Panic Braking

A panic-brake result reduces speed by `5 mph * hazardTotal`.

The speed reduction happens immediately. If another hazard roll follows in the same sequence, use the new speed.

A vehicle may not panic brake by more than its current braking characteristic within the relevant allowance window:

- during an ordinary phase, the allowance is the vehicle's current braking characteristic for that phase;
- any ordinary brake action already used in that phase reduces the remaining allowance;
- earlier panic braking in the same phase also reduces the remaining allowance;
- for late-turn hits against a vehicle that is not currently moving, the allowance is tracked across the rest of the turn.

If the required panic-brake amount exceeds remaining allowance, reduce speed by the remaining allowance and then apply control loss.

A driver forced to panic brake is distracted and cannot fire or use any other action for the rest of the phase. A panic-brake speed reduction can also lower `speedFactor` enough to remove a later move in the same turn.

Special ram rule: a panic-brake result is ignored for the target of a shunt ram and treated as no effect. The ramming vehicle still applies panic braking normally.

## Control Loss State

A vehicle enters `controlLoss` when:

- a hazard roll total is 5 or more;
- a panic-brake result cannot be fully paid from remaining braking allowance;
- a critical hit directly forces control loss;
- handling reaches zero;
- the vehicle has no driver;
- a U-turn is attempted above 30 mph.

While out of control:

- the vehicle remains in normal phase activation based on current speed;
- before each subsequent move, resolve a control-loss test unless the vehicle is already spinning under the spin-continuation rules;
- no ordinary actions may be chosen;
- no hazard rolls are taken;
- the vehicle remains out of control until a result explicitly regains control, spins to a stop, rolls, crashes, or otherwise leaves play.

## Control Loss Test Procedure

To resolve a `controlLoss` test:

1. Roll 1d6.
2. Add current `speedFactor`.
3. Subtract `adverseControl`.
4. Add +2 if the vehicle has zero handling or no driver.
5. Compare the final total to the control-loss result table.

Control-loss results:

- total 1 or less: regain control after a compulsory straight-ahead move. This uses the driver's action for the phase. Resolve new hazards encountered during that straight-ahead move.
- total 2-3: skid and regain control. Make a skid test before moving. The vehicle is out of control for the duration of the move, then regains control after completing it.
- total 4-5: skid and remain out of control. Make the skid move, but keep `controlState` as out of control.
- total 6-7: spin. Move forward, test for skid, then test for spin. Once a vehicle begins spinning, it remains out of control and automatically spins in later moves until it stops.
- total 8 or more: roll. Resolve skid/spin behaviour first, then rolling rules.

Drivers take control-loss tests at the start of each subsequent move until they regain control. A vehicle that has started spinning cannot regain control through the ordinary control-loss table; it continues spinning and does not make further control-loss tests.

## Skids

The OCR confirms skid tests are part of control-loss movement but the core skid table text is interleaved with page art and needs proofread against page images. Implementation should model skid as a staged movement result that can be straight, drift left, or drift right, because White Line Fever references that structure directly.

Candidate representation:

- `straightSkid`: vehicle advances without lateral drift.
- `driftSkidLeft`: vehicle advances and shifts one lane left.
- `driftSkidRight`: vehicle advances and shifts one lane right.

Collisions or road-edge crashes caused during a skid are resolved immediately by Rams and Crashes or crash logic. The hazard section should emit the compulsory movement intent and consume collision/crash outcomes.

## Core Spins

Under the core rules, a spin result moves the vehicle forward, resolves a skid, then resolves a spin. Once spinning starts, the vehicle automatically spins during each later move until it comes to a halt. Spinning vehicles remain out of control and do not make ordinary control-loss tests.

The core spin template, facing changes, speed loss values, and re-alignment diagrams need proofread from the page images before engine implementation. The OCR does preserve these behavioural points:

- a spinning vehicle can crash or collide during the movement before/while spinning;
- if the spin result is blocked by another vehicle, resolve the collision immediately;
- a vehicle that spins off the road is removed from play and takes crash damage;
- when a spinning vehicle comes back onto the grid, its next move must be a special re-alignment manoeuvre;
- re-alignment uses the phase's action;
- re-alignment speed cannot exceed 20 mph;
- after re-alignment, the vehicle must make a normal straight-ahead move;
- in the core rules, a vehicle that spins on a curve automatically crashes.

## White Line Fever Advanced Spins

White Line Fever replaces/extends the execution of spins and makes spins on curves possible.

Advanced spin move order:

1. Resolve a skid test before the straight-ahead part of the spin move.
2. Resolve the straight-ahead move and any drift skid produced by that skid test.
3. Resolve the final spin test.

Use strict staging. If any stage causes a collision, the move ends immediately and the collision is resolved.

The advanced skid test uses two dice:

- if the first die is odd, the vehicle drift skids;
- if a drift skid occurs, the second die decides direction: odd means left, even means right.

For vehicles at an angle to the road grid, drift-left and drift-right are judged by direction of travel, not by front facing.

A drift-skid collision during a spin is always a sideswipe regardless of the vehicle's angle. If the other vehicle is moving opposite to the spin direction, treat it as an opposed sideswipe.

## White Line Fever Spinning on Curves

Advanced rules allow spinning on curves.

Curve spin positioning:

- judge vehicle position from its centre point;
- at the end of each move, the centre point should be over a lane divider;
- use normal space divider rules;
- on uneven lanes, use the outside lane's space dividers;
- align the centre point halfway between the front and rear space dividers.

Curve skid treatment:

- resolve skid tests before moving;
- treat a drift skid inward as a straight skid;
- treat any other drift result as a drift skid outward.

This section depends on the Track Geometry Agent's curve atlas to define `inside`, `outside`, and legal curve-space dividers.

## Rolling

Core rolling:

- a vehicle that rolls first skids and spins;
- after the spin, it is wrecked and cannot take further part in the game;
- it immediately takes speed-factor damage: one hit per current `speedFactor`, each hit with damage equal to current `speedFactor`;
- critical hits from this damage are applied to the roof;
- ignore spin-template speed reductions while resolving rolling damage;
- after damage, speed falls to 0;
- leave the model in place, upside down, as a wreck for later ram/crash interactions;
- if the skid or spin before rolling carries the vehicle off-road, resolve roll damage before crash damage.

White Line Fever advanced rolling:

- a roll is preceded by an advanced spin move;
- the rolling vehicle continues over multiple phases until speed reaches 0;
- each rolling phase applies an extra 10 mph speed reduction in addition to spin-related speed loss;
- after each spin-and-move, roll for the facing that takes speed-factor damage:
  - 1-2: roof;
  - 3-4: front;
  - 5: side, then roll again with odd = left and even = right;
  - 6: floor;
- apply critical results to the landed facing;
- after speed reduction, recalculate speed factor before applying speed-factor damage.

Example to preserve as a test: a vehicle rolls from 80 mph. The advanced spin move reduces speed by 40 mph, the rolling reduction subtracts another 10 mph, leaving 30 mph. Its new speed factor is 2, so it takes two +2 hits to the rolled facing. If it survives and still has speed, it spins and rolls again next phase.

## Required Engine Behaviours

- Determine whether a hazard roll is required from current speed and safety limit.
- Calculate hazard totals with injected dice and structured modifiers.
- Apply panic braking immediately and track braking allowance correctly.
- Convert unpaid panic braking into control loss.
- Suppress further hazard rolls once a vehicle is out of control.
- Handle multiple hazards in descending safety-limit order, with oil last.
- Resolve control-loss tests before moves for out-of-control vehicles.
- Emit compulsory movement outcomes for skids/spins/rolls rather than directly duplicating movement geometry.
- Represent advanced spin movement as staged events so collisions can interrupt at the correct point.
- Represent rolling damage requests for the Damage Agent, including facing and hit count.
- Preserve structured logs for dice, modifiers, totals, speed changes, action cancellation, and state changes.

## Data Extracted

- Hazard result table: `data/rules/hazard-results.json`.
- Control-loss result table: `data/rules/hazard-results.json`.
- Safety-limit draft table: `data/rules/hazard-results.json`.
- White Line Fever advanced spin and rolling data: `data/rules/hazard-results.json`.

## Ambiguities and OCR Notes

- Dark Future p. 38: the safety-limit summary table was OCR-damaged, but reviewed values are tracked in `docs/rules/implementation-blockers.md` as data-ready/code-integration work rather than readability blockers.
- Dark Future pp. 38 and 40: U-turn has both a 10 mph safety limit and an automatic-control-loss threshold above 30 mph.
- Dark Future p. 38: debris road-hazard safety limit is 10 mph.
- Dark Future p. 39: hazard result table is recoverable: 0 or less OK, 1-4 panic brake, 5+ control loss.
- Dark Future p. 40: base handling values are partially noisy in OCR. Vehicle Design should own final vehicle template handling.
- Dark Future pp. 43-46: core skid and spin template details are obscured by page art in OCR and need page-image extraction before coding.
- Dark Future p. 40: one passive weapon exception requires a hazard roll when moving off the marker; OCR does not clearly identify the passive weapon.
- White Line Fever pp. 10-11: advanced spin and rolling prose is clear enough for a draft, but diagrams should be checked when implementing contact-zone geometry.

## Candidate Tests

### Hazard Roll Calculation

- At exactly the safety limit, no hazard roll is requested.
- At 1 mph above the safety limit, excess speed modifier is +1.
- At 10 mph above the safety limit, excess speed modifier is +1.
- At 11 mph above the safety limit, excess speed modifier is +2.
- A 90 mph vehicle with safety limit 50, optimum control 4, and die roll 5 produces total 5 and enters control loss.
- Damage-triggered hazard roll uses handling/drive skill after damage has been applied.

### Panic Braking

- Hazard total 3 reduces speed by 15 mph if braking allowance remains.
- Panic braking updates speed before the next hazard roll.
- A brake action earlier in the phase reduces remaining panic-brake allowance.
- If required panic braking exceeds remaining allowance, vehicle brakes as far as possible and enters control loss.
- Panic braking can lower speed factor enough to remove a later phase move.
- A panic-brake result prevents further actions for the rest of the phase.
- Target of a shunt treats panic brake as no effect; ramming vehicle does not.

### Multiple Hazards

- Multiple hazards resolve in descending safety-limit order.
- Oil is resolved after all non-oil hazards.
- If the first panic brake reduces speed to or below the next hazard's safety limit, skip the later roll.
- Once control loss occurs, no further hazard rolls are resolved in that sequence.

### Control Loss

- Handling zero immediately creates control loss and adds +2 to later control-loss tests.
- No driver immediately creates control loss and adds +2 to later control-loss tests.
- Out-of-control vehicles cannot choose ordinary actions.
- Out-of-control vehicles ignore hazard rolls.
- Control-loss total 1 or less regains control after a straight-ahead move.
- Control-loss total 2-3 skids and regains control.
- Control-loss total 4-5 skids and remains out of control.
- Control-loss total 6-7 starts spinning.
- Control-loss total 8+ starts rolling.

### Skid, Spin, and Roll

- A spin result suppresses future ordinary control-loss tests and continues spinning until stopped.
- Core roll creates speed-factor damage to the roof and then sets speed to 0.
- In White Line Fever, advanced spin resolves skid, straight-ahead movement/drift skid, then spin test.
- In White Line Fever, an advanced spin collision at any stage ends the move immediately.
- In White Line Fever, a drift-skid collision during a spin is a sideswipe.
- In White Line Fever, curve drift-skid inward is treated as straight, other drift results go outward.
- In White Line Fever, rolling applies the extra 10 mph reduction and then speed-factor damage to a die-selected facing.

## Dependencies

- Movement Agent: exact brake-action timing, braking allowance state, reverse action, U-turn legality, and base skid/spin movement integration.
- Track Geometry Agent: curve safety limits, inside/outside lane, contact zones, road-edge detection, and spin positioning on curves.
- Damage Agent: hazard triggers from hits/criticals and rolling damage application.
- Shooting Agent: passive-marker identities and passive hit timing.
- Rams and Crashes Agent: sideswipe/shunt hazard inputs, spin collision outcomes, and wreck ram effects.
- Vehicle Design Agent: vehicle handling, braking, driver skill, and safety-device modifiers if any.
