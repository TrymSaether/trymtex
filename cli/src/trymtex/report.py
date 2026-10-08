from __future__ import annotations

from collections import defaultdict

from .chktex import group_by_file
from .console import UI
from .formatter import diff_for_change
from .models import RunReport


def print_header(ui: UI) -> None:
    ui.panel("trymtex", "[bold]LaTeX format, lint, autofix[/]\n[cyan]Sharp output locally. Plain output in CI.[/]", "cyan")


def print_diffs(ui: UI, report: RunReport) -> None:
    for change in report.format_changes:
        ui.print(diff_for_change(change))


def print_warnings(ui: UI, report: RunReport) -> None:
    if not report.lint_ran:
        return
    warnings = report.remaining_warnings
    if not warnings:
        ui.print("[green]OK[/] No ChkTeX warnings remain.")
        return
    ui.print("[yellow]Warnings remaining[/]")
    for file, items in group_by_file(warnings).items():
        ui.print(f"[bold]{file}[/]")
        for warning in items:
            ui.print(f"  {warning.display()}")


def print_semantic_issues(ui: UI, report: RunReport) -> None:
    if not report.semantic_ran:
        return
    issues = report.remaining_semantic
    if not issues:
        ui.print("[green]OK[/] No semantic issues remain.")
        return
    ui.print("[yellow]Semantic issues remaining[/]")
    grouped = defaultdict(list)
    for issue in issues:
        grouped[issue.file].append(issue)
    for file, items in grouped.items():
        ui.print(f"[bold]{file}[/]")
        for issue in items:
            ui.print(f"  {issue.display()}")


def print_fix_notes(ui: UI, report: RunReport) -> None:
    skipped = [fix for fix in [*report.fixes, *report.semantic_fixes] if not fix.changed]
    if not skipped or ui.quiet:
        return
    reasons: dict[str, int] = defaultdict(int)
    for fix in skipped:
        reasons[fix.reason or "not fixed"] += 1
    ui.print("[yellow]Skipped autofixes[/]")
    for reason, count in sorted(reasons.items()):
        ui.print(f"  {count} {reason}")


def print_summary(ui: UI, report: RunReport) -> None:
    rows = [
        ("Files scanned", str(len(report.files_scanned))),
        ("Files formatted", str(len(report.files_formatted))),
        ("Warnings before", str(len(report.warnings_before))),
        ("Semantic issues before", str(len(report.semantic_before))),
        ("Autofixes applied", str(report.fixes_applied)),
        ("Warnings resolved", str(report.warnings_resolved)),
        ("Warnings remaining", str(len(report.remaining_warnings))),
        ("Semantic issues remaining", str(len(report.remaining_semantic))),
        ("Files changed", str(len(report.files_changed))),
        ("Cleanup files removed", str(len(report.cleanup_removed))),
    ]
    style = "green" if not report.remaining_warnings and not report.remaining_semantic and not report.tool_errors and not report.compile_error else "yellow"
    ui.table("Run report", rows, style=style)
    for error in report.tool_errors:
        ui.print(f"[red]ERROR[/] {error}")
    if report.compile_error:
        ui.print(f"[red]COMPILE FAILED[/] {report.compile_error}")
