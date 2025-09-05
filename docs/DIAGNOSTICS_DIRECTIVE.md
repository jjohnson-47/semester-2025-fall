# Diagnostics Directive

Use this exact command block to capture precise diagnostics for the three failing checks (Format, Lint, Mypy). Paste the full output back into the PR or issue for a targeted one-shot fix plan.

```bash
# 0) Context
printf "\n## GIT HEAD\n"; git log -1 --oneline
printf "\n## PY/TOOLS\n"; python --version; uv --version
printf "\n## RUFF/MYPY/PYTEST VERSIONS\n"; ruff --version; mypy --version; pytest --version

# 1) Config files (exact sections only)
printf "\n## pyproject.toml (ruff + format + project)\n"; awk '/^\[tool.ruff\]/,/^\[/{print} /^\[tool.ruff.format\]/,/^\[/{print} /^\[project\]/,/^\[/{print}' pyproject.toml
printf "\n## ruff.toml (if present)\n"; [ -f ruff.toml ] && cat ruff.toml || echo "none"
printf "\n## mypy.ini (or pyproject [tool.mypy])\n"; { [ -f mypy.ini ] && cat mypy.ini; } || awk '/^\[tool.mypy\]/,/^\[/{print}' pyproject.toml
printf "\n## .editorconfig (if present)\n"; [ -f .editorconfig ] && cat .editorconfig || echo "none"
printf "\n## .pre-commit-config.yaml (if present)\n"; [ -f .pre-commit-config.yaml ] && sed -n '1,160p' .pre-commit-config.yaml || echo "none"

# 2) Formatter failure (show the minimal diff Ruff/Black wants)
printf "\n## FORMAT CHECK (ruff format --check)\n"
ruff format --check --diff

# Also show exact file list (useful if more than one file fails)
printf "\n## FORMAT TARGETS\n"
ruff format --check 2>/dev/null | sed -n 's/^Would reformat: //p' | sort -u

# 3) Lint failure (full message + rule config)
printf "\n## LINT CHECK (ruff check)\n"
ruff check --output-format=concise --exit-zero | head -n 50
printf "\n## LINT ERRORS (exact)\n"
ruff check --select RUF006 --exit-non-zero-on-fix

# Show the call sites for asyncio.create_task
printf "\n## create_task call sites\n"
rg -n --hidden --glob '!.venv' --glob '!venv' 'asyncio\.create_task\(' || true

# 4) Mypy failure (precise context)
printf "\n## MYPY FOCUS (scripts/utils/style_system.py:90-120)\n"
nl -ba scripts/utils/style_system.py | sed -n '90,120p'
printf "\n## MYPY RUN (no color, show codes)\n"
mypy . --no-color-output --pretty --show-error-codes --hide-error-context

# 5) Project layout (lightweight)
printf "\n## TREE (top-level + key dirs)\n"
ls -la
printf "\n## PACKAGES (src tree)\n"
[ -d src ] && find src -maxdepth 2 -type d -print | sed 's|^|  |' || echo "no src/"

# 6) Env pins that could affect lint/type behavior
printf "\n## DEP PINS (top)\n"
awk '/^\[project.dependencies\]/,/^\[/{print}' pyproject.toml
printf "\n## TOOL PINS (dev-dependencies)\n"
awk '/^\[project.optional-dependencies\]/,/^\[/{print}' pyproject.toml
printf "\n## INSTALLED TOP-LEVEL VERSIONS (short)\n"
uv pip freeze --exclude-editable | rg '^(ruff|mypy|typing-extensions|pydantic|fastapi|pytest)[=~<>]' | sort
```

Notes
- This repo already includes a live status snapshot at `docs/STATUS_REPORT.md` if you want a quick overview before deep diagnostics.
- The commands above only reference tools and files that exist in this repository and CI setup.
