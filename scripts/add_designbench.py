#!/usr/bin/env python3
"""Add the DesignBench benchmark to the task catalog.

DesignBench (arXiv:2506.06251) benchmarks MLLMs on front-end code generation
across 4 frameworks (React, Vue, Angular, vanilla HTML/CSS) and 3 tasks
(generation, edit, repair) — 900 real webpage samples spanning 11 topics,
9 edit types and 6 issue categories.

The dataset is public on Hugging Face (whale99/DesignBench), organized as
<task>/<framework>/<index>/, with the per-sample reference screenshots and a
metadata JSON. We read the file tree and each sample's metadata to build 900
rows with real filtering fields and inline screenshot artifacts:
  software    - React / Vue / Angular / HTML+CSS         (Software filter)
  task_type   - Generation / Edit / Repair               (Task Type filter)
  level       - edit difficulty easy/medium/hard         (Difficulty filter)
  topic       - generation topic (11)      (shown in detail)
  issues      - repair issue categories (6) (shown in detail)
  edit_actions / edit_visuals - edit taxonomy (shown in detail)
Artifacts: generation -> target design; edit -> before/after; repair ->
buggy / annotated / repaired renderings.

Patches both the root and dist copies of benchmark_tasks.json in place.
"""

from __future__ import annotations

import concurrent.futures
import json
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

REPO = "whale99/DesignBench"
RES = f"https://huggingface.co/datasets/{REPO}/resolve/main/"
TREE = f"https://huggingface.co/datasets/{REPO}/tree/main/"
PAPER = "https://arxiv.org/abs/2506.06251"
SOURCE = "https://github.com/WebPAI/DesignBench"
API = f"https://huggingface.co/api/datasets/{REPO}/tree/main?recursive=true"

CATALOGS = [
    Path("/Users/tht0021/Downloads/benchmark-tasks/benchmark_tasks.json"),
    Path("/Users/tht0021/Downloads/benchmark-tasks/dist/benchmark_tasks.json"),
]

FW_NAME = {"react": "React", "vue": "Vue", "angular": "Angular", "vanilla": "HTML & CSS"}
FW_SOFTWARE = {"react": "React", "vue": "Vue", "angular": "Angular", "vanilla": "HTML/CSS"}
TASKS = ("generation", "edit", "repair")


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    return urllib.request.urlopen(req, timeout=60)


def paginate_tree() -> list[str]:
    files, url = [], API
    while url:
        with _get(url) as r:
            files.extend(x["path"] for x in json.loads(r.read().decode()) if x.get("type") == "file")
            nxt = None
            for part in r.headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    nxt = part[part.find("<") + 1:part.find(">")]
            url = nxt
    return files


def fetch_meta(task: str, fw: str, idx: str) -> dict | None:
    url = RES + quote(f"{task}/{fw}/{idx}/{idx}.json", safe="/")
    for _ in range(2):
        try:
            with _get(url) as r:
                return json.loads(r.read().decode())
        except Exception:
            continue
    return None


def res(path: str) -> str:
    return RES + quote(path, safe="/")


def img(label: str, path: str, dl: str = "Download ↓") -> dict:
    return {"label": label, "image_url": res(path), "links": [{"text": dl, "url": res(path)}]}


def clean_list(v):
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str) and x.strip()]
    return []


def build_rows() -> list[dict]:
    files = set(paginate_tree())
    samples: dict[tuple[str, str], set[str]] = defaultdict(set)
    for p in files:
        parts = p.split("/")
        if len(parts) >= 3 and parts[0] in TASKS and parts[2].isdigit():
            samples[(parts[0], parts[1])].add(parts[2])

    jobs = [(t, f, i) for (t, f), ids in samples.items() for i in ids]
    meta: dict[tuple[str, str, str], dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as ex:
        futs = {ex.submit(fetch_meta, t, f, i): (t, f, i) for t, f, i in jobs}
        for fut in concurrent.futures.as_completed(futs):
            d = fut.result()
            if d:
                meta[futs[fut]] = d

    rows = []
    for task, fw, idx in sorted(jobs, key=lambda x: (x[0], x[1], int(x[2]))):
        d = meta.get((task, fw, idx), {})
        fwname = FW_NAME.get(fw, fw)
        prefix = f"{task}/{fw}/{idx}"
        row = {
            "benchmark": "DesignBench",
            "task_id": prefix,
            "software": [FW_SOFTWARE.get(fw, fw)],
            "task_type": task.capitalize(),
            "framework": fwname,
        }
        artifacts = []

        def png_in(name: str) -> bool:
            return f"{prefix}/{name}" in files

        if task == "generation":
            topic = (d.get("topic") or "").strip()
            row["task_name"] = (
                f"Generate {fwname} code to reproduce this {topic} webpage design."
                if topic else f"Generate {fwname} code to reproduce this webpage design."
            )
            if topic:
                row["topic"] = topic
            if d.get("url"):
                row["source_page_url"] = d["url"]
            if png_in(f"{idx}.png"):
                artifacts.append(img("Target design (to generate)", f"{prefix}/{idx}.png"))

        elif task == "edit":
            visuals = clean_list(d.get("visual_type"))
            actions = clean_list(d.get("action_type"))
            diff = (d.get("difficulty") or "").strip().lower()
            summary = ", ".join(visuals).lower()
            row["task_name"] = (
                f"Edit this {fwname} page to match the target design"
                + (f" ({summary})." if summary else ".")
            )
            if diff in ("easy", "medium", "hard"):
                row["level"] = diff
            if actions:
                row["edit_actions"] = actions
            if visuals:
                row["edit_visuals"] = visuals
            src_id, dst_id = str(d.get("src_id", "")), str(d.get("dst_id", ""))
            # fall back to the two numeric pngs in the sample dir, sorted
            pngs = sorted(
                (f.split("/")[-1] for f in files if f.startswith(prefix + "/") and f.endswith(".png")
                 and f.split("/")[-1][:-4].isdigit()),
                key=lambda n: int(n[:-4]),
            )
            before = f"{src_id}.png" if png_in(f"{src_id}.png") else (pngs[0] if pngs else None)
            after = f"{dst_id}.png" if png_in(f"{dst_id}.png") else (pngs[-1] if len(pngs) > 1 else None)
            if before:
                artifacts.append(img("Before (original)", f"{prefix}/{before}"))
            if after and after != before:
                artifacts.append(img("After (target)", f"{prefix}/{after}"))

        else:  # repair
            issues = clean_list(d.get("issue"))
            summary = ", ".join(issues)
            row["task_name"] = (
                f"Repair the {summary} issue(s) in this {fwname} page."
                if summary else f"Repair the UI issues in this {fwname} page."
            )
            if issues:
                row["issues"] = issues
            if png_in(f"{idx}.png"):
                artifacts.append(img("Buggy rendering", f"{prefix}/{idx}.png"))
            if png_in(f"{idx}_mark.png"):
                artifacts.append(img("Annotated issues", f"{prefix}/{idx}_mark.png"))
            if png_in("repaired.png"):
                artifacts.append(img("Repaired (reference)", f"{prefix}/repaired.png"))

        if artifacts:
            artifacts[-1].setdefault("links", []).append(
                {"text": "All sample files ↗", "url": TREE + quote(prefix, safe="/")}
            )
            artifacts[0]["note"] = (
                "DesignBench ships this webpage sample with reference screenshots and code; "
                "agents are scored on visual similarity (CLIP) and code metrics."
            )
            row["artifacts"] = artifacts
        rows.append(row)

    return rows


def metadata(count: int) -> dict:
    return {
        "benchmark": "DesignBench",
        "source_url": SOURCE,
        "code_url": SOURCE,
        "paper_url": PAPER,
        "source_revision": "hf-whale99-DesignBench",
        "task_count": count,
        "scope": (
            "All 900 webpage samples across 4 frameworks (React, Vue, Angular, vanilla HTML/CSS) "
            "and 3 tasks (generation, edit, repair), from the public Hugging Face dataset "
            "whale99/DesignBench."
        ),
        "task_name_basis": (
            "Derived from each sample's metadata (framework, task, topic/edit-type/issue category). "
            "Reference screenshots and code are the official per-sample files."
        ),
    }


def main() -> None:
    rows = build_rows()
    from collections import Counter
    print("total:", len(rows))
    print("by task:", dict(Counter(r["task_type"] for r in rows)))
    print("by framework:", dict(Counter(r["framework"] for r in rows)))
    print("with artifacts:", sum(1 for r in rows if r.get("artifacts")))
    assert len(rows) == 900, f"expected 900, got {len(rows)}"
    meta = metadata(len(rows))

    for catalog_path in CATALOGS:
        catalog = json.loads(catalog_path.read_text())
        catalog["benchmarks"] = [b for b in catalog["benchmarks"] if b["benchmark"] != "DesignBench"]
        catalog["tasks"] = [t for t in catalog["tasks"] if t["benchmark"] != "DesignBench"]
        catalog["benchmarks"].append(meta)
        catalog["tasks"].extend(rows)
        catalog["benchmark_count"] = len(catalog["benchmarks"])
        catalog["task_count"] = len(catalog["tasks"])
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
        print(f"  {catalog_path.name}: added {len(rows)} (total {catalog['task_count']} tasks, {catalog['benchmark_count']} benchmarks)")


if __name__ == "__main__":
    main()
