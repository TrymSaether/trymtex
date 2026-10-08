# trymtex

`trymtex` is a Python CLI for LaTeX formatting, ChkTeX linting, built-in semantic checking, conservative autofixing, and optional compile validation.

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
trymtex --semantic --fix --diff paper.tex
trymtex --dry-run --fix --diff chapters/
trymtex --cleanup-only paper.tex
```

Important options:

- `--check`: reports what would change and exits `1` if formatting changes, warnings, or proposed fixes exist.
- `--fix`: applies safe localized autofixes from parsed ChkTeX and semantic diagnostics.
- `--format`: runs `latexindent`; local `.latexindent.yaml` or `latexindent.yaml` is detected.
- `--lint`: runs `chktex` with parseable output and groups warnings by file.
- `--semantic`: runs the built-in TeX-aware semantic checker.
- `--all`: formats, lints, runs semantic checks, autofixes, then checks again.
- `--dry-run`: computes proposed changes without writing.
- `--diff`: prints unified diffs for formatting and autofix changes.
- `--backup`: writes `.bak` files before edits.
- `--config PATH`: reads config from `trymtex.toml`, `.trymtex.toml`, or `pyproject.toml` `[tool.trymtex]`.
- `--include` / `--exclude`: repeatable glob controls.
- `--fail-on-warnings`: exits `1` when warnings remain.
- `--compile-check`: compiles after edits; compile failures exit `3`.
- `--cleanup`: removes common LaTeX auxiliary files after the run.
- `--cleanup-only`: only removes common LaTeX auxiliary files for scanned `.tex` files.
- `--plain`, `--no-color`, `--quiet`, `--verbose`: output controls for CI and local debugging.

## Report

Every run reports:

- files scanned
- files formatted
- warnings before
- semantic issues before
- autofixes applied
- warnings resolved
- warnings remaining
- semantic issues remaining
- files changed
- cleanup files removed
- remaining warnings as `file:line:col ChkTeX <num> message`
- remaining semantic issues as `file:line:col Semantic <rule> message`

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

[semantic]
enabled = [
  "duplicate-label",
  "undefined-reference",
  "unused-label",
  "duplicate-usepackage",
  "duplicate-macro-definition",
  "repeated-word",
  "bare-url",
  "math-operator",
  "math-spacing-punctuation",
  "inline-math-delimiter",
  "display-math-delimiter",
  "eqnarray-environment",
  "deprecated-font-command",
  "centerline-command",
  "dash-range",
  "spaced-em-dash",
  "tex-quotes",
  "ellipsis",
  "prose-spacing",
]
autofix = [
  "duplicate-usepackage",
  "duplicate-macro-definition",
  "repeated-word",
  "bare-url",
  "math-operator",
  "math-spacing-punctuation",
  "inline-math-delimiter",
  "display-math-delimiter",
  "eqnarray-environment",
  "deprecated-font-command",
  "centerline-command",
  "dash-range",
  "spaced-em-dash",
  "tex-quotes",
  "ellipsis",
  "prose-spacing",
]

[compile]
engine = "latexmk"
main = "main.tex"
args = ["-pdf"]
```

`.bib` formatting is skipped by default. Enable it with `formatter.format_bib = true`.

## Autofixes

Implemented ChkTeX fixers are deliberately conservative:

- `nbsp-before-ref`: replaces ordinary spacing before common reference and citation macros with `~`.
- `space-before-punctuation`: removes obvious spaces before punctuation when ChkTeX asks for it.

Fixes use parsed file, line, and column diagnostics, edit only the nearby line, and are idempotent. The ChkTeX fixer skips verbatim-like environments and macro-definition contexts.

Semantic automation:

- detects duplicate labels, undefined references, unused labels, duplicate package imports, and duplicate or conflicting macro definitions
- autofixes exact duplicate package imports and exact duplicate macro definitions
- autofixes repeated prose words and bare URLs
- parses coarse TeX contexts before math rewrites, including inline math, display math, and common math environments
- autofixes common bare math operators such as `sin`, `cos`, and `log`, plus spaces before math punctuation
- converts safe inline `$...$` to `\(...\)`, single-line `$$...$$` to `\[...\]`, and standalone `$$` display delimiters to `\[` / `\]`
- rewrites `eqnarray` / `eqnarray*` environments to `align` / `align*`
- modernizes simple old-style font groups such as `{\bf text}` to `\textbf{text}` and `\centerline{text}` to a `center` environment
- autofixes typography cases: numeric/letter ranges to `--`, spaced hyphens to `---`, straight quote pairs to TeX quotes, `...` to `\ldots{}`, and spaces before punctuation
- recognizes generated-file markers and skips generated files
- skips verbatim-like environments: `verbatim`, `Verbatim`, `minted`, `lstlisting`, `alltt`, and `comment`

Ambiguous cases are automated only when they match these local rules. Anything outside those rules is skipped and reported with the reason.

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

## Cleanup

Use `--cleanup` to remove common LaTeX auxiliary files after a run:

```bash
trymtex --all --compile-check --cleanup main.tex
```

Use `--cleanup-only` for cleanup without linting, formatting, fixing, or compiling:

```bash
trymtex --cleanup-only main.tex
```

Cleanup removes source-adjacent auxiliary files such as `.aux`, `.log`, `.out`, `.toc`, `.fls`, `.fdb_latexmk`, `.synctex.gz`, `.bbl`, `.blg`, and related LaTeX build artifacts. It does not remove `.tex`, `.pdf`, `.bak`, config files, or unrelated files.

## VS Code Tasks

Example task files are included in [.vscode/tasks.json](.vscode/tasks.json) and [.vscode/settings.json](.vscode/settings.json). Reusable templates for other LaTeX projects are in [examples/vscode](examples/vscode):

- `LaTeX: format + lint + autofix`
- `LaTeX: check only`
- `LaTeX: autofix current file`
- `TrymTeX: check project`
- `TrymTeX: dry-run/apply autofix project`
- `TrymTeX: dry-run/apply autofix current file`

These are manual tasks. This project does not implement the LaTeX Workshop Quick Fix API.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
