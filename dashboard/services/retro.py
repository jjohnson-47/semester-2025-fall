"""Weekly retro generator using events log.

Produces a compact JSON summary for the last 7 days: total tasks done, top unblockers,
category breakdown, and blocker themes (keywords from titles/notes).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from dashboard.db import Database


def generate_weekly_retro(db: Database, out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().replace(microsecond=0)
    week_ago = now - timedelta(days=7)

    with db.connect() as conn:
        ev = conn.execute(
            "select task_id, at from events where field='status' and to_val='done' and at >= ?",
            (week_ago.isoformat() + "Z",),
        ).fetchall()
        done_ids = [r["task_id"] for r in ev]

        tasks = []
        if done_ids:
            q_marks = ",".join(["?"] * len(done_ids))
            tasks = [dict(r) for r in conn.execute(f"select * from tasks where id in ({q_marks})", done_ids).fetchall()]

    cats = Counter((t.get("category") or "uncat").lower() for t in tasks)
    titles = " ".join((t.get("title") or "") + " " + (t.get("notes") or "") for t in tasks).lower()
    # Naive keyword extraction
    STOP = {"the","and","with","from","about","their","these","those","which","course","update","updates","content","materials","assessment","technical","communication","setup","syllabus","student","students"}
    tokens = titles.replace("/", " ").replace("-", " ").replace(".", " ").split()
    keywords = [w for w in tokens if len(w) > 4 and w not in STOP]
    theme = Counter(keywords).most_common(5)

    payload = {
        "generated": now.isoformat() + "Z",
        "window": [week_ago.isoformat() + "Z", now.isoformat() + "Z"],
        "completed": len(done_ids),
        "categories": cats.most_common(),
        "top_keywords": theme,
    }

    fname = out_dir / f"weekly_{now.strftime('%Y%m%d')}.json"
    with open(fname, "w") as f:
        json.dump(payload, f, indent=2)
    return payload
