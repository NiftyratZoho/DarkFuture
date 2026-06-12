from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "assets" / "weapons" / "processed" / "weapons.json"
PREVIEW_PATH = PROJECT_ROOT / "assets" / "weapons" / "processed" / "weapon_icon_preview.png"


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    items = index["items"]
    cell_w = 190
    cell_h = 86
    cols = 4
    rows = (len(items) + cols - 1) // cols
    preview = pygame.Surface((cols * cell_w, rows * cell_h), pygame.SRCALPHA)
    preview.fill((32, 36, 40, 255))
    font = pygame.font.SysFont("consolas", 14)
    for idx, item in enumerate(items):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        icon = pygame.image.load(str(PROJECT_ROOT / item["image"])).convert_alpha()
        preview.blit(icon, (x + 8, y + 8))
        label = font.render(item["weaponId"], True, (226, 229, 224))
        preview.blit(label, (x + 8, y + 66))
        pygame.draw.rect(preview, (68, 72, 72), (x, y, cell_w, cell_h), 1)
    pygame.image.save(preview, str(PREVIEW_PATH))
    pygame.quit()


if __name__ == "__main__":
    main()
