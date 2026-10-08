from __future__ import annotations

import difflib
from pathlib import Path

from .config import TrymtexConfig
from .io import read_text_file, write_text_file
from .models import FileChange
from .scanner import generated_or_excluded
from .tools import run_tool


def format_files(files: list[Path], config: TrymtexConfig, dry_run: bool, backup: bool) -> tuple[list[FileChange], list[str]]:
    changes: list[FileChange] = []
    errors: list[str] = []
    for path in files:
        if path.suffix == ".bib" and not config.formatter.format_bib:
            continue
        if generated_or_excluded(path, config):
            continue
        original = read_text_file(path)
        command = ["latexindent", "-m"]
        local_config = _latexindent_config(path, config)
        if local_config:
            command.extend(["-l", str(local_config)])
        command.append(str(path))
        if dry_run:
            result = run_tool(command)
            formatted = result.stdout
        else:
            result = run_tool([*command[:-1], "-w", command[-1]])
            formatted = read_text_file(path).text if result.returncode == 0 else original.text
        if result.returncode != 0:
            errors.append(f"latexindent failed for {path}: {result.stderr.strip() or result.stdout.strip()}")
            continue
        if dry_run and formatted and formatted != original.text:
            changes.append(FileChange(path=path, before=original.text, after=formatted, source="latexindent"))
        elif not dry_run:
            current = read_text_file(path)
            if current.text != original.text:
                changes.append(FileChange(path=path, before=original.text, after=current.text, source="latexindent"))
                if backup:
                    original.path.with_suffix(original.path.suffix + ".bak").write_bytes(original.text.encode(original.encoding))
    if dry_run:
        return changes, errors
    return changes, errors


def diff_for_change(change: FileChange) -> str:
    return "".join(
        difflib.unified_diff(
            change.before.splitlines(keepends=True),
            change.after.splitlines(keepends=True),
            fromfile=f"{change.path} (before)",
            tofile=f"{change.path} (after)",
        )
    )


def write_formatted_change(change: FileChange, backup: bool = False) -> None:
    source = read_text_file(change.path)
    write_text_file(source, change.after, backup=backup)


def _latexindent_config(path: Path, config: TrymtexConfig) -> Path | None:
    if config.formatter.latexindent_config:
        return Path(config.formatter.latexindent_config)
    for root in [path.parent, *path.parents]:
        for name in (".latexindent.yaml", "latexindent.yaml"):
            candidate = root / name
            if candidate.exists():
                return candidate
    return None
