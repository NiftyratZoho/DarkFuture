# UI Model Notes

`dark_future.ui_model` contains pygame-independent view-model builders for the current rough playable engine state. The builders are pure read-only adapters: they accept `GameState`, copy the relevant fields into frozen dataclasses, and do not mutate tactical or campaign state.

Current builders:

- `build_tactical_board_model(state)` summarizes turn/phase, sections, vehicle tokens, passive markers, and win state.
- `build_vehicle_records_model(state)` exposes per-vehicle record-sheet data for garage or record views.
- `build_campaign_summary_model(state)` exposes campaign state plus a placeholder string for the later Dead Man's Curve settlement loop.
- `build_action_panel_model(state)` wraps `engine.legal_actions()` with actor details and stable hotkey labels.
- `build_log_model(state, limit=10)` returns recent log entries with optional source references.
- `build_debug_overlay_model(state)` exposes placeholder movement, hazard, and contact payloads for debugging provisional rules.

The pygame layer should consume these models instead of directly assembling display strings from engine objects. Engine-specific behavior, rule resolution, and mutation should remain in `engine.py`; UI models should stay as presentation payloads.
