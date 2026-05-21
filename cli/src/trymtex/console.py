from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from typing import Iterable


def rich_available() -> bool:
    try:
        import rich  # noqa: F401
    except Exception:
        return False
    return True


@dataclass
class UI:
    plain: bool = False
    quiet: bool = False
    verbose: int = 0

    def __post_init__(self) -> None:
        no_color = os.environ.get("NO_COLOR") is not None
        ci = os.environ.get("CI") is not None
        self.plain = self.plain or no_color or (ci and not sys.stdout.isatty()) or not rich_available()
        if not self.plain:
            from rich.console import Console

            self.console = Console(highlight=False)
        else:
            self.console = None

    def print(self, message: str = "") -> None:
        if not self.quiet:
            if self.console:
                self.console.print(message)
            else:
                print(_strip_markup(message))

    def verbose_print(self, message: str) -> None:
        if self.verbose:
            self.print(message)

    def status(self, message: str):
        if self.quiet or self.plain or not self.console:
            return _NullStatus()
        return self.console.status(message, spinner="dots")

    def progress(self, description: str, total: int):
        if self.quiet or self.plain or not self.console:
            return _NullProgress()
        from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

        return _RichProgress(Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn()), description, total)

    def panel(self, title: str, body: str, style: str = "cyan") -> None:
        if self.quiet:
            return
        if self.console:
            from rich.panel import Panel

            self.console.print(Panel.fit(body, title=title, border_style=style))
        else:
            print(f"{_strip_markup(title)}\n{_strip_markup(body)}")

    def table(self, title: str, rows: Iterable[tuple[str, str]], style: str = "cyan") -> None:
        if self.quiet:
            return
        if self.console:
            from rich.table import Table

            table = Table(title=title, border_style=style, show_header=False)
            table.add_column("Metric", style="bold")
            table.add_column("Value", justify="right")
            for key, value in rows:
                table.add_row(key, value)
            self.console.print(table)
        else:
            print(title)
            for key, value in rows:
                print(f"{key}: {value}")


class _NullStatus:
    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _NullProgress:
    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def advance(self) -> None:
        return None


class _RichProgress:
    def __init__(self, progress, description: str, total: int) -> None:
        self.progress = progress
        self.description = description
        self.total = total
        self.task_id = None

    def __enter__(self):
        self.progress.__enter__()
        self.task_id = self.progress.add_task(self.description, total=self.total)
        return self

    def __exit__(self, *args: object) -> None:
        self.progress.__exit__(*args)

    def advance(self) -> None:
        if self.task_id is not None:
            self.progress.advance(self.task_id)


def _strip_markup(value: str) -> str:
    return re.sub(r"\[/?[^\]]*\]", "", value)
