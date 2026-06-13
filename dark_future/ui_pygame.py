from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

from .engine import (
    LANE_COUNT,
    SCENARIOS,
    GameState,
    apply_action,
    apply_ai_turn_if_needed,
    copy_state,
    load_game,
    new_game,
    initial_track_layout,
)
from .ui_model import (
    VehicleTokenModel,
    build_action_panel_model,
    build_campaign_summary_model,
    build_debug_overlay_model,
    build_garage_loadout_model,
    build_vehicle_design_model,
    build_log_model,
    build_tactical_board_model,
    build_vehicle_records_model,
)
from .track import lane_pair_section_count, lane_section_count, lane_speed_limit
from .track_layout import (
    curve_lane_boundary_radii,
    layout_track_sections,
    point_on_curve,
    point_on_straight,
)
from .vehicle_design import VehicleDesignError, build_vehicle_design


WIDTH = 1280
HEIGHT = 820
BOARD_X = 24
BOARD_Y = 92
CELL_W = 42
CELL_H = 40
LANES = LANE_COUNT
SECTION_SPACES = 4
BOARD_W = 760
ACTION_PANEL_X = 830
ACTION_PANEL_W = 426
LOG_Y = 612
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOKEN_DIR = PROJECT_ROOT / "assets" / "tokens" / "processed"
SAVE_DIR = PROJECT_ROOT / "saves"
DESIGN_LIBRARY_PATH = SAVE_DIR / "designs.json"
DEFAULT_MISSION_SAVE_PATH = SAVE_DIR / "last_mission.json"
WEAPON_ICON_INDEX_PATH = PROJECT_ROOT / "assets" / "weapons" / "processed" / "weapons.json"
VEHICLE_SHEET_INDEX_PATH = PROJECT_ROOT / "assets" / "vehicle_sheets" / "processed" / "vehicle_sheets.json"
TOKEN_FILES = {
    ("interceptor", "agency"): "interceptor_green_top.png",
    ("interceptor", "outlaw"): "interceptor_black_top.png",
    ("renegade", "agency"): "renegade_green_top.png",
    ("renegade", "outlaw"): "renegade_red_top.png",
    ("bike", "agency"): "bike_red_side.png",
    ("bike", "outlaw"): "bike_black_side.png",
}
MARKER_ICON_WEAPONS = {
    "oil": "oilLayer",
    "smoke": "smokeLayer",
    "spikes": "spikeLayer",
    "mines": "patternMineLayer",
}


COLORS = {
    "bg": (18, 21, 24),
    "panel": (32, 36, 40),
    "panel2": (42, 47, 52),
    "text": (226, 229, 224),
    "muted": (158, 166, 166),
    "road": (68, 72, 72),
    "curve": (76, 80, 88),
    "invalid_track": (37, 40, 43),
    "road_line": (116, 122, 118),
    "speed_text": (206, 188, 135),
    "oil": (30, 30, 26),
    "smoke": (138, 144, 140),
    "agency": (55, 150, 210),
    "outlaw": (201, 83, 67),
    "active": (240, 205, 90),
    "button": (59, 70, 78),
    "button_hover": (78, 92, 101),
    "debug": (120, 205, 135),
}


@dataclass(frozen=True)
class TokenPose:
    center: tuple[int, int]
    angle_degrees: float
    lane_width: int
    car_length: int


@dataclass
class Button:
    rect: pygame.Rect
    action_id: str
    label: str


@dataclass
class UIState:
    screen: str = "home"
    selected_vehicle_id: str = "agency-1"
    selected_mount_id: str | None = None
    selected_catalog_id: str | None = None


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Dark Future - Rough Pygame Pass")
        self.display = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.small = pygame.font.SysFont("consolas", 15)
        self.tiny = pygame.font.SysFont("consolas", 12, bold=True)
        self.big = pygame.font.SysFont("consolas", 28, bold=True)
        self.state = new_game()
        self.state.save_path = str(DEFAULT_MISSION_SAVE_PATH)
        self.state.campaign.last_save_path = str(DEFAULT_MISSION_SAVE_PATH)
        self.state.mode = "home"
        self.ui = UIState()
        self.buttons: list[Button] = []
        self.action_buttons: list[Button] = []
        self.selected_vehicle_id = "agency-1"
        self.selected_mount_id: str | None = None
        self.selected_catalog_id: str | None = None
        self.selected_design_index = 0
        self.board_zoom = 1.0
        self.log_scroll = 0
        self.design_specs = self._default_design_specs()
        self.design_status = "Design library loaded from defaults."
        self.ui_status = "Choose Mission, then click an action button or press 1-9."
        self.pending_mission_scenario: str | None = None
        self.pending_campaign_contract = False
        self.pending_track_section_types: list[str] = []
        self.token_images: dict[tuple[str, str], pygame.Surface] = {}
        self.weapon_images: dict[str, pygame.Surface] = {}
        self.vehicle_sheet_images: dict[str, pygame.Surface] = {}
        self._load_token_images()
        self._load_weapon_images()
        self._load_vehicle_sheet_images()

    def run(self) -> None:
        while True:
            self._tick_ai()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                self._handle_event(event)
            self._draw()
            self.clock.tick(30)

    def _tick_ai(self) -> None:
        if self.state.mode not in {"tactical", "debug"}:
            return
        apply_ai_turn_if_needed(self.state)

    def _load_token_images(self) -> None:
        for key, file_name in TOKEN_FILES.items():
            path = TOKEN_DIR / file_name
            if path.exists():
                self.token_images[key] = pygame.image.load(str(path)).convert_alpha()

    def _load_weapon_images(self) -> None:
        if not WEAPON_ICON_INDEX_PATH.exists():
            return
        data = json.loads(WEAPON_ICON_INDEX_PATH.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            path = PROJECT_ROOT / item["image"]
            if path.exists():
                self.weapon_images[item["weaponId"]] = pygame.image.load(str(path)).convert_alpha()

    def _load_vehicle_sheet_images(self) -> None:
        if not VEHICLE_SHEET_INDEX_PATH.exists():
            return
        data = json.loads(VEHICLE_SHEET_INDEX_PATH.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            path = PROJECT_ROOT / item["image"]
            if path.exists():
                self.vehicle_sheet_images[item["vehicleTemplateId"]] = pygame.image.load(str(path)).convert_alpha()

    def _set_screen(self, screen: str) -> None:
        self.ui.screen = screen
        self.state.mode = screen

    def _current_screen(self) -> str:
        if self.ui.screen != self.state.mode:
            self.ui.screen = self.state.mode
        return self.ui.screen

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state.mode == "home":
                    pygame.quit()
                    sys.exit(0)
                self._set_screen("home")
            if event.key == pygame.K_F11:
                self._toggle_fullscreen()
            if event.key == pygame.K_r:
                self.state = new_game()
                self._set_screen("tactical")
            if event.key == pygame.K_TAB:
                self._cycle_mode()
            if event.key == pygame.K_SPACE:
                self._apply_game_action("next_phase")
            if event.key == pygame.K_F5:
                self._apply_game_action("save_game")
            if event.key == pygame.K_F9:
                self._apply_game_action("load_game")
            if event.key == pygame.K_c and self._current_screen() == "campaign":
                self._apply_game_action("cycle_scenario")
            if event.key == pygame.K_g and self._current_screen() in {"campaign", "debug"}:
                self._apply_game_action("generate_track")
            if event.key == pygame.K_h and self._current_screen() == "campaign":
                self._apply_game_action("recruit_driver")
            if event.key == pygame.K_p and self._current_screen() == "campaign":
                self._apply_game_action("repair_agency")
            if pygame.K_1 <= event.key <= pygame.K_9:
                index = event.key - pygame.K_1
                if index < len(self.action_buttons):
                    self._apply_game_action(self.action_buttons[index].action_id)
        elif event.type == pygame.MOUSEWHEEL:
            pos = pygame.Vector2(self._display_to_canvas(pygame.mouse.get_pos()))
            if self._log_rect().collidepoint(pos) and self._current_screen() not in {"home", "mission_menu", "mission_new", "mission_track_setup", "mission_load"}:
                self._scroll_log(event.y)
            elif self._board_view_rect().collidepoint(pos) and self._current_screen() in {"tactical", "debug"}:
                self._zoom_board(event.y)
        elif event.type == pygame.VIDEORESIZE:
            self.display = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.Vector2(self._display_to_canvas(event.pos))
            for button in self.buttons:
                if button.rect.collidepoint(pos):
                    self._dispatch_button(button.action_id)
                    return
            for vehicle in self.state.vehicles:
                if self._vehicle_rect(vehicle).collidepoint(pos):
                    self.selected_vehicle_id = vehicle.id
                    self.ui.selected_vehicle_id = vehicle.id

    def _dispatch_button(self, action_id: str) -> None:
        if action_id in {"log_scroll_up", "log_scroll_down"}:
            self._scroll_log(1 if action_id == "log_scroll_up" else -1)
            return
        if action_id == "open_mission":
            self._set_screen("mission_menu")
            if self._mission_in_progress():
                self.ui_status = "Mission in progress. Resume, save, or load; finish before starting another contract."
            else:
                self.ui_status = "Choose Continue, Load, or New mission."
            return
        if action_id.startswith("screen:"):
            self._set_screen(action_id.split(":", 1)[1])
            return
        if action_id == "new_mission":
            self._set_screen("mission_new")
            self.ui_status = "Choose a solo mission type."
            return
        if action_id.startswith("new_mission:"):
            if self._mission_in_progress():
                self.ui_status = "Finish or load away from the active mission before starting a new one."
                return
            scenario = action_id.split(":", 1)[1]
            self._prepare_mission_track_setup(scenario, campaign_contract=False)
            return
        if action_id == "start_campaign_contract":
            if self._mission_in_progress():
                self.ui_status = "A mission is already active. Resume or complete it before starting a campaign contract."
                return
            scenario = self.state.campaign.current_scenario
            self._prepare_mission_track_setup(scenario, campaign_contract=True)
            return
        if action_id == "reroll_mission_track":
            if self.pending_mission_scenario is not None:
                self.pending_track_section_types = initial_track_layout(self.state.dice)
                self.ui_status = "Rerolled initial track."
            return
        if action_id == "accept_mission_track":
            self._start_pending_mission()
            return
        if action_id == "settle_campaign":
            self._apply_game_action(action_id)
            return
        if action_id == "new_contract":
            self._prepare_mission_track_setup(self.state.campaign.current_scenario, campaign_contract=True)
            return
        if action_id == "continue_mission":
            if self._load_mission_save(Path(self.state.campaign.last_save_path or self.state.save_path)):
                self.ui_status = "Loaded last saved mission."
                return
            if self._load_mission_save(Path(self.state.save_path)):
                self.ui_status = "Loaded current mission save."
                return
            self._set_screen("mission_menu")
            self.ui_status = "No saved mission found. Choose New to start one."
            return
        if action_id == "mission_load":
            self._set_screen("mission_load")
            self.ui_status = "Choose a saved mission."
            return
        if action_id.startswith("load_mission:"):
            save_path = Path(action_id.split(":", 1)[1])
            self._load_mission_save(save_path)
            return
        if action_id == "resume_current_mission":
            self._set_screen("tactical")
            self.ui_status = "Mission active."
            return
        if action_id.startswith("select_vehicle:"):
            vehicle_id = action_id.split(":", 1)[1]
            self.selected_vehicle_id = vehicle_id
            self.ui.selected_vehicle_id = vehicle_id
            self.ui_status = f"Selected vehicle {vehicle_id}."
            return
        if action_id.startswith("select_mount:"):
            self.selected_mount_id = action_id.split(":", 1)[1]
            self.ui.selected_mount_id = self.selected_mount_id
            self.ui_status = f"Selected hardpoint {self.selected_mount_id}."
            return
        if action_id.startswith("select_catalog:"):
            self.selected_catalog_id = action_id.split(":", 1)[1]
            self.ui.selected_catalog_id = self.selected_catalog_id
            self.ui_status = f"Selected catalogue item {self.selected_catalog_id}."
            return
        if action_id == "fit_selected_item":
            self._fit_selected_item_to_design()
            return
        if action_id == "remove_mount_item":
            self._remove_selected_mount_item()
            return
        if action_id == "save_designs":
            self._save_design_library()
            return
        if action_id == "load_designs":
            self._load_design_library()
            return
        if action_id.startswith("select_design:"):
            self.selected_design_index = int(action_id.split(":", 1)[1])
            spec = self._current_design_spec()
            template_id = spec.get("templateId")
            vehicle = next((item for item in self.state.vehicles if item.template_id == template_id), None)
            if vehicle is not None:
                self.selected_vehicle_id = vehicle.id
                self.ui.selected_vehicle_id = vehicle.id
            self.selected_mount_id = None
            self.selected_catalog_id = None
            return
        self._apply_game_action(action_id)

    def _prepare_mission_track_setup(self, scenario: str, *, campaign_contract: bool) -> None:
        self.pending_mission_scenario = scenario if scenario in SCENARIOS else "intercept"
        self.pending_campaign_contract = campaign_contract
        self.pending_track_section_types = initial_track_layout(self.state.dice)
        self._set_screen("mission_track_setup")
        self.ui_status = "Review the generated initial track, then accept or reroll."

    def _start_pending_mission(self) -> None:
        if self.pending_mission_scenario is None:
            self._set_screen("mission_menu")
            self.ui_status = "No mission setup is pending."
            return
        scenario = self.pending_mission_scenario
        campaign = self.state.campaign
        track_types = list(self.pending_track_section_types)
        self.state = new_game(scenario, campaign, track_section_types=track_types)
        self.state.save_path = str(DEFAULT_MISSION_SAVE_PATH)
        self.state.campaign.last_save_path = str(DEFAULT_MISSION_SAVE_PATH)
        self.pending_mission_scenario = None
        self.pending_campaign_contract = False
        self.pending_track_section_types = []
        self._set_screen("tactical")
        self.ui_status = f"Started {SCENARIOS[scenario]['label']} mission with generated track."

    def _apply_game_action(self, action_id: str) -> None:
        if self._blocks_campaign_setup_action(action_id):
            self.ui_status = "Campaign setup is locked while a mission is active."
            return
        before = len(self.state.logs)
        apply_action(self.state, action_id)
        if len(self.state.logs) > before:
            self.ui_status = self.state.logs[-1].message
        else:
            self.ui_status = f"Action applied: {action_id.replace('_', ' ')}."

    def _cycle_mode(self) -> None:
        modes = ["home", "campaign", "garage", "mission_menu", "mission_track_setup", "tactical", "records", "debug"]
        screen = self._current_screen()
        index = modes.index(screen) if screen in modes else 0
        self._set_screen(modes[(index + 1) % len(modes)])

    def _mission_in_progress(self) -> bool:
        return not self.state.game_over

    def _blocks_campaign_setup_action(self, action_id: str) -> bool:
        campaign_setup_actions = {
            "generate_track",
            "recruit_driver",
            "repair_agency",
            "cycle_scenario",
            "start_campaign_contract",
        }
        return self._mission_in_progress() and action_id in campaign_setup_actions

    def _toggle_fullscreen(self) -> None:
        flags = self.display.get_flags()
        if flags & pygame.FULLSCREEN:
            self.display = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        else:
            self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    def _draw(self) -> None:
        self.screen.fill(COLORS["bg"])
        self.buttons.clear()
        self.action_buttons.clear()
        self._draw_header()
        screen = self._current_screen()
        if screen == "home":
            self._draw_home()
        elif screen == "mission_menu":
            self._draw_mission_menu()
        elif screen == "mission_new":
            self._draw_mission_new()
        elif screen == "mission_track_setup":
            self._draw_mission_track_setup()
        elif screen == "mission_load":
            self._draw_mission_load()
        elif screen == "tactical":
            self._draw_board()
            self._draw_action_panel()
        elif screen == "garage":
            self._draw_garage()
        elif screen == "campaign":
            self._draw_campaign()
        elif screen == "records":
            self._draw_records()
            self._draw_action_panel()
        else:
            self._draw_board()
            self._draw_debug_panel()
        if screen not in {"home", "mission_menu", "mission_new", "mission_track_setup", "mission_load"}:
            self._draw_log()
        self._present()

    def _draw_header(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], (0, 0, WIDTH, 72))
        title = self.big.render("DARK FUTURE", True, COLORS["text"])
        self.screen.blit(title, (24, 18))
        panel = build_action_panel_model(self.state)
        result = f" | Winner: {self.state.winner or 'none'}" if self.state.game_over else ""
        status = f"{self._current_screen().upper()} | Turn {self.state.turn} Phase {self.state.phase} | Active: {panel.actor_label}{result}"
        self.screen.blit(self.font.render(status, True, COLORS["muted"]), (240, 26))
        setup_keys = " | G track" if self._current_screen() == "debug" or (
            self._current_screen() == "campaign" and not self._mission_in_progress()
        ) else ""
        help_text = f"F11 fullscreen | Tab mode | 1-9 action | Space phase{setup_keys} | F5/F9 save/load"
        self.screen.blit(self.small.render(help_text, True, COLORS["muted"]), (760, 30))
        x = 24
        nav = (
            ("Home", "screen:home", "home"),
            ("Campaign", "screen:campaign", "campaign"),
            ("Garage", "screen:garage", "garage"),
            ("Mission", "open_mission", "mission"),
            ("Records", "screen:records", "records"),
        )
        for label, action_id, active_mode in nav:
            rect = pygame.Rect(x, 50, 92, 20)
            active = self.state.mode == active_mode or (
                active_mode == "mission"
                and self.state.mode in {"mission_menu", "mission_new", "mission_track_setup", "mission_load", "tactical"}
            )
            color = COLORS["button_hover"] if active else COLORS["button"]
            pygame.draw.rect(self.screen, color, rect, border_radius=3)
            self.screen.blit(self.small.render(label, True, COLORS["text"]), (rect.x + 8, rect.y + 3))
            self.buttons.append(Button(rect, action_id, label))
            x += 100

    def _panel(self, rect_tuple: tuple[int, int, int, int], title: str | None = None) -> pygame.Rect:
        rect = pygame.Rect(rect_tuple)
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=4)
        if title:
            self.screen.blit(self.font.render(title, True, COLORS["text"]), (rect.x + 16, rect.y + 18))
        return rect

    def _draw_lines(self, lines: list[str] | tuple[str, ...], x: int, y: int, *, width: int, step: int = 24) -> None:
        for index, line in enumerate(lines):
            color = COLORS["text"] if index == 0 else COLORS["muted"]
            self.screen.blit(self.small.render(str(line)[:width], True, color), (x, y + index * step))

    def _draw_text_clipped(self, text: str, x: int, y: int, max_width: int, color, *, font=None) -> None:
        font = font or self.small
        value = str(text)
        if font.size(value)[0] <= max_width:
            self.screen.blit(font.render(value, True, color), (x, y))
            return
        ellipsis = "..."
        while value and font.size(value + ellipsis)[0] > max_width:
            value = value[:-1]
        self.screen.blit(font.render((value + ellipsis) if value else ellipsis, True, color), (x, y))

    def _wrap_text_to_width(self, text: str, max_width: int, max_lines: int, *, font=None) -> list[str]:
        font = font or self.small
        words = str(text).split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            if len(lines) >= max_lines:
                break
            current = word
            while font.size(current)[0] > max_width and len(current) > 1:
                current = current[:-1]
        if current and len(lines) < max_lines:
            lines.append(current)
        return lines[:max_lines]

    def _draw_wrapped_text(self, text: str, x: int, y: int, max_chars: int, max_lines: int, color) -> None:
        width = max_chars * max(1, self.small.size("M")[0])
        for index, line in enumerate(self._wrap_text_to_width(text, width, max_lines)):
            self.screen.blit(self.small.render(line, True, color), (x, y + index * 17))

    def _command_row(self, x: int, y: int, width: int, title: str, body: str, action_id: str) -> None:
        rect = pygame.Rect(x, y, width, 58)
        pygame.draw.rect(self.screen, COLORS["panel2"], rect, border_radius=4)
        self.screen.blit(self.font.render(title, True, COLORS["text"]), (x + 12, y + 8))
        self.screen.blit(self.small.render(body[:32], True, COLORS["muted"]), (x + 12, y + 34))
        button = pygame.Rect(x + width - 92, y + 15, 74, 28)
        pygame.draw.rect(self.screen, COLORS["button"], button, border_radius=4)
        self.screen.blit(self.small.render("Open", True, COLORS["text"]), (button.x + 20, button.y + 6))
        self.buttons.append(Button(button, action_id, title))

    def _draw_home(self) -> None:
        c = build_campaign_summary_model(self.state)
        self._panel((16, 92, 370, 500), "Company")
        company_lines = [
            c.name,
            f"Side: {c.player_kind}",
            f"Funds: ${c.funds}",
            f"Kudos: {c.kudos}",
            f"Contracts: {c.contracts_completed}",
            f"Repairs due: ${c.repairs_pending}",
            f"Roster: {len(c.roster)}",
            f"Garage: {len(c.garage)}",
        ]
        self._draw_lines(company_lines, 34, 140, width=42)

        self._panel((406, 92, 430, 500), "Operations")
        ops = [
            ("Campaign", "Roster, money, repairs, recruitment.", "screen:campaign"),
            ("Garage", "Hardpoints, saved designs, weapon art.", "screen:garage"),
            ("Mission", "Continue, load, or choose a contract.", "open_mission"),
            ("Records", "Vehicle sheets, rules state, criticals.", "screen:records"),
            ("Resume Tactical", "Return to the current roadfight.", "resume_current_mission"),
        ]
        for index, (title, body, action_id) in enumerate(ops):
            y = 138 + index * 78
            self._command_row(430, y, 380, title, body, action_id)

        self._panel((856, 92, 400, 500), "Current Contract")
        scenario = SCENARIOS[self.state.scenario_id]
        contract_lines = [
            scenario["label"],
            f"Objective: {self.state.objective}",
            f"Turn {self.state.turn}, phase {self.state.phase}",
            f"Track sections: {self.state.track_sections}",
            f"Vehicles active: {sum(1 for v in self.state.vehicles if not v.destroyed)}",
            f"Last save: {Path(self.state.campaign.last_save_path).name}",
            self.ui_status,
        ]
        self._draw_lines(contract_lines, 876, 140, width=43)

        self._panel((16, 612, 1240, 190), "Research Direction")
        notes = [
            "Garage follows a MechLab-style hardpoint bay: slots first, catalogue second, rule validation through backend.",
            "Campaign follows a mercenary command loop: funds, roster, garage, contract choice, repair/reload/salvage later.",
            "White Line Fever vehicle sheets should become the visual source for hardpoint placement on each template.",
        ]
        self._draw_lines(notes, 34, 660, width=132)

    def _draw_mission_menu(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], (16, 92, 1240, 690), border_radius=4)
        self.screen.blit(self.big.render("Contract Desk", True, COLORS["text"]), (42, 126))
        self.screen.blit(self.font.render(self.ui_status, True, COLORS["speed_text"]), (42, 164))
        actions = [
            ("Resume Current", "Return to the active roadfight.", "resume_current_mission"),
            ("Continue", "Load the last saved mission.", "continue_mission"),
            ("Load", "Choose a previously saved mission.", "mission_load"),
        ]
        if not self._mission_in_progress():
            actions.extend(
                [
                    ("New", "Start a fresh solo mission.", "new_mission"),
                    (
                        "Campaign Contract",
                        f"Start the campaign's {SCENARIOS[self.state.campaign.current_scenario]['label']} contract.",
                        "start_campaign_contract",
                    ),
                ]
            )
        for index, (title, body, action_id) in enumerate(actions[:5]):
            self._draw_large_menu_button(title, body, action_id, 42, 220 + index * 104)
        self._draw_current_mission_summary(650, 220)

    def _draw_mission_new(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], (16, 92, 1240, 690), border_radius=4)
        self.screen.blit(self.big.render("New Solo Contract", True, COLORS["text"]), (42, 126))
        if self._mission_in_progress():
            self.screen.blit(
                self.font.render("A mission is active. Resume or load a save before setting up another.", True, COLORS["speed_text"]),
                (42, 164),
            )
            self._draw_large_menu_button("Resume Current", "Return to the active roadfight.", "resume_current_mission", 42, 220)
            self._draw_large_menu_button("Back", "Return to Mission menu.", "open_mission", 650, 472)
            return
        self.screen.blit(self.font.render("Choose the contract type to set up.", True, COLORS["muted"]), (42, 164))
        y = 220
        for scenario_id, scenario in SCENARIOS.items():
            self._draw_large_menu_button(
                scenario["label"],
                scenario["objective"],
                f"new_mission:{scenario_id}",
                42,
                y,
            )
            y += 126
        self._draw_large_menu_button("Back", "Return to Mission menu.", "open_mission", 650, 472)

    def _draw_mission_track_setup(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], (16, 92, 1240, 690), border_radius=4)
        scenario = self.pending_mission_scenario or self.state.campaign.current_scenario
        scenario_data = SCENARIOS.get(scenario, SCENARIOS["intercept"])
        self.screen.blit(self.big.render("Initial Track Setup", True, COLORS["text"]), (42, 126))
        subtitle = f"{scenario_data['label']} | {self.ui_status}"
        self.screen.blit(self.font.render(subtitle[:96], True, COLORS["speed_text"]), (42, 164))
        self._panel((42, 212, 610, 372), "Generated Sections")
        if not self.pending_track_section_types:
            self.screen.blit(self.font.render("No track has been generated yet.", True, COLORS["muted"]), (66, 260))
        for index, section_type in enumerate(self.pending_track_section_types[:10]):
            col = index % 2
            row = index // 2
            x = 66 + col * 286
            y = 258 + row * 52
            rect = pygame.Rect(x, y, 248, 36)
            pygame.draw.rect(self.screen, COLORS["panel2"], rect, border_radius=4)
            label = f"{index + 1}. {self._track_piece_label(section_type)}"
            self._draw_text_clipped(label, rect.x + 10, rect.y + 9, rect.width - 20, COLORS["text"])
        self._panel((696, 212, 500, 372), "Rules")
        rules = [
            "Start with three complete straight sections.",
            "Each straight section has three movement spaces per lane.",
            "Roll 1-4 straight, 5-6 curve until ten sections are in play.",
            "Curve roll: 1-4 broad 60-degree bend, 5-6 tight 90-degree corner.",
            "Odd direction rolls turn left; even rolls turn right.",
            "Every generated curve is followed by an automatic straight.",
        ]
        for i, line in enumerate(rules):
            self._draw_text_clipped(line, 720, 258 + i * 32, 450, COLORS["muted"])
        self._draw_large_menu_button("Accept Track", "Start the mission with this generated road.", "accept_mission_track", 42, 620)
        self._draw_large_menu_button("Reroll", "Generate a different initial road.", "reroll_mission_track", 650, 620)
        self._draw_large_menu_button("Back", "Return to contract selection.", "new_mission", 650, 720)

    def _track_piece_label(self, section_type: str) -> str:
        labels = {
            "straight": "Straight section",
            "curve50to80_left": "60-degree bend left",
            "curve50to80_right": "60-degree bend right",
            "curve30to60_left": "90-degree corner left",
            "curve30to60_right": "90-degree corner right",
        }
        return labels.get(section_type, section_type)

    def _draw_mission_load(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], (16, 92, 1240, 690), border_radius=4)
        self.screen.blit(self.big.render("Load Mission", True, COLORS["text"]), (42, 126))
        saves = self._mission_save_paths()
        if not saves:
            self.screen.blit(self.font.render("No saved missions found.", True, COLORS["speed_text"]), (42, 174))
            self._draw_large_menu_button("Back", "Return to Mission menu.", "open_mission", 42, 220)
            return
        self.screen.blit(self.font.render("Choose a save file.", True, COLORS["muted"]), (42, 164))
        for index, save_path in enumerate(saves[:8]):
            y = 210 + index * 58
            rect = pygame.Rect(42, y, 560, 42)
            pygame.draw.rect(self.screen, COLORS["button"], rect, border_radius=4)
            self.screen.blit(self.font.render(save_path.stem, True, COLORS["text"]), (rect.x + 14, rect.y + 8))
            self.screen.blit(self.small.render(self._mission_save_summary(save_path)[:42], True, COLORS["muted"]), (rect.x + 250, rect.y + 12))
            self.buttons.append(Button(rect, f"load_mission:{save_path}", save_path.name))
        self._draw_large_menu_button("Back", "Return to Mission menu.", "open_mission", 650, 472)

    def _draw_large_menu_button(self, title: str, body: str, action_id: str, x: int, y: int) -> None:
        rect = pygame.Rect(x, y, 520, 90)
        pygame.draw.rect(self.screen, COLORS["panel2"], rect, border_radius=5)
        button = pygame.Rect(x + 18, y + 48, 164, 30)
        pygame.draw.rect(self.screen, COLORS["button"], button, border_radius=4)
        self.screen.blit(self.font.render(title, True, COLORS["text"]), (x + 18, y + 14))
        self._draw_wrapped_text(body, x + 204, y + 43, 34, 2, COLORS["muted"])
        self.screen.blit(self.small.render("Select", True, COLORS["text"]), (button.x + 52, button.y + 7))
        self.buttons.append(Button(button, action_id, title))

    def _draw_current_mission_summary(self, x: int, y: int) -> None:
        pygame.draw.rect(self.screen, COLORS["panel2"], (x, y, 520, 342), border_radius=5)
        lines = [
            "Current Mission",
            f"Scenario: {SCENARIOS[self.state.scenario_id]['label']}",
            f"Turn {self.state.turn}, phase {self.state.phase}",
            f"Objective: {self.state.objective}",
            f"Status: {'complete' if self.state.game_over else 'active'}",
            f"Save: {self.state.save_path}",
        ]
        for index, line in enumerate(lines):
            color = COLORS["text"] if index == 0 else COLORS["muted"]
            self.screen.blit(self.font.render(line[:58], True, color), (x + 18, y + 18 + index * 34))
        rect = pygame.Rect(x + 18, y + 286, 180, 30)
        pygame.draw.rect(self.screen, COLORS["button"], rect, border_radius=4)
        self.screen.blit(self.small.render("Resume Current", True, COLORS["text"]), (rect.x + 16, rect.y + 7))
        self.buttons.append(Button(rect, "resume_current_mission", "Resume Current"))
        if self.state.game_over and self.state.campaign.settlement_pending:
            settle = pygame.Rect(x + 218, y + 286, 136, 30)
            pygame.draw.rect(self.screen, COLORS["button"], settle, border_radius=4)
            self.screen.blit(self.small.render("Settle", True, COLORS["text"]), (settle.x + 34, settle.y + 7))
            self.buttons.append(Button(settle, "settle_campaign", "Settle"))
        if self.state.game_over:
            contract = pygame.Rect(x + 366, y + 286, 120, 30)
            pygame.draw.rect(self.screen, COLORS["button"], contract, border_radius=4)
            self.screen.blit(self.small.render("Next", True, COLORS["text"]), (contract.x + 38, contract.y + 7))
            self.buttons.append(Button(contract, "new_contract", "Next"))

    def _draw_board(self) -> None:
        board = build_tactical_board_model(self.state)
        board_rect = self._board_view_rect()
        pygame.draw.rect(self.screen, COLORS["panel"], board_rect, border_radius=4)
        self.screen.blit(self.font.render("Tactical Board - connected geometric track", True, COLORS["text"]), (28, 100))
        status = f"{self.ui_status[:78]} | Wheel zoom {self.board_zoom:.1f}x"
        self.screen.blit(self.small.render(status, True, COLORS["speed_text"]), (28, 124))
        cell_w = self._cell_w()
        lane_w = self._lane_w()
        placements = self._section_placements(board)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(board_rect)
        for section in board.track_sections:
            section_cells = [cell for cell in board.cells if cell.section == section.index]
            if section.is_curve:
                self._draw_curve_section(section, section_cells, placements[section.index], cell_w, lane_w)
            else:
                self._draw_straight_section(section, section_cells, placements[section.index], cell_w, lane_w)
            x, y = self._world_to_screen(placements[section.index].entry)
            label = f"{section.label} {section.angle_degrees}deg" if section.is_curve else section.label
            self.screen.blit(self.small.render(label, True, COLORS["muted"]), (x + 6, y - 22))
        for marker in board.markers:
            self._draw_marker(marker, board, placements)
        for vehicle in board.vehicles:
            pose = self._vehicle_pose(vehicle, board, placements)
            token = self._vehicle_token_surface(vehicle, pose)
            token = pygame.transform.rotate(token, self._token_render_angle(pose))
            rect = token.get_rect(center=pose.center)
            self.screen.blit(token, rect)
            if vehicle.active:
                pygame.draw.rect(self.screen, COLORS["active"], rect, 3, border_radius=3)
            label = self.small.render(vehicle.label[:10], True, COLORS["text"])
            self.screen.blit(label, (rect.x, rect.bottom + 1))
            if vehicle.destroyed:
                x_mark = self.font.render("X", True, COLORS["outlaw"])
                self.screen.blit(x_mark, (rect.centerx - 5, rect.centery - 10))
        self.screen.set_clip(previous_clip)

    def _vehicle_token_surface(self, vehicle: VehicleTokenModel, pose: TokenPose) -> pygame.Surface:
        token = self.token_images.get((vehicle.template_id, vehicle.side))
        width = pose.car_length
        height = max(8, int(pose.lane_width * 1.45))
        if token is None:
            color = (72, 72, 72) if vehicle.destroyed else COLORS[vehicle.side]
            fallback = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(fallback, color, fallback.get_rect(), border_radius=3)
            return fallback
        scaled = pygame.transform.smoothscale(token, (width, height))
        if vehicle.destroyed:
            scaled = scaled.copy()
            overlay = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
            overlay.fill((20, 20, 20, 145))
            scaled.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return scaled

    def _token_render_angle(self, pose: TokenPose) -> float:
        return -pose.angle_degrees

    def _section_placements(self, board):
        piece_types = tuple(section.kind for section in board.track_sections)
        return layout_track_sections(
            piece_types,
            lane_width=self._lane_w(),
            car_length=self._cell_w(),
            start=(0.0, 0.0),
            heading_degrees=0.0,
        )

    def _draw_straight_section(self, section, cells, placement, cell_w: int, lane_w: int) -> None:
        for cell in cells:
            if not cell.valid:
                continue
            p1 = point_on_straight(
                placement,
                space=cell.space,
                lane_pair=cell.lane - 0.5,
                lane_width=lane_w,
                car_length=cell_w,
            )
            points = self._oriented_rect_points(p1, placement.heading_degrees, cell_w, lane_w)
            pygame.draw.polygon(self.screen, COLORS["road"], [self._world_to_screen(point) for point in points])
            pygame.draw.lines(self.screen, COLORS["road_line"], True, [self._world_to_screen(point) for point in points], 1)

    def _draw_curve_section(self, section, cells, placement, cell_w: int, lane_w: int) -> None:
        speed_labels: list[tuple[str, tuple[int, int]]] = []
        for cell in cells:
            if not cell.valid:
                continue
            points = self._curve_cell_polygon(placement, section, cell, lane_w)
            screen_points = [self._world_to_screen(point) for point in points]
            pygame.draw.polygon(self.screen, COLORS["curve"], screen_points)
            pygame.draw.lines(self.screen, COLORS["road_line"], True, screen_points, 1)
            if self._should_draw_curve_speed_label(section, cell):
                lane_end = self._speed_label_lane_end(section, cell.lane, cell.speed_limit_mph)
                tx, ty = self._curve_speed_label_position(
                    placement,
                    section,
                    cell,
                    cell_w,
                    lane_w,
                    lane_end=lane_end,
                )
                tx, ty = self._world_to_screen((tx, ty))
                speed_labels.append((str(cell.speed_limit_mph), (tx, ty)))
        for label, center in speed_labels:
            speed = self.small.render(label, True, COLORS["speed_text"])
            speed_rect = speed.get_rect(center=center)
            pygame.draw.rect(self.screen, COLORS["panel"], speed_rect.inflate(3, 1), border_radius=2)
            self.screen.blit(speed, speed_rect)

    def _curve_cell_polygon(self, placement, section, cell, lane_w: int) -> list[tuple[float, float]]:
        if placement.center is None or placement.radius is None:
            raise ValueError("curve placement missing center/radius")
        start_radial = placement.heading_degrees - placement.turn_direction * 90
        angle_step = (
            placement.exit_heading_degrees - placement.heading_degrees
        ) / lane_section_count(section.kind, cell.lane)
        a0 = math.radians(start_radial + angle_step * (cell.space - 1))
        a1 = math.radians(start_radial + angle_step * cell.space)
        boundaries = curve_lane_boundary_radii(
            section.kind,
            lane_width=lane_w,
            car_length=self._cell_w(),
        )
        r0 = boundaries[cell.lane - 1]
        r1 = boundaries[cell.lane]
        steps = 5
        outer = [self._polar_point(placement.center, r1, a0 + (a1 - a0) * i / steps) for i in range(steps + 1)]
        inner = [self._polar_point(placement.center, r0, a1 - (a1 - a0) * i / steps) for i in range(steps + 1)]
        return outer + inner

    def _should_draw_curve_speed_label(self, section, cell) -> bool:
        if not cell.speed_limit_mph:
            return False
        if cell.space != lane_section_count(section.kind, cell.lane):
            return False
        if cell.lane > 1 and lane_speed_limit(section.kind, cell.lane - 1) == cell.speed_limit_mph:
            return False
        return True

    def _speed_label_lane_end(self, section, lane: int, speed_limit_mph: int) -> int:
        lane_end = lane
        while lane_end < LANE_COUNT and lane_speed_limit(section.kind, lane_end + 1) == speed_limit_mph:
            lane_end += 1
        return lane_end

    def _curve_speed_label_position(
        self,
        placement,
        section,
        cell,
        cell_w: int,
        lane_w: int,
        *,
        lane_end: int | None = None,
    ) -> tuple[float, float]:
        if placement.center is None:
            raise ValueError("curve placement missing center")
        lane_end = lane_end or cell.lane
        boundaries = curve_lane_boundary_radii(
            section.kind,
            lane_width=lane_w,
            car_length=cell_w,
        )
        radius = (boundaries[cell.lane - 1] + boundaries[lane_end]) / 2
        angle_step = (
            placement.exit_heading_degrees - placement.heading_degrees
        ) / lane_section_count(section.kind, cell.lane)
        radial = placement.heading_degrees - placement.turn_direction * 90
        radial += placement.exit_heading_degrees - placement.heading_degrees
        radial -= angle_step * 0.18
        return self._polar_point(placement.center, radius, math.radians(radial))

    def _polar_point(self, center, radius: float, angle: float) -> tuple[float, float]:
        return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)

    def _vehicle_pose(self, vehicle: VehicleTokenModel, board, placements) -> TokenPose:
        cell_w = self._cell_w()
        lane_w = self._lane_w()
        section = board.track_sections[vehicle.section]
        car_length = max(18, int(cell_w * 0.9))
        placement = placements[vehicle.section]
        if section.is_curve:
            cx, cy = point_on_curve(
                placement,
                space=vehicle.space,
                lane_pair=vehicle.lane_pair,
                lane_width=lane_w,
                car_length=cell_w,
                spaces=section.spaces,
            )
            angle_step = (
                placement.exit_heading_degrees - placement.heading_degrees
            ) / lane_pair_section_count(section.kind, vehicle.lane_pair)
            tangent = placement.heading_degrees + angle_step * (vehicle.space - 0.5)
            if vehicle.direction == -1:
                tangent += 180
            return TokenPose(self._world_to_screen((cx, cy)), tangent, lane_w, car_length)
        x, y = point_on_straight(
            placement,
            space=vehicle.space,
            lane_pair=vehicle.lane_pair,
            lane_width=lane_w,
            car_length=cell_w,
        )
        angle = placement.heading_degrees if vehicle.direction == 1 else placement.heading_degrees + 180
        return TokenPose(self._world_to_screen((x, y)), angle, lane_w, car_length)

    def _vehicle_rect(self, vehicle: VehicleTokenModel, board=None, placements=None) -> pygame.Rect:
        board = board or build_tactical_board_model(self.state)
        placements = placements or self._section_placements(board)
        pose = self._vehicle_pose(vehicle, board, placements)
        return pygame.Rect(
            pose.center[0] - pose.car_length // 2,
            pose.center[1] - pose.lane_width,
            pose.car_length,
            pose.lane_width * 2,
        )

    def _draw_action_panel(self) -> None:
        panel = build_action_panel_model(self.state)
        x = ACTION_PANEL_X
        panel_rect = pygame.Rect(x, 82, ACTION_PANEL_W, 500)
        pygame.draw.rect(self.screen, COLORS["panel"], panel_rect, border_radius=4)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(panel_rect)
        self.screen.blit(self.font.render("Driver Console", True, COLORS["text"]), (x + 16, 100))
        actor_lines = list(panel.actor_lines)
        for i, line in enumerate(actor_lines[:6]):
            self._draw_text_clipped(line, x + 16, 132 + i * 18, ACTION_PANEL_W - 32, COLORS["muted"])

        count_suffix = f" ({min(8, len(panel.actions))}/{len(panel.actions)})" if len(panel.actions) > 8 else ""
        self.screen.blit(self.small.render(f"Legal Actions{count_suffix}", True, COLORS["speed_text"]), (x + 16, 246))
        visible_actions = panel.actions[:8]
        mouse = pygame.Vector2(self._display_to_canvas(pygame.mouse.get_pos()))
        for index, action in enumerate(visible_actions):
            row_y = 268 + index * 25
            rect = pygame.Rect(x + 16, row_y, 286, 22)
            color = COLORS["button_hover"] if rect.collidepoint(mouse) else COLORS["button"]
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            self._draw_text_clipped(f"{action.hotkey}. {action.label}", rect.x + 10, rect.y + 3, rect.width - 18, COLORS["text"])
            button = Button(rect, action.id, action.label)
            self.buttons.append(button)
            self.action_buttons.append(button)
            self._draw_text_clipped(action.kind, x + 314, row_y + 4, 94, COLORS["speed_text"])

        preview = visible_actions[0] if visible_actions else None
        pygame.draw.rect(self.screen, COLORS["panel2"], (x + 16, 476, 394, 54), border_radius=4)
        if preview is not None:
            self._draw_text_clipped(f"Preview: {preview.label}", x + 28, 486, 370, COLORS["text"])
            for line_index, line in enumerate(self._wrap_text_to_width(preview.details, 370, 2)):
                self.screen.blit(self.small.render(line, True, COLORS["muted"]), (x + 28, 506 + line_index * 15))
        else:
            self.screen.blit(self.small.render("No legal action for current actor.", True, COLORS["muted"]), (x + 28, 498))
        quick = [("Contracts", "open_mission"), ("Phase", "next_phase")]
        if self._current_screen() == "debug":
            quick.insert(1, ("Track", "generate_track"))
        for idx, (label, action_id) in enumerate(quick):
            rect = pygame.Rect(x + 16 + idx * 132, 544, 124, 26)
            pygame.draw.rect(self.screen, COLORS["button"], rect, border_radius=4)
            self._draw_text_clipped(label, rect.x + 8, rect.y + 5, rect.width - 16, COLORS["text"])
            self.buttons.append(Button(rect, action_id, label))
        self.screen.set_clip(previous_clip)

    def _draw_campaign(self) -> None:
        c = build_campaign_summary_model(self.state)
        self._panel((16, 82, 790, 230), "Campaign Command")
        summary = [
            c.name,
            f"Player side: {c.player_kind}",
            f"Scenario: {c.scenario}",
            f"Objective: {c.objective}",
            f"Funds: ${c.funds}  Kudos: {c.kudos}  Contracts: {c.contracts_completed}",
            f"Repairs pending: ${c.repairs_pending}  Recruits hired: {c.recruits_hired}",
            f"Save: {c.save_path}",
        ]
        self._draw_lines(summary, 34, 128, width=92)

        self._panel((16, 330, 382, 250), "Roster")
        roster_lines = list(c.roster) or ["No drivers hired."]
        self._draw_lines(roster_lines, 34, 376, width=42)

        self._panel((424, 330, 382, 250), "Garage")
        garage_lines = list(c.garage) or ["No vehicles in garage."]
        self._draw_lines(garage_lines, 442, 376, width=42)

        self._panel((830, 82, 426, 498), "Campaign Actions")
        if self.state.game_over:
            actions = [
                ("New Contract", "Start another roadfight.", "new_contract"),
                ("Start Contract", f"Launch {SCENARIOS[self.state.campaign.current_scenario]['label']}.", "start_campaign_contract"),
                ("Recruit Driver", "Hire into roster.", "recruit_driver"),
                ("Repair Agency", "Resolve current repair bill.", "repair_agency"),
                ("Cycle Scenario", "Step to next solo contract.", "cycle_scenario"),
                ("Generate Track", "Roll a new road layout.", "generate_track"),
                ("Save Campaign", "Save current state.", "save_game"),
                ("Load Campaign", "Load saved state.", "load_game"),
            ]
            if self.state.campaign.settlement_pending:
                actions.insert(0, ("Settle Campaign", "Apply rewards and repairs.", "settle_campaign"))
        else:
            actions = [
                ("Resume Mission", "Return to the active roadfight.", "resume_current_mission"),
                ("Save Mission", "Save current tactical state.", "save_game"),
                ("Load Mission", "Load a mission save.", "load_game"),
            ]
        for index, (title, body, action_id) in enumerate(actions):
            self._command_row(852, 126 + index * 52, 374, title, body, action_id)
        footer = c.placeholder if self.state.game_over else "Campaign setup unlocks when the current mission is complete."
        self._draw_text_clipped(footer, 852, 530, 360, COLORS["speed_text"])

    def _draw_garage(self) -> None:
        design = build_vehicle_design_model(self.state, self.selected_vehicle_id)
        loadout = build_garage_loadout_model(self.state, self.selected_vehicle_id)
        current_spec = self._current_design_spec()
        current_record, current_error = self._design_record(current_spec)
        preview_spec = self._preview_design_spec()
        preview_record, preview_error = self._design_record(preview_spec)
        self._panel((16, 82, 250, 498), "Vehicles")
        for index, vehicle in enumerate(self.state.vehicles):
            y = 128 + index * 60
            rect = pygame.Rect(34, y, 214, 48)
            color = COLORS["button_hover"] if vehicle.id == self.selected_vehicle_id else COLORS["panel2"]
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            self.screen.blit(self.font.render(vehicle.label[:16], True, COLORS["text"]), (rect.x + 10, rect.y + 6))
            self.screen.blit(self.small.render(f"{vehicle.side} | {vehicle.template_id}", True, COLORS["muted"]), (rect.x + 10, rect.y + 28))
            self.buttons.append(Button(rect, f"select_vehicle:{vehicle.id}", vehicle.label))
        self.screen.blit(self.small.render("WLF sheet hardpoints.", True, COLORS["speed_text"]), (34, 526))

        self._panel((286, 82, 520, 498), "Loadout Bay")
        design_name = current_spec.get("vehicleId", loadout.label)
        heading = f"{design_name} ({current_spec.get('templateId', loadout.template_label)})"
        self.screen.blit(self.font.render(heading[:44], True, COLORS["text"]), (304, 128))
        stats = self._design_stat_lines(current_record, current_error, preview_record, preview_error)
        self._draw_lines(stats, 304, 156, width=58, step=18)
        self._draw_hardpoint_bay(loadout, 330, 260, current_record)
        msg_y = 528
        messages = [self._garage_selection_status()]
        if preview_error:
            messages.append(f"Preview blocked: {preview_error}")
        messages.extend(loadout.validation_messages[:1])
        for message in messages[:3]:
            self.screen.blit(self.small.render(message[:50], True, COLORS["speed_text"]), (304, msg_y))
            msg_y += 18

        self._panel((830, 82, 426, 498), "Equipment Catalogue")
        self._draw_design_list("Weapons And Passives", design.equipment, 852, 128, 374, 7, show_weapon_icons=True, clickable=True)
        self._draw_garage_fit_buttons()
        self._draw_design_library()

    def _draw_hardpoint_bay(self, loadout, x: int, y: int, record: dict | None = None) -> None:
        sheet = self.vehicle_sheet_images.get(loadout.template_id or "")
        if sheet is not None:
            target = pygame.Rect(x + 96, y - 24, 198, 250)
            scaled = pygame.transform.smoothscale(sheet, target.size)
            self.screen.blit(scaled, target)
        else:
            pygame.draw.rect(self.screen, COLORS["panel2"], (x + 112, y + 20, 160, 150), border_radius=8)
            pygame.draw.rect(self.screen, COLORS["road_line"], (x + 112, y + 20, 160, 150), 2, border_radius=8)
            self.screen.blit(self.small.render(loadout.kind.upper(), True, COLORS["muted"]), (x + 162, y + 82))
        installed_by_mount = self._installed_weapons_by_mount(record)
        positions = {
            "hood": (x + 144, y - 18),
            "roof": (x + 144, y + 66),
            "leftWing": (x + 10, y + 50),
            "rightWing": (x + 286, y + 50),
            "leftSide": (x + 10, y + 116),
            "rightSide": (x + 286, y + 116),
            "passiveCenter": (x + 144, y + 184),
            "passiveLeft": (x + 76, y + 184),
            "passiveRight": (x + 212, y + 184),
            "leftFairing": (x + 64, y + 54),
            "rightFairing": (x + 224, y + 54),
            "passiveRear": (x + 144, y + 184),
        }
        for mount in loadout.mounts:
            mx, my = positions.get(mount.id, (x + 144, y + 184))
            rect = pygame.Rect(mx, my, 96, 50)
            selected = mount.id == self.selected_mount_id
            installed = installed_by_mount.get(mount.id)
            icon_weapon_id = installed.get("weaponId") if installed else mount.icon_weapon_id
            slot = pygame.Surface(rect.size, pygame.SRCALPHA)
            slot.fill((78, 92, 101, 170) if selected else (59, 70, 78, 115))
            self.screen.blit(slot, rect)
            pygame.draw.rect(self.screen, COLORS["active"] if installed or mount.status == "fitted" else COLORS["road_line"], rect, 1, border_radius=4)
            if icon_weapon_id and icon_weapon_id in self.weapon_images:
                icon = pygame.transform.smoothscale(self.weapon_images[icon_weapon_id], (56, 31))
                self.screen.blit(icon, (rect.x + 4, rect.y + 4))
            self.screen.blit(self.small.render(mount.label[:11], True, COLORS["text"]), (rect.x + 6, rect.y + 32))
            self.buttons.append(Button(rect, f"select_mount:{mount.id}", mount.label))

    def _draw_garage_fit_buttons(self) -> None:
        actions = (
            ("Fit", "fit_selected_item", 852),
            ("Remove", "remove_mount_item", 914),
        )
        for label, action_id, x in actions:
            rect = pygame.Rect(x, 394, 56, 24)
            pygame.draw.rect(self.screen, COLORS["button"], rect, border_radius=4)
            self.screen.blit(self.small.render(label, True, COLORS["text"]), (rect.x + 8, rect.y + 5))
            self.buttons.append(Button(rect, action_id, label))

    def _draw_design_library(self) -> None:
        x = 830
        y0 = 430
        pygame.draw.rect(self.screen, COLORS["panel2"], (x + 16, y0, 394, 134), border_radius=4)
        self.screen.blit(self.small.render("Saved Loadouts", True, COLORS["muted"]), (x + 28, y0 + 10))
        for index, spec in enumerate(self.design_specs[:3]):
            rect = pygame.Rect(x + 28, y0 + 36 + index * 28, 214, 23)
            color = COLORS["button_hover"] if index == self.selected_design_index else COLORS["button"]
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            label = f"{index + 1}. {spec.get('vehicleId', spec.get('templateId', 'design'))}"
            self.screen.blit(self.small.render(label[:28], True, COLORS["text"]), (rect.x + 8, rect.y + 5))
            self.buttons.append(Button(rect, f"select_design:{index}", label))
        selected = self.design_specs[self.selected_design_index] if self.design_specs else None
        y = y0 + 36
        if selected:
            try:
                record = build_vehicle_design(selected)
                lines = [
                    f"T: {record['templateId']}",
                    f"$ {record['totalCost']}  W {record['totalWeight']}",
                    f"P {record['payloadUsed']} / {record['payloadLimit']}",
                ]
            except VehicleDesignError as exc:
                lines = [f"Invalid design: {exc}"]
            for line in lines:
                self.screen.blit(self.small.render(line[:18], True, COLORS["text"]), (x + 252, y))
                y += 18
        for label, action_id, bx in (("Save", "save_designs", x + 28), ("Load", "load_designs", x + 88)):
            rect = pygame.Rect(bx, y0 + 104, 52, 22)
            pygame.draw.rect(self.screen, COLORS["button"], rect, border_radius=4)
            self.screen.blit(self.small.render(label, True, COLORS["text"]), (rect.x + 8, rect.y + 4))
            self.buttons.append(Button(rect, action_id, label))
        self.screen.blit(self.small.render(self.design_status[:42], True, COLORS["speed_text"]), (x + 150, y0 + 106))

    def _draw_design_list(self, title: str, items, x: int, y: int, width: int, limit: int, *, show_weapon_icons: bool = False, clickable: bool = False) -> None:
        self.screen.blit(self.small.render(title, True, COLORS["muted"]), (x, y))
        for index, item in enumerate(items[:limit]):
            row_h = 32 if show_weapon_icons else 20
            step = 36 if show_weapon_icons else 23
            rect = pygame.Rect(x, y + 22 + index * step, width, row_h)
            selected = item.id == self.selected_catalog_id
            pygame.draw.rect(self.screen, COLORS["button_hover"] if selected else COLORS["panel2"], rect, border_radius=3)
            cost = "-" if item.cost is None else f"${item.cost}"
            weight = "-" if item.weight is None else f"{item.weight}lb"
            if show_weapon_icons:
                icon = self.weapon_images.get(item.icon_id or item.id)
                if icon is not None:
                    scaled_icon = pygame.transform.smoothscale(icon, (62, 28))
                    self.screen.blit(scaled_icon, (rect.x + 4, rect.y + 2))
                label = f"{item.label[:16]:16} {cost:>7}"
                self.screen.blit(self.small.render(label[:26], True, COLORS["text"]), (rect.x + 72, rect.y + 4))
                self.screen.blit(self.small.render(weight, True, COLORS["muted"]), (rect.x + 72, rect.y + 18))
            else:
                label = f"{item.label[:18]:18} {cost:>7} {weight:>6}"
                self.screen.blit(self.small.render(label[:34], True, COLORS["text"]), (rect.x + 6, rect.y + 3))
            if clickable:
                self.buttons.append(Button(rect, f"select_catalog:{item.id}", item.label))

    def _draw_records(self) -> None:
        records = build_vehicle_records_model(self.state)
        pygame.draw.rect(self.screen, COLORS["panel"], (16, 82, 790, 430), border_radius=4)
        self.screen.blit(self.font.render("Vehicle Records", True, COLORS["text"]), (32, 104))
        y = 146
        for vehicle in records.records:
            lines = [
                f"{vehicle.id}: {vehicle.label}",
                f"Template {vehicle.template_id} | Side {vehicle.side} | Damage {vehicle.damage} | {vehicle.status.title()}",
                f"Max {vehicle.max_mph} Accel {vehicle.acceleration_mph} Brake {vehicle.braking_mph}",
                f"Weapon {vehicle.weapon} Acc {vehicle.weapon_accuracy} Dmg +{vehicle.weapon_damage_modifier}",
                f"Control {vehicle.control_state} Driver {vehicle.driver_skill} Criticals: {', '.join(vehicle.critical_notes) or 'none'}",
            ]
            for line in lines:
                self.screen.blit(self.font.render(line, True, COLORS["text"]), (34, y))
                y += 24
            y += 18

    def _draw_debug_panel(self) -> None:
        self._draw_action_panel()
        debug = build_debug_overlay_model(self.state)
        x = 830
        self.screen.blit(self.font.render("Debug Overlay", True, COLORS["debug"]), (x + 16, 470))
        lines = list(debug.placeholders)
        lines.extend(
            f"{item.label}: {item.current} -> {item.forward or 'off road'}"
            for item in debug.movement[:2]
        )
        for i, line in enumerate(lines):
            self.screen.blit(self.small.render(line, True, COLORS["debug"]), (x + 16, 500 + i * 22))

    def _draw_log(self) -> None:
        log = build_log_model(self.state, limit=len(self.state.logs))
        rect = self._log_rect()
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=4)
        self.screen.blit(self.font.render(log.title, True, COLORS["text"]), (32, LOG_Y + 18))
        entries = self._visible_log_entries(log.entries)
        content_rect = pygame.Rect(rect.x + 16, LOG_Y + 48, rect.width - 32, rect.height - 58)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(content_rect)
        for i, entry in enumerate(entries):
            color = COLORS["debug"] if entry.kind in {"phase", "activation"} else COLORS["text"]
            text = f"[{entry.kind}] {entry.message}"
            self._draw_text_clipped(text, content_rect.x, content_rect.y + i * 18, content_rect.width - 12, color)
        self.screen.set_clip(previous_clip)
        if self._max_log_scroll(log.entries) > 0:
            position = f"{self.log_scroll + 1}-{self.log_scroll + len(entries)} / {len(log.entries)}"
            self.screen.blit(self.tiny.render(position, True, COLORS["muted"]), (1090, LOG_Y + 20))
            for label, action_id, x in (("Up", "log_scroll_up", 1162), ("Down", "log_scroll_down", 1206)):
                button = pygame.Rect(x, LOG_Y + 18, 42, 18)
                pygame.draw.rect(self.screen, COLORS["button"], button, border_radius=3)
                self._draw_text_clipped(label, button.x + 5, button.y + 3, button.width - 10, COLORS["text"], font=self.tiny)
                self.buttons.append(Button(button, action_id, label))

    def _log_rect(self) -> pygame.Rect:
        return pygame.Rect(16, LOG_Y, 1240, 190)

    def _log_visible_line_count(self) -> int:
        return 7

    def _max_log_scroll(self, entries) -> int:
        return max(0, len(entries) - self._log_visible_line_count())

    def _scroll_log(self, wheel_delta: int) -> None:
        max_scroll = self._max_log_scroll(self.state.logs)
        self.log_scroll = max(0, min(max_scroll, self.log_scroll + wheel_delta))

    def _visible_log_entries(self, entries):
        visible = self._log_visible_line_count()
        max_scroll = self._max_log_scroll(entries)
        self.log_scroll = max(0, min(max_scroll, self.log_scroll))
        end = len(entries) - self.log_scroll
        start = max(0, end - visible)
        return entries[start:end]

    def _present(self) -> None:
        display_w, display_h = self.display.get_size()
        scaled = pygame.transform.smoothscale(self.screen, (display_w, display_h))
        self.display.blit(scaled, (0, 0))
        pygame.display.flip()

    def _display_to_canvas(self, pos: tuple[int, int]) -> tuple[int, int]:
        display_w, display_h = self.display.get_size()
        scale_x = WIDTH / max(1, display_w)
        scale_y = HEIGHT / max(1, display_h)
        return int(pos[0] * scale_x), int(pos[1] * scale_y)

    def _marker_center(self, marker, board, placements) -> tuple[int, int]:
        cell_w = self._cell_w()
        lane_w = self._lane_w()
        section = board.track_sections[marker.section]
        placement = placements[marker.section]
        if section.is_curve:
            x, y = point_on_curve(
                placement,
                space=marker.space,
                lane_pair=marker.lane_pair,
                lane_width=lane_w,
                car_length=cell_w,
                spaces=section.spaces,
            )
            return self._world_to_screen((x, y))
        x, y = point_on_straight(
            placement,
            space=marker.space,
            lane_pair=marker.lane_pair,
            lane_width=lane_w,
            car_length=cell_w,
        )
        return self._world_to_screen((x, y))

    def _draw_marker(self, marker, board, placements) -> None:
        x, y = self._marker_center(marker, board, placements)
        icon = self.weapon_images.get(MARKER_ICON_WEAPONS.get(marker.kind, ""))
        if icon is not None:
            size = max(24, self._lane_w() * 3)
            scaled = pygame.transform.smoothscale(icon, (size, size))
            rect = scaled.get_rect(center=(x, y))
            self.screen.blit(scaled, rect)
            pygame.draw.rect(self.screen, COLORS["active"], rect, 1, border_radius=3)
        else:
            color = COLORS.get(marker.kind, COLORS["debug"])
            pygame.draw.circle(self.screen, color, (x, y), 12)
        text = self.small.render(marker.kind[0].upper(), True, COLORS["text"])
        self.screen.blit(text, (x - 4, y - 8))

    def _cell_w(self) -> int:
        base = min(CELL_W, BOARD_W // max(1, self.state.track_sections * SECTION_SPACES))
        return max(18, int(base * self.board_zoom))

    def _lane_w(self) -> int:
        return max(6, min(24, self._cell_w() // 3))

    def _world_to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        return round(BOARD_X + 10 + point[0]), round(BOARD_Y + 230 + point[1])

    def _board_view_rect(self) -> pygame.Rect:
        return pygame.Rect(16, 82, 790, 510)

    def _zoom_board(self, wheel_delta: int) -> None:
        if wheel_delta == 0:
            return
        step = 0.1 if wheel_delta > 0 else -0.1
        self.board_zoom = max(0.6, min(1.8, round(self.board_zoom + step, 2)))

    def _oriented_rect_points(
        self,
        center: tuple[float, float],
        heading_degrees: float,
        length: float,
        width: float,
    ) -> list[tuple[float, float]]:
        h = math.radians(heading_degrees)
        forward = (math.cos(h), math.sin(h))
        lateral = (-math.sin(h), math.cos(h))
        return [
            (
                center[0] + sx * forward[0] * length / 2 + sy * lateral[0] * width / 2,
                center[1] + sx * forward[1] * length / 2 + sy * lateral[1] * width / 2,
            )
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))
        ]

    def _current_design_spec(self) -> dict:
        if not self.design_specs:
            self.design_specs = self._default_design_specs()
            self.selected_design_index = 0
        self.selected_design_index = min(self.selected_design_index, len(self.design_specs) - 1)
        return self.design_specs[self.selected_design_index]

    def _design_record(self, spec: dict) -> tuple[dict | None, str | None]:
        try:
            return build_vehicle_design(spec), None
        except VehicleDesignError as exc:
            return None, str(exc)

    def _preview_design_spec(self) -> dict:
        spec = copy.deepcopy(self._current_design_spec())
        if not self.selected_catalog_id:
            return spec
        item = self._catalog_item(self.selected_catalog_id)
        if item is None:
            return spec
        category = item.category
        if category == "weapons":
            if not self.selected_mount_id:
                return spec
            weapons = [
                row
                for row in spec.get("installedWeapons", [])
                if row.get("mountId") != self.selected_mount_id
            ]
            weapons.append(
                {
                    "id": f"{self.selected_catalog_id}-{self.selected_mount_id}",
                    "weaponId": self.selected_catalog_id,
                    "mountId": self.selected_mount_id,
                    "facing": self._default_mount_facing(self.selected_mount_id),
                }
            )
            spec["installedWeapons"] = weapons
        else:
            key = self._spec_list_key_for_category(category)
            if key is not None:
                values = list(spec.get(key, []))
                if self.selected_catalog_id not in values:
                    values.append(self.selected_catalog_id)
                spec[key] = values
        return spec

    def _fit_selected_item_to_design(self) -> None:
        if not self.selected_catalog_id:
            self.design_status = "Select catalogue item first."
            return
        item = self._catalog_item(self.selected_catalog_id)
        if item is None:
            self.design_status = "Selected item is not in the catalogue."
            return
        if item.category == "weapons" and not self.selected_mount_id:
            self.design_status = "Select a hardpoint before fitting a weapon."
            return
        preview = self._preview_design_spec()
        _, error = self._design_record(preview)
        if error:
            self.design_status = error[:58]
            return
        self.design_specs[self.selected_design_index] = preview
        self.design_status = f"Fitted {self.selected_catalog_id}."

    def _remove_selected_mount_item(self) -> None:
        if not self.selected_mount_id:
            self.design_status = "Select a hardpoint before removing."
            return
        spec = copy.deepcopy(self._current_design_spec())
        before = len(spec.get("installedWeapons", []))
        spec["installedWeapons"] = [
            row
            for row in spec.get("installedWeapons", [])
            if row.get("mountId") != self.selected_mount_id
        ]
        if len(spec["installedWeapons"]) == before:
            self.design_status = "No fitted weapon on selected hardpoint."
            return
        self.design_specs[self.selected_design_index] = spec
        self.design_status = f"Cleared {self.selected_mount_id}."

    def _catalog_item(self, item_id: str):
        model = build_vehicle_design_model(self.state, self.selected_vehicle_id)
        return next((item for item in model.equipment if item.id == item_id), None)

    def _spec_list_key_for_category(self, category: str) -> str | None:
        return {
            "mountUpgrades": "mountUpgrades",
            "engineAddOns": "engineAddOns",
            "drivingSystems": "drivingSystems",
            "fireControlComputers": "fireControlComputers",
            "safetyDevices": "safetyDevices",
        }.get(category)

    def _default_mount_facing(self, mount_id: str) -> str:
        if "passive" in mount_id.lower() or mount_id == "tailgate":
            return "rear"
        return "front"

    def _installed_weapons_by_mount(self, record: dict | None) -> dict[str, dict]:
        if record is None:
            return {}
        installed: dict[str, dict] = {}
        for mount in record.get("mounts", []):
            weapons = mount.get("installedWeapons", [])
            if weapons:
                installed[str(mount["mountId"])] = weapons[0]
        return installed

    def _design_stat_lines(
        self,
        current: dict | None,
        current_error: str | None,
        preview: dict | None,
        preview_error: str | None,
    ) -> list[str]:
        if current is None:
            return [f"Current design invalid: {current_error or 'unknown'}"]
        lines = [
            f"Weight {current['totalWeight']}  Cost ${current['totalCost']}",
            f"Payload {current['payloadUsed']} / {current['payloadLimit']}",
            (
                f"Max {current['maximumSpeedMph']}  Acc {current['accelerationMph']}  "
                f"Brake {current['brakingMph']}  Hand {current['handling']}"
            ),
        ]
        if preview is None:
            if preview_error:
                lines.append(f"Preview: {preview_error}")
            else:
                lines.append("Preview: select a hardpoint and item.")
            return lines
        deltas = [
            self._delta("W", preview["totalWeight"], current["totalWeight"]),
            self._delta("$", preview["totalCost"], current["totalCost"], prefix_value=True),
            self._delta("Max", preview["maximumSpeedMph"], current["maximumSpeedMph"]),
            self._delta("Acc", preview["accelerationMph"], current["accelerationMph"]),
            self._delta("Br", preview["brakingMph"], current["brakingMph"]),
            self._delta("H", preview["handling"], current["handling"]),
        ]
        lines.append("Preview " + " ".join(deltas))
        return lines

    def _delta(self, label: str, new: int, old: int, *, prefix_value: bool = False) -> str:
        change = new - old
        sign = "+" if change >= 0 else ""
        if prefix_value:
            return f"{label}{new}({sign}{change})"
        return f"{label}{new}({sign}{change})"

    def _garage_selection_status(self) -> str:
        if self.selected_catalog_id and self.selected_mount_id:
            return f"Previewing {self.selected_catalog_id} on {self.selected_mount_id}."
        if self.selected_catalog_id:
            return f"Selected {self.selected_catalog_id}; choose a hardpoint."
        if self.selected_mount_id:
            return f"Selected {self.selected_mount_id}; choose equipment."
        return "Select a hardpoint and weapon to preview fitting impact."

    def _default_design_specs(self) -> list[dict]:
        return [
            {
                "vehicleId": "Agency Interceptor V6",
                "templateId": "interceptor",
                "designMode": "advancedWeight",
                "engineSize": "v6",
                "installedWeapons": [{"id": "ac-1", "weaponId": "autocannon15mm", "mountId": "hood", "facing": "front"}],
            },
            {
                "vehicleId": "Renegade Pursuit V8",
                "templateId": "renegade",
                "designMode": "advancedWeight",
                "engineSize": "v8",
                "installedWeapons": [{"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "hood", "facing": "front"}],
            },
        ]

    def _mission_save_paths(self) -> list[Path]:
        paths: list[Path] = []
        if DEFAULT_MISSION_SAVE_PATH.exists():
            paths.append(DEFAULT_MISSION_SAVE_PATH)
        if Path("dark_future_save.json").exists():
            paths.append(Path("dark_future_save.json"))
        if SAVE_DIR.exists():
            paths.extend(
                path
                for path in SAVE_DIR.glob("*.json")
                if path.name not in {DESIGN_LIBRARY_PATH.name, DEFAULT_MISSION_SAVE_PATH.name}
            )
        unique: dict[str, Path] = {str(path.resolve()): path for path in paths}
        return sorted(unique.values(), key=lambda path: path.stat().st_mtime, reverse=True)

    def _mission_save_summary(self, save_path: Path) -> str:
        try:
            saved = load_game(save_path)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return "Unreadable save"
        scenario = SCENARIOS.get(saved.scenario_id, {}).get("label", saved.scenario_id)
        result = f", winner {saved.winner}" if saved.game_over and saved.winner else ""
        return f"{scenario} T{saved.turn} P{saved.phase}, ${saved.campaign.funds}{result}"

    def _load_mission_save(self, save_path: Path) -> bool:
        if not save_path.exists():
            self.ui_status = f"Save not found: {save_path.name}."
            return False
        try:
            loaded = load_game(save_path)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            self.ui_status = f"Load failed: {exc}"
            return False
        copy_state(self.state, loaded)
        self.state.save_path = str(save_path)
        self.state.campaign.last_save_path = str(save_path)
        self._set_screen("tactical")
        self.ui_status = f"Loaded mission from {save_path.name}."
        return True

    def _save_design_library(self) -> None:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        DESIGN_LIBRARY_PATH.write_text(json.dumps({"designs": self.design_specs}, indent=2), encoding="utf-8")
        self.design_status = f"Saved {len(self.design_specs)} designs to {DESIGN_LIBRARY_PATH.name}."

    def _load_design_library(self) -> None:
        if not DESIGN_LIBRARY_PATH.exists():
            self.design_status = "No saved designs file yet."
            return
        data = json.loads(DESIGN_LIBRARY_PATH.read_text(encoding="utf-8"))
        self.design_specs = list(data.get("designs", [])) or self._default_design_specs()
        self.selected_design_index = min(self.selected_design_index, len(self.design_specs) - 1)
        self.design_status = f"Loaded {len(self.design_specs)} designs."


def run_smoke() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    app = App()
    app._draw()
    pygame.display.flip()
    pygame.quit()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Render one frame and exit.")
    args = parser.parse_args(argv)
    if args.smoke:
        run_smoke()
    else:
        App().run()


if __name__ == "__main__":
    main()
