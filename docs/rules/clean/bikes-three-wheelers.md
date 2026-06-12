# Bikes and Three-Wheelers

> Status: cleaned implementation draft, not engine code.  
> Owner: Bikes and Three-Wheelers Agent  
> Source files: `docs/rules/core/10-bikes.md`, `docs/rules/white-line-fever/06-three-wheelers.md`, plus cross-checks against Movement, Shooting, Hazards, Damage, Rams/Crashes, and Vehicle Design cleaned drafts.  
> Source pages: Dark Future Rulebook pp. 64-73; White Line Fever pp. 38-40.

## Scope

This section defines vehicle-type exceptions for motorcycles, trikes, and motorcycle-sidecar combinations. It covers contact-zone behaviour, bike-only movement actions, bike hazard handling, bike rolling and road damage, bike-specific target matrices and collision overrides, trike and sidecar movement/shooting/damage/design rules, and implementation handoffs.

This section does not own generic movement timing, phase activation, shooting hit rolls, ordinary damage rolls, passive marker deployment, generic control-loss calculation, ordinary ram classification, campaign repair, or advanced vehicle-design table extraction.

## Shared Rule Model

Use the normal car rules unless a bike, trike, or sidecar rule explicitly overrides them.

Motorcycles and riders are treated as one tactical entity. If the bike leaves play, the rider leaves with it. If a bike is wrecked or takes terminal damage, the rider escapes at the start of the following turn after the bike has come to a halt, if the rider is still able to do so.

Source pages: core p. 64.

## Motorcycles

### Base Profile

Core motorcycle profile:

- damage: 9;
- armour: 2;
- maximum speed: 110 mph;
- acceleration: 40 mph;
- braking: 40 mph;
- handling: 6;
- payload: 300;
- damage increments at 6 and 3 damage remaining.

Source pages: core pp. 68, 81, 83.

### Contact Zones and Placement

A moving bike is placed with its wheels over a lane divider and its base close to the space divider in front. It occupies a two-lane contact zone like a car, even though its rendered model is narrower.

Straight-ahead movement covers one space, like a car. On curves and odd lane pairs, bikes use the same outside-lane space-divider convention as cars.

When a bike drifts, align it using the normal car-sized drift contact zone. On curves, bikes can drift outward but not inward under the core rules, matching car curve drift limits.

Stationary, upright, or fallen bikes use the normal contact-zone footprint. A bike may use the dodge action to temporarily reduce its contact zone, but only as described below.

Source pages: core pp. 64-65.

### Overlapping Bike Contact Zones

Bikes may share one or both lanes of their contact zones with other bikes. This state is called overlapping contact zones and is not automatically a collision.

When bikes finish a move with overlapping contact zones, the relevant riders take immediate hazard rolls:

- same direction or neck-and-neck overlap: safety limit 80 mph;
- opposite direction or opposed overlap: safety limit 40 mph.

Stationary and fallen bikes have the normal contact zone and do not use the overlapping-contact-zone exception as moving bikes do.

Bikes in overlapping contact-zone positions can sometimes sideswipe each other, subject to the bike collision rules.

Source pages: core pp. 64-65.

### Legal and Illegal Actions

Bikes use most ordinary rider actions, with these exceptions:

- bikes cannot reverse;
- bikes cannot bootlegger;
- bikes cannot bulldoze;
- bikes cannot deliberately ram or sideswipe cars;
- bikes cannot sideswipe bikes travelling in the opposite direction;
- bikes can sideswipe only other bikes travelling in the same direction and only from overlapping contact-zone positions;
- bikes have the special `dodge` manoeuvre.

Source pages: core pp. 64-65, 70-73; Movement cleaned draft.

### U-Turns and Moving Off

Bike U-turns use the ordinary U-turn restrictions and limits:

- maximum automatic speed: 10 mph;
- safety limit: 30 mph in the cleaned movement interpretation;
- at 31 mph or faster, the bike loses control before completing the U-turn.

When a bike moves off from stationary and chooses a different direction, turn it around and align it against the space dividers at the opposite end of the square. This is legal only when moving off and not accelerating above 20 mph.

Source pages: core pp. 65-66.

### Dodge Manoeuvre

A dodge is a bike-only manoeuvre. It lets a bike perform a normal straight-ahead move while using a reduced one-lane contact zone for that move.

Rules:

- safety limit: 40 mph;
- the rider chooses which side of the bike keeps the reduced contact zone;
- it may be used on curves, but exact curve geometry must come from the curve atlas;
- it can avoid surface hazards such as passive weapon markers;
- it cannot be used to avoid cars, bikes, or other vehicles;
- riders who panic brake or lose control after declaring/performing the dodge still complete the dodge with the reduced contact zone;
- on the following move, the rider may choose any legal action, including another dodge in either direction;
- if no new dodge is used on the following move, restore the normal two-lane contact zone.

Source pages: core pp. 65-66.

### Passive Deployment

Bikes place passive markers behind the bike model. The exact marker cells, especially on curves, must be supplied by Track Geometry.

Stationary bikes cannot deploy passives.

Oil-injection smoke from White Line Fever uses the bike smoke-trail limit from Shooting: bike trails are two markers long.

Source pages: core p. 66; WLF p. 18.

### Bike Direct Fire and Targeting

Bike left and right mounted direct-fire weapons use the same two-lane bike fire corridor. On curves, check the corridor using the ruler/template method instead of rectangular approximations.

Bike weapon table from the core OCR, represented by Shooting data:

- 4.2mm MG: range 8, accuracy +2;
- lightweight 20mm tube grenade launcher: range 12, accuracy 0;
- lightweight combat laser: range 12, accuracy +2;
- 40mm RAG launcher tube: range 12, accuracy 0.

Bike target penalties:

- if only one of the bike's occupied lanes lies in the fire corridor, apply -2 to hit;
- if both lanes lie in the fire corridor, apply -1 to hit.

Fallen bikes cannot be fired at except by turret-mounted weapons.

Source pages: core pp. 66-67.

### Bike Damage and Road Damage

Bikes suffer incremental damage like cars, using bike thresholds 6 and 3. The effects are the same as car damage increments: handling -1, acceleration -3 mph, and maximum speed -10 mph.

Bikes take terminal damage tests in the same way as cars. When a terminal bike comes to a halt, place it fallen at a slight angle to the grid and treat it as a wreck; the rider leaves at the start of the next turn if still alive.

Road damage represents the rider being thrown or dragged. A rider takes road damage when the bike:

- rolls;
- crashes;
- is involved in a head-on ram.

Road damage is resolved as an automatic rider/driver critical with a speed-factor modifier:

- speed factor 1: -4;
- speed factor 2: -2;
- speed factor 3: 0;
- speed factor 4: +2;
- speed factor 5: +3;
- speed factor 6: +4;
- speed factor 7: +5;
- speed factor 8 or more: +6.

Source pages: core p. 68.

### Bike Target Matrix

Bikes use their own target matrix rather than the ordinary car matrix. The structured draft is in `data/rules/bikes-three-wheelers.json`.

Recovered matrix summary:

- front: bodywork, front wheel, weapons left/right, engine, fuel, rider;
- sides: bodywork, front/rear wheels, weapons/passives, fuel/engine, rider;
- rear: bodywork, rear wheel, passives, fuel/engine, rider;
- floor: bodywork, front/rear wheels, weapons/passives, engine, fuel, rider;
- roof: bodywork or rider.

Critical-hit result tables are mostly the normal car tables, but bike bodywork, engine, wheel, fuel, and rider entries have bike-specific effects recorded in the JSON draft. Weapon criticals use the ordinary weapon critical meanings.

Source pages: core pp. 68-69.

### Bike Hazard and Control Loss

Bikes have full handling and reduced handling.

Full handling is used for ordinary manoeuvres and curve handling. Reduced handling is full handling minus 3 and is used when bike stability is worse than car stability.

Use reduced handling for:

- HE hits;
- oil on curves;
- oil on straights if the rider adjusted speed earlier in the phase;
- critical hits;
- mine hits;
- debris;
- sand on curves;
- collisions;
- sideswipe tests made while the bike is out of control.

Use full handling for straight-ahead oil when the rider has not adjusted speed earlier in the phase, and for smoke hazard rolls.

When a bike loses control, use the same control-loss formula as cars except that the bike control-loss table is:

- total 1 or less: regain control;
- total 2-3: skid and regain control;
- total 4-5: skid and remain out of control;
- total 6 or more: roll.

The bike's adverse control is calculated from drive skill and full handling, not reduced handling.

Source pages: core p. 70.

### Bike Rolling

When a bike receives a roll result:

- at 81 mph or faster, it crashes immediately, is removed from play, takes crash damage, and the rider takes road damage;
- at 80 mph or slower, it makes the standard skid movement, then rolls;
- rolling damage is speed-factor damage minus 2, using the current speed factor;
- roll damage facing is random: 1 left side, 2 right side, 3 roof, 4 floor, 5 front, 6 rear;
- after rolling, the bike stops immediately and its speed track is adjusted;
- place the model on its side at an angle to the grid;
- if the bike takes terminal damage or the rider is KO'd, treat it as a wreck;
- if bike and rider both survive, the bike remains in place until the start of its next move, when the rider may pick it up and resume.

Source pages: core p. 70.

### Disabled Engine, No Rider, and Pushing

Bikes with disabled engines slow to a halt. Once halted, the rider may abandon the bike at the start of any turn. The abandoned bike is left as a wreck-like obstacle.

If the rider does not abandon a halted disabled-engine bike, the rider may push it. Pushing counts as a normal action, gives the bike acceleration and maximum speed of 5 mph, and prevents shooting that turn.

If a bike has no rider, it automatically rolls on its next move. If it has no rider and finishes a move on a curve, it automatically crashes.

If full handling reaches zero, the bike automatically loses control.

Source pages: core pp. 69-70.

## Bike Collisions

### General Restrictions

Bikes may not deliberately ram cars. If a bike and car collide, the bike generally suffers the harsher special result.

Bikers can ram only when collision is inevitable or when making a legal bike-vs-bike sideswipe.

Source pages: core pp. 70-73.

### Bike vs Bike

Head-on:

- use the usual head-on sequence;
- both bikes take combined speed-factor damage;
- both bikes halt and fall;
- surviving riders take road damage at the impact speed.

Shunt:

- use the usual shunt sequence;
- both bikes involved automatically lose control, so skip the ordinary post-shunt hazard roll;
- as with any shunt, the ramming bike model is not moved when the contact is first detected.

Sideswipe:

- legal only between bikes travelling in the same direction with overlapping contact zones;
- resolve the normal sideswipe test;
- if an out-of-control bike accidentally creates an opposed bike sideswipe, use normal collision rules, but the out-of-control rider uses reduced handling on the sideswipe test.

Source pages: core pp. 70-72.

### Bike vs Car

Head-on:

- both vehicles suffer one combined speed-factor hit;
- the rider takes road damage;
- the bike is removed from play and does not take additional crash damage;
- if the car was the rammer, it completes its move;
- the car loses 30 mph and goes out of control.

Shunt:

- both vehicles suffer relative speed-factor damage;
- if the bike shunt-rams the car, the bike slows to the car's speed and the car's speed is unaffected;
- if the car shunt-rams the bike, the bike accelerates to the car's impact speed and the car slows by 10 mph;
- the car driver does not take the usual shunt hazard roll;
- the biker automatically loses control.

Sideswipe:

- bikes automatically lose sideswipe tests against cars;
- partial head-on and partial shunt rams involving a bike are treated as sideswipes;
- cars do not need overlapping contact zones to sideswipe bikes and may use the ordinary car sideswipe positions.

Fallen or wrecked bikes:

- when a car hits a fallen bike, treat it as a head-on ram, remove the bike after damage, and the car completes its move but loses control;
- when a bike hits a wrecked bike, the moving bike crashes, is removed, and takes crash and road damage; the wreck remains.

Source pages: core pp. 72-73.

## White Line Fever Three-Wheelers

Three-wheelers include trikes and motorcycle-sidecar combinations. These are optional WLF rules intended to give bike gangs heavier and more flexible equipment.

Source pages: WLF pp. 38-40.

### Trikes

Base trike profile:

- damage track: 12/8/4;
- armour: 2;
- maximum speed: 110 mph;
- acceleration: 35 mph;
- braking: 35 mph;
- handling: 3;
- cost: $20,000;
- maximum payload: 350.

Movement:

- use car contact zones, action choices, and manoeuvre rules;
- use bike-style collision restrictions;
- trikes cannot deliberately sideswipe cars, bikes, or trikes travelling in the opposite direction;
- trikes never test against reduced handling;
- trikes behave like cars after losing control until they would spin at 81 mph or faster, in which case they roll instead;
- rolled trikes are wrecks and cannot be righted;
- crew take road damage when the trike rolls or crashes.

Shooting:

- all fire directed at a trike has a -1 hit modifier, whether the trike occupies one or both lanes in the fire corridor;
- a trike may have a pintle-mounted tail-gunner weapon, firing forward or rearward with the WLF diagram corridor;
- if no tail gunner is fitted, the weapon must be fixed forward and uses the normal hood-mounted fire corridor.

Design:

- trikes have two armour points per facing;
- trike armour may be changed using bike armour rules;
- two front hard points each hold one lightweight weapon;
- two rear hard points may hold lightweight or full-sized passives;
- the optional pintle mount can hold a lightweight or medium weapon.

Source pages: WLF pp. 38-39.

### Motorcycle-Sidecar Combinations

A bike with sidecar is treated as a trike in all respects unless the sidecar-specific rules say otherwise. It has the same characteristics and uses the same movement and firing rules.

Differences:

- the crew weapon operator is a side-gunner, not a tail gunner;
- the side-gunner operates a swivel weapon at the front of the sidecar;
- the side-gunner has the limited sidecar fire corridor shown on WLF p. 40;
- if the mount is not crewed, it may instead hold a fixed forward-firing rider-controlled weapon using the usual side-mounted fire corridor;
- outriggers may not be fitted to motorcycle-sidecar combinations.

Motorcycle combinations use their own target matrix, recorded in the JSON draft.

Source pages: WLF p. 40.

## Required Engine Behaviours

- Represent `vehicleKind` separately from render model: `bike`, `trike`, and `motorcycleCombination` have different rule overrides.
- Ask Track Geometry for bike contact zones, dodge reduced contact zones, overlapping bike contact zones, passive placement behind bikes, and WLF trike/sidecar fire corridors.
- Restore a bike's normal contact zone after a dodge unless it dodges again.
- Suppress bike reverse, bootlegger, bulldozer, and illegal sideswipe actions in legal-action generation.
- Emit hazard requests for overlapping bike contact zones with same/opposed direction safety limits.
- Switch bike hazard calculations between full and reduced handling according to hazard source.
- Use the bike-specific control-loss result table.
- Resolve bike roll results using the bike speed threshold and road-damage hooks.
- Emit road-damage critical requests for riders after bike rolls, crashes, and head-on rams.
- Route bike/trike/sidecar target matrices to Damage instead of car matrices.
- Route bike-car and bike-bike collision overrides before generic ram post-processing.
- Apply trike spin-to-roll conversion at 81 mph or faster.
- Apply trike and sidecar shooting penalties and crewed-mount restrictions.
- For campaign records, preserve whether a wreck is a fallen functioning bike, abandoned disabled bike, trike wreck, or removed crashed bike.

## Data Extracted

- Bike and three-wheeler exception rules, matrices, collision overrides, and tests: `data/rules/bikes-three-wheelers.json`.
- Core bike template and standard mounts remain in `data/rules/vehicles.json`.
- Bike weapons and outrigger shooting traits remain in `data/rules/weapons-draft.json` and `data/rules/shooting-modifiers.json`.
- Bike armour caps, crash bars, two-wheel drive, computer drive, and outriggers remain in `data/rules/equipment.json`.

## Ambiguities and OCR Doubts

- Bike dodge curve examples are diagram-dependent; exact legal reduced contact-zone cells must be traced by Track Geometry.
- Bike passive placement diagrams are visual; exact cells behind a bike on curves need the curve atlas.
- Bike 40mm RAG accuracy is confirmed from the page image as 0.
- Bike target matrix side/floor subroll wording is column-damaged; the JSON records the best reconstruction and marks damaged rows.
- Bike road-damage modifier table is readable enough for draft, but the speed-factor 3 cell is visually blank in OCR and interpreted as 0.
- Core p. 70 has an OCR phrase that appears to say `81mph or faster`; this draft uses 81+ for immediate bike crash and 80 or less for bike rolling because that matches surrounding wording.
- Bike vs car partial-collision diagrams are visual. Generic collision classification must expose a `partialBikeCollision` branch rather than relying on rectangular overlap.
- WLF trike target matrix OCR is damaged in several rows. The JSON records a conservative reconstruction and marks it as `needsProofread`.
- WLF p. 38 pintle front/rear fire corridor is diagram-defined and must be traced before implementation.
- WLF p. 40 side-gunner fire corridor is diagram-defined and must be traced before implementation.
- WLF p. 39 says trike armour follows bike armour modification rules; exact advanced armour cost/weight remains blocked by the Vehicle Design proofread.

## Candidate Tests

### Bike Movement and Contact

- A bike straight-ahead move advances one space while retaining a two-lane contact zone.
- A bike on an odd curve lane uses the outside-lane space divider.
- A bike cannot reverse.
- A bike cannot bootlegger.
- A bike cannot bulldoze.
- A bike moving off in a different direction at 20 mph is legal.
- A bike moving off in a different direction at 25 mph is illegal.
- Two same-direction bikes ending with overlapping contact zones request 80 mph safety-limit hazard rolls.
- Two opposed bikes ending with overlapping contact zones request 40 mph safety-limit hazard rolls.

### Dodge

- A dodge uses a one-lane reduced contact zone for that move.
- A dodge at 40 mph does not request a dodge-speed hazard roll.
- A dodge at 41 mph requests a hazard roll.
- A dodge can avoid a passive marker in the omitted lane.
- A dodge cannot avoid another vehicle.
- If the next move is not another dodge, the bike's normal two-lane contact zone is restored.

### Shooting

- A bike target with one occupied lane in the fire corridor applies -2 to hit.
- A bike target with both occupied lanes in the fire corridor applies -1 to hit.
- A fallen bike cannot be targeted by a fixed weapon.
- A fallen bike can be targeted by a turret weapon.
- A stationary bike cannot deploy passives.
- A bike oil-injection smoke trail keeps at most two markers.

### Damage and Control Loss

- A bike crossing from 7 to 5 damage applies the 6-point damage increment once.
- A bike crossing from 7 to 2 damage applies both 6 and 3 increments once.
- Straight-ahead oil with no speed adjustment uses full handling.
- Oil on a curve uses reduced handling.
- Mine-hit hazard uses reduced handling.
- Smoke hazard uses full handling.
- Bike control-loss total 6 produces a roll, not a spin.
- Bike adverse control is based on full handling, not reduced handling.
- Bike roll at 81 mph crashes immediately.
- Bike roll at 80 mph resolves skid, roll damage, stop, and fallen-bike placement.
- Bike road damage at speed factor 2 applies a -2 modifier to the rider critical roll.

### Bike Collisions

- Bike head-on bike collision emits combined speed-factor damage for both bikes and road damage for both surviving riders.
- Bike shunting bike causes both bikes to lose control without ordinary shunt hazard rolls.
- Bike sideswipe against same-direction overlapping bike is legal.
- Bike sideswipe against opposed bike is illegal unless it is an accidental out-of-control collision.
- Bike head-on car removes the bike, gives the rider road damage, slows the car by 30 mph, and makes the car out of control.
- Bike shunting car sets the bike to the car speed and leaves the car speed unchanged.
- Car shunting bike sets the bike to car impact speed and slows the car by 10 mph.
- Bike automatically loses a sideswipe test against a car.
- Bike hitting a wrecked bike crashes and is removed while the wreck remains.

### Trikes and Sidecars

- A trike uses car contact zones and car manoeuvre options.
- A trike never uses reduced handling.
- A trike spin result at 80 mph behaves as a car spin.
- A trike spin result at 81 mph converts to a roll and wrecks the trike.
- Crew on a crashing trike take road damage.
- All direct fire at a trike applies -1 to hit.
- A trike without tail gunner uses a fixed forward hood-style corridor.
- A trike pintle weapon may be forward or rear firing.
- A sidecar combination rejects outriggers.
- A sidecar side-gunner uses the traced sidecar fire corridor.
