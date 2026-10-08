from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trymtex import cli
from trymtex.models import ChktexWarning, EXIT_SUCCESS, EXIT_WARNINGS


class CliTests(unittest.TestCase):
    def test_check_exits_nonzero_when_warnings_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tex = tmp_path / "paper.tex"
            tex.write_text("Text.\n", encoding="utf-8")
            with patch.object(cli, "missing_tools", lambda names: []), patch.object(
                cli, "run_chktex", lambda files: ([ChktexWarning(tex, 1, 1, 1, "warning")], [])
            ):
                code = cli.main(["--check", "--quiet", str(tmp_path)])

            self.assertEqual(code, EXIT_WARNINGS)

    def test_lint_success_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tex = tmp_path / "paper.tex"
            tex.write_text("Text.\n", encoding="utf-8")
            with patch.object(cli, "missing_tools", lambda names: []), patch.object(cli, "run_chktex", lambda files: ([], [])):
                code = cli.main(["--lint", "--quiet", str(tmp_path)])

            self.assertEqual(code, EXIT_SUCCESS)

    def test_cleanup_only_removes_aux_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tex = tmp_path / "paper.tex"
            aux = tmp_path / "paper.aux"
            tex.write_text("Text.\n", encoding="utf-8")
            aux.write_text("aux", encoding="utf-8")

            code = cli.main(["--cleanup-only", "--quiet", str(tex)])

            self.assertEqual(code, EXIT_SUCCESS)
            self.assertFalse(aux.exists())


if __name__ == "__main__":
    unittest.main()
