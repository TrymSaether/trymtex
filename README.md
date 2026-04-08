# trymtex

`trymtex` is a general-purpose LaTeX package extracted from a personal preamble and reorganized into a reusable package.

## Features

- engine-agnostic support for pdfLaTeX, XeLaTeX, and LuaLaTeX
- optional font presets (`pagella`, `ibmplex`, `fira`, `none`)
- math helpers and theorem boxes
- tables, floats, algorithms, TikZ/pgfplots, glossaries, and bibliography support
- optional `minted`

## Basic use

```tex
\usepackage[pagella,mainlanguage=english,languages={norsk,english}]{trymtex}
```

## Notes

- `minted=true` requires shell escape when code listings are used.
- `ibmplex` and `fira` require the corresponding OpenType fonts under XeLaTeX/LuaLaTeX.
- Under pdfLaTeX, non-default Unicode font presets fall back to `newpxtext/newpxmath`.

## Test suite

The bundle ships with a small smoke-test setup:

- `testfiles/smoke-pdftex.lvt`
- `testfiles/smoke-unicode.lvt`
- `build.lua`

Use `l3build check` if available, or compile the test documents directly.
