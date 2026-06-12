import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


HTML_PATH = Path(r"D:\Stream Resources\minecraft_wheel.html")
TEXTURE_BASE = Path(r"D:\Stream Resources\Default-Java-1.21.11\assets\minecraft\textures")
CACHE_DIR = Path(r"D:\Stream Resources\minecraft_icon_cache")
WIKI_ICON_BASE = "https://minecraft.wiki/images/ItemSprite_"
WIKI_FILE_BASE = "https://minecraft.wiki/w/Special:FilePath/"


OVERRIDES = {
    "acacia boat with chest": "chest-boat-acacia",
    "birch boat with chest": "chest-boat-birch",
    "cherry boat with chest": "chest-boat-cherry",
    "dark oak boat with chest": "chest-boat-dark-oak",
    "jungle boat with chest": "chest-boat-jungle",
    "mangrove boat with chest": "chest-boat-mangrove",
    "oak boat with chest": "chest-boat-oak",
    "spruce boat with chest": "chest-boat-spruce",
    "bamboo raft with chest": "chest-raft-bamboo",
    "block of amethyst": "amethyst-block",
    "block of bamboo": "bamboo-block",
    "block of coal": "coal-block",
    "block of copper": "copper-block",
    "block of diamond": "diamond-block",
    "block of emerald": "emerald-block",
    "block of gold": "gold-block",
    "block of iron": "iron-block",
    "block of lapis lazuli": "lapis-block",
    "block of netherite": "netherite-block",
    "block of quartz": "quartz-block",
    "block of raw copper": "raw-copper-block",
    "block of raw gold": "raw-gold-block",
    "block of raw iron": "raw-iron-block",
    "block of redstone": "redstone-block",
    "block of resin": "resin-block",
    "block of stripped bamboo": "stripped-bamboo-block",
    "book and quill": "writable-book",
    "carrot on a stick": "carrot-on-a-stick",
    "disc fragment 5": "disc-fragment-5",
    "experience bottle": "experience-bottle",
    "jack o'lantern": "jack-o-lantern",
    "leather cap": "leather-helmet",
    "leather pants": "leather-leggings",
    "leather tunic": "leather-chestplate",
    "tnt": "tnt",
    "tnt minecart": "tnt-minecart",
    "warped fungus on a stick": "warped-fungus-on-a-stick",
    "wither skeleton skull": "wither-skeleton-skull",
    "cooked porkchop": "cooked-porkchop",
}

LOCAL_OVERRIDES = {
    "book and quill": "writable_book",
    "carrot on a stick": "carrot_on_a_stick",
    "disc fragment 5": "disc_fragment_5",
    "enchanted golden apple": "enchanted_golden_apple",
    "experience bottle": "experience_bottle",
    "glistering melon slice": "glistering_melon_slice",
    "jack o'lantern": "jack_o_lantern",
    "leather cap": "leather_helmet",
    "leather pants": "leather_leggings",
    "leather tunic": "leather_chestplate",
    "chain": "iron_chain",
    "deepslate lapis lazuli ore": "deepslate_lapis_ore",
    "redstone repeater": "repeater",
    "tnt": "tnt",
    "warped fungus on a stick": "warped_fungus_on_a_stick",
    "wither skeleton skull": "wither_skeleton_skull",
}


def parse_items():
    html = HTML_PATH.read_text(encoding="utf-8")
    match = re.search(r"const ITEMS = \[([\s\S]*?)\];", html)
    if not match:
        raise RuntimeError("Could not find ITEMS in minecraft_wheel.html")
    return json.loads(f"[{match.group(1)}]")


def cache_name(name):
    return re.sub(r"(^_+|_+$)", "", re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", ""))) + ".png"


def wiki_name(name):
    lower = name.lower()
    return OVERRIDES.get(lower, lower.replace("'", "").replace(" ", "-"))


def texture_name(name):
    lower = name.lower()
    unwrapped = re.sub(r"^waxed ", "", lower)
    chest_boat = re.match(r"^(.+) boat with chest$", lower)
    if chest_boat:
        return chest_boat.group(1).replace(" ", "_") + "_chest_boat"
    chest_raft = re.match(r"^(.+) raft with chest$", lower)
    if chest_raft:
        return chest_raft.group(1).replace(" ", "_") + "_chest_raft"
    if unwrapped == "block of lapis lazuli":
        return "lapis_block"
    block_of = re.match(r"^block of (.+)$", unwrapped)
    if block_of:
        return block_of.group(1).replace(" ", "_") + "_block"
    return LOCAL_OVERRIDES.get(lower) or LOCAL_OVERRIDES.get(unwrapped) or unwrapped.replace("'", "").replace(" ", "_")


def fallback_texture_names(name, texture):
    names = []
    lower = name.lower()
    wood = {"acacia", "bamboo", "birch", "cherry", "dark_oak", "jungle", "mangrove", "oak", "spruce", "warped"}
    suffixes = ["_button", "_fence_gate", "_fence", "_pressure_plate", "_slab", "_stairs", "_wall"]
    for suffix in suffixes:
        if texture.endswith(suffix):
            base = texture[: -len(suffix)]
            names.extend([base, f"{base}s", f"{base}_block", f"{base}_bricks"])
            if base in wood:
                names.append(f"{base}_planks")
    if texture.endswith("_wood"):
        names.append(texture.removesuffix("_wood") + "_log")
    if lower.endswith(("bricks", "brick wall", "brick slab", "brick stairs")):
        names.append(re.sub(r"_brick(_wall|_slab|_stairs)?$", "_bricks", texture))
    return list(dict.fromkeys(names))


def exact_local_candidates(name):
    texture = texture_name(name)
    paths = [
        TEXTURE_BASE / "item" / f"{texture}.png",
        TEXTURE_BASE / "block" / f"{texture}.png",
    ]
    if texture == "chest":
        paths.append(TEXTURE_BASE / "entity" / "chest" / "normal.png")
    return paths


def fallback_local_candidates(name):
    texture = texture_name(name)
    names = fallback_texture_names(name, texture)
    paths = []
    for texture in names:
        paths.extend([
            TEXTURE_BASE / "item" / f"{texture}.png",
            TEXTURE_BASE / "block" / f"{texture}.png",
            TEXTURE_BASE / "item" / f"{texture}_00.png",
            TEXTURE_BASE / "item" / f"{texture}_standby.png",
            TEXTURE_BASE / "block" / f"{texture}_top.png",
            TEXTURE_BASE / "block" / f"{texture}_side.png",
            TEXTURE_BASE / "block" / f"{texture}_front.png",
            TEXTURE_BASE / "map" / "decorations" / f"{texture}.png",
        ])
    return paths


def wiki_candidates(name):
    sprite = wiki_name(name)
    spaced = name.replace("'", "")
    underscored = spaced.replace(" ", "_")
    encoded = urllib.parse.quote(spaced).replace("%20", "_")
    return [
        f"{WIKI_ICON_BASE}{sprite}.png",
        f"{WIKI_FILE_BASE}ItemSprite_{sprite}.png",
        f"{WIKI_FILE_BASE}Invicon_{encoded}.png",
        f"{WIKI_FILE_BASE}{underscored}_JE1_BE1.png",
        f"{WIKI_FILE_BASE}{underscored}_JE1.png",
        f"{WIKI_FILE_BASE}{underscored}.png",
    ]


def download(url, target):
    request = urllib.request.Request(url, headers={"User-Agent": "OBS Minecraft wheel icon cache"})
    with urllib.request.urlopen(request, timeout=12) as response:
        content_type = response.headers.get("content-type", "")
        data = response.read()
    if not data.startswith(b"\x89PNG") and "image" not in content_type:
        return False
    target.write_bytes(data)
    return True


def main():
    force = "--force" in sys.argv
    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        if idx + 1 < len(sys.argv):
            only = {name.strip().lower() for name in sys.argv[idx + 1].split("|") if name.strip()}

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    copied = downloaded = missing = existing = 0
    missing_items = []

    for item in parse_items():
        if only and item.lower() not in only:
            continue

        target = CACHE_DIR / cache_name(item)
        if target.exists() and target.stat().st_size > 0 and not force:
            existing += 1
            continue

        local = next((path for path in exact_local_candidates(item) if path.exists()), None)
        if local:
            shutil.copyfile(local, target)
            copied += 1
            continue

        for url in wiki_candidates(item):
            try:
                if download(url, target):
                    downloaded += 1
                    time.sleep(0.05)
                    break
            except Exception:
                continue
        else:
            fallback = next((path for path in fallback_local_candidates(item) if path.exists()), None)
            if fallback:
                shutil.copyfile(fallback, target)
                copied += 1
            else:
                missing += 1
                missing_items.append(item)

    print(f"existing={existing} copied_local={copied} downloaded_wiki={downloaded} missing={missing}")
    if missing_items:
        print("Missing:")
        for item in missing_items[:80]:
            print(f" - {item}")


if __name__ == "__main__":
    main()
