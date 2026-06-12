# Rules Data Schema

This document defines shared data conventions. Exact JSON Schema files can be derived from this once cleaned rules are available.

## General Conventions

- Use `camelCase` for keys.
- Use stable string ids for rules data.
- Include `source` metadata where data comes from a specific book page.
- Store display labels separately from ids.
- Do not encode rules prose as executable string fragments.

Example:

```json
{
  "id": "hazard-roll-results-core",
  "source": {
    "book": "Dark Future Rulebook",
    "pages": [39]
  },
  "rows": []
}
```

## Dice

All dice rolls must be requested through a dice API.

Represent dice requests with:

```json
{
  "kind": "d6",
  "count": 1,
  "reason": "hazardRoll",
  "sourceRule": "core.hazards.hazardRoll"
}
```

Tests must be able to provide fixed dice sequences.

## Rule Logs

Every rule resolution should produce structured log entries.

```json
{
  "type": "hazardRoll",
  "vehicleId": "renegade-1",
  "message": "Hazard roll caused panic braking.",
  "rolls": [5],
  "modifiers": [
    { "id": "excessSpeed", "value": 2 },
    { "id": "optimumControl", "value": -4 }
  ],
  "total": 3,
  "source": {
    "book": "Dark Future Rulebook",
    "pages": [39]
  }
}
```

The UI may render `message`, but tests should assert structured fields.

## Track Geometry

Track geometry is graph-based.

Use `trackSpace`, not `tile` or `cell`.

```json
{
  "id": "curve-broad-left-a",
  "kind": "broadCurve",
  "turnDirection": "left",
  "lanes": 4,
  "spaces": [
    {
      "id": "s01",
      "lane": 1,
      "render": { "x": 0, "y": 0, "rotation": 0 },
      "forward": ["s02"],
      "driftLeft": [],
      "driftRight": ["s03"],
      "contactZone": ["s04", "s05"]
    }
  ],
  "source": {
    "book": "Dark Future Rulebook",
    "pages": [13, 52, 74]
  }
}
```

`render` is for display only. Movement must use graph links.

## Vehicle State

Vehicle instances should separate template data from battle state.

```json
{
  "id": "interceptor-1",
  "templateId": "interceptor",
  "driverId": "driver-1",
  "trackSpaceId": "s01",
  "facing": "north",
  "mph": 60,
  "speedFactor": 3,
  "controlState": "underControl",
  "damage": {},
  "weapons": []
}
```

## Actions

Legal actions should be represented explicitly.

```json
{
  "id": "action-123",
  "vehicleId": "interceptor-1",
  "kind": "drift",
  "phase": 2,
  "targets": ["s02"],
  "risk": {
    "requiresHazardRoll": true,
    "reason": "curve"
  }
}
```

The UI should present legal actions returned by the engine, not construct them.

## Tables

Tables should use machine-readable ranges, not prose-only cells.

```json
{
  "id": "hazardRollResult.panicBrake",
  "range": { "min": 1, "max": 4 },
  "effect": "panicBrake"
}
```

If OCR uncertainty exists in a table, add:

```json
{
  "status": "needsProofread",
  "notes": "OCR unclear on modifier value."
}
```

## Source References

Use source references to trace data back to extraction files:

```json
{
  "source": {
    "book": "White Line Fever",
    "pages": [4],
    "extractionFile": "docs/rules/white-line-fever/01-advanced-manoeuvres.md"
  }
}
```

Source references are mandatory for tables, track geometry, and rules with non-obvious edge cases.
