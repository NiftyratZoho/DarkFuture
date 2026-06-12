# Campaign UI Research Notes

## Sources Reviewed

- MechWarrior Online Mech Lab, hardpoint and loadout model: https://mwo.fandom.com/wiki/Mech_Lab
- MechWarrior 2 manual, customization areas: https://www.sarna.net/files/docs/products/manuals/mechwarrior_2.pdf
- MechWarrior 2: Mercenaries overview, independent company loop: https://www.sarna.net/wiki/MechWarrior_2%3A_Mercenaries
- MechWarrior 2: Mercenaries salvage and repair loop: https://strategywiki.org/wiki/MechWarrior_2%3A_Mercenaries/Salvage
- MobyGames summary of MechWarrior 2: Mercenaries: https://www.mobygames.com/game/1710/mechwarrior-2-mercenaries/

## Useful Patterns

The MechLab pattern maps cleanly to Dark Future vehicle design. The garage should be built around hardpoints, not a flat shopping list. Vehicle diagrams from White Line Fever character sheets should become the visual source for hardpoint positions, while the data model continues to use stable mount ids such as `hood`, `roof`, `leftWing`, `rightWing`, `passiveLeft`, and `passiveRight`.

The useful MechWarrior concepts are:

- hardpoints and equipment slots
- weight and capacity pressure
- armour and facing visibility
- weapon classes and compatibility
- weapon groups or linked-fire sets
- repair, reload, salvage, and resupply after missions
- contract choice as the bridge between campaign state and tactical deployment

Dark Future should translate these as:

- hardpoints map to `coreMounts` and `optionalMounts`
- tonnage maps to payload, total weight, and campaign purchase validation
- heat sinks are not relevant, but ammo and reloads are
- armour maps to facings from White Line Fever design data
- salvage maps to post-engagement recovery, sale, refit, repair, and reload actions
- mercenary unit management maps to agency/gang roster, garage, cash, kudos, and contract history

## UI Direction

The first screen should be an operations desk, not a landing page. It should expose campaign money, roster readiness, garage readiness, current contract status, and direct routes to Campaign, Garage, Mission, and Records.

Campaign should feel like a management console: finance, roster, garage, current scenario, repairs, recruitment, and saved game state should all be visible together. Campaign actions should still call the backend; the UI should not calculate funds or repairs itself.

Garage should feel like a loadout bay. The center of the screen should show the selected vehicle and its hardpoint boxes. Equipment and weapon art belongs beside the hardpoints so the player can understand what is fitted and what might fit. Until fitting actions are fully connected, slot selection should be read-only but explicit.

Mission setup should be a contract desk. The flow is Continue, Load, New. New then shows solo mission cards with objective and start validation.

Tactical should feel like a driver console. The board stays central, the right side shows active vehicle status, legal actions, selected action details, and quick command buttons, and the bottom stays a structured rule/combat log.
