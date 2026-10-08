from pathlib import Path
import unittest

from trymtex.chktex import FIELD_SEP, parse_chktex_output


class ChktexParseTests(unittest.TestCase):
    def test_parse_structured_chktex_output(self) -> None:
        output = FIELD_SEP.join(["paper.tex", "12", "9", "2", "Non-breaking space should have been used.", "see \\ref{x}"])

        warnings = parse_chktex_output(output)

        self.assertEqual(len(warnings), 1)
        warning = warnings[0]
        self.assertEqual(warning.file, Path("paper.tex"))
        self.assertEqual(warning.line, 12)
        self.assertEqual(warning.column, 9)
        self.assertEqual(warning.number, 2)
        self.assertIn("Non-breaking", warning.message)
        self.assertEqual(warning.context, "see \\ref{x}")

    def test_parse_warning_in_fallback(self) -> None:
        output = "Warning 13 in thesis.tex line 4, column 19: Intersentence spacing should perhaps be used."

        warnings = parse_chktex_output(output)

        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].file, Path("thesis.tex"))
        self.assertEqual(warnings[0].line, 4)
        self.assertEqual(warnings[0].column, 19)
        self.assertEqual(warnings[0].number, 13)


if __name__ == "__main__":
    unittest.main()
