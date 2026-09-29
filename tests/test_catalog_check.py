"""The catalog check must not pass without its generated index."""

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class CatalogCheckTests(unittest.TestCase):
    def test_missing_index_or_markers_fails_check(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_catalog.py"
        spec = importlib.util.spec_from_file_location("generate_catalog", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "README.md"
            for case in ("missing", "no markers"):
                with self.subTest(case=case):
                    if case == "no markers":
                        target.write_text("# Catalog\n", encoding="utf-8")
                    output = io.StringIO()
                    with mock.patch.object(module, "ROOT", Path(tmp)), mock.patch.object(
                        module, "TARGETS", [target]
                    ), mock.patch.object(sys, "argv", [str(script), "--check"]), contextlib.redirect_stdout(output):
                        self.assertEqual(module.main(), 1)
                    self.assertIn("README.md", output.getvalue())
                    self.assertNotIn("index fresh", output.getvalue())


if __name__ == "__main__":
    unittest.main()
