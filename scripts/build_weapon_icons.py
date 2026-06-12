from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "assets" / "weapons" / "source_crops.json"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "weapons" / "processed"
ICON_SIZE = (96, 54)


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    generated: dict[str, Path] = {}
    index_entries: list[dict[str, str]] = []

    for item in manifest["items"]:
        weapon_id = item["weaponId"]
        if item.get("aliasOf"):
            source_path = generated.get(item["aliasOf"])
            if source_path is None:
                continue
            output_path = OUTPUT_DIR / f"{weapon_id}.png"
            pygame.image.save(pygame.image.load(str(source_path)), str(output_path))
            generated[weapon_id] = output_path
            index_entries.append({"weaponId": weapon_id, "image": str(output_path.relative_to(PROJECT_ROOT)).replace("\\", "/")})
            continue
        if item.get("placeholder"):
            continue
        source = pygame.image.load(str(PROJECT_ROOT / item["source"])).convert_alpha()
        crop = source.subsurface(pygame.Rect(*item["rect"])).copy()
        icon = _make_icon(crop)
        output_path = OUTPUT_DIR / f"{weapon_id}.png"
        pygame.image.save(icon, str(output_path))
        generated[weapon_id] = output_path
        index_entries.append({"weaponId": weapon_id, "image": str(output_path.relative_to(PROJECT_ROOT)).replace("\\", "/")})

    index = {
        "status": "generated",
        "sourceManifest": str(MANIFEST_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "items": index_entries,
    }
    (OUTPUT_DIR / "weapons.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    pygame.quit()


def _make_icon(crop: pygame.Surface) -> pygame.Surface:
    transparent = pygame.Surface(crop.get_size(), pygame.SRCALPHA)
    width, height = crop.get_size()
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = crop.get_at((x, y))
            brightness = (red + green + blue) // 3
            if alpha == 0 or brightness > 232:
                continue
            line_alpha = min(255, max(80, 255 - brightness))
            transparent.set_at((x, y), (230, 233, 226, line_alpha))

    bounds = transparent.get_bounding_rect()
    if bounds.width <= 0 or bounds.height <= 0:
        return pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
    trimmed = transparent.subsurface(bounds).copy()
    scale = min(ICON_SIZE[0] / trimmed.get_width(), ICON_SIZE[1] / trimmed.get_height())
    scaled_size = (
        max(1, int(trimmed.get_width() * scale)),
        max(1, int(trimmed.get_height() * scale)),
    )
    scaled = pygame.transform.smoothscale(trimmed, scaled_size)
    icon = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
    icon.blit(scaled, ((ICON_SIZE[0] - scaled_size[0]) // 2, (ICON_SIZE[1] - scaled_size[1]) // 2))
    return icon


if __name__ == "__main__":
    main()
