# Architecture

## Goal

Build a faithful, turn-based digital tabletop adaptation of Dark Future. The engine must preserve the rulebook's phase system, lane/grid movement, curve geometry, dice tables, and vehicle records. The UI can be simple boxes; the rules cannot be approximate.

## Core Principle

Rules are implemented as pure, testable functions over explicit game state.

All randomness is injected. All tables are data. All geometry is graph-based. The UI displays state and asks the engine for legal actions.

## Module Boundaries

### Rules Engine

Owns legal actions, rule resolution, dice use, state transitions, and rule logs.

The engine must not:

- Read browser or UI state.
- Depend on pixels or rendered positions.
- Generate random numbers directly.
- Mutate hidden global state.

### Data Layer

Owns JSON or typed data for tables, vehicles, weapons, track pieces, scenarios, and extracted rule references.

Rules data must be loadable and validated independently of the UI.

### Track Geometry

Owns track spaces, lanes, facings, movement links, contact zones, and firing geometry.

Curves are explicit movement graphs. Do not infer curve movement from drawings.

### UI

Owns display, input, board rendering, overlays, and log presentation.

The UI may ask the engine:

- What actions are legal?
- What spaces can this vehicle move to?
- What targets can this weapon attack?
- What happened after this action resolved?

The UI must not duplicate rules.

The project must have one unified UI shell for tactical play, campaign management, setup, vehicle records, logs, and rule-debug views. Agents may build isolated debug views while extracting and testing, but those views must be designed as panels that can be folded into the unified shell.

Required top-level UI areas:

- Tactical board.
- Action panel.
- Vehicle and driver record panel.
- Combat/rule log.
- Campaign roster and garage.
- Contract/scenario setup.
- Rules debug overlays for legal moves, fire corridors, contact zones, and hazard calculations.

### AI

Owns computer-side decision making. AI must choose from legal actions produced by the rules engine. It must not bypass legality checks.

## State Model

Use a single explicit game state object containing:

- Turn and phase state.
- Track state.
- Vehicle instances.
- Driver instances.
- Deployed passive markers.
- Scenario state.
- Pending rolls or pending decisions.
- Public log entries.

State transitions should return:

- Updated state.
- Structured log entries.
- Any pending choices.
- Any requested dice rolls, if the engine is staged that way.

## Determinism

Given the same starting state, action, and dice sequence, the engine must produce the same result every time.

This is required for:

- Rule tests.
- Replay/debug tools.
- AI simulation.
- Campaign save/load integrity.

## First Implementation Slice

Do not start with campaign features.

The first code slice should prove:

1. Turn sequence.
2. Speed factor activation.
3. Straight road movement.
4. Basic manoeuvres.
5. Initial curve geometry.
6. Hazard roll trigger points.

Shooting, damage, rams, bikes, vehicle design, scenarios, and campaign systems should follow after movement and track geometry are stable.

The UI shell should still be created early, even if campaign panels initially contain placeholder data. This prevents tactical and campaign features from growing separate interfaces.
