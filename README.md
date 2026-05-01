# trymtex

`trymtex` is a modular, general-purpose LaTeX package for personal document setup. It provides defaults for fonts, layout, theorem styling, utility boxes, math helpers, and optional feature modules.

The package reduces boilerplate when starting new LaTeX documents by bundling commonly used packages and configuring them to work together.

## Usage

Simply load the package in your preamble:

```latex
\usepackage[
  fontset=lmodern, % Or pagella, ibmplex, fira, none
  minted=true,     % Enable code listings via minted
  theorems=true,   % Enable pre-styled theorem environments
  plots=true       % Enable TikZ/pgfplots helpers
]{trymtex}
```

### Key Options

- **`fontset`**: Choose between `lmodern` (default), `pagella`, `ibmplex`, `fira`, or `none`.
- **Feature toggles**: `minted`, `glossaries`, `theorems`, `plots`, `pagegeometry`, `fancyhdr`, and `toc` are enabled by default; `biblatex`, `babel`, and `subfiles` are disabled by default.
- **Language support**: Pass `babel=true` along with `mainlanguage` and `languages`.
- **Bibliographies**: Pass `biblatex=true` to load `biblatex`; the default backend is `biber`.

See the provided manual for extensive examples of the environments and features available.

## Repository Layout

- `source/` — canonical authored package files
- `doc/` — manual sources (`manual.tex`)
- `examples/` — usage examples (`minimal.tex`, `showcase.tex`)
- `testfiles/` — smoke/regression tests (`l3build` test suite)
- `build.lua` — `l3build` configuration

This repository uses the plain-source `l3build` model. The canonical package entrypoint is `source/trymtex.sty`; installed users load it with `\usepackage{trymtex}`. Internal modules are package-owned files named `trymtex-*.tex`.

## Common Tasks

Building the package, documentation, and running tests is handled by `l3build` (which wraps around normal LaTeX tools):

```bash
l3build check      # Run smoke tests
l3build doc        # Build the manual inside build/doc/
l3build ctan       # Build the CTAN release archive
l3build install    # Install the package into your local texmf tree
l3build clean      # Remove generated artifacts
```

Wrapper targets are also available through `make`.

Build the examples from the repository root with:

```bash
latexmk -lualatex examples/minimal.tex
TEXINPUTS=source: latexmk -lualatex -shell-escape -outdir=build examples/showcase.tex
```

## Notes

- The `minted=true` option requires Python/Pygments and a LaTeX setup that permits the needed external command execution. Pass `-shell-escape` only for documents that use minted code blocks.
- The package is licensed under the MIT License; see `LICENSE`.
