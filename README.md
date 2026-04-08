# trymtex

`trymtex` is a LuaLaTeX-oriented package bundling a modern mathematical writing setup:
fonts, microtypography, `biblatex`, theorem boxes via `tcolorbox`, tables, algorithms,
graphics, and a few utility macros.

## Files

- `trymtex.dtx` — documented source
- `trymtex.ins` — installer
- `trymtex.sty` — extracted package file
- `trymtex-example.tex` — minimal example

## Installation

### Local installation
Place `trymtex.sty` somewhere TeX can find it, for example in the same directory as your document.

### TDS-style installation
Run:

```bash
latex trymtex.ins
```

Then place the generated `trymtex.sty` in your local `texmf` tree, for example:

```text
~/texmf/tex/latex/trymtex/trymtex.sty
```

Refresh the filename database if your TeX distribution requires it.

## Usage

```latex
\usepackage{trymtex}
```

The package is intended for **LuaLaTeX**.

## Package options

### Font options
Choose at most one:

- `pagella` (default)
- `ibmplex`
- `fira`

### Feature toggles
All default to `true`.

- `theorems`
- `algorithms`
- `minted`
- `glossaries`
- `plots`
- `layout`
- `headers`
- `hyperrefsetup`

Example:

```latex
\usepackage[
  ibmplex,
  minted=false,
  mainlanguage=english,
  languages={norsk,english}
]{trymtex}
```

## Notes

- `minted` requires shell escape and Python/Pygments.
- `biblatex` is configured with `backend=biber`.
- The package does **not** set PDF metadata such as title or author. That belongs in the document.
- The package does **not** globally redefine `\mathbf`.

## License

Choose the license you want before public release. If you want a standard LaTeX package license,
LPPL 1.3c is the usual choice.
