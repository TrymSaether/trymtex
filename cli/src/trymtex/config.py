from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_EXCLUDES = [
    ".git/**",
    ".hg/**",
    ".svn/**",
    ".venv/**",
    "venv/**",
    "build/**",
    "dist/**",
    "_build/**",
    "out/**",
    "target/**",
    "**/*.aux",
    "**/*.bbl",
    "**/*.blg",
    "**/*.fdb_latexmk",
    "**/*.fls",
    "**/*.log",
    "**/*.synctex.gz",
    "**/*.generated.tex",
    "**/generated/**",
]


@dataclass
class CompileConfig:
    engine: str = "latexmk"
    main: str | None = None
    args: list[str] = field(default_factory=list)


@dataclass
class FormatterConfig:
    format_bib: bool = False
    latexindent_config: str | None = None


@dataclass
class FixerConfig:
    enabled: list[str] = field(default_factory=lambda: ["nbsp-before-ref", "space-before-punctuation"])


@dataclass
class TrymtexConfig:
    include: list[str] = field(default_factory=lambda: ["**/*.tex"])
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    backup: bool = False
    fail_on_warnings: bool = False
    formatter: FormatterConfig = field(default_factory=FormatterConfig)
    fixers: FixerConfig = field(default_factory=FixerConfig)
    compile: CompileConfig = field(default_factory=CompileConfig)


def find_config(start: Path) -> Path | None:
    for candidate in (
        start / "trymtex.toml",
        start / ".trymtex.toml",
        start / "pyproject.toml",
    ):
        if candidate.exists():
            return candidate
    return None


def load_config(path: Path | None) -> TrymtexConfig:
    if path is None:
        found = find_config(Path.cwd())
        if found is None:
            return TrymtexConfig()
        path = found
    if not path.exists():
        raise FileNotFoundError(f"Config file does not exist: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if path.name == "pyproject.toml":
        data = data.get("tool", {}).get("trymtex", {})
    return _from_mapping(data)


def _list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ValueError(f"Expected string or list of strings, got {value!r}")


def _from_mapping(data: dict[str, Any]) -> TrymtexConfig:
    config = TrymtexConfig()
    config.include = _list(data.get("include"), config.include)
    config.exclude = _list(data.get("exclude"), config.exclude)
    config.backup = bool(data.get("backup", config.backup))
    config.fail_on_warnings = bool(data.get("fail_on_warnings", config.fail_on_warnings))

    fmt = data.get("formatter", {})
    if not isinstance(fmt, dict):
        raise ValueError("[formatter] must be a table")
    config.formatter = FormatterConfig(
        format_bib=bool(fmt.get("format_bib", config.formatter.format_bib)),
        latexindent_config=fmt.get("latexindent_config", config.formatter.latexindent_config),
    )

    fixers = data.get("fixers", {})
    if not isinstance(fixers, dict):
        raise ValueError("[fixers] must be a table")
    config.fixers = FixerConfig(enabled=_list(fixers.get("enabled"), config.fixers.enabled))

    compile_data = data.get("compile", {})
    if not isinstance(compile_data, dict):
        raise ValueError("[compile] must be a table")
    config.compile = CompileConfig(
        engine=str(compile_data.get("engine", config.compile.engine)),
        main=compile_data.get("main", config.compile.main),
        args=_list(compile_data.get("args"), config.compile.args),
    )
    return config

