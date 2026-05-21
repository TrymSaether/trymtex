from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .models import ChktexWarning
from .tools import run_tool


FIELD_SEP = "\x1f"
FORMAT = f"%f{FIELD_SEP}%l{FIELD_SEP}%c{FIELD_SEP}%n{FIELD_SEP}%m{FIELD_SEP}%r\\n"


def run_chktex(files: list[Path]) -> tuple[list[ChktexWarning], list[str]]:
    warnings: list[ChktexWarning] = []
    errors: list[str] = []
    for path in files:
        result = run_tool(["chktex", "-q", "-v0", "-f", FORMAT, str(path)])
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        warnings.extend(parse_chktex_output(output, default_file=path))
        if result.returncode not in (0, 1, 2):
            errors.append(f"chktex failed for {path}: {result.stderr.strip() or result.stdout.strip()}")
    return warnings, errors


def parse_chktex_output(output: str, default_file: Path | None = None) -> list[ChktexWarning]:
    parsed: list[ChktexWarning] = []
    for raw_line in output.splitlines():
        line = raw_line.strip("\n")
        if not line:
            continue
        structured = _parse_structured(line)
        if structured:
            parsed.append(structured)
            continue
        fallback = _parse_fallback(line, default_file)
        if fallback:
            parsed.append(fallback)
    return parsed


def group_by_file(warnings: list[ChktexWarning]) -> dict[Path, list[ChktexWarning]]:
    grouped: dict[Path, list[ChktexWarning]] = defaultdict(list)
    for warning in warnings:
        grouped[warning.file].append(warning)
    return dict(grouped)


def _parse_structured(line: str) -> ChktexWarning | None:
    parts = line.split(FIELD_SEP)
    if len(parts) < 6:
        return None
    file_name, line_s, col_s, number_s, message, context = parts[:6]
    try:
        return ChktexWarning(
            file=Path(file_name),
            line=int(line_s),
            column=int(col_s),
            number=int(number_s),
            message=message.strip(),
            context=context.strip(),
        )
    except ValueError:
        return None


_FALLBACK_RE = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+):(?P<col>\d+):\s*(?:Warning\s*)?(?P<num>\d+)?[:\s-]*(?P<msg>.*)$"
)
_WARNING_IN_RE = re.compile(
    r"^Warning\s+(?P<num>\d+)\s+in\s+(?P<file>.*?)\s+line\s+(?P<line>\d+)(?:,\s*column\s*(?P<col>\d+))?:\s*(?P<msg>.*)$",
    re.IGNORECASE,
)


def _parse_fallback(line: str, default_file: Path | None) -> ChktexWarning | None:
    match = _WARNING_IN_RE.match(line)
    if match:
        return ChktexWarning(
            file=Path(match.group("file")),
            line=int(match.group("line")),
            column=int(match.group("col") or 1),
            number=int(match.group("num")),
            message=match.group("msg").strip(),
        )
    match = _FALLBACK_RE.match(line)
    if not match:
        return None
    number = match.group("num")
    return ChktexWarning(
        file=Path(match.group("file")) if match.group("file") else default_file or Path("<unknown>"),
        line=int(match.group("line")),
        column=int(match.group("col")),
        number=int(number) if number else 0,
        message=match.group("msg").strip(),
    )
