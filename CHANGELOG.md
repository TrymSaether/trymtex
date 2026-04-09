# Changelog

## 0.5.0 - 2026-04-09

- Normalized repository to a plain-source `l3build` layout
- Renamed `l3build.lua` to standard `build.lua`
- Removed checked-in TDS install tree from the source repository
- Kept `source/` as the single source of truth
- Split implementation into fonts, layout, colors, math, boxes, theorems, algorithms, graphics, glossaries, plots, and code modules
- Fixed theorem style key definitions and Unicode `\bm` fallback
- Added basic examples, smoke test, and wrapper build targets
