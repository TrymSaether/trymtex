from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextFile:
    path: Path
    text: str
    encoding: str
    newline: str


def read_text_file(path: Path) -> TextFile:
    data = path.read_bytes()
    encoding = "utf-8-sig" if data.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        text = data.decode(encoding)
    except UnicodeDecodeError:
        encoding = "latin-1"
        text = data.decode(encoding)
    newline = "\r\n" if "\r\n" in text else "\n"
    return TextFile(path=path, text=text, encoding=encoding, newline=newline)


def write_text_file(original: TextFile, text: str, backup: bool = False) -> None:
    if backup:
        original.path.with_suffix(original.path.suffix + ".bak").write_bytes(original.path.read_bytes())
    original.path.write_bytes(text.encode(original.encoding))

