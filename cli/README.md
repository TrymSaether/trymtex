# trymtex

`trymtex` is a Python CLI for LaTeX formatting, ChkTeX linting, conservative autofixing, and optional compile validation.

It uses Rich when available for panels, colored states, grouped warnings, and summary tables. In CI, `NO_COLOR`, `--plain`, or environments without Rich, it falls back to readable plain output.

## Install

```bash
python -m pip install -e .
```

The CLI expects these tools to be installed and on `PATH` when their feature is used:

- `chktex`
- `latexindent`
- `latexmk`
- `pdflatex`
- `tectonic`

## Usage

```bash
trymtex --check --format --lint --diff
trymtex --fix --lint --backup paper.tex
trymtex --all --compile-check
trymtex --dry-run --fix --diff chapters/
```

Important options:

- `--check`: reports what would change and exits `1` if formatting changes, warnings, or proposed fixes exist.
- `--fix`: applies safe localized autofixes from parsed ChkTeX diagnostics.
- `--format`: runs `latexindent`; local `.latexindent.yaml` or `latexindent.yaml` is detected.
- `--lint`: runs `chktex` with parseable output and groups warnings by file.
- `--all`: formats, lints, autofixes, then lints again.
- `--dry-run`: computes proposed changes without writing.
- `--diff`: prints unified diffs for formatting changes.
- `--backup`: writes `.bak` files before edits.
- `--config PATH`: reads config from `trymtex.toml`, `.trymtex.toml`, or `pyproject.toml` `[tool.trymtex]`.
- `--include` / `--exclude`: repeatable glob controls.
- `--fail-on-warnings`: exits `1` when warnings remain.
- `--compile-check`: compiles after edits; compile failures exit `3`.
- `--plain`, `--no-color`, `--quiet`, `--verbose`: output controls for CI and local debugging.

## Report

Every run reports:

- files scanned
- files formatted
- warnings before
- autofixes applied
- warnings resolved
- warnings remaining
- files changed
- remaining warnings as `file:line:col ChkTeX <num> message`

Exit codes:

- `0`: success
- `1`: warnings remain or check failed
- `2`: tool, config, or runtime error
- `3`: compile check failed

## Config

See [examples/trymtex.toml](examples/trymtex.toml).

```toml
include = ["**/*.tex"]
exclude = ["build/**", "**/*.generated.tex"]
backup = false
fail_on_warnings = false

[formatter]
format_bib = false

[fixers]
enabled = ["nbsp-before-ref", "space-before-punctuation"]

[compile]
engine = "latexmk"
main = "main.tex"
args = ["-pdf"]
```

`.bib` formatting is skipped by default. Enable it with `formatter.format_bib = true`.

## Autofixes

Implemented fixers are deliberately conservative:

- `nbsp-before-ref`: replaces ordinary spacing before common reference and citation macros with `~`.
- `space-before-punctuation`: removes obvious spaces before punctuation when ChkTeX asks for it.

Fixes use parsed file, line, and column diagnostics, edit only the nearby line, and are idempotent. The fixer skips verbatim-like environments and macro-definition contexts.

Not automated:

- semantic rewrites where ChkTeX does not identify a safe local edit
- math-mode changes requiring TeX parsing
- macro definitions and generated files
- verbatim, minted, listings, alltt, and comment environments
- ambiguous dash, quote, spacing, or typography warnings

Skipped warnings are reported with the reason.

## Compile Validation

`--compile-check` supports `latexmk`, `pdflatex`, `lualatex`, and `tectonic`.

Configure the engine and root document:

```toml
[compile]
engine = "latexmk"
main = "main.tex"
args = ["-pdf"]
```

Compile failures are summarized clearly and exit with code `3`.

## VS Code Tasks

Example task files are included in [.vscode/tasks.json](.vscode/tasks.json) and [.vscode/settings.json](.vscode/settings.json):

- `LaTeX: format + lint + autofix`
- `LaTeX: check only`
- `LaTeX: autofix current file`

These are manual tasks. This project does not implement the LaTeX Workshop Quick Fix API.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
