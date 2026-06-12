# Agent Workflow

This workflow controls how agents move from OCR extraction to implementation.

## Rule

Agents do not code from raw OCR.

An agent may only code against a cleaned rule section that has:

- Source page references.
- OCR doubts marked or resolved.
- Tables identified.
- Required behaviours listed.
- Candidate tests listed.

## Agent Roles

### Rules Lead Agent

Owns consistency across all rule sections.

Responsibilities:

- Maintain glossary and schema decisions.
- Review each cleaned rule section.
- Approve cross-section data changes.
- Keep the implementation checklist current.
- Resolve conflicts between diagrams, tables, and prose.

Primary outputs:

- `docs/rules/clean/`
- `docs/rules/implementation-spec.md`
- `data/schema/`

### Unified UI Agent

Owns the shared interface plan and eventual UI shell. This agent does not own rule logic.

Inputs:

- `docs/engineering/architecture.md`
- `docs/engineering/rules-data-schema.md`
- Cleaned outputs from Turn Sequence, Movement, Track Geometry, Vehicle Design, Scenario, and Campaign agents.

Outputs:

- Unified UI information architecture.
- Panel and state-view contracts.
- Debug overlay requirements.
- Tactical/campaign navigation flow.
- UI integration tests or screenshot checklist once implementation begins.

### Turn Sequence Agent

Inputs:

- `docs/rules/core/02-turn-sequence.md`
- White Line Fever speed factor changes from `docs/rules/white-line-fever/01-advanced-manoeuvres.md`

Outputs:

- Clean turn sequence rules.
- Speed/phase activation data.
- Tests for phase ordering and action timing.

### Movement Agent

Inputs:

- `docs/rules/core/03-movement.md`
- `docs/rules/white-line-fever/01-advanced-manoeuvres.md`

Outputs:

- Clean movement and manoeuvre rules.
- Action definitions.
- Tests for movement, acceleration, braking, drift, U-turn, reverse, regain control, dual actions, and double moves.

### Track Geometry Agent

Inputs:

- `docs/rules/core/03-movement.md`
- `docs/rules/core/09-rams-and-crashes.md`
- `docs/rules/core/11-track-generation.md`
- Relevant diagrams in `_analysis/ocr_pages/dark_future/`

Outputs:

- Clean track and curve geometry rules.
- `track-pieces` data draft.
- Contact-zone definitions.
- Tests for curve movement and track generation.

### Shooting Agent

Inputs:

- `docs/rules/core/04-shooting.md`
- `docs/rules/core/06-passive-damage.md`
- `docs/rules/white-line-fever/03-advanced-shooting.md`
- Relevant equipment from `docs/rules/white-line-fever/04-new-equipment.md`

Outputs:

- Clean shooting rules.
- Weapon and shooting modifier data.
- Tests for firing legality, fire corridors, range, hit rolls, turrets, passives, and linked weapons.

### Damage Agent

Inputs:

- `docs/rules/core/05-damage.md`
- `docs/rules/core/06-passive-damage.md`
- `docs/rules/core/07-critical-hits.md`
- White Line Fever ammo/equipment effects.

Outputs:

- Clean damage rules.
- Damage tables and target matrices.
- Tests for damage increments, multiple hits, critical hits, and terminal damage.

### Hazards Agent

Inputs:

- `docs/rules/core/08-hazards-control-loss-tests.md`
- `docs/rules/white-line-fever/02-advanced-hazards.md`

Outputs:

- Clean hazards/control loss rules.
- Hazard result data.
- Tests for hazard totals, panic braking, skids, spins, rolling, and control loss.

### Rams and Crashes Agent

Inputs:

- `docs/rules/core/09-rams-and-crashes.md`
- Track contact-zone output.
- Hazard output for post-ram checks.

Outputs:

- Clean ram/crash rules.
- Ram type data.
- Tests for head-on, shunt, sideswipe, stationary vehicles, speed adjustment, and crash damage.

### Bikes and Three-Wheelers Agent

Inputs:

- `docs/rules/core/10-bikes.md`
- `docs/rules/white-line-fever/06-three-wheelers.md`

Outputs:

- Clean bike, trike, and motorcycle-combination rules.
- Vehicle type data.
- Tests for bike movement, bike damage, bike collisions, and three-wheeler exceptions.

### Vehicle Design Agent

Inputs:

- `docs/rules/core/12-vehicle-design.md`
- `docs/rules/core/13-vehicles-and-hardware.md`
- `docs/rules/white-line-fever/04-new-equipment.md`
- `docs/rules/white-line-fever/07-design-section.md`

Outputs:

- Clean vehicle design rules.
- Vehicle, equipment, engine, armour, mount, ammo, and safety-device data.
- Tests for cost, weight, payload, mount legality, and record sheet fields.

### Scenario Agent

Inputs:

- `docs/rules/core/14-scenarios.md`
- `docs/rules/white-line-fever/08-scenarios.md`
- Vehicle and rules outputs from other agents.

Outputs:

- Scenario setup data.
- Victory condition rules.
- Tests for scenario initialization and completion.

### Campaign Agent

Inputs:

- `docs/rules/dead-mans-curve/01-white-dwarf-124-pages-18-31.md`
- `docs/rules/dead-mans-curve/02-white-dwarf-125-pages-68-76.md`
- Scenario, vehicle design, damage, and driver state outputs from other agents.

Outputs:

- Clean campaign rules.
- Unit, driver progression, funds, contract sequence, kudos, recruitment, repair, re-equipping, and agency/gang data.
- Tests for campaign setup, post-engagement sequence, money changes, mileage, kudos, recruitment, repairs, and persistent driver/vehicle state.

Notes:

- Treat the White Dwarf 125 reference to White Dwarf 123 as a publication-delay typo. The first part used by this project is White Dwarf 124 pages 18-31.
- Campaign work is not optional. The desired game includes running an agency or gang, so campaign state must be represented in the same canonical state model as tactical play.

## Handoff Format

Each agent handoff must include:

```text
Section:
Source files:
Source pages:
Cleaned files:
Data files:
Tests:
Ambiguities:
Dependencies:
Schema changes requested:
```

## Review Gates

### Gate 1: Extraction Complete

All assigned pages are in Markdown with source references.

### Gate 2: Clean Rule Spec

OCR errors are corrected enough to implement. Tables and diagrams are described.

### Gate 3: Data Draft

Tables, track pieces, vehicles, weapons, or scenarios are represented in structured draft data.

### Gate 4: Test Plan

Example-based and edge-case tests are listed.

### Gate 5: Implementation

Code can begin only after the Rules Lead approves Gates 1-4 for that section.

## Parallel Work Order

First wave:

- Rules Lead Agent.
- Unified UI Agent.
- Turn Sequence Agent.
- Movement Agent.
- Track Geometry Agent.

Second wave:

- Hazards Agent.
- Rams and Crashes Agent.
- Shooting Agent.
- Damage Agent.

Third wave:

- Bikes and Three-Wheelers Agent.
- Vehicle Design Agent.
- Scenario Agent.
- Campaign Agent.

The Track Geometry Agent is a blocker for faithful movement, rams, and firing corridors. Treat curve geometry as a critical-path task.
The Unified UI Agent is a blocker for polished integration. Treat its early output as the shared target shell, not as final visual styling.
