"""Schema migrator (compat) bridging to current migration utilities.

Provides a minimal facade expected by the feature branch to migrate schedules
to v1.1.0 with stable IDs. Internally delegates to `scripts.migrations`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import warnings


def migrate_schedule_file(course: str, in_path: str | Path, out_path: str | Path) -> dict[str, Any]:
  """Migrate a single schedule JSON to v1.1.0 with stable IDs.

  Returns the migrated payload for further inspection.
  """
  from scripts.migrations.add_stable_ids import infer_term_label, migrate_schedule

  in_p = Path(in_path)
  out_p = Path(out_path)
  prefix = infer_term_label(Path("variables/semester.json"))
  payload = json.loads(in_p.read_text(encoding="utf-8"))
  migrated = migrate_schedule(course, payload, prefix)
  out_p.parent.mkdir(parents=True, exist_ok=True)
  out_p.write_text(json.dumps(migrated, indent=2), encoding="utf-8")
  return migrated


def migrate_all(content_root: str | Path = "content/courses") -> list[Path]:  # pragma: no cover - utility
  """Migrate all course schedules under the content root into build/normalized."""
  out_paths: list[Path] = []
  root = Path(content_root)
  for course_dir in root.iterdir():
    if not course_dir.is_dir():
      continue
    course = course_dir.name
    sched = course_dir / "schedule.json"
    if sched.exists():
      out = Path("build/normalized") / course / "schedule.v1_1_0.json"
      migrate_schedule_file(course, sched, out)
      out_paths.append(out)
  return out_paths


# Deprecation notice: Keep for a short window post-merge, then remove.
warnings.warn(
    "scripts.schema.migrator is deprecated and will be removed after Fall 2025. "
    "Use scripts.migrations.add_stable_ids and current v1.1.0 helpers instead.",
    DeprecationWarning,
    stacklevel=2,
)
