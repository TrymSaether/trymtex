from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .chktex import run_chktex
from .compiler import compile_check
from .config import TrymtexConfig, load_config
from .console import UI
from .fixers import apply_fixes
from .formatter import diff_for_change, format_files, write_formatted_change
from .models import EXIT_COMPILE, EXIT_RUNTIME, EXIT_SUCCESS, EXIT_WARNINGS, RunReport
from .report import print_diffs, print_fix_notes, print_header, print_summary, print_warnings
from .scanner import scan_files
from .tools import missing_tools


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    ui = UI(plain=args.plain or args.no_color, quiet=args.quiet, verbose=args.verbose)
    if not args.quiet:
        print_header(ui)
    try:
        config = load_config(Path(args.config) if args.config else None)
        _merge_cli_config(config, args)
    except Exception as exc:
        ui.print(f"[red]ERROR[/] {exc}")
        return EXIT_RUNTIME

    run_format = args.format or args.all
    run_lint = args.lint or args.fix or args.all or args.check
    run_fix = args.fix or args.all
    check_mode = args.check
    dry_run = args.dry_run or check_mode
    if not any([run_format, run_lint, run_fix, args.compile_check]):
        run_lint = True
        check_mode = True
        dry_run = True

    needed = _needed_tools(run_format, run_lint, run_fix, args.compile_check, config)
    missing = missing_tools(needed)
    if missing:
        ui.print(f"[red]ERROR[/] Missing required tool(s): {', '.join(missing)}")
        return EXIT_RUNTIME

    report = RunReport()
    paths = [Path(item) for item in args.paths]
    report.files_scanned = scan_files(paths, config, args.include, args.exclude)
    ui.verbose_print(f"Scanning {len(report.files_scanned)} file(s)")

    total_steps = sum(1 for enabled in (run_format, run_lint, run_fix, args.compile_check and not dry_run) if enabled)
    with ui.progress("Running trymtex", max(total_steps, 1)) as progress:
        if run_format:
            changes, errors = format_files(report.files_scanned, config, dry_run=dry_run, backup=args.backup)
            report.format_changes.extend(changes)
            report.tool_errors.extend(errors)
            report.files_formatted.update(change.path for change in changes)
            report.files_changed.update(change.path for change in changes)
            if args.diff:
                print_diffs(ui, report)
            if changes and not dry_run:
                report.files_changed.update(change.path for change in changes)
            elif changes and args.fix and not check_mode:
                for change in changes:
                    write_formatted_change(change, backup=args.backup)
            progress.advance()

        if run_lint:
            warnings, errors = run_chktex(report.files_scanned)
            report.warnings_before = warnings
            report.tool_errors.extend(errors)
            progress.advance()

        if run_fix and report.warnings_before:
            fixes, changed, fix_changes = apply_fixes(report.warnings_before, config, dry_run=dry_run, backup=args.backup)
            report.fixes.extend(fixes)
            report.files_changed.update(changed)
            report.format_changes.extend(fix_changes)
            if args.diff:
                for change in fix_changes:
                    ui.print(diff_for_change(change))
            warnings_after, errors = run_chktex(report.files_scanned)
            report.warnings_after = warnings_after
            report.tool_errors.extend(errors)
            progress.advance()
        elif run_lint:
            report.warnings_after = report.warnings_before
            if run_fix:
                progress.advance()

        if args.compile_check and not dry_run:
            try:
                compile_result = compile_check(config.compile, report.files_scanned)
            except Exception as exc:
                report.compile_error = str(exc)
            else:
                if compile_result.returncode != 0:
                    report.compile_error = compile_result.stderr.strip() or compile_result.stdout.strip() or "compile command failed"
            progress.advance()

    print_warnings(ui, report)
    print_fix_notes(ui, report)
    print_summary(ui, report)

    if report.compile_error:
        return EXIT_COMPILE
    if report.tool_errors:
        return EXIT_RUNTIME
    if check_mode and (report.format_changes or report.warnings_before or report.fixes_applied):
        return EXIT_WARNINGS
    if (args.fail_on_warnings or config.fail_on_warnings) and report.remaining_warnings:
        return EXIT_WARNINGS
    if report.remaining_warnings and run_lint and not run_fix:
        return EXIT_WARNINGS
    return EXIT_SUCCESS


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trymtex", description="Polished LaTeX formatting, linting, and autofixing.")
    parser.add_argument("paths", nargs="*", default=["."], help="Files or directories to scan.")
    parser.add_argument("--check", action="store_true", help="Report what would change; exit nonzero if changes or warnings exist.")
    parser.add_argument("--fix", action="store_true", help="Apply safe autofixes.")
    parser.add_argument("--format", action="store_true", help="Run latexindent.")
    parser.add_argument("--lint", action="store_true", help="Run chktex.")
    parser.add_argument("--all", action="store_true", help="Format, lint, autofix, then lint again.")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed changes without writing.")
    parser.add_argument("--diff", action="store_true", help="Print unified diffs.")
    parser.add_argument("--backup", action="store_true", help="Create .bak files before edits.")
    parser.add_argument("--config", help="Read project config from PATH.")
    parser.add_argument("--include", action="append", default=[], help="Include glob; may be repeated.")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude glob; may be repeated.")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Exit nonzero if warnings remain.")
    parser.add_argument("--compile-check", action="store_true", help="Compile after fixes.")
    parser.add_argument("--plain", action="store_true", help="Use plain output without Rich styling.")
    parser.add_argument("--no-color", action="store_true", help="Disable color.")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only print essential output.")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Print extra diagnostics.")
    return parser


def _merge_cli_config(config: TrymtexConfig, args: argparse.Namespace) -> None:
    config.backup = args.backup or config.backup
    config.fail_on_warnings = args.fail_on_warnings or config.fail_on_warnings


def _needed_tools(formatting: bool, linting: bool, fixing: bool, compile_enabled: bool, config: TrymtexConfig) -> list[str]:
    tools: list[str] = []
    if formatting:
        tools.append("latexindent")
    if linting or fixing:
        tools.append("chktex")
    if compile_enabled:
        tools.append(config.compile.engine)
    return sorted(set(tools))


if __name__ == "__main__":
    sys.exit(main())
