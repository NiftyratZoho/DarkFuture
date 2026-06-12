from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "_analysis" / "wlf_pages"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "vehicle_sheets" / "processed"


CROPS = {
    "interceptor": {
        "source": "wlf-50.jpg",
        "rect": [425, 690, 330, 640],
    },
    "renegade": {
        "source": "wlf-54.jpg",
        "rect": [430, 700, 330, 620],
    },
    "bike": {
        "source": "wlf-52.jpg",
        "rect": [435, 760, 330, 540],
    },
}


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for vehicle_id, crop in CROPS.items():
        source_path = SOURCE_DIR / crop["source"]
        surface = pygame.image.load(str(source_path)).convert()
        rect = pygame.Rect(crop["rect"])
        image = pygame.Surface(rect.size, pygame.SRCALPHA)
        image.blit(surface, (0, 0), rect)
        image = _white_to_alpha(image)
        out_path = OUTPUT_DIR / f"{vehicle_id}.png"
        pygame.image.save(image, str(out_path))
        items.append(
            {
                "vehicleTemplateId": vehicle_id,
                "image": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "source": str(source_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "cropRect": crop["rect"],
            }
        )
    (OUTPUT_DIR / "vehicle_sheets.json").write_text(
        json.dumps({"items": items}, indent=2),
        encoding="utf-8",
    )
    pygame.quit()


def _white_to_alpha(surface: pygame.Surface) -> pygame.Surface:
    result = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            r, g, b, _ = surface.get_at((x, y))
            alpha = 0 if r > 246 and g > 246 and b > 246 else 235
            result.set_at((x, y), (r, g, b, alpha))
    return result


if __name__ == "__main__":
    main()
