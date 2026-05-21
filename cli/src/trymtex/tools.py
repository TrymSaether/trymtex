from __future__ import annotations

import shutil
import subprocess

from .models import ToolResult


REQUIRED_TOOLS = ["chktex", "latexindent", "latexmk", "pdflatex", "tectonic"]


def missing_tools(names: list[str]) -> list[str]:
    return [name for name in names if shutil.which(name) is None]


def run_tool(command: list[str], timeout: int | None = None) -> ToolResult:
    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        shell=False,
    )
    return ToolResult(command=command, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)

