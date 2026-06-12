# Campaign Backend Notes

## Scope

`dark_future/campaign.py` is a pure Python campaign-state backend. It does not import
Pygame and does not depend on tactical geometry, movement, lane state, or
`dark_future.engine`.

The tactical engine should eventually hand it plain post-engagement records:

- participating and surviving driver ids
- destroyed, terminal, or repaired vehicle ids
- killed driver ids
- bounty, loot, and mileage awards
- engagement objective success or deliberate failure

## Implemented

- Persistent dataclasses for campaign, units, drivers, vehicles, stores,
  recruitment locks, contract outcomes, bounty claims, repair estimates, and
  settlement reports.
- Unit kinds from `data/rules/campaign-sequence.json`: `independentOp`,
  `agency`, `outlawGang`, and `renegadeOp`.
- Post-engagement settlement for:
  - killed drivers
  - destroyed and terminal vehicles
  - Op bounty claims
  - explicit outlaw loot awards
  - explicit mileage awards
  - objective-failure forfeits
  - unit contract counters and aggregate kudos
- Repair estimates and repair application:
  - `$250` per damage point
  - `$250` per critical hit
  - `$500` per hack-damaged system
  - written-off vehicles cannot be repaired
- Recruitment stubs:
  - novice drivers are always available
  - agency novice licensing costs `$5,000`
  - experienced drivers can be generated with explicit drive skill and own
    vehicle value
  - experienced-driver sequence upkeep is tracked as 10% of own vehicle value
- Save/load conversion through `to_dict()` and `from_dict()` methods using
  plain JSON-compatible dictionaries.

## Deliberate Provisional Handling

Several source tables in `docs/rules/clean/campaign.md` are marked
`needsProofread`. The backend avoids random table generation for those areas.
Callers must provide explicit settlement values until the tables are verified.

Provisional constants currently present:

- Outlaw bounty by drive skill.
- Mileage-to-drive-skill thresholds.
- Agency novice licence cost.
- Agency running cost.
- Experienced-driver upkeep rate.

These should be revisited after page-image proofread of the damaged White Dwarf
tables.

## Integration Shape

Keep the boundary record-based. Tactical code should not pass `Vehicle` objects
from `dark_future.engine` into campaign functions. Convert tactical end-state
into `ContractOutcome`, then call `settle_post_engagement()`.

Repair and recruitment should run in later post-engagement phases, not during
tactical play.
