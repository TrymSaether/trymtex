from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .config import TrymtexConfig
from .io import read_text_file, write_text_file
from .models import FileChange, FixResult, SemanticIssue


VERBATIM_ENVIRONMENTS = {"verbatim", "Verbatim", "lstlisting", "minted", "alltt", "comment"}
REF_COMMANDS = {"ref", "eqref", "pageref", "autoref", "cref", "Cref", "vref", "nameref"}
CITE_COMMANDS = {"cite", "citet", "citep", "parencite", "textcite", "autocite"}

LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
REF_RE = re.compile(r"\\(" + "|".join(sorted(REF_COMMANDS)) + r")\*?\{([^}]+)\}")
CITE_RE = re.compile(r"\\(" + "|".join(sorted(CITE_COMMANDS)) + r")\*?\{([^}]+)\}")
BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]+\])?\{([^}]+)\}")
USEPACKAGE_RE = re.compile(r"^\\usepackage(?:\[[^\]]*\])?\{(?P<packages>[^}]+)\}\s*$")
URL_RE = re.compile(r"(?<![\\{])\bhttps?://[^\s{}<>]+")
WORD_RE = re.compile(r"\b([A-Za-z][A-Za-z'-]*)\s+\1\b", re.IGNORECASE)
MATH_OPERATOR_RE = re.compile(r"(?<![\\{])\b(sin|cos|tan|cot|sec|csc|log|ln|exp|min|max|lim|sup|inf|arg|det|dim|ker|hom|Pr)\b")
MATH_SPACING_PUNCT_RE = re.compile(r"[ \t]+([,.;:])")
INLINE_MATH_DOLLAR_RE = re.compile(r"(?<![\\$])\$(?!\$)([^$\n]+?)(?<![\\$])\$(?!\$)")
DISPLAY_MATH_DOLLAR_RE = re.compile(r"(?<!\\)\$\$([^$\n]+?)(?<!\\)\$\$")
STANDALONE_DISPLAY_DOLLAR_RE = re.compile(r"^(?P<indent>\s*)\$\$(?P<trailing>\s*)$")
EQNARRAY_ENV_RE = re.compile(r"\\(begin|end)\{eqnarray(\*)?\}")
DEPRECATED_FONT_RE = re.compile(r"\{\\(bf|it|em|tt|sc|rm|sf)\s+([^{}\n]+)\}")
CENTERLINE_RE = re.compile(r"\\centerline\{([^{}\n]+)\}")
DASH_RANGE_RE = re.compile(r"\b([A-Za-z]|\d{1,4})-([A-Za-z]|\d{1,4})\b")
SPACED_EM_DASH_RE = re.compile(r"\b([A-Za-z][A-Za-z']*)\s+-\s+([A-Za-z][A-Za-z']*)\b")
TEX_QUOTES_RE = re.compile(r'"([^"\n{}\\]+)"')
ELLIPSIS_RE = re.compile(r"(?<!\\)\.\.\.")
PROSE_SPACING_RE = re.compile(r"[ \t]+([,.;:!?])")
MACRO_DEF_RE = re.compile(r"^\\(?:re)?newcommand\*?\{?(\\[A-Za-z@]+)\}?")


@dataclass(frozen=True)
class ParsedLine:
    path: Path
    number: int
    text: str
    code: str
    in_verbatim: bool
    in_math: bool
    math_spans: list[tuple[int, int]]
    generated: bool


def run_semantic(files: list[Path], config: TrymtexConfig) -> list[SemanticIssue]:
    lines = _read_lines(files)
    enabled = set(config.semantic.enabled)
    issues: list[SemanticIssue] = []
    if enabled & {"duplicate-label", "undefined-reference", "unused-label"}:
        issues.extend(_label_reference_issues(lines, enabled))
    if "duplicate-usepackage" in enabled:
        issues.extend(_duplicate_usepackage_issues(lines))
    if "duplicate-macro-definition" in enabled:
        issues.extend(_duplicate_macro_definition_issues(lines))
    if "repeated-word" in enabled:
        issues.extend(_repeated_word_issues(lines))
    if "bare-url" in enabled:
        issues.extend(_bare_url_issues(lines))
    if "math-operator" in enabled:
        issues.extend(_math_operator_issues(lines))
    if "math-spacing-punctuation" in enabled:
        issues.extend(_math_spacing_punctuation_issues(lines))
    if "inline-math-delimiter" in enabled:
        issues.extend(_inline_math_delimiter_issues(lines))
    if "display-math-delimiter" in enabled:
        issues.extend(_display_math_delimiter_issues(lines))
    if "eqnarray-environment" in enabled:
        issues.extend(_eqnarray_environment_issues(lines))
    if "deprecated-font-command" in enabled:
        issues.extend(_deprecated_font_command_issues(lines))
    if "centerline-command" in enabled:
        issues.extend(_centerline_command_issues(lines))
    if "dash-range" in enabled:
        issues.extend(_dash_range_issues(lines))
    if "spaced-em-dash" in enabled:
        issues.extend(_spaced_em_dash_issues(lines))
    if "tex-quotes" in enabled:
        issues.extend(_tex_quotes_issues(lines))
    if "ellipsis" in enabled:
        issues.extend(_ellipsis_issues(lines))
    if "prose-spacing" in enabled:
        issues.extend(_prose_spacing_issues(lines))
    return sorted(issues, key=lambda issue: (str(issue.file), issue.line, issue.column, issue.rule))


def apply_semantic_fixes(
    issues: list[SemanticIssue],
    config: TrymtexConfig,
    dry_run: bool,
    backup: bool,
) -> tuple[list[FixResult], set[Path], list[FileChange]]:
    active = set(config.semantic.autofix)
    grouped: dict[Path, list[SemanticIssue]] = defaultdict(list)
    for issue in issues:
        grouped[issue.file].append(issue)

    results: list[FixResult] = []
    changed_files: set[Path] = set()
    changes: list[FileChange] = []
    for path, file_issues in grouped.items():
        source = read_text_file(path)
        lines = source.text.splitlines(keepends=True)
        changed = False
        for issue in sorted(file_issues, key=lambda item: (item.line, item.column), reverse=True):
            if issue.rule not in active:
                results.append(FixResult(issue, "semantic", False, "semantic rule has no enabled autofix"))
                continue
            result = _apply_one(lines, issue)
            results.append(result)
            changed = changed or result.changed
        if changed:
            after = "".join(lines)
            changed_files.add(path)
            changes.append(FileChange(path=path, before=source.text, after=after, source="semantic"))
            if not dry_run:
                write_text_file(source, after, backup=backup)
    return results, changed_files, changes


def _read_lines(files: list[Path]) -> list[ParsedLine]:
    parsed: list[ParsedLine] = []
    for path in files:
        text = read_text_file(path).text
        generated = _generated_file(text)
        if generated:
            continue
        stack: list[str] = []
        math_stack: list[str] = []
        for number, raw in enumerate(text.splitlines(keepends=True), start=1):
            code = _strip_comment(raw)
            in_verbatim = bool(stack)
            math_spans = _math_spans(code, bool(math_stack))
            if re.search(r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}", code):
                math_spans.append((0, len(code)))
            parsed.append(
                ParsedLine(
                    path=path,
                    number=number,
                    text=raw,
                    code=code,
                    in_verbatim=in_verbatim,
                    in_math=bool(math_spans),
                    math_spans=math_spans,
                    generated=generated,
                )
            )
            for match in re.finditer(r"\\begin\{([^}]+)\}|\\end\{([^}]+)\}", code):
                begin, end = match.group(1), match.group(2)
                if begin in VERBATIM_ENVIRONMENTS:
                    stack.append(begin)
                elif end in VERBATIM_ENVIRONMENTS and end in stack:
                    stack.remove(end)
                elif begin in {"equation", "equation*", "align", "align*", "gather", "gather*", "multline", "multline*"}:
                    math_stack.append(begin)
                elif end in math_stack:
                    math_stack.remove(end)
            if "\\[" in code:
                math_stack.append("\\[")
            if "\\]" in code and "\\[" in math_stack:
                math_stack.remove("\\[")
    return parsed


def _label_reference_issues(lines: list[ParsedLine], enabled: set[str]) -> list[SemanticIssue]:
    labels: dict[str, list[ParsedLine]] = defaultdict(list)
    refs: list[tuple[str, ParsedLine, int]] = []
    cites: list[tuple[str, ParsedLine, int]] = []
    bibitems: set[str] = set()
    for line in lines:
        if line.in_verbatim or line.generated or _macro_definition(line.code):
            continue
        for match in LABEL_RE.finditer(line.code):
            labels[match.group(1)].append(line)
        for match in REF_RE.finditer(line.code):
            refs.append((match.group(2), line, match.start(2) + 1))
        for match in CITE_RE.finditer(line.code):
            for key in match.group(2).split(","):
                cites.append((key.strip(), line, match.start(2) + 1))
        for match in BIBITEM_RE.finditer(line.code):
            bibitems.add(match.group(1))

    issues: list[SemanticIssue] = []
    if "duplicate-label" in enabled:
        for label, occurrences in labels.items():
            for line in occurrences[1:]:
                issues.append(SemanticIssue(line.path, line.number, _column(line.code, label), "duplicate-label", f"Duplicate label `{label}`.", line.code.strip()))
    if "undefined-reference" in enabled:
        for label, line, column in refs:
            if label not in labels:
                issues.append(SemanticIssue(line.path, line.number, column, "undefined-reference", f"Reference `{label}` has no matching \\label.", line.code.strip()))
        for key, line, column in cites:
            if bibitems and key and key not in bibitems:
                issues.append(SemanticIssue(line.path, line.number, column, "undefined-reference", f"Citation `{key}` has no matching \\bibitem in scanned files.", line.code.strip()))
    if "unused-label" in enabled:
        used = {label for label, _, _ in refs}
        for label, occurrences in labels.items():
            if label not in used:
                line = occurrences[0]
                issues.append(SemanticIssue(line.path, line.number, _column(line.code, label), "unused-label", f"Label `{label}` is not referenced in scanned files.", line.code.strip()))
    return issues


def _duplicate_usepackage_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    seen_by_file: dict[Path, set[str]] = defaultdict(set)
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated:
            continue
        normalized = _normalized_package_line(line.code)
        if not normalized:
            continue
        seen = seen_by_file[line.path]
        if normalized in seen:
            issues.append(SemanticIssue(line.path, line.number, 1, "duplicate-usepackage", "Duplicate exact \\usepackage line can be removed.", line.code.strip()))
        seen.add(normalized)
    return issues


def _duplicate_macro_definition_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    seen: dict[Path, dict[str, str]] = defaultdict(dict)
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated:
            continue
        stripped = line.code.strip()
        match = MACRO_DEF_RE.match(stripped)
        if not match:
            continue
        name = match.group(1)
        previous = seen[line.path].get(name)
        if previous == stripped:
            issues.append(SemanticIssue(line.path, line.number, 1, "duplicate-macro-definition", f"Duplicate exact macro definition for `{name}` can be removed.", stripped))
        elif previous is not None:
            issues.append(SemanticIssue(line.path, line.number, 1, "duplicate-macro-definition", f"Conflicting macro definition for `{name}`.", stripped))
        else:
            seen[line.path][name] = stripped
    return issues


def _repeated_word_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in WORD_RE.finditer(line.code):
            if "\\" in line.code[max(0, match.start() - 2) : match.end()]:
                continue
            issues.append(SemanticIssue(line.path, line.number, match.start(1) + 1, "repeated-word", f"Repeated word `{match.group(1)}`.", line.code.strip()))
    return issues


def _bare_url_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or "\\url{" in line.code or "\\href{" in line.code:
            continue
        for match in URL_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "bare-url", "Bare URL should be wrapped in \\url{...}.", line.code.strip()))
    return issues


def _math_operator_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or not line.in_math:
            continue
        for start, end in line.math_spans:
            for match in MATH_OPERATOR_RE.finditer(line.code, start, end):
                issues.append(SemanticIssue(line.path, line.number, match.start(1) + 1, "math-operator", f"Use TeX math operator `\\{match.group(1)}`.", line.code.strip()))
    return issues


def _math_spacing_punctuation_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or not line.in_math:
            continue
        for start, end in line.math_spans:
            for match in MATH_SPACING_PUNCT_RE.finditer(line.code, start, end):
                issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "math-spacing-punctuation", "Remove extra math-mode space before punctuation.", line.code.strip()))
    return issues


def _inline_math_delimiter_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or _macro_definition(line.code):
            continue
        for match in INLINE_MATH_DOLLAR_RE.finditer(line.code):
            body = match.group(1).strip()
            if _looks_like_currency_or_empty_math(body):
                continue
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "inline-math-delimiter", "Use \\(...\\) instead of inline $...$ delimiters.", line.code.strip()))
    return issues


def _display_math_delimiter_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    open_by_file: dict[Path, bool] = defaultdict(bool)
    for line in lines:
        if line.in_verbatim or line.generated or _macro_definition(line.code):
            continue
        standalone = STANDALONE_DISPLAY_DOLLAR_RE.match(line.code)
        if standalone:
            state = "close" if open_by_file[line.path] else "open"
            open_by_file[line.path] = not open_by_file[line.path]
            issues.append(SemanticIssue(line.path, line.number, len(standalone.group("indent")) + 1, "display-math-delimiter", f"Use {'\\]' if state == 'close' else '\\['} instead of standalone $$.", state))
            continue
        for match in DISPLAY_MATH_DOLLAR_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "display-math-delimiter", "Use \\[...\\] instead of display $$...$$ delimiters.", line.code.strip()))
    return issues


def _eqnarray_environment_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated:
            continue
        for match in EQNARRAY_ENV_RE.finditer(line.code):
            replacement = "align" + (match.group(2) or "")
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "eqnarray-environment", f"Use `{replacement}` instead of deprecated `eqnarray`.", line.code.strip()))
    return issues


def _deprecated_font_command_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in DEPRECATED_FONT_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "deprecated-font-command", f"Use modern text command instead of `\\{match.group(1)}`.", line.code.strip()))
    return issues


def _centerline_command_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in CENTERLINE_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "centerline-command", "Use a center environment instead of plain TeX \\centerline.", line.code.strip()))
    return issues


def _dash_range_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in DASH_RANGE_RE.finditer(line.code):
            if line.code[max(0, match.start() - 1) : match.end() + 1].count("-") > 1:
                continue
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "dash-range", "Use LaTeX en dash `--` for ranges.", line.code.strip()))
    return issues


def _spaced_em_dash_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in SPACED_EM_DASH_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "spaced-em-dash", "Use LaTeX em dash `---` instead of spaced hyphen.", line.code.strip()))
    return issues


def _tex_quotes_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in TEX_QUOTES_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "tex-quotes", "Use TeX opening and closing quotes.", line.code.strip()))
    return issues


def _ellipsis_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in ELLIPSIS_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "ellipsis", "Use `\\ldots{}` for prose ellipsis.", line.code.strip()))
    return issues


def _prose_spacing_issues(lines: list[ParsedLine]) -> list[SemanticIssue]:
    issues: list[SemanticIssue] = []
    for line in lines:
        if line.in_verbatim or line.generated or line.in_math or _macro_definition(line.code):
            continue
        for match in PROSE_SPACING_RE.finditer(line.code):
            issues.append(SemanticIssue(line.path, line.number, match.start() + 1, "prose-spacing", "Remove space before punctuation.", line.code.strip()))
    return issues


def _apply_one(lines: list[str], issue: SemanticIssue) -> FixResult:
    if not 1 <= issue.line <= len(lines):
        return FixResult(issue, "semantic", False, "line not available")
    line = lines[issue.line - 1]
    if issue.rule == "duplicate-usepackage":
        if _normalized_package_line(_strip_comment(line)):
            lines[issue.line - 1] = ""
            return FixResult(issue, "semantic:duplicate-usepackage", True)
        return FixResult(issue, "semantic:duplicate-usepackage", False, "line no longer matches exact duplicate package import")
    if issue.rule == "duplicate-macro-definition":
        if issue.message.startswith("Duplicate exact macro definition") and MACRO_DEF_RE.match(_strip_comment(line).strip()):
            lines[issue.line - 1] = ""
            return FixResult(issue, "semantic:duplicate-macro-definition", True)
        return FixResult(issue, "semantic:duplicate-macro-definition", False, "macro definition is conflicting or no longer exact duplicate")
    if issue.rule == "repeated-word":
        fixed, count = WORD_RE.subn(r"\1", line, count=1)
        if count:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:repeated-word", True)
        return FixResult(issue, "semantic:repeated-word", False, "repeated word no longer found")
    if issue.rule == "bare-url":
        fixed, count = URL_RE.subn(_wrap_url, line, count=1)
        if count:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:bare-url", True)
        return FixResult(issue, "semantic:bare-url", False, "bare URL no longer found")
    if issue.rule == "math-operator":
        fixed = _replace_first_at_or_after(MATH_OPERATOR_RE, line, issue.column, lambda m: "\\" + m.group(1))
        if fixed != line:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:math-operator", True)
        return FixResult(issue, "semantic:math-operator", False, "math operator no longer found")
    if issue.rule == "math-spacing-punctuation":
        fixed = _replace_first_at_or_after(MATH_SPACING_PUNCT_RE, line, issue.column, lambda m: m.group(1))
        if fixed != line:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:math-spacing-punctuation", True)
        return FixResult(issue, "semantic:math-spacing-punctuation", False, "math punctuation spacing no longer found")
    if issue.rule == "inline-math-delimiter":
        fixed = _replace_first_at_or_after(INLINE_MATH_DOLLAR_RE, line, issue.column, lambda m: r"\(" + m.group(1) + r"\)")
        if fixed != line:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:inline-math-delimiter", True)
        return FixResult(issue, "semantic:inline-math-delimiter", False, "inline dollar math no longer found")
    if issue.rule == "display-math-delimiter":
        fixed = _fix_display_math_delimiter(line, issue)
        if fixed != line:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:display-math-delimiter", True)
        return FixResult(issue, "semantic:display-math-delimiter", False, "display dollar math no longer found")
    if issue.rule == "eqnarray-environment":
        fixed = _replace_first_at_or_after(EQNARRAY_ENV_RE, line, issue.column, lambda m: "\\" + m.group(1) + "{align" + (m.group(2) or "") + "}")
        if fixed != line:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:eqnarray-environment", True)
        return FixResult(issue, "semantic:eqnarray-environment", False, "eqnarray environment no longer found")
    if issue.rule == "deprecated-font-command":
        fixed = _replace_first_at_or_after(DEPRECATED_FONT_RE, line, issue.column, _modern_font_command)
        if fixed != line:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:deprecated-font-command", True)
        return FixResult(issue, "semantic:deprecated-font-command", False, "deprecated font command no longer found")
    if issue.rule == "centerline-command":
        fixed = _replace_first_at_or_after(CENTERLINE_RE, line, issue.column, lambda m: r"\begin{center}" + m.group(1) + r"\end{center}")
        if fixed != line:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:centerline-command", True)
        return FixResult(issue, "semantic:centerline-command", False, "centerline command no longer found")
    if issue.rule == "dash-range":
        fixed, count = DASH_RANGE_RE.subn(r"\1--\2", line, count=1)
        if count:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:dash-range", True)
        return FixResult(issue, "semantic:dash-range", False, "dash range no longer found")
    if issue.rule == "spaced-em-dash":
        fixed, count = SPACED_EM_DASH_RE.subn(r"\1---\2", line, count=1)
        if count:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:spaced-em-dash", True)
        return FixResult(issue, "semantic:spaced-em-dash", False, "spaced hyphen no longer found")
    if issue.rule == "tex-quotes":
        fixed, count = TEX_QUOTES_RE.subn(r"``\1''", line, count=1)
        if count:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:tex-quotes", True)
        return FixResult(issue, "semantic:tex-quotes", False, "straight quote pair no longer found")
    if issue.rule == "ellipsis":
        fixed, count = ELLIPSIS_RE.subn(r"\\ldots{}", line, count=1)
        if count:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:ellipsis", True)
        return FixResult(issue, "semantic:ellipsis", False, "ellipsis no longer found")
    if issue.rule == "prose-spacing":
        fixed, count = PROSE_SPACING_RE.subn(r"\1", line, count=1)
        if count:
            lines[issue.line - 1] = fixed
            return FixResult(issue, "semantic:prose-spacing", True)
        return FixResult(issue, "semantic:prose-spacing", False, "prose spacing issue no longer found")
    return FixResult(issue, "semantic", False, "semantic rule is intentionally not autofixed")


def _wrap_url(match: re.Match[str]) -> str:
    url = match.group(0)
    trimmed = url.rstrip(".,;)")
    suffix = url[len(trimmed) :]
    return rf"\url{{{trimmed}}}" + suffix


def _fix_display_math_delimiter(line: str, issue: SemanticIssue) -> str:
    standalone = STANDALONE_DISPLAY_DOLLAR_RE.match(line)
    if standalone:
        replacement = r"\]" if issue.context == "close" else r"\["
        return standalone.group("indent") + replacement + standalone.group("trailing")
    return _replace_first_at_or_after(DISPLAY_MATH_DOLLAR_RE, line, issue.column, lambda m: r"\[" + m.group(1) + r"\]")


def _modern_font_command(match: re.Match[str]) -> str:
    command = {
        "bf": "textbf",
        "it": "textit",
        "em": "emph",
        "tt": "texttt",
        "sc": "textsc",
        "rm": "textrm",
        "sf": "textsf",
    }[match.group(1)]
    return "\\" + command + "{" + match.group(2) + "}"


def _looks_like_currency_or_empty_math(body: str) -> bool:
    if not body:
        return True
    return bool(re.fullmatch(r"[\d.,\s]+", body))


def _strip_comment(line: str) -> str:
    escaped = False
    for index, char in enumerate(line):
        if char == "\\":
            escaped = not escaped
            continue
        if char == "%" and not escaped:
            return line[:index]
        escaped = False
    return line


def _macro_definition(line: str) -> bool:
    return line.lstrip().startswith(("\\newcommand", "\\renewcommand", "\\providecommand", "\\def", "\\Declare"))


def _math_spans(line: str, in_display: bool) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    if in_display:
        spans.append((0, len(line)))
    spans.extend((match.start(), match.end()) for match in re.finditer(r"\\\(.*?\\\)|\\\[.*?\\\]", line))
    dollar_positions = _dollar_positions(line)
    for start, end in zip(dollar_positions[0::2], dollar_positions[1::2]):
        spans.append((start, end + 1))
    return spans


def _dollar_positions(line: str) -> list[int]:
    positions: list[int] = []
    if "\\(" in line or "\\)" in line:
        pass
    escaped = False
    for index, char in enumerate(line):
        if char == "\\":
            escaped = not escaped
            continue
        if char == "$" and not escaped:
            positions.append(index)
        escaped = False
    return positions


def _replace_first_at_or_after(pattern: re.Pattern[str], line: str, column: int, replacement) -> str:
    min_index = max(0, column - 1)
    for match in pattern.finditer(line):
        if match.start() >= min_index:
            return line[: match.start()] + replacement(match) + line[match.end() :]
    return line


def _generated_file(text: str) -> bool:
    head = "\n".join(text.splitlines()[:20]).lower()
    markers = ("generated file", "auto-generated", "autogenerated", "do not edit", "generated by")
    return any(marker in head for marker in markers)


def _normalized_package_line(line: str) -> str | None:
    stripped = line.strip()
    match = USEPACKAGE_RE.match(stripped)
    if not match:
        return None
    packages = ",".join(sorted(part.strip() for part in match.group("packages").split(",") if part.strip()))
    return re.sub(r"\s+", "", stripped.replace(match.group("packages"), packages))


def _column(text: str, needle: str) -> int:
    index = text.find(needle)
    return index + 1 if index >= 0 else 1
