# Parallel Implementation Plan

## Why Campaign Can Run In Parallel

The campaign backend does not depend on tactical curve geometry for its core responsibilities:

- agency/gang identity;
- funds and kudos;
- roster and garage;
- repairs and re-equipping;
- recruitment;
- contract history;
- post-engagement settlement;
- save/load serialization.

Only the bridge from campaign contracts into tactical engagement setup depends on scenario and track geometry. That bridge needs deployment zones, track layout, victory conditions, and opposing-force generation. The backend can therefore be built now as a pure state/action module, while the tactical geometry agents build the exact movement/contact systems.

## Active Workstreams

- `dark_future/campaign.py`: persistent campaign backend.
- `dark_future/track.py`: 8-lane track geometry helpers from `data/rules/track-definitions.json`.
- `dark_future/combat_tables.py`: pure damage, critical, and hazard table helpers.
- `dark_future/ui_model.py`: Pygame-independent view models and debug overlays.

## Integration Order

1. Keep current `dark_future/engine.py` playable while new modules are developed.
2. Integrate `track.py` first for movement, lane limits, curve safety, and render grid.
3. Integrate `combat_tables.py` for damage, hazards, and critical results.
4. Integrate `campaign.py` for settlement/new-contract state.
5. Switch Pygame rendering to `ui_model.py` once view models cover the existing UI.
6. Add contact-zone, ram, shooting, and AI agents after track geometry contracts are stable.
