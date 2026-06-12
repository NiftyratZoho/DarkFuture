# Turn Sequence

> Status: cleaned implementation draft  
> Owner: Turn Sequence Agent  
> Source files: `docs/rules/core/02-turn-sequence.md`, `docs/rules/core/03-movement.md`, `docs/rules/white-line-fever/01-advanced-manoeuvres.md`  
> Source pages: Dark Future Rulebook pp. 9, 11-12; White Line Fever p. 4

## Scope

This section defines the tactical turn loop, phase progression, activation order, action timing, and speed-factor phase activation. It does not define movement geometry, manoeuvre legality, shooting resolution, damage, hazards, or campaign state.

## Core Concepts

- A `turn` is divided into numbered `phase`s.
- Core Dark Future uses up to six phases per turn.
- A vehicle normally has one forward move per turn for each point of `speedFactor`.
- `speedFactor` is calculated from current `mph`: divide mph by 20 and round up.
- A vehicle can move in a phase when its current `speedFactor` is greater than or equal to that phase number.
- Every non-stationary vehicle that is eligible to move in a phase must make its forward move unless another rule interrupts or replaces that movement.
- Each driver may use one `action` in a phase, subject to action-specific restrictions.
- A turn always has at least one phase, even if all vehicles are stationary.

## Phase Lifecycle

1. The caller sets the current phase number, starting at phase 1.
2. At the start of each phase, determine the activation order for that phase from current vehicle speeds.
3. Resolve each driver in activation order.
4. After all drivers have resolved their permitted move/action for the phase, end the phase.
5. If no vehicle is fast enough to move in the next phase, the turn ends.
6. At the start of the next turn, reset the phase number to 1.

The caller decides the activation order at the start of each phase. Later speed changes from acceleration, braking, hazards, or control loss do not reorder that same phase. Collisions may interrupt the normal sequence.

## Activation Order

Vehicles resolve from highest current `mph` to lowest current `mph`.

Tie handling:

- If two vehicles have the same speed and one is clearly in front, the front vehicle moves first.
- If two vehicles at the same speed are neck and neck or travelling in different directions, roll a die for ordering; the lowest roll moves first.
- Stationary vehicles use a die roll to determine action order when more than one stationary vehicle is acting.

Implementation note: the ordering system should return a stable activation list for the phase, plus any pending tie-break dice requests.

## Per-Driver Sequence

For an eligible moving vehicle, resolve the driver in this order:

1. Declare the action, or declare no action.
2. If the vehicle is fast enough for the current phase, move it forward and resolve any movement-linked action effects such as manoeuvre, brake, or accelerate.
3. Resolve required `hazardRoll`s from manoeuvres, curves, or passive hits.
4. If the declared action was shooting passives, and the driver did not panic brake or lose control during hazard resolution, place the passive markers.
5. If the declared action was ordinary shooting, and the driver did not panic brake or lose control during hazard resolution, the driver may fire.

For ordinary shooting, the driver may still choose not to fire when the shooting step is reached. Once the player checks range or the `fireCorridor`, the shot is committed.

Targets that suffer damage or critical hits may be forced to take immediate hazard rolls. The hazard and damage agents own those details.

## Vehicles Without a Move in the Current Phase

A driver whose vehicle is not fast enough to move in the current phase may still act, but only with restricted options:

- shoot direct-fire weapons;
- use smoke.

These drivers skip the movement, hazard, and passive-marker steps in the normal per-driver sequence.

## Stationary Vehicles

Vehicles at 0 mph do not move. Their drivers may still act in phase 1, but are restricted to:

- shoot direct-fire weapons;
- lay smoke.

When multiple stationary vehicles act, determine their order by die roll.

## White Line Fever: Speed Factor 7+

White Line Fever keeps the six-phase turn structure but allows vehicles to have `speedFactor` values above 6.

At `speedFactor` 7 or higher, a vehicle takes double moves in some phases. In a double-move phase:

- the vehicle moves twice;
- the driver still receives only one action;
- that action may be used during either the first move or the second move, but not both.

If multiple vehicles take double moves in the same phase:

1. all first moves are resolved in descending speed order;
2. all second moves are then resolved in descending speed order.

The extracted table is represented in `data/rules/speed-phases.json`.

## Required Engine Behaviours

- Calculate `speedFactor` from `mph` using rounded-up 20 mph bands.
- Determine whether a vehicle has zero, one, or two moves in a given phase from the speed-phase data.
- Always create phase 1, even when every vehicle is stationary.
- End the turn after a phase if no vehicle will have a move in the next phase.
- Build the phase activation order once at the start of the phase.
- Preserve the phase activation order after speed changes during that phase.
- Represent tie-breaks as dice requests rather than direct random calls.
- Distinguish action eligibility from move eligibility.
- In double-move phases, expose action timing as a choice of first move or second move.

## Data Extracted

- Core speed-factor ranges and ordinary move phases: `data/rules/speed-phases.json`.
- White Line Fever speed-factor 7-12 double-move table: `data/rules/speed-phases.json`.

## Ambiguities and OCR Notes

- Dark Future Rulebook p. 9: OCR is noisy around the per-driver sequence, but the five-step order is recoverable from the page.
- Dark Future Rulebook p. 9: the exact wording for non-moving and stationary action restrictions is noisy; the recovered rule allows direct-fire shooting and smoke only.
- Dark Future Rulebook p. 12: tie-break wording says the lowest die roll moves first; confirm against page image during proofread.
- Dark Future Rulebook p. 12: speed changes do not alter the already determined phase order, but collisions can interrupt. Collision interrupt behaviour belongs to Rams and Crashes.
- White Line Fever p. 4: OCR loses the speed-factor 7+ table layout. The table in `speed-phases.json` was extracted from the local page image `_analysis/wlf_pages/wlf-04.jpg`.
- White Line Fever p. 4: action timing inside a double move is clear enough to model as first-or-second move timing, but the Movement Agent must define how actions that modify speed interact with the two movement steps.

## Candidate Tests

### Phase Progression

- With all vehicles stationary, a turn still creates phase 1 and then ends.
- With fastest vehicle at speed factor 1, the turn ends after phase 1.
- With fastest vehicle at speed factor 3, phases 1-3 occur and phase 4 is not created.
- A vehicle reduced below the next phase threshold during the turn does not move in later phases for which it is no longer eligible.

### Core Activation

- At 15 mph, a vehicle moves only in phase 1.
- At 30 mph, a vehicle moves in phases 1 and 2.
- At 60 mph, a vehicle moves in phases 1, 2, and 3.
- At 61 mph, a vehicle moves in phases 1, 2, 3, and 4.
- In a phase containing vehicles at 70 mph and 65 mph, the 70 mph vehicle resolves first.
- If two same-speed vehicles are aligned front/back, the front vehicle resolves first.
- If two same-speed vehicles are neck and neck, the engine requests a tie-break die roll and the lower roll resolves first.

### Action Timing

- A moving vehicle gets at most one action in a normal phase.
- A vehicle not eligible to move in the phase can only choose direct-fire shooting or smoke.
- A stationary vehicle in phase 1 can only choose direct-fire shooting or lay smoke.
- A declared ordinary shooting action can be cancelled before range or fire-corridor checking.
- Once range or fire corridor is checked, the ordinary shooting action is committed.

### Phase Order Stability

- If a vehicle accelerates during its activation, it does not move earlier in the same phase.
- If a vehicle brakes during its activation, it does not move later in the same phase.
- A collision can interrupt activation order; the detailed result is delegated to Rams and Crashes.

### White Line Fever Speed Factor 7+

- At speed factor 7, the vehicle receives two moves in phase 1 and one move in phases 2-6.
- At speed factor 8, the vehicle receives two moves in phases 1-2 and one move in phases 3-6.
- At speed factor 12, the vehicle receives two moves in every phase.
- In a double-move phase, the vehicle receives one action total, not one action per move.
- In a phase where two vehicles both have double moves, all first moves resolve in descending speed order before any second moves resolve.

## Dependencies

- Movement Agent: defines action legality, movement effects, acceleration/braking timing, and double-move action interactions.
- Hazards Agent: defines panic braking, control loss, and hazard roll consequences.
- Shooting Agent: defines direct-fire, passive shooting, smoke, fire corridor, range checking, and committed shots.
- Rams and Crashes Agent: defines collision interrupts.
