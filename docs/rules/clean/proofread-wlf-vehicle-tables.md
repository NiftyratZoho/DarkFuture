# Proofread WLF Vehicle Tables

> Status: proofread draft from rendered page images.  
> Source: White Line Fever pp. 42-44, rendered images in `_analysis/ocr_pages/white_line_fever/`.  
> Output data: `data/rules/wlf-vehicle-tables-proofread.json`.

## Scope

This note resolves the OCR-damaged vehicle-design summary tables and characteristic tables used by the Vehicle Design extraction. It covers chassis and bike base costs, engine add-ons, armour cost/weight, driving systems, safety devices, weapon mounts, fire-control computers, weapon/reload costs and weights, double-load facilities, car acceleration/maximum speed, car braking/handling modifiers, and bike characteristics.

The table text has been paraphrased into implementation terms. Long source wording is not reproduced.

## Cleared Blockers

- WLF p. 42 vehicle base rows are readable. Interceptor V12 is `$90,000`, confirming the earlier OCR correction.
- WLF p. 42 bike base row is readable: bike cost `$15,000`, weight `200`.
- WLF p. 42 armour rows are readable for carbon steel, carbon plastic, carbon-plastic armoured vehicles, conversions, and reinforced tyres.
- WLF p. 42 driving system rows are readable, including two-wheel drive and computer drive costs/weights.
- WLF p. 42 single rocket booster row is readable: cost `$30,000`, weight `150`.
- WLF p. 42 safety device rows are readable, including crash suppression weight `10` and crash bars weight `0`.
- WLF p. 43 weapon mount rows are readable: cupola `$10,000`/`200`, pintle `$6,000`/`100`, outrigger `$5,000`/`0`.
- WLF p. 43 fire-control computer rows are readable: missile fire computer `$10,000`/`0`; turret fire computer `$10,000` plus turret, weight `0`.
- WLF p. 43 weapon, reload, missile, passive, lightweight passive, and most double-load rows are readable.
- WLF p. 44 acceleration/maximum speed, braking/handling, and bike characteristic tables are readable.

## Remaining Uncertainty

One double-load cell on WLF p. 43 remains uncertain:

- `doubleLoads.lightweightWeapons.7.62mmMinigun.addWeight`: the cost `$2,000` is clear, but the added-weight value is not visually reliable in the rendered page image. It is marked `needsProofread` in JSON.

## Implementation Notes

- Costs are stored as integer dollars without commas.
- Weights are stored as integer weight points. Negative conversion weights are stored as negative integers.
- Handling columns on WLF p. 44 are stored as modifiers to the vehicle's handling, split into non-HE and HE-hit use.
- A dash in the source characteristic table is represented as `null` where that engine/weight combination is unavailable.
- The fire-control computer row for turret fire computer is represented as a `$10,000` computer with `requiresTurret: true`; the visible `+turret` note means the turret cost is separate.
- Asterisks marking difficult Outlaw availability are represented as `sanctioned: true`.
