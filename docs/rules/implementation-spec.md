# Implementation Spec

This is the coordinating spec for a faithful, turn-based Dark Future adaptation.

Status: draft coordination document. It depends on cleaned rule sections and must be updated as agents complete extraction.

## Product Target

The game is a digital tabletop adaptation, not a real-time driving game.

Required modes:

- Tactical roadfight play using the Dark Future phase and lane/grid rules.
- Solo play where the computer controls the opposing side.
- Campaign play where the player runs a Sanctioned Op agency or Outlaw gang.
- Unified UI for tactical play, vehicle records, campaign management, logs, and setup.

## Source Rule Sets

- Dark Future Rulebook.
- White Line Fever.
- Dead Man's Curve from White Dwarf 124 pages 18-31 and White Dwarf 125 pages 68-76.

The White Dwarf 125 reference to White Dwarf 123 is treated as a known publication-delay typo for this project.

## Non-Negotiable Fidelity Rules

- Turn-based phase sequence must be preserved.
- Movement must use explicit track-space geometry, not physics.
- Curve movement must use verified lane mapping.
- Dice must be injected and logged.
- Tables must be represented as data.
- The UI must not duplicate rule resolution.
- AI must choose from legal actions supplied by the rules engine.
- Campaign state must persist drivers, vehicles, funds, repairs, recruitment, and progression.

## Canonical State Areas

The eventual game state must cover:

- `turnState`
- `trackState`
- `vehicleState`
- `driverState`
- `weaponState`
- `passiveMarkers`
- `scenarioState`
- `campaignState`
- `pendingChoices`
- `ruleLog`

## Clean Rule Sections

Cleaned rule files should be created under `docs/rules/clean/`.

Initial required clean sections:

- `turn-sequence.md`
- `movement.md`
- `track-geometry.md`
- `hazards-control-loss.md`
- `rams-crashes.md`
- `shooting.md`
- `damage-critical-hits.md`
- `vehicle-design.md`
- `bikes-three-wheelers.md`
- `scenarios.md`
- `campaign.md`

## Data Outputs

Rules data should be created under `data/rules/`.

Initial expected files:

- `speed-phases.json`
- `track-pieces-draft.json`
- `curve-atlas-work-items.json`
- `movement-actions.json`
- `hazard-results.json`
- `ram-types.json`
- `weapons.json`
- `damage-tables.json`
- `target-matrices.json`
- `vehicles.json`
- `equipment.json`
- `bikes-three-wheelers.json`
- `wlf-vehicle-tables-proofread.json`
- `scenarios.json`
- `campaign-sequence.json`

## Review Gate

Implementation code begins only when a section has:

1. Clean paraphrased rule summary.
2. Source pages identified.
3. Tables or diagrams converted to draft data.
4. Ambiguities listed.
5. Candidate tests listed.

The first code slice may begin once these sections pass the gate:

- Turn sequence.
- Basic movement.
- Initial track geometry.
- Basic hazards.

Campaign coding begins only after campaign sequence, driver state, vehicle state, and post-engagement dependencies are clean enough to test.

## Unified UI Requirement

The UI must be one shell with panels, not separate tactical and campaign apps.

Required panels:

- Tactical board.
- Action selection.
- Vehicle and driver record.
- Rule/combat log.
- Campaign roster.
- Garage and repairs.
- Contract/scenario setup.
- Rules debug overlays.

Agents may create debug-only views, but each view must have a path into the unified shell.

## Current Agent Assignments

- Turn Sequence Agent: `docs/rules/clean/turn-sequence.md`, `data/rules/speed-phases.json` complete as cleaned draft.
- Movement Agent: `docs/rules/clean/movement.md`, `data/rules/movement-actions.json` complete as cleaned draft.
- Track Geometry Agent: `docs/rules/clean/track-geometry.md`, `data/rules/track-pieces-draft.json` complete as cleaned draft; curve atlas trace remains blocking follow-up.
- Curve Atlas Trace Plan: `docs/rules/clean/curve-atlas-trace-plan.md`, `data/rules/curve-atlas-work-items.json` complete as work plan; actual curve graph tracing remains blocking.
- Hazards Agent: `docs/rules/clean/hazards-control-loss.md`, `data/rules/hazard-results.json` complete as cleaned draft; safety-limit/skid-spin proofread remains follow-up.
- Rams and Crashes Agent: `docs/rules/clean/rams-crashes.md`, `data/rules/ram-types.json` complete as cleaned draft; exact contact-zone enumeration remains tied to curve atlas follow-up.
- Shooting Agent: `docs/rules/clean/shooting.md`, `data/rules/weapons-draft.json`, `data/rules/shooting-modifiers.json` complete as cleaned draft.
- Damage Agent: `docs/rules/clean/damage-critical-hits.md`, `data/rules/damage-tables.json`, `data/rules/target-matrices.json` complete as cleaned draft.
- Vehicle Design Agent: `docs/rules/clean/vehicle-design-equipment.md`, `data/rules/vehicles.json`, `data/rules/equipment.json` complete as cleaned draft; WLF characteristic and cost tables marked for proofread.
- WLF Vehicle Table Proofread Agent: `docs/rules/clean/proofread-wlf-vehicle-tables.md`, `data/rules/wlf-vehicle-tables-proofread.json` complete as proofread draft; one minigun double-load added-weight cell remains marked `needsProofread`.
- Bikes and Three-Wheelers Agent: `docs/rules/clean/bikes-three-wheelers.md`, `data/rules/bikes-three-wheelers.json` complete as cleaned draft; exact bike diagram/contact details remain tied to curve/contact-zone atlas follow-up.
- Campaign Agent: `docs/rules/clean/campaign.md`, `data/rules/campaign-sequence.json` complete as cleaned draft; numeric tables marked for proofread.
- Scenario Agent: `docs/rules/clean/scenarios-contracts.md`, `data/rules/scenarios.json` complete as cleaned draft; diagram track layouts and some WLF/core details need proofread.
- Unified UI Agent: `docs/ui/unified-ui-spec.md` complete as shell contract draft.

Additional agents should use disjoint write targets and follow `docs/engineering/agent-workflow.md`.
