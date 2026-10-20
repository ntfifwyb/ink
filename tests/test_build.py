import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402


class BuildTest(unittest.TestCase):
    def test_archive_has_addon_files_at_root(self):
        out = build.build()
        with zipfile.ZipFile(out) as z:
            names = z.namelist()
        self.assertIn("__init__.py", names)
        self.assertIn("manifest.json", names)
        self.assertIn("config.json", names)
        self.assertFalse([n for n in names if "__pycache__" in n or n.endswith(".pyc")])
        self.assertIn("web/deck_list.css", names)
        self.assertNotIn("meta.json", names)
        self.assertFalse([n for n in names if n.startswith("user_files")])

    def test_build_is_reproducible(self):
        first = build.build().read_bytes()
        second = build.build().read_bytes()
        self.assertEqual(first, second)

    def test_manifest_names_the_package(self):
        manifest = json.loads((build.SRC / "manifest.json").read_text())
        self.assertEqual(manifest["package"], "ink")

    def test_package_imports_outside_anki(self):
        sys.path.insert(0, str(ROOT / "src"))
        import ink

        self.assertIsNone(ink.mw)


if __name__ == "__main__":
    unittest.main()
