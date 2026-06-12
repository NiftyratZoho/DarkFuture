# Unified UI Spec

## Purpose

This document defines the shared UI shell for the faithful, turn-based Dark Future adaptation. It is a contract for rules, campaign, scenario, AI, and UI agents so tactical play, campaign management, setup, records, logs, and debug tools do not grow into separate interfaces.

This is not a visual-polish document. The first UI can use simple boxes for cars and track spaces. Fidelity comes from the rule engine, graph-based track geometry, source-backed data, and structured logs.

## Design Principles

- The UI displays state and sends player intent. It does not duplicate rule logic.
- Legal actions, risks, targets, dice requests, and rule outcomes come from the rules engine.
- Tactical and campaign views share one shell and one canonical game state.
- Debug views are first-class panels and overlays, not separate one-off tools.
- All game records shown in the UI must be traceable to structured state or rules data.
- Raw OCR is not UI authority. UI labels and flows should be based on cleaned rule sections and approved schemas.

## Top-Level Shell

The unified shell has these persistent areas:

- `modeNav`: switches between tactical play, campaign, contract setup, vehicle/driver records, and debug views.
- `statusBar`: current campaign, contract/scenario, turn, phase, active side, active vehicle, pending choice, pending dice, and save/replay state.
- `mainWorkspace`: the current primary view, usually tactical board, campaign roster/garage, or contract setup.
- `sidePanel`: context-sensitive action panel or selected record summary.
- `bottomPanel`: combat/rule log, dice history, event feed, and replay controls.

Agents may create temporary extraction/debug views, but each must map cleanly into one of these shell areas before integration.

## Navigation Modes

### Tactical Play

Primary mode for resolving engagements.

Required shell layout:

- `mainWorkspace`: tactical board.
- `sidePanel`: action panel plus selected vehicle/driver record tabs.
- `bottomPanel`: combat/rule log.
- Optional right-side or bottom drawer: debug inspector.

### Campaign

Primary mode for running an agency or gang between engagements.

Required shell layout:

- `mainWorkspace`: campaign roster and garage.
- `sidePanel`: selected driver, vehicle, agency/gang, repair, recruitment, or finance detail.
- `bottomPanel`: campaign log and post-engagement event feed.

### Contract Setup

Primary mode for choosing or generating the next engagement.

Required shell layout:

- `mainWorkspace`: contract/scenario setup.
- `sidePanel`: selected contract details, deployment limits, opposing force preview, and validation messages.
- `bottomPanel`: contract generation log, rule references, and warnings.

### Records

Cross-mode record browser for vehicles, drivers, agencies/gangs, equipment, weapons, and source-backed rules data.

Required shell layout:

- `mainWorkspace`: searchable record list or detail sheet.
- `sidePanel`: source references, derived stats, and usage links.
- `bottomPanel`: audit log for edits, repairs, purchases, injuries, and progression.

### Debug

Rules-debug mode for extraction validation, test authoring, replay inspection, and agent integration.

Required shell layout:

- `mainWorkspace`: tactical board or data inspector.
- `sidePanel`: selected object state, legal actions, rule inputs, and pending decisions.
- `bottomPanel`: structured log, dice queue, replay timeline, and source references.

## Tactical Board

The tactical board renders the engagement state.

Required display data:

- `track`: ordered track pieces and `trackSpace` render coordinates.
- `vehicles`: vehicle positions, facing, speed, control state, side, and active/inactive status.
- `passiveMarkers`: deployed passive weapons, hazards, wrecks, smoke, oil, or other board markers.
- `scenarioState`: objectives, deployment zones, exits, time limits, and victory progress.
- `turnState`: turn, phase, acting side, active vehicle, pending action, and activation order.

Required interactions:

- Select vehicle.
- Select visible `trackSpace`.
- Request legal actions for selected vehicle.
- Preview engine-supplied move targets, fire targets, contact zones, and risk flags.
- Submit one engine-approved action.
- Resolve or acknowledge pending dice and pending choices.

The board must not infer legal movement from screen position. Movement uses `trackSpace` links returned by track geometry and rule agents.

## Action Panel

The action panel shows only actions returned by the engine for the current state.

Required sections:

- `activeVehicleSummary`: vehicle id, label, side, driver, mph, `speedFactor`, control state, damage summary, current `trackSpace`.
- `legalActions`: grouped by `kind`, such as move, drift, brake, accelerate, shoot, ram, regain control, reverse, or scenario action.
- `actionPreview`: selected action details, target spaces, target vehicles, weapon choices, modifiers, risk, and source references.
- `pendingDecision`: any required player choice before the action can resolve.
- `pendingDice`: dice requests, reason, source rule, and deterministic/replay status.
- `validation`: why an expected action is unavailable when the engine can provide explanatory diagnostics.

Rule agents expose actions as structured objects. The UI may filter, group, sort, or label them, but must submit the original action id or full approved action payload back to the engine.

## Vehicle And Driver Records

Vehicle and driver records must appear in tactical, campaign, setup, and records modes with the same fields and ids.

Vehicle record display:

- `vehicleId`, `templateId`, display label, side/owner, agency/gang ownership.
- Position: `trackSpaceId`, facing, mph, `speedFactor`, control state.
- Core stats from template and equipment.
- Weapons, mounts, ammo, passive weapons, turrets, linked weapons, and fire-control equipment.
- Weapon and equipment rows should be able to reference cropped source art assets by stable `weaponId`/`equipmentId`, with source page and crop metadata retained outside UI code.
- Garage hardpoint layouts should use the White Line Fever character/vehicle sheets as the visual source for hardpoint placement, while preserving stable mount ids from `vehicles.json` for rule validation.
- Armour, damage increments, component damage, critical hits, terminal damage state.
- Campaign fields: mileage, repair state, modifications, cost/value, availability, and garage status.

Driver record display:

- `driverId`, display label, side/owner, agency/gang membership.
- Skill, handling modifiers, injuries, status, progression, reputation/kudos where approved by campaign rules.
- Current vehicle assignment.
- Contract history, kills/achievements if represented by campaign rules.

The UI must distinguish battle state from template/campaign state. Tactical damage should not silently overwrite campaign garage state until the campaign/post-engagement sequence commits it.

## Combat And Rule Log

The log renders structured rule entries from the engine and campaign systems.

Required log capabilities:

- Show chronological tactical and campaign events.
- Expand an entry to show dice rolls, modifiers, totals, source references, affected ids, and state changes.
- Filter by vehicle, driver, rule type, phase, turn, campaign step, or source.
- Support replay/debug mode where selecting a log entry highlights affected board objects.
- Preserve machine-readable fields for tests and replay comparison.

The UI may render `message` text, but the source of truth is the structured log entry.

## Campaign Roster And Garage

The campaign view presents persistent agency/gang management from Dead Man's Curve and any approved campaign extensions.

Required sections:

- `campaignSummary`: campaign id, player side, agency/gang identity, funds, kudos/reputation/media state, current contract sequence step, and calendar/turn if represented.
- `roster`: drivers, status, skills, injuries, progression, assignments, and availability.
- `garage`: vehicles, repair status, damage carried from engagements, installed equipment, available mounts, mileage, value, and assignment.
- `resources`: funds, salvage, equipment inventory, recruitment options, repairs, re-equipping, cybernetics/computer hacking where approved by cleaned campaign rules.
- `opposition`: known opposing agency/gang/Op state when public to the player or visible in debug mode.
- `postEngagement`: success, rewards, repair, recruitment, progression, injury/death, and persistent-state commit workflow.

Campaign agents must expose state transitions as structured actions and logs, using the same action/log patterns as tactical rules. The UI should not calculate campaign funds, repairs, recruitment results, or kudos directly.

## Contract Setup

Contract setup bridges campaign state and tactical engagement state.

Required sections:

- `contractList`: available contracts, generated contracts, scenarios, or campaign-mandated engagements.
- `contractDetail`: objectives, sides, setup rules, rewards, penalties, entry requirements, victory conditions, source references.
- `forceSelection`: eligible drivers, vehicles, loadouts, repairs needed, deployment restrictions, and validation.
- `oppositionSetup`: computer-controlled side generation, visible enemy details, hidden data indicators, and AI profile if applicable.
- `trackSetup`: chosen/generated track, deployment zones, starting spaces, direction, exits, and special markers.
- `startValidation`: blocking errors and warnings returned by scenario/campaign/rules agents.

Starting a contract creates a tactical engagement state from campaign/scenario state through an approved setup transition. The UI must not hand-assemble tactical state from unrelated records.

## Debug Overlays

Debug overlays are available in tactical and debug modes. They must be engine/data driven.

Required overlays:

- `legalMoves`: target `trackSpace` ids for selected vehicle/action.
- `movementGraph`: forward, driftLeft, driftRight, reverse, and special manoeuvre links.
- `fireCorridors`: firing corridors, target eligibility, range bands, blockers, and selected weapon arcs.
- `contactZones`: ram/crash contact zones and candidate collision classifications.
- `hazardCalculations`: safety limits, speed excess, driver/handling modifiers, pending `hazardRoll`, and possible result table.
- `damageResolution`: target matrix inputs, damage increments, critical hit candidates, and affected components.
- `activationOrder`: current turn/phase order and skipped/ineligible vehicles.
- `sourceReferences`: source book/page/extraction file behind selected rule data.

Overlays may be visually simple. They exist to validate rules and help agents test curve geometry, movement, shooting, rams, hazards, and campaign transitions.

## State/View Contracts

The UI shell consumes a read-only view model derived from canonical game state.

Minimum view model shape:

```json
{
  "mode": "tactical",
  "status": {
    "campaignId": "campaign-1",
    "engagementId": "engagement-1",
    "turn": 2,
    "phase": 4,
    "activeVehicleId": "vehicle-1",
    "pending": "action"
  },
  "board": {
    "trackPieceIds": [],
    "trackSpaces": [],
    "vehicles": [],
    "passiveMarkers": [],
    "overlays": {}
  },
  "selection": {
    "vehicleId": "vehicle-1",
    "trackSpaceId": "s01",
    "recordId": null
  },
  "actions": [],
  "records": {},
  "campaign": {},
  "contractSetup": {},
  "logs": []
}
```

Rules and campaign agents may add fields through approved schema changes, but should preserve these top-level concepts.

## Agent Data Exposure Requirements

Rule agents should expose UI-facing data through stable contracts:

- `getViewModel(state, uiSelection, debugOptions)` returns display-ready references without hiding canonical ids.
- `getLegalActions(state, actorId)` returns action objects with ids, kind, targets, risks, pending decisions, and source references.
- `previewAction(state, actionId)` returns predicted highlights, required choices, dice requests if knowable, and explanatory diagnostics.
- `applyAction(state, action, diceResults)` returns updated state, logs, pending choices, and pending dice.
- `getRecord(state, recordId)` returns vehicle, driver, campaign, equipment, weapon, or scenario record data.
- `getDebugOverlay(state, overlayKind, selection)` returns overlay primitives keyed by canonical ids.

Campaign agents should mirror the same pattern:

- `getCampaignActions(state, campaignContext)` for recruitment, repairs, re-equipping, contract selection, post-engagement commits, and progression.
- `previewCampaignAction(state, actionId)` for funds, roster, garage, and contract effects.
- `applyCampaignAction(state, action, diceResults)` for approved campaign state transitions.

AI agents must choose from legal actions returned by the engine and should expose their chosen action plus scoring/debug notes to the log or debug inspector when debug mode is enabled.

## Pending Choices And Dice

The UI must handle staged resolution.

Pending choices:

- target selection
- weapon selection
- route or manoeuvre option
- repair/recruitment/equipment choice
- campaign post-engagement choice

Pending dice:

- all dice requests must include kind, count, reason, source rule, requesting entity, and replay ordering.
- manual dice entry, automatic dice, and fixed replay dice should use the same request/response shape.

No UI component may call random directly.

## Save, Replay, And Audit

The unified shell should be compatible with deterministic replay from the start.

Required persisted concepts:

- canonical starting state
- action list
- dice sequence
- resulting structured logs
- campaign commits between engagements
- UI-independent selected debug options where useful for reproducing reports

Replay controls live in the bottom panel and debug mode. Campaign changes should be auditable with the same log system used for tactical play.

## Initial UI Slice

The first UI shell implementation should include:

1. Tactical board with simple track spaces and vehicle boxes.
2. Status bar with turn, phase, active vehicle, and pending state.
3. Action panel driven by `getLegalActions`.
4. Vehicle/driver record summary for selected vehicle.
5. Structured combat/rule log.
6. Campaign roster/garage placeholders backed by the same state shape.
7. Contract setup placeholder that can later create tactical state through scenario/campaign agents.
8. Debug overlays for legal moves and movement graph.

Do not wait for full campaign rules before creating the shell. Campaign panels can initially display empty or placeholder state, but their structure must remain compatible with Dead Man's Curve campaign data.

## Non-Goals

- No final art direction or visual polish.
- No engine implementation.
- No copied rulebook prose in the UI.
- No separate tactical-only UI that cannot host campaign panels.
- No UI-created rule shortcuts for movement, shooting, rams, hazards, damage, repairs, contracts, or progression.
