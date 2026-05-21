from pathlib import Path
import tempfile
import unittest

from trymtex.config import TrymtexConfig
from trymtex.fixers import apply_fixes
from trymtex.io import read_text_file
from trymtex.models import ChktexWarning


class FixerTests(unittest.TestCase):
    def test_nbsp_fix_is_local_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tex = tmp_path / "paper.tex"
            tex.write_text("See \\ref{eq:a} and See~\\ref{eq:b}.\n", encoding="utf-8")
            warning = ChktexWarning(tex, 1, 5, 2, "Non-breaking space should have been used.", "See \\ref{eq:a}")

            fixes, changed, changes = apply_fixes([warning], TrymtexConfig(), dry_run=False, backup=False)
            second_fixes, second_changed, second_changes = apply_fixes([warning], TrymtexConfig(), dry_run=False, backup=False)

            self.assertTrue(fixes[0].changed)
            self.assertIn(tex, changed)
            self.assertEqual(len(changes), 1)
            self.assertEqual(tex.read_text(encoding="utf-8"), "See~\\ref{eq:a} and See~\\ref{eq:b}.\n")
            self.assertFalse(second_fixes[0].changed)
            self.assertFalse(second_changed)
            self.assertFalse(second_changes)

    def test_fix_skips_verbatim_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tex = tmp_path / "paper.tex"
            tex.write_text("\\begin{verbatim}\nSee \\ref{eq:a}\n\\end{verbatim}\n", encoding="utf-8")
            warning = ChktexWarning(tex, 2, 5, 2, "Non-breaking space should have been used.", "See \\ref{eq:a}")

            fixes, changed, changes = apply_fixes([warning], TrymtexConfig(), dry_run=False, backup=False)

            self.assertFalse(fixes[0].changed)
            self.assertIn("verbatim", fixes[0].reason)
            self.assertFalse(changed)
            self.assertFalse(changes)

    def test_backup_preserves_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tex = tmp_path / "paper.tex"
            tex.write_text("See \\ref{eq:a}\r\n", encoding="utf-8")
            warning = ChktexWarning(tex, 1, 5, 2, "Non-breaking space should have been used.", "See \\ref{eq:a}")

            apply_fixes([warning], TrymtexConfig(), dry_run=False, backup=True)

            self.assertEqual((tmp_path / "paper.tex.bak").read_text(encoding="utf-8"), "See \\ref{eq:a}\n")
            self.assertEqual(read_text_file(tex).newline, "\r\n")


if __name__ == "__main__":
    unittest.main()
