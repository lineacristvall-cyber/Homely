"""Deterministic founder tracker from the canonical weighted checklist and logs."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "PROGRESS_CHECKLIST.json"
PROGRESS = ROOT / "PROGRESS.md"
DECISIONS = ROOT / "DECISIONS.md"
OPEN = ROOT / "OPEN_ACTION_ITEMS.md"


def _score(criteria):
    total = 0
    earned = 0
    rendered = []
    for item in criteria:
        weight = item.get("weight")
        if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
            raise ValueError("Checklist weights must be positive integers.")
        checked = item.get("checked") is True
        total += weight
        earned += weight if checked else 0
        rendered.append({
            "label": str(item.get("label", "")),
            "weight": weight,
            "met": checked,
            "evidence": str(item.get("evidence", "")),
        })
    return {
        "earned": earned, "total": total,
        "percent": round(100 * earned / total) if total else 0,
        "criteria": rendered,
    }


def _lines(path, pattern, limit):
    if not path.exists():
        return []
    result = []
    for line in path.read_text().splitlines():
        match = re.match(pattern, line)
        if match:
            result.append(match.group(1).strip())
    return result[-limit:]


def build_progress():
    raw = json.loads(CHECKLIST.read_text())
    components = []
    for item in raw["components"]:
        components.append({
            "id": item["id"], "name": item["name"],
            "owner": item.get("owner", ""), "currentTask": item.get("currentTask", ""),
            "blockers": item.get("blockers", []),
            "poc": _score(item.get("poc", [])),
            "production": _score(item.get("production", [])),
        })
    def aggregate(kind):
        earned = sum(c[kind]["earned"] for c in components)
        total = sum(c[kind]["total"] for c in components)
        return {"earned": earned, "total": total, "percent": round(100 * earned / total) if total else 0}
    updated = max(p.stat().st_mtime for p in (CHECKLIST, PROGRESS, DECISIONS, OPEN) if p.exists())
    evidence = []
    for component in components:
        for kind in ("poc", "production"):
            for criterion in component[kind]["criteria"]:
                if criterion["met"] and criterion["evidence"]:
                    evidence.append(criterion["evidence"])
    return {
        "schemaVersion": raw.get("schemaVersion", 1),
        "updatedAt": datetime.fromtimestamp(updated, timezone.utc).isoformat(),
        "planningAssumptions": raw.get("planningAssumptions", ""),
        "poc": aggregate("poc"),
        "production": aggregate("production"),
        "components": components,
        "openActions": _lines(OPEN, r"^- \[ \] (.*)$", 100),
        "recentDecisions": _lines(DECISIONS, r"^- (.*)$", 8),
        "evidence": list(dict.fromkeys(evidence))[-30:],
    }
