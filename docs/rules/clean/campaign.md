# Campaign Rules

> Sources:
> - `docs/rules/dead-mans-curve/01-white-dwarf-124-pages-18-31.md`
> - `docs/rules/dead-mans-curve/02-white-dwarf-125-pages-68-76.md`
>
> Status: cleaned implementation summary from raw OCR. This is not a full transcription. Numeric tables marked `needsProofread` must be checked against page images before implementation.
>
> Publication note: the White Dwarf 125 reference to White Dwarf 123 is treated as a publication-delay typo. The first part for this project is White Dwarf 124 pages 18-31.

## Scope

Dead Man's Curve adds persistent campaign play to Dark Future. A campaign is a series of contract sequences. Each sequence schedules one or more engagements, resolves those tabletop fights, then applies persistent consequences to drivers, vehicles, funds, reputation, mental state, recruitment, and equipment.

The campaign engine must not replace tactical rules. It schedules engagements, records outcomes, and applies before/after effects. Tactical combat remains owned by the turn, movement, shooting, damage, hazards, and rams agents.

## Campaign Entities

### Player

A player controls one or more campaign units. All players should start a campaign with the same number of units, even if units later retire or are destroyed.

Required state:

- `playerId`
- active `unitIds`
- retired or destroyed unit history
- attack declaration order roll for the current sequence

### Unit

A unit is either a sanctioned operative structure or an outlaw structure.

Unit kinds:

- `independentOp`: a single sanctioned operative with one driver and vehicle.
- `agency`: a sanctioned operative organisation with multiple drivers and vehicles.
- `outlawGang`: a criminal gang with multiple drivers and vehicles.
- `renegadeOp`: an operative who has lost sanction and now counts as outlaw-side for campaign/media purposes.

Required state:

- `unitId`
- `kind`
- `playerId`
- `driverIds`
- `vehicleIds`
- `funds`
- `store`: surplus weapons, turrets, engines, and allowed stored equipment
- `bankedFunds` or hidden funds; rules treat saved cash as available in later sequences
- `failedEngagementObjectiveCount`
- `activeThisSequence`
- `pendingMediaPsychosis`: psychosis points from media rolls to add at the next psychosis phase
- `recruitmentLocks`: restrictions from media manipulation results
- `expensesDue`: agency running costs and experienced-driver payments

### Driver

Drivers and characters are interchangeable terms in the source. Use canonical engine term `driver`.

Required state:

- `driverId`
- `unitId`
- `role`: sanctioned, outlaw, renegade
- `driveSkill`
- `mileagePoints`
- `psychosisPoints`
- `kudosPoints`
- `mediaVisibility`
- `disorders`
- `injuryState`
- cybernetics and software
- owned vehicle ids, including personal vehicle for experienced recruits
- temporary next-engagement effects, such as investigation suspension or high-visibility approach penalty
- history flags used for kudos modifiers, such as prior agencies/gangs and vehicle-role mismatch

### Vehicle

Campaign vehicle state persists between engagements.

Required state:

- `vehicleId`
- `ownerDriverId` or `unitId`
- roadworthy state
- partial damage by location/system
- unrepaired critical hits
- terminal damage/write-off state
- mounted equipment
- stored/salvaged equipment state
- hack-damaged systems needing repair

## Starting Campaign State

Each player begins with the same agreed starting funds: `$100,000`.

Everything a unit uses in its first engagement must be bought from starting funds, except the first driver allowance:

- A sanctioned operative starts as a solitary independent Op. The first drive-skill 2 driver is free; the vehicle and equipment are paid from funds.
- An outlaw player starts with a gang: the first two drive-skill 2 drivers are free; vehicles and equipment are paid from funds.
- Players should agree which vehicles and equipment are legal in the campaign before play starts. The source allows the vehicle list to be widened by agreement, including role-mismatched vehicles such as an Op with a Renegade or an Outlaw with an Interceptor.

## Contract Sequence

A contract sequence represents a campaign time block. All engagements scheduled within a sequence are treated as broadly simultaneous and may be played in any convenient order. No new sequence starts until every scheduled engagement has been played and every post-engagement phase has been completed.

Canonical sequence:

1. Attack declarations.
2. Approach and engagement setup.
3. Tactical engagements.
4. Injury phase.
5. Salvage phase.
6. Mileage phase.
7. Pay phase.
8. Psychosis phase.
9. Kudos phase.
10. Recruitment phase.
11. Re-equipment phase.
12. Record keeping phase.

This ordering is implementation-critical. Some resources cannot be spent before they are earned, and some psychosis from media is delayed until the next sequence.

## Attack Declarations

At the start of a contract sequence, players determine which units will fight.

Restrictions:

- Each unit may make only one attack declaration in a contract sequence.
- Each unit may be the target of only one attack declaration in a contract sequence.
- A unit that is already the target of an attack declaration cannot make its own attack declaration.
- The units involved must form a legal engagement pairing.
- A unit may decline to be the target of an attack declaration only by retiring from the campaign immediately. That player cannot create a replacement unit until the start of the next contract sequence.

Legal engagement pairings from WD124 page 18:

- sanctioned Op vs outlaw gang
- outlaw gang vs outlaw gang
- outlaw gang vs renegade Op
- sanctioned Op vs renegade Op
- renegade Op vs renegade Op

Declaration order:

- Each player rolls one die.
- Starting with the highest roller and proceeding clockwise, each player may declare one attack with one eligible unit.
- After every player has had the chance to declare with one unit, the order continues for players with additional eligible units.
- No engagements are played until all declarations are complete.

Units that neither attack nor are attacked do not enter an engagement this sequence. Their drivers receive no Op pay; outlaw units may still receive loot according to the pay rules. Drivers in inactive units with more than two psychosis points must still make the required psychosis test.

## Approach and Engagement Setup

Once two units are paired:

- The attacker chooses how many of its vehicles participate, subject to engagement objective constraints.
- The defender uses all vehicles in the unit, unless a later agency/gang rule or scenario rule allows reserve handling.
- Both sides are entitled to know the opponent drivers' drive skills and the total dollar value of the opposing unit before approach.
- The two sides roll for approach. The approach winner chooses the engagement type within the allowed result.

Approach roll inputs:

- one die per side
- drive-skill bonus from the least skilled participating driver
- approach bonuses purchased before the approach roll

Least skilled driver approach bonus:

- drive skill `4-5`: `+1`
- drive skill `6-7`: `+2`
- drive skill `8-9`: `+3`
- drive skill `10`: `+4`

Purchased approach information:

- Sanctioned Ops/agencies may buy Ratcatchers data before an engagement at `$15,000` per `+1`.
- Outlaws may buy grapevine information before an engagement at `$10,000` per `+1`.
- Either side may buy at most `+3` in approach bonuses for a single engagement.

Approach result:

- Calculate attacker total minus defender total.
- On `<= 0`, the defender chooses intercept, pursuit, or ambush.
- On `1-2`, the attacker chooses intercept or pursuit.
- On `>= 3`, the attacker chooses intercept, pursuit, or ambush.

Engagement types:

- `intercept`: combat engagement.
- `ambush`: combat engagement.
- `pursuit`: flight engagement.

The chosen type affects setup and later mileage calculation.

Setup summaries:

- In an `intercept`, generate `7` track sections. The approach winner chooses which end they start from. The loser places vehicles at the opposite end, anywhere within the first two track sections, facing the other end and under cruising restrictions. The winner then places vehicles within the first two sections at the nominated end, heading toward the middle and without cruising restrictions.
- In a `pursuit`, generate `7` track sections. The loser places vehicles on the fourth track section facing toward the seventh section and under cruising restrictions. The winner starts on the first track section facing along the rest of the track, at minimum `60 mph` unless on a curve where safe speed is the minimum, and no faster than vehicle top speed.
- In an `ambush`, generate `9` track sections. The loser places vehicles on the middle track section, chooses one direction of travel for all loser vehicles, and is under cruising restrictions. The winner places vehicles on the two sections at either or both road ends, facing any direction unless behind the target, where they must face the target. The ambusher may also place vehicles in the two edge lanes of any section; these start at `20 mph` / speed factor `1` and may face either way.

Cruising restrictions:

- Some engagement starts place one side under cruising restrictions until hostile vehicles are spotted.
- Cruising vehicles must travel in the same direction, occupy the right side of the road, maintain cruising speed, obey curve safety limits, and avoid drifting on curves.
- Restrictions end when the cruising side spots a hostile vehicle by line of sight or a vista roll.
- If hostile vehicles are visible at start, cruising restrictions end immediately after setup, but the affected side still begins at cruising speed.

## Engagement Objective

The attacking unit must show serious intent before it can safely disengage.

Objective:

- At least one attacking vehicle must remain within four spaces of at least one defending vehicle for six phases.
- The six phases do not need to involve the same pair of vehicles if either side has multiple vehicles.
- A simple counter should track successful phases.

Failure penalties:

- Sanctioned Ops that deliberately fail the objective forfeit pay and mileage for the engagement. A second deliberate failure causes loss of licence and removal from the campaign.
- Outlaws that deliberately fail forfeit loot and mileage for the engagement. A second deliberate failure causes the unit to disband and be removed.

Objective failure exceptions:

- If the attacker cannot meet the objective because every attacking vehicle is destroyed, disabled, or otherwise made inactive before it can reasonably reach the defender, the failure is not deliberate.
- If an attacking vehicle takes a critical hit before it can reasonably satisfy the objective, the failure is not deliberate.
- If crashes, forced movement, or loss of control prevent contact before the attacker can reasonably satisfy the objective, the failure is not deliberate.
- If the defender leaves, escapes, or is removed from play before the attacker can reasonably reach objective range, the failure is not deliberate.
- If the setup is an ambush, the ambushed unit is not subject to the attacker objective restriction.
- These exceptions prevent objective failure penalties; they do not change normal salvage, injury, mileage, or pay rules unless those rules separately require an active vehicle or completed objective.

## Ending Engagements and Salvage Rights

An engagement continues until only one side has active vehicles in play.

An active vehicle must have:

- a working engine
- usable ammunition and a means to fire it, excluding passives
- a driver who has not suffered a disabling critical result

The side with the only active vehicles at the end gains salvage rights. A player must have an active vehicle left at the end of the engagement to claim salvage. If neither side has active vehicles, no side claims salvage and equipment is lost to the desert.

## Injury, Death, and Escape

Post-engagement injury determines whether a driver continues and what state carries forward.

Driver conditions:

- `unhurt`: no campaign effect.
- `hurt`: cosmetic or minor injuries only.
- `injured`: drive skill is reduced by 1 for the following contract sequence, then returns to normal.
- `limbDisabled`: does not heal naturally; use cybernetics rules for replacement.

Recovery clauses:

- Ops may pay for a recovery clause before an engagement, apparently `$1,000` per contract sequence.
- If an insured Op dies from an engagement, roll one die. On a sufficiently high result, emergency care restores the driver and the driver misses the next contract sequence.
- The exact success number and restrictions need proofread from WD124 page 26.
- Invoking a recovery clause after roadfight fatality gives psychosis points per the psychosis rules.

Escape:

- Losing-side drivers whose vehicles are destroyed or abandoned may need rescue.
- Scavenger rescue appears to cost `$200`; a driver who cannot or will not pay risks being lost to the desert.
- If every member of the non-winning unit must be rescued by scavengers or recovery clauses, that unit cannot claim salvage.

## Salvage

Salvage happens before pay, so players must already have cash available to pay scavengers.

Salvage rules:

- The winner may salvage equipment from vehicles made inactive during the engagement.
- Salvaged equipment may be fitted, sold later, or stored.
- Weapons, turrets, engines, and some miscellaneous equipment can be removed.
- Driving systems, fire-control computers, armour, and engine add-ons generally cannot be individually salvaged.
- Whole vehicles may sometimes be recovered, allowing armour and otherwise non-removable systems to remain with the vehicle.
- Vehicles with terminal damage are write-offs and cannot be repaired or used again, but equipment may still be salvaged from them at higher cost.
- Critical-hit damage on salvaged equipment must be repaired before use.

Tables needing structured extraction after proofread:

- equipment salvage cost by item and source state
- vehicle salvage cost and critical repair cost
- list of equipment categories that cannot be salvaged

## Mileage and Progression

Mileage points represent road-combat experience and influence both drive skill and kudos.

Only surviving drivers calculate mileage after an engagement.

Engagement forms:

- Combat engagements use the combat mileage table.
- Flight engagements use the flight mileage table.

Common visible rules from WD124 page 28:

- Each participating surviving driver receives a point for fighting the engagement.
- Drive skill bonus is based on opponent highest drive skill minus 2; negative results are ignored.
- Combat mileage uses a casualty ratio: original number of drivers divided by survivors, rounded down.
- Flight mileage adds points for enemy vehicles disabled or escaped from and subtracts for friendly vehicles disabled.

The exact combat/flight table wording needs proofread before data extraction.

Drive skill thresholds from OCR:

| Mileage points | Drive skill |
|---:|---:|
| 0 | 2 |
| 5 | 3 |
| 10 | 4 |
| 20 | 5 |
| 40 | 6 |
| 60 | 7 |
| 120 | 8 |
| 100? | 9? |
| 200 | 10 |

The `100`/`120` ordering is probably an OCR/table-layout error and must be checked against WD124 page 28. Drive skill can never exceed 10.

## Pay and Funds

Money persists between contract sequences.

Ops:

- Only Op units that fought in the current contract sequence receive pay.
- Ops claim bounty based on outlaw driver drive skill at the time of the roadfight.
- A surviving Op receives half bounty for each enemy car that crashes or suffers at least one terminal damage point.
- Full bounty is paid if the outlaw driver is killed.

Outlaw bounty table from OCR, needs proofread:

| Drive skill | Bounty |
|---:|---:|
| 2 | $8,000 |
| 3 | $12,000 |
| 4 | $20,000 |
| 5 | $40,000 |
| 6 | $80,000 |
| 7 | $120,000 |
| 8 | $250,000 |
| 9 | $500,000 |
| 10 | $1,000,000 |

Outlaws:

- Outlaw gangs and renegade Ops receive loot based on criminal activity between engagements.
- A gang with at least one active vehicle at the end of an engagement takes a loot test.
- Outlaws may still get loot when not roadfighting, subject to sequence and objective rules.

Loot test outline:

- Roll one die per surviving car.
- Bikes/trikes count as half a die; roll one die per two bikes/trikes, ignoring a single leftover.
- Maximum four dice.
- Add a leader drive-skill modifier based on highest gang drive skill.
- Add arsenal bonus: sum ranged-weapon damage modifiers in the unit, divide by 4, round up, maximum bonus 5.
- Multiply the final total by `$5,000`.

The leader modifier table is damaged and must be proofread from WD124 page 29.

## Psychosis and Disorders

Psychosis points persist between contract sequences.

Psychosis gain:

- At the end of every engagement, each surviving driver gains psychosis for friendly driver fatalities and half as much for opposing fatalities, rounded down.
- A limb loss gives 1 psychosis point.
- Invoking a recovery clause after roadfight fatality gives psychosis points; OCR suggests 6, but this must be proofread.
- Each roll on any Media Table gives 1 psychosis point, added in the psychosis phase of the next contract sequence.
- Fitting cybernetic enhancement also adds psychosis; see cybernetics.

Psychosis test:

- Drivers with 2 or more psychosis points test in the psychosis phase.
- Roll two dice.
- If the total is greater than current psychosis points, no disorder is gained.
- If the total is less than or equal to psychosis points, make a disorder test.

Disorder test:

- Roll one die, add current psychosis points, and consult the severity table.
- After gaining a disorder, roll 2d6 and subtract that amount from psychosis points, never below 0.

Outlaw gang exception:

- The first outlaw gang member who gains a disorder rolls normally.
- Later gang members who fail psychosis tests gain the same disorders as that first member in the same order, reflecting a shared gang identity.

Disorder categories:

- harmless
- minor
- costly
- dangerous

Implementation note: disorders produce persistent modifiers, temporary engagement modifiers, compelled choices, expenses, recruitment/attendance effects, and vehicle/equipment presentation state. They should be represented as structured effects rather than prose flags.

Disorder duration:

- Some effects are one-off; others last a number of contract sequences.
- Duration roll uses one die plus category modifier: harmless `-2`, minor `-1`, costly `0`, dangerous `+1`; results below 1 count as 1.
- A GM may roll duration secretly.
- Worn-off disorders may leave cosmetic habits if the player wants.
- Contradictory disorders cancel or replace relevant effects.

Disorder tables require a separate proofread pass from WD124 pages 30-31.

## Kudos, Media, and Fame

Kudos is calculated in every kudos phase for surviving drivers.

Base kudos:

- `floor(mileagePoints / 10)`.
- If mileage is below 10, the driver earns no kudos and ignores eccentricity/media rolls.

Eccentricity:

- Disorders and status add or subtract kudos modifiers.
- Modifiers are cumulative and compulsory.
- OCR for the eccentricity table on WD125 page 69 is mostly readable but several entries need proofread.

Media visibility:

| Kudos points | Visibility |
|---:|---|
| 0-5 | obscure |
| 6-10 | known |
| 11-15 | respected |
| 16-20 | famous |
| 21-25 | star |
| 26+ | livingLegend |

Media rolls:

- Obscure drivers gain no special media advantages.
- Higher visibility drivers who fought in the sequence may roll on Media Tables.
- The player may decline media rolls to avoid stress and adverse attention.
- If entitled to multiple media rolls, the player can take the first and then decide whether to take the second.
- Renegade Ops roll as Outlaws.
- Every Media Table roll adds 1 psychosis point in the next sequence's psychosis phase.

Media Tables:

- Op results include appearance fees, interviews, advertising, free weapons/equipment, TV rights, and royalties.
- Outlaw results include extra protection, organised crime payments, vulture backhanders, black-market credit, and TV documentary payments.
- Black-market credit can only be spent on weapons/equipment and is lost if unspent at the start of the next contract sequence.
- Free equipment/weapon results must be spent on the indicated category; unused value is lost.

Media manipulation:

- Once per contract sequence, after Media Table rolls, roll one die for each driver with at least 10 mileage points.
- Add `+1` for each Media Table roll that driver made in the sequence.
- On 1-5, nothing unusual happens.
- On 6+, roll on the Media Manipulation Table.

Op manipulation results:

- high visibility: next approach roll treats drive skill as 2 lower.
- blackmail: pay `10000 * kudosScore` or lose 2d6 kudos.
- investigation: miss next engagement/sequence; on a failed follow-up roll lose licence and retire or become renegade; bribes can modify the roll.
- compensation: pay legal costs based on kudos and miss next sequence; follow-up roll can add further costs and kudos loss; bribes can modify.
- libel: pay `5000 * kudosScore` or lose 2d6 kudos.
- assassination: roll one die; on 1, driver is killed.

Outlaw manipulation results:

- organised crime: pay `10000 * highestGangKudos` or gang disbands.
- member killed: lowest drive-skill gang member dies; replacement recruitment delayed until end of next sequence.
- vigilante: roll one die per character; each 6 kills that character; new recruits delayed until end of next sequence.
- internal feud: roll one die per gang member; each 1 leaves with vehicle/equipment and may form a hostile new gang under another player.

## Recruitment and Expansion

Recruitment occurs after kudos and before re-equipment.

Agencies:

- An independent Op can form an agency by paying a `$10,000` formation cost.
- Once formed, the agency can license new Ops for `$5,000` each.
- New novice drivers begin at drive skill 2.
- The agency must provide vehicles for new novice drivers.
- Experienced drivers have drive skill above 2 and may bring their own vehicles.
- Experienced drivers must be paid 10% of the value of their own vehicle at the end of each contract sequence, plus any salvage/bounty entitlement.
- If not paid, they leave immediately and will not work for that agency again.
- If an experienced driver sits out a contract sequence, the agency does not have to pay them, but the driver leaves.
- The agency founder does not take normal agency wages; his money comes from salvage, bounty, and media deals.
- Agencies can own any number of vehicles and choose drivers/vehicles after accepting or declaring an attack but before approach.
- An agency may fight multiple engagements in one sequence if it uses different drivers and vehicles for each engagement.
- Bounty from an agency engagement is split evenly between surviving participating drivers and the agency.
- Salvage claimed by agency Ops is allocated among participating drivers however the controlling player chooses; the agency itself claims none.
- Agency running costs are `$10,000` per contract sequence while the agency has more than one driver.
- If the agency cannot pay expenses, it must disband or become an outlaw/renegade structure.
- If reduced to one driver, running costs cease and central funds may be absorbed into that driver's finances while the agency shell may remain.

Gangs:

- Gangs may recruit new drivers like agencies.
- A gang must operate a central fund.
- Experienced drivers provide their own vehicles and must be paid 10% of vehicle value per sequence, plus entitled salvage/loot, and must fight one engagement per sequence.
- Original starting gang members do not become subject to experienced-driver rules just because their drive skill rises.
- Gangs reduced to a single active vehicle and two surviving drivers may obtain a free basic V6 Renegade; weapons/equipment must come from gang resources. OCR wording needs proofread.
- A gang must disperse if all vehicles are written off.
- A player may save one surviving character to start a new gang with `$100,000` and one new driver, then must buy two vehicles; verify exact wording from WD125 page 72.

Random driver generation:

- Novice drive-skill 2 drivers are always available.
- Experienced-driver availability depends on the Driver Generation Table.
- Roll one die and cross-reference by Op/Outlaw.
- Funds column indicates maximum value of the experienced driver's own vehicle; unspent allowance is lost.
- A generated driver starts with the minimum mileage for their drive skill.
- Roll one die per drive skill? OCR is unclear; this determines psychosis points and number of pre-use psychosis tests.
- A generated driver starts with cash equal to `$2,000 * driveSkill`.

Driver Generation Table from OCR needs proofread; several rows are damaged.

## Repair, Re-equipping, and Redesign

Re-equipment happens after recruitment.

Repair:

- Partial vehicle damage may be carried forward or repaired.
- Repairing 1 point of damage costs `$250`.
- Vehicle characteristics are restored as damage rises past damage increment thresholds.
- Critical hits must be repaired; each critical repair costs `$250`.
- Terminal-damage vehicles cannot be repaired or used; equipment may still be salvaged.
- Repair may be delayed, but a unit must always have enough roadworthy vehicles for its drivers or retire extra drivers.

Resale:

- Surplus weapons, turrets, or engines may be sold.
- Other equipment generally may not be sold.
- If stripping equipment from a player's own vehicle, pay `$250` per item first.
- Roll one die per item. Each pip is 10% of original purchase price, then add 30%; the player must accept that offer.
- Ops use ordinary purchase price; Outlaws selling sanctioned weapons use black-market value.
- Players may not sell equipment to other players, but may transfer/sell within the same unit.

Redesign and new vehicles:

- Vehicles may be modified within normal design restrictions and available funds.
- After salvage or purchase costs are paid, no extra labour cost is charged for removing or adding weapons.
- Update vehicle records for all characteristic changes.
- Drivers may own multiple vehicles and choose which to use after attack declaration/acceptance and before approach.
- Newly recruited drivers must receive vehicles during re-equipment or are lost.

## Cybernetics, Software, and Hacking

Cybernetics are bought in re-equipment. This section touches tactical rules and should be coordinated with Vehicle Design, Damage, Shooting, and AI agents.

General:

- Replaces the core limb-disabled driver critical result.
- Each cybernetic enhancement adds 1 psychosis point, except the plug/interface adds 2.
- This is not additional to the psychosis point from the original limb-disabled critical if replacing that loss.
- Effects apply immediately.

Cyber devices:

- arms: `$8,000` each; one replacement arm causes `-1` drive skill, both arms no modifier.
- legs: `$10,000` each; one replacement leg causes `-1` drive skill, both legs no modifier.
- artificial eyes: `$15,000` for a pair; ignore negative smoke/night driving modifiers.
- plaskin: `$18,000`; gives a driver-critical saving throw on crashes/rolls.
- holoskin: `$25,000`; plaskin benefits plus environmental/pollutant protection.
- plug/interface: `$30,000` and 2 psychosis points; enables software and hacking.

Software:

- fire control software: turret and missile variants, equivalent to relevant fire-control decks; one OCR-visible cost is `$15,000`.
- drive software: bike version equivalent to computer drive, `$8,000`; car version equivalent to robotic drive, `$18,000`; requires artificial arms and legs.
- doublethink: `$8,000`; removes normal dual-action penalty.
- roadfight: `$40,000`; suite containing the listed software routines, with each subroutine requiring its normal cybernetic prerequisites.
- hack-attack modules: `$2,000` each, up to 6.
- head-hunt modules: `$2,000` each, up to 6.

Hacking:

- Any driver with plug and Hack-Attack software can hack.
- Vehicles with robotic drive, computer drive, or fire-control devices are vulnerable, whether hardware or software.
- At the beginning of an engagement when cruising restrictions end, drivers with relevant systems know whether opponents use such systems.
- A hack attack is declared as an action, may be part of a dual action, consumes one shoot action, and cannot be combined with another shoot action.
- A driver cannot hack a target already victim of a successful hack attack, but may target other drivers.
- Roll one die, add attacker's Hack-Attack module count, subtract defender's Head-Hunt module count, then consult the Hack Attack Table.

Hack Attack Table from OCR:

| Total | Result |
|---:|---|
| 0 or less | backfire |
| 1-4 | neutralised |
| 5-8 | system malfunction |
| 9+ | system hostility |

Effects:

- backfire: defensive software traces the attack. On 1-5, attacker's Hack-Attack modules are wiped and attacker's software stops functioning for the rest of the engagement. On 6, attacker suffers a KO driver critical.
- neutralised: attack/defence modules clash; both players roll and may lose involved modules on 6.
- system malfunction: attacker chooses one qualifying opposing system; it stops functioning for the rest of the engagement.
- system hostility: qualifying systems behave harmfully for the rest of the engagement; listed effects include robotic-drive handling penalty, computer-drive handling/acceleration/braking penalties, missile fire computer attacking friendlies only, and turret fire computer firing at friendly targets only.
- hacked systems cannot be disabled to avoid the effect.
- hack-damaged systems cost `$500` to repair in re-equipment. Destroyed hack-damaged systems cannot be repaired.

## Persistent State Summary

The campaign save model must persist:

- current contract sequence number
- players, units, drivers, vehicles, stores, and funds
- declared attacks and scheduled engagements for the active sequence
- approach modifiers purchased and temporary approach penalties
- engagement outcomes: participants, casualties, disabled vehicles, destroyed vehicles, terminal damage, salvage rights, objective result
- driver mileage, drive skill, psychosis, pending media psychosis, disorders, kudos, media visibility, injuries, cybernetics, software
- vehicle damage, critical hits, terminal/write-off state, salvage/recovery state, hack damage
- recruitment locks, experienced-driver obligations, agency running costs, gang disband conditions
- campaign end state and winner/side result

## Dependencies

Required from other agents:

- Tactical outcome records from Scenario/Rules Engine.
- Vehicle values and equipment categories from Vehicle Design.
- Damage, critical, KO, limb disabled, terminal damage, and crash state from Damage/Hazards.
- Active vehicle determination from engine state.
- Legal action/hack action integration from Shooting/Turn Sequence.
- UI panels from Unified UI Agent for roster, garage, contracts, post-engagement phases, and rule logs.

## Ambiguities and OCR Doubts

| Source | Issue | Implementation handling |
|---|---|---|
| WD124 p18 | Starting funds and free starting drivers. | Resolved from page image: `$100,000`, Op first drive-skill 2 driver free, outlaw first two drive-skill 2 drivers free. |
| WD124 p18 | Starting vehicles and equipment. | Vehicles and equipment are bought from starting funds. |
| WD124 p20 | Approach roll structure and purchased information costs. | Resolved as `d6 + least-skilled-driver bonus + purchased bonuses`; Ratcatchers cost `$15,000` per `+1`, grapevine costs `$10,000` per `+1`, maximum `+3`. |
| WD124 p20 | Approach result table bands. | Resolved as attacker total minus defender total: `<= 0` defender chooses all types, `1-2` attacker chooses intercept/pursuit, `>= 3` attacker chooses all types. |
| WD124 p21 | Intercept/pursuit/ambush setup details. | Summary setup rules are captured; exact diagram-level deployment geometry remains scenario/track implementation detail if needed. |
| WD124 p22 | Non-deliberate engagement-objective exceptions. | Resolved as exceptions for unavoidable inactive/lost vehicles, critical hits, crashes or loss of control before contact, defender escape/removal before objective range, and ambushed units. |
| WD124 p26 | Recovery clause success roll and exact psychosis wording are damaged. | Do not implement recovery odds until verified. |
| WD124 p27 | Salvage and vehicle recovery tables have severe OCR errors. | Require page-image table extraction. |
| WD124 p28 | Campaign Mileage Table has likely row-order OCR error around 100/120. | Verify thresholds before implementing progression. |
| WD124 p29 | Loot leader drive-skill modifier table is damaged. | Do not implement loot modifier table until proofread. |
| WD124 p29 | Recovery-clause psychosis amount OCR says `06`; likely `6` or `D6`. | Verify before implementation. |
| WD124 p30-p31 | Disorder severity and disorder result tables contain many OCR errors. | Separate table-cleaning pass required. |
| WD125 p69 | Eccentricity factor table has several damaged entries. | Extract as structured data only after proofread. |
| WD125 p72 | Agency formation cost. | Resolved from page image: `$10,000`. |
| WD125 p72 | Driver Generation Table rows are damaged. | Require proofread before random recruitment. |
| WD125 p75 | Turret computer hostility result. | Resolved from page image: hostile turret fire computer fires at friendly targets only. |

## Candidate Tests

### Contract Sequence

- A sequence cannot start post-engagement phases until all scheduled engagements are resolved.
- Post-engagement phases run in the exact canonical order.
- Money earned in pay cannot be used for salvage in the same sequence.
- Unspent funds persist into the next sequence.

### Attack Declarations

- A unit can declare only one attack per sequence.
- A unit cannot be attacked by more than one unit in a sequence.
- A target unit cannot declare an attack after being targeted.
- Illegal pairings such as sanctioned Op vs sanctioned Op are rejected.
- Declining an attack retires the unit and blocks replacement until the next sequence.

### Engagement Objective

- Six qualifying phases within four spaces satisfy the objective.
- The counter can use different attacking/defending vehicle pairs across phases.
- Deliberate failure applies first-offence penalties and increments failure count.
- Second deliberate failure removes an Op licence or disbands an outlaw unit.
- Ambushed units are exempt from objective restriction.

### Salvage and Repair

- Salvage rights go only to the side with the last active vehicle.
- No active vehicles means no salvage.
- Salvage cannot be paid using pay earned later in the sequence.
- Terminal-damage vehicles are write-offs but can provide salvageable equipment.
- Partial damage can be carried forward or repaired at `$250` per point.
- Critical repairs cost `$250` each.

### Mileage and Progression

- Surviving combat participants receive engagement mileage.
- Highest opposing drive skill below threshold never creates negative bonus.
- Casualty ratio rounds down.
- Drive skill updates immediately when a mileage threshold is crossed.
- Drive skill never exceeds 10.

### Pay

- Op half bounty is awarded for qualifying crashed/terminal-damaged enemy cars.
- Op full bounty is awarded for killed outlaw drivers.
- Outlaw loot counts surviving cars and pairs of bikes/trikes, maximum four dice.
- Arsenal bonus rounds up and caps at 5.

### Psychosis and Disorders

- Drivers with fewer than two psychosis points do not test.
- 2d6 greater than psychosis passes; less/equal fails.
- Failed disorder test subtracts 2d6 psychosis, minimum 0.
- Media-roll psychosis is delayed to the next psychosis phase.
- Later outlaw gang members copy the first gang disorder sequence.

### Kudos and Media

- Base kudos is `floor(mileagePoints / 10)`.
- Drivers below 10 mileage do not roll media or apply eccentricity for media visibility.
- Visibility thresholds map correctly.
- Optional media rolls can be declined.
- Taking media rolls schedules psychosis for next sequence.
- Black-market credit cannot be banked into the next sequence.
- Media manipulation triggers on modified 6+ only.

### Recruitment

- Agency formation creates central fund/running-cost obligations.
- Experienced drivers leave if unpaid.
- Experienced drivers leave if not used in an engagement.
- Founder does not draw ordinary agency pay.
- Agency bounty is split between surviving participants and agency.
- Gang starting members never become experienced-driver employees.
- Gang with all vehicles written off disperses.

### Re-equipment

- Units without enough roadworthy vehicles must retire extra drivers.
- Stripping own equipment costs `$250` per item.
- Sale offer is die pips * 10% plus 30%.
- Newly recruited driver without vehicle is lost.

### Cybernetics and Hacking

- Cybernetic enhancement adds psychosis immediately.
- One artificial arm/leg gives `-1` drive skill; two remove the imbalance modifier.
- Artificial eyes remove night/smoke penalties.
- Hack attack total applies module modifiers and table ranges.
- Successful hack prevents repeat hack against same already-victim target.
- Hack repair costs `$500`; destroyed systems cannot be repaired.

## Handoff

Section: Campaign

Source files:

- `docs/rules/dead-mans-curve/01-white-dwarf-124-pages-18-31.md`
- `docs/rules/dead-mans-curve/02-white-dwarf-125-pages-68-76.md`

Source pages:

- White Dwarf 124 pages 18-31
- White Dwarf 125 pages 68-76

Cleaned files:

- `docs/rules/clean/campaign.md`

Data files:

- `data/rules/campaign-sequence.json`

Tests:

- Candidate tests listed above. No engine tests added in this extraction pass.

Ambiguities:

- Listed in `Ambiguities and OCR Doubts`.

Dependencies:

- Tactical outcome data, vehicle/equipment values, damage/critical state, and unified campaign UI.

Schema changes requested:

- Add campaign-level `unit`, `contractSequence`, `engagementDeclaration`, `postEngagementPhase`, `driverProgression`, `mediaEvent`, `recruitmentObligation`, `repairOrder`, and `storeItem` structures to the eventual canonical schema.
