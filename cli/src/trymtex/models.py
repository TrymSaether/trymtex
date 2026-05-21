from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


EXIT_SUCCESS = 0
EXIT_WARNINGS = 1
EXIT_RUNTIME = 2
EXIT_COMPILE = 3


@dataclass(frozen=True)
class ChktexWarning:
    file: Path
    line: int
    column: int
    number: int
    message: str
    context: str = ""

    def display(self) -> str:
        return f"{self.file}:{self.line}:{self.column} ChkTeX {self.number} {self.message}"


@dataclass(frozen=True)
class ToolResult:
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass
class FixResult:
    warning: ChktexWarning
    fixer: str
    changed: bool
    reason: str = ""


@dataclass
class FileChange:
    path: Path
    before: str
    after: str
    source: str

    @property
    def changed(self) -> bool:
        return self.before != self.after


@dataclass
class RunReport:
    files_scanned: list[Path] = field(default_factory=list)
    files_formatted: set[Path] = field(default_factory=set)
    files_changed: set[Path] = field(default_factory=set)
    warnings_before: list[ChktexWarning] = field(default_factory=list)
    warnings_after: list[ChktexWarning] = field(default_factory=list)
    fixes: list[FixResult] = field(default_factory=list)
    format_changes: list[FileChange] = field(default_factory=list)
    tool_errors: list[str] = field(default_factory=list)
    compile_error: str | None = None

    @property
    def fixes_applied(self) -> int:
        return sum(1 for fix in self.fixes if fix.changed)

    @property
    def warnings_resolved(self) -> int:
        before = {(w.file, w.line, w.column, w.number, w.message) for w in self.warnings_before}
        after = {(w.file, w.line, w.column, w.number, w.message) for w in self.warnings_after}
        return len(before - after)

    @property
    def remaining_warnings(self) -> list[ChktexWarning]:
        if self.fixes or self.warnings_after:
            return self.warnings_after
        return self.warnings_before
