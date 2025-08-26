#!/usr/bin/env bash
set -euo pipefail

# Create GitHub issues from .github/refactor-issues.yaml using GitHub CLI (gh).
# Prereqs: gh auth login; repo is the current origin.

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install https://cli.github.com/ and run 'gh auth login'." >&2
  exit 1
fi

YAML_FILE=".github/refactor-issues.yaml"
if [ ! -f "$YAML_FILE" ]; then
  echo "Missing $YAML_FILE" >&2
  exit 1
fi

python - "$YAML_FILE" << 'PY'
import sys, yaml, subprocess
path = sys.argv[1]
data = yaml.safe_load(open(path))
for w in data.get('workstreams', []):
    title = w['title']
    body = w.get('body', '')
    labels = ','.join(w.get('labels', []))
    cmd = [
        'gh','issue','create',
        '--title', title,
        '--body', body,
    ]
    if labels:
        cmd += ['--label', labels]
    print('Creating:', title)
    subprocess.check_call(cmd)
print('Done.')
PY

