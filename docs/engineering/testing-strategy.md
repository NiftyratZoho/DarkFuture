# Testing Strategy

## Goal

Tests prove that the implementation follows the extracted rules, not that the UI appears to work.

Every rules section should have tests before it is considered integrated.

## Test Types

### Data Validation Tests

Validate JSON/data files for:

- Required ids.
- Source references.
- Unique ids.
- Valid ranges.
- Valid references between vehicles, weapons, mounts, tables, and track spaces.

### Rule Unit Tests

Test one rule at a time:

- Turn phase progression.
- Legal action generation.
- Movement results.
- Hazard roll totals.
- Damage table lookup.
- Target matrix lookup.
- Ram type resolution.

### Example-Based Tests

Every rulebook example or diagram that affects implementation should become a test.

Priority examples:

- Phase activation by speed.
- Straight movement.
- Uneven lane movement on curves.
- Drift on curves.
- Hazard roll calculation.
- Panic braking.
- Control loss movement.
- Ram contact zones.
- Firing corridor legality.
- Target facing and target matrix lookup.

### Integration Tests

Test short, complete sequences:

- One phase with two vehicles at different speeds.
- One turn with acceleration and shooting.
- A curve traversal with hazard rolls.
- A ram followed by speed adjustment and hazard roll.
- A hit followed by damage, critical hit, and hazard trigger.

### Replay Tests

Given a fixed starting state, action list, and dice sequence, the final state and log must match exactly.

Replay tests are required before AI work starts.

## Dice Testing

All dice must be injected.

Tests should use:

- Fixed single rolls for simple rules.
- Fixed roll queues for multi-step resolution.
- Failure tests when a rule asks for unexpected dice.

## Track Geometry Tests

Track geometry is high risk and must have dedicated tests.

Required checks:

- Every `forward` link points to an existing track space.
- Drift links are valid for the manoeuvre and curve direction.
- Mirrored left/right curves preserve lane order correctly.
- Contact zones are symmetric where the rules require symmetry.
- Render coordinates are not used for movement resolution.

## AI Test Boundary

AI tests should verify that the AI:

- Chooses only legal actions.
- Can complete a scenario turn without invalid state.
- Does not bypass dice or rule resolution.

AI tests should not assert that the AI makes the perfect tactical choice unless a deterministic scoring rule is explicitly defined.

## Regression Rule

Any bug found in a rule interaction must create a regression test before or with the fix.

## Minimum Acceptance Before Implementation Planning

Before planning the full implementation, the cleaned extraction should identify tests for:

- Turn sequence.
- Movement.
- Track geometry and curves.
- Hazards/control loss.
- Rams/crashes.
- Shooting.
- Damage and critical hits.

Implementation planning can proceed section by section only when each section has enough extracted detail to write tests.
