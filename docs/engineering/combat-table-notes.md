# Combat Table Helpers

`dark_future.combat_tables` provides pure, deterministic helper functions for damage, critical-hit table lookup, hazard rolls, control-loss tests, and damage increment penalties. The helpers do not mutate `engine.Vehicle` and do not import `engine.py`; callers are expected to apply returned effects to game state.

## Data Sources

- `data/rules/damage-tables.json`
  - vehicle damage profiles;
  - damage increment thresholds and penalties;
  - weapon damage modifiers;
  - ordinary damage and natural-six critical trigger;
  - critical result tables.
- `data/rules/hazard-results.json`
  - hazard roll formula and result bands;
  - control-loss formula and result bands;
  - extracted safety-limit ids.

## Implemented API Shape

- `resolve_damage(...) -> DamageResult`
  - calculates ordinary damage as `d6 + damageModifier - armour`, floored at zero;
  - reports natural-six critical triggers separately from ordinary damage;
  - reports terminal damage when a positive current damage total falls to zero;
  - reports crossed damage increment thresholds and their stat penalties;
  - reports HE hazard safety limit bands as 50 mph for +4 or less, 30 mph for +5 or more.
- `critical_result(table_id, roll) -> CriticalResult`
  - looks up a component critical table row from extracted ranges;
  - preserves structured effects and confirmation-roll metadata for the caller.
- `resolve_hazard_test(...) -> HazardTestResult`
  - skips rolls at or below the safety limit;
  - calculates the JSON formula: `d6 + ceil(excess mph / 10) - max(handling, driveSkill)`;
  - maps totals through the extracted result bands.
- `resolve_control_loss_test(...) -> HazardTestResult`
  - calculates `d6 + speedFactor - min(handling, driveSkill)`;
  - adds the extracted +2 modifier for zero handling or no driver;
  - maps totals through the extracted control-loss bands.
- `damage_increment_penalties(...)`
  - reports thresholds crossed from at-or-above to below;
  - intentionally does not treat the starting damage total as an increment threshold.

## Integration Notes

The current engine still has a rough inline damage and hazard implementation. These helpers are ready for a later integration pass, but this task deliberately leaves `dark_future/engine.py` untouched.

Critical effects are returned as immutable mappings where practical, but their meanings remain table data. Engine integration should translate effect ids into explicit state transitions and log entries rather than branching on prose.
