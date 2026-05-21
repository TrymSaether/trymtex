from __future__ import annotations

from pathlib import Path

from .config import CompileConfig
from .models import ToolResult
from .tools import run_tool


def compile_check(config: CompileConfig, files: list[Path]) -> ToolResult:
    target = Path(config.main) if config.main else _guess_main(files)
    engine = config.engine
    if engine == "latexmk":
        command = ["latexmk", "-interaction=nonstopmode", "-halt-on-error", *config.args, str(target)]
    elif engine in {"pdflatex", "lualatex"}:
        command = [engine, "-interaction=nonstopmode", "-halt-on-error", *config.args, str(target)]
    elif engine == "tectonic":
        command = ["tectonic", *config.args, str(target)]
    else:
        raise ValueError(f"Unsupported compile engine: {engine}")
    return run_tool(command)


def _guess_main(files: list[Path]) -> Path:
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "\\documentclass" in text:
            return path
    if not files:
        raise ValueError("No files available for compile check and no compile.main configured")
    return files[0]

