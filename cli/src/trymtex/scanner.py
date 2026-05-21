from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from .config import TrymtexConfig


def scan_files(paths: list[Path], config: TrymtexConfig, include: list[str], exclude: list[str]) -> list[Path]:
    includes = include or config.include
    excludes = config.exclude + exclude
    files: set[Path] = set()
    roots = paths or [Path.cwd()]
    for root in roots:
        root = root.resolve()
        if root.is_file():
            if _matches(root, includes, excludes):
                files.add(root)
            continue
        for pattern in includes:
            for path in root.glob(pattern):
                if path.is_file() and _matches(path, ["**/*"], excludes):
                    files.add(path.resolve())
    return sorted(files)


def generated_or_excluded(path: Path, config: TrymtexConfig) -> bool:
    return _excluded(path, config.exclude)


def _matches(path: Path, includes: list[str], excludes: list[str]) -> bool:
    return any(_match(path, pat) for pat in includes) and not _excluded(path, excludes)


def _excluded(path: Path, excludes: list[str]) -> bool:
    return any(_match(path, pat) for pat in excludes)


def _match(path: Path, pattern: str) -> bool:
    text = path.as_posix()
    name = path.name
    return fnmatch(text, pattern) or fnmatch(name, pattern)

