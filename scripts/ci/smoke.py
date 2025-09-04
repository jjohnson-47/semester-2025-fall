#!/usr/bin/env python
"""Lightweight dashboard smoke test.

Hits key endpoints and prints a concise status summary.

Usage:
  uv run python scripts/ci/smoke.py            # assume server already running
  uv run python scripts/ci/smoke.py --spawn    # start server, run checks, shutdown

Exit codes:
  0 on success (all checks passed)
  1 if any endpoint fails
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE = "http://127.0.0.1:5055"


def http_get(url: str, timeout: float = 5.0) -> tuple[int, bytes, dict[str, str]]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - local endpoint
            return resp.getcode(), resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:  # pragma: no cover - connectivity dependent
        return int(e.code), e.read() or b"", dict(e.headers)
    except Exception as e:  # pragma: no cover - connectivity dependent
        return 0, str(e).encode(), {}


def http_post(
    url: str, data: bytes | None = None, timeout: float = 5.0
) -> tuple[int, bytes, dict[str, str]]:
    req = urllib.request.Request(url, data=data or b"", method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - local endpoint
            return resp.getcode(), resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:  # pragma: no cover
        return int(e.code), e.read() or b"", dict(e.headers)
    except Exception as e:  # pragma: no cover
        return 0, str(e).encode(), {}


def ok(status: int) -> bool:
    return 200 <= status < 300


@dataclass
class CheckResult:
    name: str
    ok: bool
    status: int
    detail: str = ""


def wait_for_ready(base: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, body, _ = http_get(f"{base}/api/health", timeout=2.0)
        if ok(status):
            try:
                payload = json.loads(body.decode() or "{}")
                if payload.get("ok", True) is not False:
                    return True
            except Exception:
                return True
        time.sleep(0.4)
    return False


def spawn_server(port: int) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.setdefault("BUILD_MODE", "v2")
    env.setdefault("DASH_PORT", str(port))
    # Use uv to run module entrypoint
    return subprocess.Popen(
        ["uv", "run", "python", "-m", "dashboard.app"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Dashboard smoke test")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Base URL, default %(default)s")
    parser.add_argument(
        "--spawn", action="store_true", help="Start the server for the duration of the test"
    )
    args = parser.parse_args()

    server_proc: subprocess.Popen[str] | None = None
    try:
        if args.spawn:
            port = int(urllib.parse.urlparse(args.base).port or 5055)
            server_proc = spawn_server(port)
            if not wait_for_ready(args.base, timeout=20.0):
                print("✗ Server failed to become ready", file=sys.stderr)
                return 1

        checks: list[CheckResult] = []

        # health
        s, b, _ = http_get(f"{args.base}/api/health")
        checks.append(CheckResult("health", ok(s), s))

        # phase
        s, b, _ = http_get(f"{args.base}/api/phase")
        checks.append(CheckResult("phase", ok(s), s))

        # now_queue refresh
        s, b, _ = http_post(f"{args.base}/api/now_queue/refresh?timebox=90&energy=medium")
        checks.append(CheckResult("now_queue.refresh", ok(s), s))

        # tasks list (to fetch an id)
        s, b, _ = http_get(f"{args.base}/api/tasks")
        task_id: str | None = None
        if ok(s):
            try:
                payload = json.loads(b.decode() or "{}")
                tasks = payload.get("tasks") or payload
                if isinstance(tasks, list) and tasks:
                    t0 = tasks[0]
                    if isinstance(t0, dict):
                        task_id = t0.get("id") or t0.get("task_id")
            except Exception:
                pass
        checks.append(CheckResult("tasks", ok(s), s))

        # explain (best-effort)
        if task_id:
            s, _, _ = http_get(f"{args.base}/api/explain/{urllib.parse.quote(task_id)}")
            checks.append(CheckResult("explain", ok(s), s))
        else:
            checks.append(CheckResult("explain", True, 204, detail="no tasks"))

        # export formats
        for fmt in ("json", "csv", "ics"):
            s, body, hdr = http_get(f"{args.base}/api/export?format={fmt}")
            ok_fmt = ok(s) and bool(body)
            checks.append(CheckResult(f"export.{fmt}", ok_fmt, s))

        # stats
        s, _, _ = http_get(f"{args.base}/api/stats")
        checks.append(CheckResult("stats", ok(s), s))

        # Print summary
        failures = [c for c in checks if not c.ok]
        for c in checks:
            icon = "✓" if c.ok else "✗"
            extra = f" ({c.detail})" if c.detail else ""
            print(f"{icon} {c.name} [{c.status}]{extra}")

        if failures:
            print(
                f"\n{len(failures)} failure(s): " + ", ".join(f.name for f in failures),
                file=sys.stderr,
            )
            return 1
        return 0
    finally:
        if server_proc is not None:
            try:
                server_proc.terminate()
                try:
                    server_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_proc.kill()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
