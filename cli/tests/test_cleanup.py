from pathlib import Path
import tempfile
import unittest

from trymtex.cleanup import cleanup_latex_artifacts


class CleanupTests(unittest.TestCase):
    def test_cleanup_removes_aux_files_but_keeps_source_pdf_and_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tex = root / "paper.tex"
            tex.write_text("Text.\n", encoding="utf-8")
            aux = root / "paper.aux"
            log = root / "paper.log"
            pdf = root / "paper.pdf"
            backup = root / "paper.tex.bak"
            for path in (aux, log, pdf, backup):
                path.write_text("x", encoding="utf-8")

            result = cleanup_latex_artifacts([tex])

            self.assertEqual(result.errors, [])
            self.assertEqual(set(result.removed), {aux, log})
            self.assertFalse(aux.exists())
            self.assertFalse(log.exists())
            self.assertTrue(pdf.exists())
            self.assertTrue(backup.exists())
            self.assertTrue(tex.exists())

    def test_cleanup_dry_run_does_not_remove_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tex = root / "paper.tex"
            tex.write_text("Text.\n", encoding="utf-8")
            aux = root / "paper.aux"
            aux.write_text("x", encoding="utf-8")

            result = cleanup_latex_artifacts([tex], dry_run=True)

            self.assertEqual(result.removed, [aux])
            self.assertTrue(aux.exists())


if __name__ == "__main__":
    unittest.main()
