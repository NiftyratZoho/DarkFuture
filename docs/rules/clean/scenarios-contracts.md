# Scenarios and Contract Setup

> Sources:
> - `docs/rules/core/14-scenarios.md`
> - `docs/rules/white-line-fever/08-scenarios.md`
> - `docs/rules/clean/campaign.md`
>
> Status: cleaned implementation summary from raw OCR. This is not a full transcription. Diagram-based track layouts and several OCR-damaged details must be proofread against page images before implementation.

## Scope

This section owns tactical scenario setup, victory conditions, initial forces, starting speed, track setup, and the bridge between Dead Man's Curve contract setup and tactical engagements.

It does not own:

- turn and phase rules
- movement, shooting, damage, hazards, rams, or bikes
- vehicle design legality beyond referencing required budgets/templates
- campaign post-engagement rewards, progression, repair, salvage, or recruitment
- AI action selection during tactical play

The scenario system creates a valid tactical engagement state from a scenario or campaign contract. Once play begins, the rules engine resolves the engagement through the other rule sections.

## Shared Scenario Concepts

### Side Roles

Common scenario roles:

- `lead`: starts ahead and usually tries to escape or reach an exit.
- `chase`: starts behind and tries to stop the lead side.
- `attacker`: initiates the engagement or has first setup choice.
- `target`: target of a hunt, attack, pursuit, or ambush.
- `op`: sanctioned operative or agency side.
- `outlaw`: outlaw gang or renegade side.
- `escort`: side protecting a non-combat or priority vehicle.

Side labels are scenario roles only. Campaign legality and unit identity come from the Campaign Agent.

### Position Roll

Several introductory scenarios use a single die to determine which player is lead/chase:

- odd result: the named driver/player is lead
- even result: the named driver/player is chase

Where the scenario says players roll to determine attacker, use the stated high/low result for that game.

### Starting Speed

Core Games One and Two start both vehicles at 60 mph, speed factor 3.

Core Game Three introduces randomized starting speed:

- roll two dice
- add results and multiply by 10 mph
- reroll low totals of 2, 3, or 4
- either player may veto and reroll a result of 10+ before multiplication
- the lead player may veto and reroll a result of 8+ before multiplication
- repeat until no permitted veto is used

The rule intent is to avoid forcing a player into an unmanageable high-speed corner at setup.

White Line Fever scenarios often allow each side to choose any starting speed from 0 mph up to the vehicle's maximum speed, unless the scenario specifies 60 mph.

### Vehicle Records and Templates

Scenarios may use:

- fixed prebuilt vehicles
- randomly selected weapon packages
- budget-built vehicles
- campaign vehicles selected from a unit roster

Scenario setup should produce vehicle instance requests, not complete vehicle design logic. Vehicle cost, mounts, weight, armour, equipment legality, and derived characteristics are owned by the Vehicle Design Agent.

### Victory Results

Scenario victory answers only the tactical question: who won this engagement and why.

Campaign consequences such as bounty, loot, mileage, salvage, kudos, psychosis, recovery, and repair are handled by the Campaign Agent after the tactical result is committed.

## Core Rulebook Scenarios

### Core Game One: Straight Chase Duel

Purpose:

- introductory straight-road chase
- uses basic movement, speed, shooting, and passive weapon handling without curves or generated track

Forces:

- two Renegades
- each has hood-mounted machine gun and oil layer
- both drivers have drive skill 3

Setup:

- lay out all straight track sections as shown in the source diagram
- chase car deploys in the shaded rear start section
- lead car deploys in the shaded section ahead of the chase car
- both start at 60 mph, speed factor 3

Victory:

- lead wins by crossing the finish line
- chase wins only by preventing the lead car from reaching the finish line

Implementation notes:

- finish line must be represented as a scenario exit boundary
- shaded deployment sections require diagram proofread
- this is the simplest test scenario for the unified UI and replay system

### Core Game Two: Fixed Curved Chase

Purpose:

- introduces fixed track layouts with curves

Forces:

- same as Core Game One

Setup:

- roll one die
- select the matching source diagram layout
- chase deploys on the first track section
- lead deploys on the section ahead
- both start at 60 mph, speed factor 3

Victory:

- same as Core Game One

Implementation notes:

- all six diagram layouts must be traced into track-piece sequences before implementation
- curve legality depends on Track Geometry Agent output

### Core Game Three: Random Loadout Chase

Purpose:

- introduces varied weapon packages and randomized starting speeds

Forces:

- both players use Renegades
- each player chooses offensive or defensive package before position is determined
- both drivers have drive skill 3

Offensive package die table:

- 1: hood-mounted machine gun plus oil layer
- 2: two wing-mounted 20mm grenade launchers plus smoke layer
- 3: two wing-mounted machine guns plus spike layer
- 4: hood-mounted 40mm grenade launcher plus smoke layer
- 5: hood-mounted 15mm autocannon
- 6: hood-mounted chain gun

Defensive package die table:

- 1: hood-mounted machine gun plus spike layer
- 2: hood-mounted machine gun plus smoke layer
- 3: hood-mounted machine gun plus oil layer
- 4: hood-mounted 20mm grenade launcher plus oil layer
- 5: hood-mounted 20mm grenade launcher plus pattern mine layer
- 6: hood-mounted 15mm autocannon plus pattern mine layer

Setup:

- determine lead/chase position after records are completed
- roll for track layout as in Core Game Two
- roll starting speed using the randomized starting speed rule

Victory:

- same as Core Game One

Implementation notes:

- weapon ids must map to Vehicle Design/Shooting data once finalized
- package table source needs proofread because OCR damaged some formatting but the rows are mostly recoverable

### Core Game Four: Budget Duel

Purpose:

- introduces vehicle design budget and randomized driver skill

Forces:

- each player buys a Renegade and at least one weapon
- each player has $50,000 total budget for car, weapons, and equipment

Driver skill table:

- die 1: drive skill 2
- die 2-4: drive skill 3
- die 5: drive skill 4
- die 6: drive skill 5

Setup:

- players design vehicles under budget before play
- dice for position
- setup track as in Core Game Two
- roll starting speed as in Core Game Three

Victory:

- same as Core Game One

Implementation notes:

- budget validation depends on Vehicle Design Agent
- the OCR for one row marks `3°`; treat as drive skill 3 pending proofread

### Core Game Five: Generated Track Chase

Purpose:

- introduces initial track generation

Forces:

- same design budget and driver skill generation as Core Game Four

Setup:

- each player has $50,000
- use Initial Track Generation
- roll starting speed as in Core Game Three

Victory:

- lead wins by moving off the seventh track section
- chase wins by stopping the lead before that exit

Implementation notes:

- seventh section is counted from the generated starting track sequence
- exact Initial Track Generation rules come from Track Geometry Agent

### Core Game Six: Op Pursuit Against Outlaws

Purpose:

- introduces Op versus outlaw gang force building and continuous track generation

Forces:

- lower die roller buys and equips an Interceptor as the Op side
- other player buys and equips an outlaw gang
- each side has $100,000
- outlaw gang minimum is either two Renegades, three bikes, or one Renegade and two bikes
- each outlaw vehicle must have at least one weapon
- outlaw vehicles may be controlled by different players

Setup:

- Outlaws are always lead side
- Op is chase side
- use Continuous Track Generation
- starting speeds use the Core Game Three randomized method

Victory:

- play until all vehicles on one side are wrecked, crashed, or immobilized without usable weapons

Implementation notes:

- active-vehicle determination should be shared with Campaign Agent wording
- this is a bridge scenario for campaign-style Op/outlaw engagements

### Core Game Seven: Gang or Op Attack

Purpose:

- introduces attacker choice and gang versus gang outcomes

Forces and setup:

- both players roll one die
- high roller is attacker
- attacker chooses to design either a gang or an Op
- the other player designs a gang, called the target
- Op versus gang rules follow Core Game Six

Victory:

- Op versus gang uses Core Game Six victory
- gang versus gang attacker wins only if the whole target gang is taken out
- target gang wins by escaping all vehicles, taking out attackers, or outdistancing attackers

Implementation notes:

- `outdistance` needs a tactical distance/exit definition from the scenario or campaign setup
- gang-versus-gang victory needs precise active/escaped vehicle state

### Core Game Eight: Intercept or Pursuit

Purpose:

- introduces attacker choice between pursuit and intercept setup

Forces:

- design sides as in Core Game Six
- determine attacker as in Core Game Seven

Setup:

- attacker chooses pursuit or intercept
- pursuit uses Core Game Six setup
- intercept lays out a fixed number of sections using Continuous Track Generation
- target deploys on the third track section at 60 mph facing toward attacker
- attacker deploys on sections 5, 6, or 7 facing toward target
- attacker may choose any speed from 0 mph to maximum speed

Victory:

- same as Core Game Six

Implementation notes:

- OCR reads the fixed number of generated sections unclearly; context suggests enough sections to include sections 5-7, and the printed text appears to say seven sections, but this needs page-image proofread
- intercept setup should become the tactical template for Dead Man's Curve approach results

## White Line Fever Scenarios

### WLF Game One: Bulldozer Alley

Purpose:

- introduces WLF equipment, missile rules, speed choice, and road hazard generation

Forces:

- both players use identical V8 Renegades
- each has a turret-mounted missile launcher with missile fire computer
- listed missile load includes HE, canister, smoke, and HiVAP rounds
- each player rolls drive skill from the WLF table

Drive skill table:

- die 1-4: drive skill 3
- die 5: drive skill 4
- die 6: drive skill 5

Setup:

- players roll to select one of the printed starting track layouts
- lead car is determined by die roll
- lead starts anywhere in the second track section
- following car starts in the first track section
- each driver chooses starting speed from 0 mph to maximum
- all generated track sections after initial setup contain sand or debris hazards

Road hazard generation:

- roll two dice
- higher die gives hazard type: 1-3 sand, 4-6 debris
- lower die determines side and number of markers: 1-2 left, 3-4 right, 5-6 both
- markers occupy three lanes in one space
- place markers from nearest to start and continue forward
- on straights, use three spaces; on curves, use two to five spaces
- overflow markers continue onto the next track section
- markers may be reused after both drivers pass them

Victory:

- first car to travel along ten sections of Bulldozer Alley wins

Implementation notes:

- printed track layouts must be traced
- hazard side placement depends on track direction and lane order
- scenario needs `roadHazardQueue` state for generated future sections

### WLF Game Two: Gang Leader Duel

Purpose:

- variant of Bulldozer Alley using custom Renegades

Forces:

- each player has $100,000 to build and equip a Renegade

Setup and victory:

- otherwise follows WLF Game One

Implementation notes:

- uses the same generated hazard rules as WLF Game One

### WLF Game Three: Outlaw Gang Battle

Purpose:

- larger outlaw gang fight with opposite-end deployment

Forces:

- each player has $200,000 to build an outlaw gang
- each gang must include at least two Renegades and three bikes
- players may exceed the minimum within budget

Setup:

- select starting track from WLF Game One layouts
- players begin at opposite ends, facing each other
- each side chooses starting speeds from 0 mph to maximum

Victory:

- play until no opposing vehicles remain alive or capable of doing damage
- vehicles leaving either end of the track are out of battle and cannot return
- winner is the player with at least one vehicle capable of moving and firing

Implementation notes:

- exit handling is different from chase scenarios: leaving the board removes a vehicle but is not necessarily a win condition

### WLF Game Four: Executive Escort

Purpose:

- escort/assassination scenario with Op, protected executive, and biker gang

Forces:

- one side controls an Op and executive car
- other side controls biker gang
- players may decide sides or roll; lower scorer takes Op and executive
- executive car is a custom saloon represented by an unarmed Interceptor or model
- executive car is effectively a V6 Interceptor with four points of carbon plastic armour on all facings and no weapons
- Op player has $100,000 to design and equip an Interceptor escort
- outlaw player has $100,000 to design and equip a biker gang
- trikes may be used

Setup:

- choose a starting track from WLF Game One layouts
- extend extra track using ordinary continuous generation
- roll one die for engagement form: 1-4 pursuit, 5-6 intercept
- pursuit: Op and executive start on track section 3 at 0 mph to maximum; bikers start on section 1 at 0 mph to maximum
- intercept: bikers start on section 1 at 0 mph to maximum; Op side starts facing the opposite direction on section 8, 9, or 10 at 60 mph

Victory:

- OCR does not preserve explicit victory text on page 46. Likely objective is assassination of the executive versus protecting/escaping the executive, but this must be proofread before implementation.

Implementation notes:

- requires protected-objective support in scenario state
- AI opposition should prioritize the executive if playing bikers and protect/intercept if playing Op

### WLF Game Five: Renegade Op

Purpose:

- pursuit between a renegade former Op and an agency pursuer

Restrictions:

- missiles cannot be used

Forces:

- each player has $100,000 to build an Interceptor

Setup:

- select starting track from WLF Game One layouts
- renegade starts on section 3
- pursuer starts on section 2
- further track is generated as in WLF Game Four

Victory:

- renegade wins by destroying or outdistancing the opponent
- agency Op wins by destroying or immobilizing the fugitive

Implementation notes:

- missile restriction should be a setup validator and equipment ban
- `outdistance` needs a numeric exit/distance rule proofread or scenario convention

### WLF Game Six: Trike Race

Purpose:

- trike race through dangerous track

Forces:

- both players use identical standard trikes

Setup:

- track is generated as in WLF Game One

Victory:

- first trike to complete twenty sections of track wins

Implementation notes:

- standard trike template depends on Bikes and Three-Wheelers / Vehicle Design agents

## Contract Setup Bridge

Dead Man's Curve campaign setup produces one or more scheduled engagements in a contract sequence. The Scenario Agent must provide the tactical setup templates used by the campaign approach result.

Campaign-to-scenario transition:

1. Campaign Agent validates legal unit pairing and attack declaration.
2. Campaign Agent resolves approach and chooses engagement type.
3. Scenario Agent receives participating units, eligible vehicles/drivers, engagement type, and any approach restrictions.
4. Scenario Agent validates force selection, deployment, track setup, initial speeds, and scenario-specific bans.
5. Scenario Agent creates tactical engagement state.
6. Tactical rules resolve the engagement.
7. Campaign Agent consumes the tactical outcome and applies post-engagement phases.

Required bridge fields:

- `contractId`
- `campaignSequenceId`
- `engagementType`: `pursuit`, `intercept`, `ambush`, or standalone scenario id
- `attackerUnitId`
- `defenderUnitId`
- `participantVehicleIds`
- `participantDriverIds`
- `forceSelectionValidation`
- `trackSetup`
- `deploymentZones`
- `initialSpeeds`
- `cruisingRestrictions`
- `engagementObjective`
- `victoryCondition`
- `aiProfile`

### Campaign Engagement Types

`pursuit`:

- typically maps attacker/target to chase/lead roles
- lead side starts ahead and tries to escape or outdistance
- use chase-style victory and exit handling

`intercept`:

- sides may start facing each other
- setup should support attacker choosing speed and deployment range when allowed
- use active-side elimination or contract objective as victory

`ambush`:

- setup details are OCR-damaged in campaign source and need proofread
- must support surprise/restriction flags, concealed attackers if present in proofread rules, and exemption from some attacker objective penalties where campaign rules specify

## AI and Opposition Setup Implications

Scenario setup should expose enough structured data for computer-controlled opposition without giving the AI illegal shortcuts.

Required AI setup data:

- side role and objective priority
- escape target or finish boundary
- protected vehicle ids
- target vehicle ids
- deployment constraints
- equipment restrictions
- whether the side may choose pursuit/intercept
- whether the side is currently under cruising restrictions
- scenario-specific risk preference, such as race, assassination, escort, or elimination

AI must choose from legal tactical actions returned by the engine. Scenario data may guide goal scoring but must not create direct movement, firing, or damage shortcuts.

## UI Requirements

The unified UI must represent scenario and contract setup in the `Contract Setup` mode described by `docs/ui/unified-ui-spec.md`.

Required setup panels:

- scenario/contract list
- scenario detail and source refs
- side roles and objective summary
- force selection and budget validation
- vehicle/driver records
- track setup preview
- deployment zone selection
- starting speed selection
- setup validation warnings
- AI/opposition preview

Starting a scenario must call a scenario setup transition that creates tactical state. The UI must not assemble tactical state from raw form fields.

## Ambiguities and OCR Doubts

| Source | Issue | Implementation handling |
|---|---|---|
| Core p87 | Game One shaded start sections and finish line are diagram-based. | Trace diagram before implementation. |
| Core p87 | Game Two six possible track layouts are diagram-only in OCR. | Trace all layouts into track-piece sequences. |
| Core p88 | Game Three weapon package table has OCR noise. | Rows are drafted but require page proofread before data lock. |
| Core p88 | Game Four driver skill row for die 4 is damaged. | Provisional value is drive skill 3; verify. |
| Core p89 | Game Eight fixed generated section count OCR is damaged. | Verify whether setup uses seven sections or another count. |
| Core p89 | `outdistancing` is not numerically defined in scenario OCR. | Coordinate with track/scenario proofread before engine tests. |
| WLF p45 | WLF Game One printed track layouts are diagram-only in OCR. | Trace layouts before implementation. |
| WLF p45 | Missile load text has OCR damage. | Verify exact missile sequence and names against page image. |
| WLF p46 | WLF Game Four victory conditions are missing/damaged in OCR. | Proofread before implementation. |
| WLF p47 | WLF Game Five setup text has damaged section references. | Provisional section 3/2 setup must be verified. |
| WLF p47 | WLF Game Six standard trike template not present in scenario extract. | Requires Bikes/Three-Wheelers and Vehicle Design outputs. |
| Campaign WD124 p20-p22 | Approach, intercept, pursuit, and ambush setup details are damaged. | Campaign contract templates remain draft until proofread. |

## Candidate Tests

### Scenario Data Validation

- Every scenario id is unique.
- Every scenario has source refs, side definitions, setup steps, victory condition, and proofread status.
- Every vehicle template reference is either resolvable or marked `needsVehicleDesign`.
- Every track layout reference is either resolvable or marked `needsTrace`.

### Core Scenario Setup

- Core Game One creates two Renegades with drive skill 3 at 60 mph.
- Core Game One refuses to start without a finish boundary.
- Core Game Two selects a track layout from die result 1-6.
- Core Game Three applies offensive/defensive package choice before lead/chase roll.
- Core Game Three starting speed veto loop rejects 20, 30, and 40 mph results and allows permitted high-speed vetoes.
- Core Game Four enforces $50,000 budget and at least one weapon.
- Core Game Five lead exit is the end of the seventh generated section.
- Core Game Six enforces outlaw gang minimum vehicle composition.
- Core Game Eight pursuit setup delegates to Game Six while intercept setup creates opposed-facing deployment.

### White Line Fever Scenario Setup

- WLF Game One creates identical missile Renegades and lets each side choose speed from 0 to max.
- WLF Game One hazard generation maps high die to sand/debris and low die to side/marker count.
- WLF Game One overflow hazard markers carry to the next section.
- WLF Game Three removes vehicles leaving either end without granting automatic victory.
- WLF Game Four creates a protected executive vehicle with no weapons.
- WLF Game Five rejects missile-equipped Interceptors.
- WLF Game Six ends when a trike completes twenty sections.

### Contract Bridge

- A campaign approach result can instantiate pursuit, intercept, or ambush setup only through Scenario Agent data.
- Contract setup refuses ineligible campaign vehicles or drivers.
- Contract setup records engagement objective state for campaign post-engagement checks.
- Tactical victory result does not directly pay bounty, loot, mileage, or repair.
- Campaign post-engagement can consume scenario outcome and participant ids.

### AI Setup

- AI setup receives objective hints but only legal engine actions.
- Pursuit AI receives an escape/stop objective.
- Escort AI receives protected vehicle id.
- Elimination AI receives active-opposition objective.

## Dependencies

Required from other agents:

- Track Geometry: traced track layouts, continuous generation, exits, section counting, curve links.
- Turn/Movement: starting speed to speed factor, legal action generation, movement off exit boundaries.
- Vehicle Design: Renegade, Interceptor, Bike, Trike, GenTech/executive car, budgets, mounts, weapons, equipment legality.
- Shooting/Damage/Hazards/Rams: active/capable vehicle status and immobilized/wrecked state.
- Bikes and Three-Wheelers: bike/trike templates and gang minimum validation.
- Campaign: legal pairings, approach result, engagement objective, post-engagement sequence.
- Unified UI: contract setup panels and tactical state handoff.

## Handoff

Section: Scenarios and Contract Setup

Source files:

- `docs/rules/core/14-scenarios.md`
- `docs/rules/white-line-fever/08-scenarios.md`
- `docs/rules/clean/campaign.md`

Source pages:

- Dark Future Rulebook pages 87-90
- White Line Fever pages 45-48
- Dead Man's Curve campaign bridge from White Dwarf 124 pages 18-22

Cleaned files:

- `docs/rules/clean/scenarios-contracts.md`

Data files:

- `data/rules/scenarios.json`

Tests:

- Candidate tests listed above. No engine tests added in this extraction pass.

Ambiguities:

- Listed in `Ambiguities and OCR Doubts`.

Dependencies:

- Listed in `Dependencies`.

Schema changes requested:

- Add scenario-level `sideRole`, `forceDefinition`, `trackSetup`, `deploymentZone`, `startingSpeedRule`, `victoryCondition`, `contractBridge`, `aiSetup`, and `setupValidation` structures to the eventual canonical schema.
