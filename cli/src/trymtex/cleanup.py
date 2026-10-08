from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


LATEX_AUX_SUFFIXES = {
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".brf",
    ".dvi",
    ".fdb_latexmk",
    ".fls",
    ".glg",
    ".glo",
    ".gls",
    ".idx",
    ".ilg",
    ".ind",
    ".ist",
    ".lof",
    ".log",
    ".lol",
    ".lot",
    ".nav",
    ".out",
    ".run.xml",
    ".snm",
    ".synctex",
    ".synctex.gz",
    ".toc",
    ".vrb",
    ".xdv",
}


@dataclass
class CleanupResult:
    removed: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def cleanup_latex_artifacts(files: list[Path], dry_run: bool = False) -> CleanupResult:
    result = CleanupResult()
    for artifact in _candidate_artifacts(files):
        if not artifact.exists() or not artifact.is_file():
            continue
        if dry_run:
            result.removed.append(artifact)
            continue
        try:
            artifact.unlink()
            result.removed.append(artifact)
        except OSError as exc:
            result.errors.append(f"Could not remove {artifact}: {exc}")
    return result


def _candidate_artifacts(files: list[Path]) -> list[Path]:
    candidates: set[Path] = set()
    for path in files:
        if path.suffix != ".tex":
            continue
        base = path.with_suffix("")
        for suffix in LATEX_AUX_SUFFIXES:
            candidates.add(Path(str(base) + suffix))
    return sorted(candidates)

