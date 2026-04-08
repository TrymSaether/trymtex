# trymtex

`trymtex` is a reusable LaTeX package extracted from a larger personal preamble.

## Features

- engine-agnostic: pdfLaTeX, XeLaTeX, LuaLaTeX
- language support via `babel`
- typography defaults and optional `microtype`
- theorem boxes built on `tcolorbox`
- math helpers and common shortcuts
- table, float, plotting, and algorithm support
- documented source in `trymtex.dtx`
- installer in `trymtex.ins`
- small `l3build` smoke-test suite

## Installation

### Local installation
Place `trymtex.sty` somewhere TeX can find it, for example in a local `texmf`
tree.

### From documented source
Run:

```bash
tex trymtex.ins
```

This extracts `trymtex.sty` from `trymtex.dtx`.

## Documentation

Generate the package documentation with:

```bash
pdflatex trymtex.dtx
makeindex -s gind.ist trymtex.idx
makeindex -s gglo.ist -o trymtex.gls trymtex.glo
pdflatex trymtex.dtx
pdflatex trymtex.dtx
```

## Tests

This bundle includes a minimal `l3build` setup.

Run:

```bash
l3build check
```

The tests are smoke tests intended to catch package-level regressions across
engines.

## Example

```latex
\documentclass{article}
\usepackage[minted=false,glossaries=false,pagella]{trymtex}

\begin{document}
$\R \subseteq \C$ and $\norm{x} \le \abs{x}$.

\begin{definition}{Sample}{sample}
A short theorem-box example.
\end{definition}

\begin{proof}
A boxed proof environment.
\end{proof}
\end{document}
```

## Notes

- `minted=true` requires shell escape and a working Pygments installation.
- The `ibmplex` and `fira` font presets for XeLaTeX/LuaLaTeX require those
  fonts to be installed on the target system.
- Under pdfLaTeX, non-default OpenType font presets fall back to
  `newpxtext/newpxmath`.
