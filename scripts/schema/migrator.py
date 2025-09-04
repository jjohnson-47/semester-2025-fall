#!/usr/bin/env python3
"""Schema migrator (v1.0.0 → v1.1.0 scaffolding).

Provides utilities to evolve course JSON to newer schemas without
breaking existing behavior. This module does not mutate repo files by
default; it exposes helpers that callers can run against copies.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class Migration:
    source: str
    target: str
    apply: MigrationFn


class SchemaMigrator:
    """Apply schema migrations in order."""

    def __init__(self) -> None:
        self._migrations: dict[tuple[str, str], MigrationFn] = {}

    def register(self, source: str, target: str, fn: MigrationFn) -> None:
        self._migrations[(source, target)] = fn

    def get_chain(self, from_version: str, to_version: str) -> list[MigrationFn]:
        if from_version == to_version:
            return []
        key = (from_version, to_version)
        if key in self._migrations:
            return [self._migrations[key]]
        raise ValueError(f"No direct migration path {from_version} -> {to_version}")

    def migrate(self, data: dict[str, Any], from_version: str, to_version: str) -> dict[str, Any]:
        result = dict(data)
        for step in self.get_chain(from_version, to_version):
            result = step(result)
            meta = result.setdefault("_meta", {})
            meta["schemaVersion"] = to_version
        return result

    @staticmethod
    def write_json(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

