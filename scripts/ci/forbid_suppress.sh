#!/usr/bin/env bash
set -euo pipefail

# Files allowed to use contextlib.suppress temporarily (startup-only goal)
ALLOW=("dashboard/startup.py")

violations=0
while IFS= read -r -d '' f; do
  if grep -n "contextlib\.suppress" "$f" >/dev/null; then
    allowed=0
    for a in "${ALLOW[@]}"; do
      if [[ "$f" == "$a" ]]; then
        allowed=1
        break
      fi
    done
    if [[ $allowed -eq 0 ]]; then
      echo "::error file=$f::contextlib.suppress not allowed here"
      violations=1
    fi
  fi
done < <(git ls-files "*.py" -z)

exit $violations
