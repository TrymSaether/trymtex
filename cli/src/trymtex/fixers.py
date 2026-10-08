from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .chktex import group_by_file
from .config import TrymtexConfig
from .io import read_text_file, write_text_file
from .models import ChktexWarning, FileChange, FixResult


VERBATIM_ENVIRONMENTS = {
    "verbatim",
    "Verbatim",
    "lstlisting",
    "minted",
    "alltt",
    "comment",
}
REF_COMMANDS = (
    "ref",
    "eqref",
    "pageref",
    "autoref",
    "cref",
    "Cref",
    "cite",
    "citet",
    "citep",
    "parencite",
    "textcite",
)


class Fixer(Protocol):
    name: str

    def supports(self, warning: ChktexWarning) -> bool: ...

    def apply(self, lines: list[str], warning: ChktexWarning) -> FixResult: ...


@dataclass
class NbspBeforeRefFixer:
    name: str = "nbsp-before-ref"

    def supports(self, warning: ChktexWarning) -> bool:
        msg = warning.message.lower()
        return (
            "non-breaking space" in msg
            or "should have been used" in msg
            or any(f"\\{cmd}" in warning.context for cmd in REF_COMMANDS)
        )

    def apply(self, lines: list[str], warning: ChktexWarning) -> FixResult:
        if not _line_available(lines, warning):
            return FixResult(warning, self.name, False, "line not available")
        line = lines[warning.line - 1]
        if _unsafe_context(lines, warning.line, line):
            return FixResult(warning, self.name, False, "inside verbatim-like or macro-definition context")
        pattern = re.compile(r"(?<!\\)([ \t]+)(\\(?:" + "|".join(map(re.escape, REF_COMMANDS)) + r")\s*\{)")
        search_start = max(0, warning.column - 20)
        search_end = min(len(line), warning.column + 80)
        window = line[search_start:search_end]
        match = pattern.search(window)
        if not match:
            return FixResult(warning, self.name, False, "no safe reference/citation spacing pattern found")
        absolute_start = search_start + match.start(1)
        absolute_end = search_start + match.end(1)
        lines[warning.line - 1] = line[:absolute_start] + "~" + line[absolute_end:]
        return FixResult(warning, self.name, True)


@dataclass
class SpaceBeforePunctuationFixer:
    name: str = "space-before-punctuation"

    def supports(self, warning: ChktexWarning) -> bool:
        msg = warning.message.lower()
        return "delete this space" in msg or "space before punctuation" in msg

    def apply(self, lines: list[str], warning: ChktexWarning) -> FixResult:
        if not _line_available(lines, warning):
            return FixResult(warning, self.name, False, "line not available")
        line = lines[warning.line - 1]
        if _unsafe_context(lines, warning.line, line):
            return FixResult(warning, self.name, False, "inside verbatim-like or macro-definition context")
        idx = max(0, warning.column - 1)
        search_start = max(0, idx - 5)
        search_end = min(len(line), idx + 8)
        window = line[search_start:search_end]
        match = re.search(r"(?<!\\)[ \t]+([,.;:!?])", window)
        if not match:
            return FixResult(warning, self.name, False, "no safe punctuation spacing pattern found")
        absolute_start = search_start + match.start()
        absolute_end = search_start + match.end() - 1
        lines[warning.line - 1] = line[:absolute_start] + line[absolute_end:]
        return FixResult(warning, self.name, True)


def available_fixers() -> dict[str, Fixer]:
    fixers: list[Fixer] = [NbspBeforeRefFixer(), SpaceBeforePunctuationFixer()]
    return {fixer.name: fixer for fixer in fixers}


def apply_fixes(
    warnings: list[ChktexWarning],
    config: TrymtexConfig,
    dry_run: bool,
    backup: bool,
) -> tuple[list[FixResult], set[Path], list[FileChange]]:
    registry = available_fixers()
    active = [registry[name] for name in config.fixers.enabled if name in registry]
    results: list[FixResult] = []
    changed_files: set[Path] = set()
    changes: list[FileChange] = []
    for path, file_warnings in group_by_file(warnings).items():
        source = read_text_file(path)
        lines = source.text.splitlines(keepends=True)
        changed = False
        for warning in sorted(file_warnings, key=lambda item: (item.line, item.column), reverse=True):
            fixer = next((item for item in active if item.supports(warning)), None)
            if fixer is None:
                results.append(FixResult(warning, "none", False, "no safe fixer registered"))
                continue
            result = fixer.apply(lines, warning)
            results.append(result)
            changed = changed or result.changed
        if changed:
            after = "".join(lines)
            changed_files.add(path)
            changes.append(FileChange(path=path, before=source.text, after=after, source="autofix"))
            if not dry_run:
                write_text_file(source, after, backup=backup)
    return results, changed_files, changes


def _line_available(lines: list[str], warning: ChktexWarning) -> bool:
    return 1 <= warning.line <= len(lines)


def _unsafe_context(lines: list[str], line_number: int, line: str) -> bool:
    stripped = line.lstrip()
    if stripped.startswith(("\\newcommand", "\\renewcommand", "\\providecommand", "\\def", "\\Declare")):
        return True
    env_stack: list[str] = []
    begin = re.compile(r"\\begin\{([^}]+)\}")
    end = re.compile(r"\\end\{([^}]+)\}")
    for prior in lines[:line_number]:
        for match in begin.finditer(prior):
            env_stack.append(match.group(1))
        for match in end.finditer(prior):
            env = match.group(1)
            if env in env_stack[::-1]:
                env_stack.remove(env)
    return any(env in VERBATIM_ENVIRONMENTS for env in env_stack)
