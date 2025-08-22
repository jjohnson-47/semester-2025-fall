
# scripts/fetch-docs.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

# Fetch the latest/stable documentation pages needed for the Flask+HTMX task system.
# It uses wget with timestamping so re-runs only update when sources change.
#
# Output tree:
#   docs/vendor/<host>/<path>.html
#
# Requirements: bash, wget, coreutils
#
# Usage:
#   chmod +x scripts/fetch-docs.sh
#   ./scripts/fetch-docs.sh
#
# Optional:
#   DOCS_DIR=custom/path ./scripts/fetch-docs.sh

DOCS_DIR="${DOCS_DIR:-docs/vendor}"
mkdir -p "$DOCS_DIR"

# --- Helper to fetch a single URL into a mirrored path under $DOCS_DIR ---
fetch() {
  local url="$1"
  # Normalize target path: docs/vendor/<host>/<path>.html
  local host path file
  host="$(printf '%s' "$url" | awk -F/ '{print $3}')"
  path="$(printf '%s' "$url" | cut -d/ -f4-)"
  # ensure trailing "index.html" when URL ends with /
  if [[ "$url" =~ /$ ]]; then
    file="$DOCS_DIR/$host/${path}index.html"
  else
    # convert last segment (possibly empty) to .html if no extension
    if [[ "$path" =~ \.([a-zA-Z0-9]+)$ ]]; then
      file="$DOCS_DIR/$host/$path"
    else
      file="$DOCS_DIR/$host/$path.html"
    fi
  fi
  mkdir -p "$(dirname "$file")"

  # Use wget with timestamping and page requisites to make pages viewable offline.
  # We keep URLs absolute to avoid rewriting docs; -E adds .html when needed.
  wget \
    --quiet \
    --timestamping \
    --adjust-extension \
    --page-requisites \
    --convert-links \
    --domains "$host" \
    --no-parent \
    --directory-prefix "$(dirname "$file")" \
    "$url"

  echo "[docs] fetched: $url"
}

# ----------------------------------
# Manifest (edit as needed)
# ----------------------------------

URLS=(
  # Flask (stable = current maintained series)
  "https://flask.palletsprojects.com/en/stable/"
  "https://flask.palletsprojects.com/en/stable/tutorial/"
  "https://flask.palletsprojects.com/en/stable/blueprints/"
  "https://flask.palletsprojects.com/en/stable/tutorial/views/"

  # Jinja (stable)
  "https://jinja.palletsprojects.com/en/stable/"
  "https://jinja.palletsprojects.com/en/stable/templates/"

  # Python stdlib (latest 3.x landing picks current; add explicit 3.12 for pinning if needed)
  "https://docs.python.org/3/library/graphlib.html"

  # JSON Schema (official site + Python library)
  "https://json-schema.org/specification"
  "https://json-schema.org/docs"
  "https://python-jsonschema.readthedocs.io/"
  "https://pypi.org/project/jsonschema/"

  # PyYAML (official site + docs hub + PyPI)
  "https://pyyaml.org/"
  "https://pyyaml.org/wiki/PyYAMLDocumentation"
  "https://pypi.org/project/PyYAML/"

  # HTMX (current docs, not v1)
  "https://htmx.org/attributes/hx-get/"
  "https://htmx.org/attributes/hx-post/"
  "https://htmx.org/attributes/hx-target/"
  "https://htmx.org/attributes/hx-swap/"
  "https://htmx.org/attributes/hx-swap-oob/"

  # Alpine.js (current docs)
  "https://alpinejs.dev/start-here"
  "https://alpinejs.dev/directives/on"
  "https://alpinejs.dev/essentials/events"
  "https://alpinejs.dev/essentials/installation"
  "https://alpinejs.dev/upgrade-guide"

  # Tailwind CSS (current docs emphasize utility patterns & logical padding)
  "https://tailwindcss.com/docs/styling-with-utility-classes"
  "https://tailwindcss.com/docs/padding"

  # Accessibility (APG modal + MDN dialog role + HTML <dialog>)
  "https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/"
  "https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/examples/dialog/"
  "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/dialog_role"
  "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog"
)

# ----------------------------------
# Fetch all
# ----------------------------------
for u in "${URLS[@]}"; do
  fetch "$u"
done

echo "[docs] complete. See: $DOCS_DIR"
```

## Why these endpoints (forward-looking, official)

* **Flask “stable” & tutorial/blueprints**: Pallets’ “stable” channel is the actively maintained series intended for production, reflecting current patterns. ([flask.palletsprojects.com][1])
* **Jinja “stable”**: Current templating syntax & best practices. ([jinja.palletsprojects.com][2])
* **Python `graphlib`**: Latest 3.x landing page, ensuring future-compatible `TopologicalSorter` semantics. If you need to pin to 3.12, swap in the 3.12 URL. ([Python documentation][3])
* **JSON Schema**: Official specification + Python library docs for validation tooling. ([json-schema.org][4], [jsonschema][5], [PyPI][6])
* **PyYAML**: Official site + documentation hub + PyPI metadata. ([pyyaml.org][7], [PyPI][8])
* **HTMX**: Current attribute docs (avoid older v1 mirror), including `hx-swap-oob` for out-of-band updates. ([htmx.org][9])
* **Alpine.js**: Official start guide, `x-on`/keyboard modifiers, events, install & upgrade guidance for modern usage (e.g., `Alpine.start()` in module builds). ([alpinejs.dev][10])
* **Tailwind CSS**: Current docs emphasizing utility-first and logical properties (`ps-*`/`pe-*`), compatible with future patterns; padding utility reference included. ([tailwindcss.com][11])
* **Accessibility**: WAI-ARIA APG modal dialog pattern + MDN `role="dialog"` and HTML `<dialog>` element—aligning with modern, standards-based modal behavior. ([W3C][12], [MDN Web Docs][13])

### Tips

* If you want **offline** reading with a nicer local index, add a tiny `index.md` in `docs/vendor/` that links to the fetched files.
* To **pin** versions (e.g., Python 3.12), replace `https://docs.python.org/3/…` with `https://docs.python.org/3.12/…`. ([Python documentation][14])

If you want me to also generate a minimal `docs/vendor/INDEX.md` and a Makefile target (`make docs`) around this, say the word and I’ll include them.

[1]: https://flask.palletsprojects.com/?utm_source=chatgpt.com "Welcome to Flask — Flask Documentation (3.1.x)"
[2]: https://jinja.palletsprojects.com/?utm_source=chatgpt.com "Jinja — Jinja Documentation (3.1.x)"
[3]: https://docs.python.org/3/library/graphlib.html?utm_source=chatgpt.com "graphlib — Functionality to operate with graph-like structures"
[4]: https://json-schema.org/specification?utm_source=chatgpt.com "JSON Schema - Specification [#section]"
[5]: https://python-jsonschema.readthedocs.io/?utm_source=chatgpt.com "jsonschema 4.25.1 documentation"
[6]: https://pypi.org/project/jsonschema/?utm_source=chatgpt.com "jsonschema"
[7]: https://pyyaml.org/?utm_source=chatgpt.com "PyYAML"
[8]: https://pypi.org/project/PyYAML/?utm_source=chatgpt.com "PyYAML"
[9]: https://htmx.org/attributes/hx-swap-oob/?utm_source=chatgpt.com "hx-swap-oob Attribute"
[10]: https://alpinejs.dev/start-here?utm_source=chatgpt.com "Start Here"
[11]: https://tailwindcss.com/docs/styling-with-utility-classes?utm_source=chatgpt.com "Styling with utility classes - Core concepts"
[12]: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/?utm_source=chatgpt.com "Dialog (Modal) Pattern | APG | WAI"
[13]: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/dialog_role?utm_source=chatgpt.com "ARIA: dialog role - MDN - Mozilla"
[14]: https://docs.python.org/uk/3.12/library/graphlib.html?utm_source=chatgpt.com "graphlib — Functionality to operate with graph-like structures"

