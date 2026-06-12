import json
from pathlib import Path
import unittest

from dark_future.ui_pygame import MARKER_ICON_WEAPONS


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WeaponAssetTests(unittest.TestCase):
    def test_generated_weapon_icon_index_paths_exist(self):
        index_path = PROJECT_ROOT / "assets" / "weapons" / "processed" / "weapons.json"
        self.assertTrue(index_path.exists())
        data = json.loads(index_path.read_text(encoding="utf-8"))
        weapon_ids = {item["weaponId"] for item in data["items"]}

        self.assertIn("chainGun", weapon_ids)
        self.assertIn("autocannon15mm", weapon_ids)
        self.assertIn("lightweightMachineGun42mm", weapon_ids)
        for item in data["items"]:
            self.assertTrue((PROJECT_ROOT / item["image"]).exists(), item["image"])

    def test_passive_marker_kinds_have_weapon_icons(self):
        index_path = PROJECT_ROOT / "assets" / "weapons" / "processed" / "weapons.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        weapon_ids = {item["weaponId"] for item in data["items"]}

        self.assertEqual(
            MARKER_ICON_WEAPONS,
            {
                "oil": "oilLayer",
                "smoke": "smokeLayer",
                "spikes": "spikeLayer",
                "mines": "patternMineLayer",
            },
        )
        self.assertTrue(set(MARKER_ICON_WEAPONS.values()).issubset(weapon_ids))

    def test_generated_vehicle_sheet_assets_exist(self):
        index_path = PROJECT_ROOT / "assets" / "vehicle_sheets" / "processed" / "vehicle_sheets.json"
        self.assertTrue(index_path.exists())
        data = json.loads(index_path.read_text(encoding="utf-8"))
        template_ids = {item["vehicleTemplateId"] for item in data["items"]}

        self.assertEqual({"interceptor", "renegade", "bike"}, template_ids)
        for item in data["items"]:
            self.assertTrue((PROJECT_ROOT / item["image"]).exists(), item["image"])
            self.assertTrue((PROJECT_ROOT / item["source"]).exists(), item["source"])


if __name__ == "__main__":
    unittest.main()
