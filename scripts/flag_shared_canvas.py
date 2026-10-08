#!/usr/bin/env python3
"""Classify ProSoftArena and DesignBench tasks against the shared-canvas criterion.

Criterion: the task naturally decomposes into two or more concurrent regions,
layers, views, or components of ONE shared artifact, while requiring global
visual/spatial coherence.

Each task is sorted into high / medium / low confidence of matching, with the
work regions, a rationale, and a pre-filled review note, then merged into
shared_canvas_candidates.json (existing benchmarks preserved).

Confidence rules:
  DesignBench generation -> high  (a web page is one canvas with several
                                   independent sections built concurrently)
  DesignBench edit        -> high (>=3 visual-change types), medium (2), low (<=1)
  DesignBench repair      -> high (>=2 issue regions), medium (1)
  ProSoftArena L4 Creative -> high (one canvas, several design elements)
  ProSoftArena L2 Software -> high (>=3 parsed sub-regions), medium (2), low (unclear)
  ProSoftArena L1 Operation -> low (atomic single-region operation)
  ProSoftArena L3 Pipeline  -> low (spans separate applications -> multi-cursor fit)

ProSoftArena currently uses repeated representative descriptions because its
per-task data is not public. Candidates with the same benchmark and normalized
task name are emitted only once so the review queue does not show duplicates.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

CANDIDATES = [
    Path("/Users/tht0021/Downloads/benchmark-tasks/shared_canvas_candidates.json"),
    Path("/Users/tht0021/Downloads/benchmark-tasks/dist/shared_canvas_candidates.json"),
]
CATALOG = Path("/Users/tht0021/Downloads/benchmark-tasks/benchmark_tasks.json")
MANAGED = {"ProSoftArena", "DesignBench"}

AGENTS = ["A", "B", "C", "D", "E", "F"]


def note(regions, artifact, match=True):
    lines = []
    if match:
        lines.append("Why this is a shared-canvas task:")
        lines.append(
            f"The task splits into {len(regions)} concrete regions on the same {artifact}, "
            "so the work can happen concurrently without creating separate deliverables."
        )
    else:
        lines.append("Why this is a weak shared-canvas fit:")
        lines.append(
            f"This task does not clearly split into two or more concurrent regions on one {artifact}; "
            "review before treating it as a shared-canvas task."
        )
    lines.append("")
    lines.append("Agent assignments:")
    for i, r in enumerate(regions):
        lines.append(f"Agent {AGENTS[i % len(AGENTS)]}: {r}")
    lines.append("")
    lines.append("Final coordination check:")
    lines.append(f"Check boundaries, visual consistency, and integration across the combined {artifact}.")
    return "\n".join(lines)


def match_rationale(regions, artifact):
    return (
        f"This task has {len(regions)} concrete work regions on the same {artifact}: "
        + ", ".join(regions)
        + f". Different agents can own these regions at the same time, then review the combined {artifact} as one deliverable."
    )


def split_regions(name: str) -> list[str]:
    text = name.strip().rstrip(".")
    if ":" in text:
        text = text.split(":", 1)[1]
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+|\s*;\s*|,?\s*then\s+", text)
    out = []
    for p in parts:
        p = p.strip().strip(".").strip()
        p = re.sub(r"^(a|an|the)\s+", "", p, flags=re.I)
        if len(p) >= 4:
            out.append(p)
    return out


def classify_designbench(t):
    task = t["task_type"].lower()
    fw = t.get("framework", t["software"][0])
    if task == "generation":
        regions = ["header and navigation bar", "main content and hero section", "footer and supporting sections"]
        return "high", regions, "web page"
    if task == "edit":
        visuals = [v for v in (t.get("edit_visuals") or []) if v]
        regions = [f"{v.lower()} changes" for v in visuals] or ["targeted component changes"]
        conf = "high" if len(visuals) >= 3 else "medium" if len(visuals) == 2 else "low"
        return conf, regions, "web page"
    # repair
    issues = [i for i in (t.get("issues") or []) if i]
    regions = [f"{i} fixes" for i in issues] or ["layout issue fixes"]
    conf = "high" if len(issues) >= 2 else "medium"
    return conf, regions, "web page"


def classify_prosoftarena(t):
    cap = t.get("capability_level")
    if cap == "L4":
        return "high", ["layout and composition", "color and styling", "typography and detail elements"], "design canvas"
    if cap == "L3":
        apps = t["software"]
        regions = [f"{a} stage" for a in apps]
        return "low", regions, "workflow"  # cross-application -> multi-cursor, weak shared-canvas
    if cap == "L1":
        return "low", [t["task_name"].rstrip(".")], "canvas"
    # L2
    regions = split_regions(t["task_name"])
    if len(regions) >= 3:
        return "high", regions[:5], "document"
    if len(regions) == 2:
        return "medium", regions, "document"
    return "low", regions or [t["task_name"].rstrip(".")], "document"


def main():
    catalog = json.loads(CATALOG.read_text())
    tasks = catalog["tasks"]

    new_candidates = []
    seen_candidate_names = set()
    for t in tasks:
        b = t["benchmark"]
        if b == "ProSoftArena":
            name_key = " ".join(t["task_name"].casefold().split()).rstrip(".")
            candidate_key = (b, name_key)
            if candidate_key in seen_candidate_names:
                continue
            seen_candidate_names.add(candidate_key)

        if b == "DesignBench":
            conf, regions, artifact = classify_designbench(t)
        elif b == "ProSoftArena":
            conf, regions, artifact = classify_prosoftarena(t)
        else:
            continue
        is_match = conf in ("high", "medium")
        rationale = match_rationale(regions, artifact) if is_match else (
            f"This task has a single work region or spans separate artifacts, so it is a weak fit for "
            f"concurrent work on one {artifact}."
        )
        new_candidates.append({
            "benchmark": b,
            "task_id": t["task_id"],
            "confidence": conf,
            "rationale": rationale,
            "regions": regions,
            "suggested_note": note(regions, artifact, match=is_match),
        })

    print("New candidates:", len(new_candidates))
    print("By confidence:", dict(Counter(c["confidence"] for c in new_candidates)))
    print("By benchmark:", dict(Counter(c["benchmark"] for c in new_candidates)))

    managed_task_counts = Counter(t["benchmark"] for t in tasks if t["benchmark"] in MANAGED)

    for path in CANDIDATES:
        data = json.loads(path.read_text())
        kept = [c for c in data["tasks"] if c["benchmark"] not in MANAGED]
        data["tasks"] = kept + new_candidates
        data["candidate_count"] = len(data["tasks"])
        data["confidence_counts"] = dict(Counter(c["confidence"] for c in data["tasks"]))
        data["benchmark_counts"] = dict(Counter(c["benchmark"] for c in data["tasks"]))
        rb = data.get("reviewed_benchmark_task_counts", {})
        for b, n in managed_task_counts.items():
            rb[b] = n
        data["reviewed_benchmark_task_counts"] = rb
        data["reviewed_task_count"] = catalog["task_count"]
        data["generated_on"] = "2026-10-08"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"  {path.parent.name}/{path.name}: {len(data['tasks'])} candidates "
              f"({data['confidence_counts']})")


if __name__ == "__main__":
    main()
