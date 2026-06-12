# Agent Coding Guidelines

## Required Reading

Before coding, every agent must read:

- `docs/engineering/architecture.md`
- `docs/engineering/rules-data-schema.md`
- `docs/engineering/testing-strategy.md`
- The cleaned rule section assigned to that agent.

Raw OCR files are not implementation authority. If a cleaned section is missing, the agent's job is extraction/proofreading, not coding.

## Canonical Terms

Use these names consistently:

- `turn`
- `phase`
- `speedFactor`
- `mph`
- `vehicle`
- `driver`
- `action`
- `move`
- `manoeuvre`
- `trackSpace`
- `lane`
- `facing`
- `contactZone`
- `fireCorridor`
- `hazardRoll`
- `controlLoss`
- `damageIncrement`
- `criticalHit`
- `passiveMarker`

Do not introduce synonyms such as `unit`, `actor`, `tile`, `cell`, `speedBand`, or `crashCheck` unless the rules lead approves a schema change.

## Coding Rules

- Keep rule logic separate from UI logic.
- Use structured data for tables.
- Use typed identifiers instead of free-form strings where practical.
- Inject dice rolls; never call random directly inside rule resolution.
- Return structured logs for every meaningful rule step.
- Preserve source references from the extracted rules in comments or data metadata where useful.
- Prefer small functions that resolve one rule step.
- Make illegal states hard to represent or easy to validate.

## State Mutation

Agents may choose immutable updates or controlled mutation inside a reducer-like boundary, but hidden mutation is not allowed.

Every public rule operation should make state changes inspectable through:

- Return value.
- Log entries.
- Tests.

## Agent Boundaries

### Turn Sequence Agent

Owns turn, phase, activation order, action timing, and end-phase/end-turn conditions.

Must not redefine movement geometry or dice tables outside activation timing.

### Movement Agent

Owns speed, acceleration, braking, basic movement, drift, U-turn, reverse, regain control, and White Line Fever advanced manoeuvres.

Must consume track geometry from the Track Geometry Agent.

### Track Geometry Agent

Owns track spaces, lanes, curve mapping, movement links, contact zones, and track generation data.

Must not encode vehicle-specific movement exceptions unless they are represented as geometry capabilities consumed by movement rules.

### Shooting Agent

Owns firing legality, fire corridors, range, hit modifiers, passive weapon deployment, turrets, linked weapons, and White Line Fever advanced shooting.

Must not own damage results after a hit is established.

### Damage Agent

Owns damage increments, target matrices, critical hits, terminal damage, and passive damage effects.

Must not own firing legality or vehicle design costs.

### Hazards Agent

Owns hazard roll calculations, safety limits, driver skill/handling inputs, panic braking, control loss, skids, spins, and rolling.

Must consume movement events and damage events rather than duplicate them.

### Rams and Crashes Agent

Owns collision detection outcomes after contact zones are supplied by track geometry, including ram type, speed adjustment, ram damage, and crash damage.

### Vehicle Design Agent

Owns vehicle templates, payload, costs, mounts, equipment, armour, engines, ammo, safety devices, and record sheet fields.

Must coordinate schema changes with Shooting, Damage, and Movement agents.

### Scenario Agent

Owns setup, victory conditions, prebuilt vehicles, drivers, and scenario-specific rules.

Must not introduce new rule shortcuts to make a scenario work.

## Required Agent Deliverables

Each implementation agent must provide:

1. Clean rule summary for its section.
2. Data files added or modified.
3. Engine behaviours added.
4. Tests added.
5. Ambiguities or OCR doubts.
6. Dependencies or requested schema changes.

## Ambiguity Handling

When the rulebook text, diagram, or OCR is unclear:

- Mark it in an ambiguity list.
- Add the source page reference.
- Do not silently guess if the result affects legal moves, dice modifiers, damage, or campaign persistence.
- If a temporary assumption is needed for a prototype, label it as provisional in code and tests.

## Definition of Done

An agent section is done when:

- Clean rules exist for the assigned section.
- Relevant tables are represented as data.
- Tests cover ordinary cases and edge cases from rulebook examples.
- The rules lead can run validation without knowing the agent's private assumptions.
