# VS Code Templates

Copy these files into another LaTeX project to run `trymtex` from VS Code tasks.

## Project Tasks

```bash
mkdir -p /path/to/latex-project/.vscode
cp examples/vscode/tasks.json /path/to/latex-project/.vscode/tasks.json
cp examples/vscode/settings.json /path/to/latex-project/.vscode/settings.json
```

Then in VS Code:

- Open the LaTeX project folder.
- Run `Tasks: Run Task`.
- Pick a `TrymTeX: ...` task.

## Single-File Prompt Tasks

Use `tasks-single-file.json` when you want VS Code to ask for the `.tex` file path each time:

```bash
cp examples/vscode/tasks-single-file.json /path/to/latex-project/.vscode/tasks.json
```

## Snippets

Copy `trymtex.code-snippets` into a project's `.vscode/` folder if you want snippets for quickly inserting TrymTeX task/settings JSON.

```bash
cp examples/vscode/trymtex.code-snippets /path/to/latex-project/.vscode/trymtex.code-snippets
```

These templates use VS Code tasks only. They do not implement LaTeX Workshop Quick Fix API support.
