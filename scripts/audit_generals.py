#!/usr/bin/env python3
"""Read-only roster audit for the Codex rebuild.

This script never mutates master data. It reports structural problems and checks
known S2/S3/S4 additions so Codex can produce docs/data_audit.md before editing
any roster data.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERALS_PATH = ROOT / "data" / "generals_master.json"
PUBLIC_ROSTER_TARGET = 137  # comparison target only; not an authoritative invariant

EXPECTED_BY_SEASON = {
    "S2": {
        "黒田官兵衛",
        "前田慶次",
        "山県昌景",
        "高橋紹運",
        "里見義堯",
        "相馬盛胤",
        "大内義隆",
        "瑞渓院",
    },
    "S3": {
        "柿崎景家",
        "まつ",
        "真田昌幸",
        "立花誾千代",
        "鈴木佐大夫",
        "安宅冬康",
        "伊達輝宗",
        "加藤嘉明",
    },
    "S4": {
        "伊達政宗",
        "長野業正",
        "佐竹義重",
        "三好実休",
        "藤林正保",
        "浦上宗景",
        "堀直政",
        "大久保長安",
    },
}

REQUIRED_KEYS = ("unit_id", "name", "base_stats", "unique_skill_id")


def load_generals() -> list[dict]:
    with GENERALS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = list(data.values())
    if not isinstance(data, list):
        raise TypeError("generals_master.json must contain a list or dict")
    return data


def inferred_season(name: str, explicit: str | None) -> str:
    if explicit in {"S1", "S2", "S3", "S4"}:
        return explicit
    for season, names in EXPECTED_BY_SEASON.items():
        if name in names:
            return season
    return "S1?"  # audit-only inference; do not write this value back automatically


def main() -> int:
    generals = load_generals()
    names = [str(g.get("name", "")) for g in generals]
    ids = [str(g.get("unit_id", "")) for g in generals]

    print("=== generals_master audit ===")
    print(f"path: {GENERALS_PATH}")
    print(f"current rows: {len(generals)}")
    print(f"public comparison target: {PUBLIC_ROSTER_TARGET}")
    print(f"difference vs target: {len(generals) - PUBLIC_ROSTER_TARGET:+d}")

    duplicate_names = sorted(k for k, v in Counter(names).items() if k and v > 1)
    duplicate_ids = sorted(k for k, v in Counter(ids).items() if k and v > 1)
    print(f"duplicate names ({len(duplicate_names)}): {duplicate_names}")
    print(f"duplicate unit_ids ({len(duplicate_ids)}): {duplicate_ids}")

    missing_fields: dict[str, list[str]] = defaultdict(list)
    for i, g in enumerate(generals):
        label = g.get("name") or g.get("unit_id") or f"row#{i}"
        for key in REQUIRED_KEYS:
            if key not in g or g.get(key) in (None, "", {}):
                missing_fields[key].append(str(label))

    print("\n=== required-field audit ===")
    for key in REQUIRED_KEYS:
        vals = missing_fields.get(key, [])
        print(f"{key}: missing {len(vals)}")
        if vals:
            print("  " + ", ".join(vals))

    existing = set(names)
    print("\n=== known season additions ===")
    for season in ("S2", "S3", "S4"):
        expected = EXPECTED_BY_SEASON[season]
        missing = sorted(expected - existing)
        present = sorted(expected & existing)
        print(f"{season}: {len(present)}/{len(expected)} present")
        print("  present: " + (", ".join(present) if present else "(none)"))
        print("  missing: " + (", ".join(missing) if missing else "(none)"))

    inferred_counts = Counter(
        inferred_season(str(g.get("name", "")), g.get("season_added")) for g in generals
    )
    print("\n=== season labels/inference (audit only) ===")
    for season in ("S1", "S1?", "S2", "S3", "S4"):
        if inferred_counts[season]:
            print(f"{season}: {inferred_counts[season]}")

    explicit_bad = [
        g.get("name", g.get("unit_id", "?"))
        for g in generals
        if g.get("season_added") not in (None, "S1", "S2", "S3", "S4")
    ]
    if explicit_bad:
        print("invalid season_added values on: " + ", ".join(map(str, explicit_bad)))

    problems = bool(duplicate_names or duplicate_ids or any(missing_fields.values()))
    later_missing = any(EXPECTED_BY_SEASON[s] - existing for s in ("S2", "S3", "S4"))

    print("\n=== conclusion ===")
    if len(generals) != PUBLIC_ROSTER_TARGET:
        print("NOTE: roster count differs from the public comparison target; audit sources before editing.")
    if later_missing:
        print("NOTE: one or more known S2/S3/S4 additions are absent from the current master.")
    if not problems and not later_missing:
        print("Structural checks passed and all known later-season additions are present.")

    # Non-zero only for structural corruption. Missing public roster entries are an audit finding,
    # not a CI failure until authoritative roster data is established.
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
