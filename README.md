# Dark Future Pygame Rough Pass

This is the first playable Python/Pygame shell for the extracted Dark Future rules.

Run:

```powershell
python main.py
```

Controls:

- `1-9`: choose the visible action.
- `Space`: advance phase.
- `Tab`: switch tactical, campaign, records, and debug modes.
- `C`: cycle the next contract scenario.
- `H`: hire a novice driver.
- `P`: repair the agency vehicle.
- `F5` / `F9`: save / load `dark_future_save.json`.
- `R`: reset.
- `Esc`: quit.

Current scope:

- Turn and phase progression from `data/rules/speed-phases.json`.
- Straight and curve movement using the extracted 8-lane track-piece definitions.
- Player agency vehicle and computer-controlled outlaw vehicle.
- Scenario-aware AI choosing from legal engine actions.
- Direct-fire shooting with hit rolls, range penalty, adjacent-lane targeting, smoke/vehicle blocking, armour, damage, criticals, and destruction.
- Basic ram/contact resolution for head-on and shunt impacts.
- Passive oil and smoke marker placement and resolution.
- Hazard/control-loss tests, including recovery actions.
- Extracted critical hit table integration with practical effects for driver, engine, wheels, bodywork, and weapons.
- Provisional curve sections with safety-limit hazard checks.
- Track-piece inventory informed by `D:/Users/Niftyrat/Desktop/s-l1600.jpg`.
- 8-lane track definitions with `curve30to60` and `curve50to80` lane speed limits.
- Intercept, ambush, and pursuit scenario setups with distinct objectives and settlement rewards/losses.
- Engagement victory when one side is destroyed, the agency exits, or the outlaw escapes a pursuit.
- Campaign settlement, recruitment, repair, scenario selection, save/load, and new-contract flow.
- Full vehicle-design backend for core payload and WLF advanced-weight designs, including chassis, armour, mounts, linked weapons, ammo/reloads, add-ons, driving systems, safety devices, and proofread blocker errors.
- Unified shell with tactical, campaign, records, debug, and rule log panels.
- Garage/design UI tab showing templates, chassis, equipment catalog, selected vehicle summary, and validation notes.
- Implementation blocker ledger at `docs/rules/implementation-blockers.md` for every rule/table/diagram that still needs manual proofread notes.
- Private-use scanned vehicle token art extracted from the local rulebook renders in `assets/tokens`; Interceptor, Renegade, and Bike token variants are mapped by side.

Known rough-pass limits:

- Curve movement uses the lane speed/section counts supplied from the track-piece definitions. Exact curved lane-link art, lateral contact zones, and printed graphic traces still need the traced curve atlas.
- Detailed contract tables, campaign vehicle-buy workflow wiring, and every unusual critical side effect are playable simplifications rather than final proofread-complete rules.
- The current track photo plus user-provided definitions confirm the playable 8-lane model, but final faithful curve movement still needs exact lane-link/contact-zone tracing.
- Rams, shooting, damage, hazards, critical hits, passives, curves, AI, and campaign settlement are now implemented as first-pass playable systems, not final proofread-complete rules.
- Vehicle design rejects still-blocked rows instead of guessing; see `docs/rules/implementation-blockers.md`.
- The UI is deliberately simple boxes so rules fidelity stays in the engine.
- Token art is extracted for this private local project only; fallback box tokens still render if an image is missing.
