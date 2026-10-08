#!/usr/bin/env python3
"""Attach the artifacts an agent works with to tasks across benchmarks.

CANVAS (public HF dataset seooyxx/canvas): rendered design images (PNG), vector
SVGs, Figma node JSON, plus the original Figma community file. Modification tasks
have base/target (and, in task-2, a component); replication tasks have a reference.

PSBench (public HF dataset zyn1216/PSBench): input (start) image and reference
output (end) image per task, plus the grading rubric.

AutoCAD Bench (public GitHub repo): reference drawing (rendered PNG) and the gold
DWG per task, derived from catalog fields.

GUIDE (gated HF dataset kixlab/GuideBench): the real artifact is a user screen
recording; per-task recordings/brief require dataset access. We link the gated
brief, the paper task list, the project page, and a public sample session video
for the task's app family when one exists.

Patches both the root and dist copies of benchmark_tasks.json in place.
"""

import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import quote

CANVAS_REPO = "seooyxx/canvas"
CANVAS_RES = f"https://huggingface.co/datasets/{CANVAS_REPO}/resolve/main/"
CANVAS_BLOB = f"https://huggingface.co/datasets/{CANVAS_REPO}/blob/main/"

GUIDE_BLOB = "https://huggingface.co/datasets/kixlab/GuideBench/blob/main/"
GUIDE_PROJECT = "https://guide-bench.github.io/"
GUIDE_PAPER = "https://arxiv.org/abs/2603.25864"
GUIDE_VID = "https://guide-bench.github.io/assets/example_videos/"
# One public sample-session video per app category (only 3 exist).
GUIDE_CATEGORY_VIDEO = {
    "Adobe Photoshop": "video_1_Photoshop.mp4",
    "GIMP": "video_1_Photoshop.mp4",
    "Google Slides": "video_2_GoogleSlides.mp4",
    "Microsoft PowerPoint": "video_2_GoogleSlides.mp4",
    "Adobe Premiere Pro": "video_3_PremierePro.mp4",
    "CapCut": "video_3_PremierePro.mp4",
}

PSBENCH_REPO = "zyn1216/PSBench"
PSBENCH_RES = f"https://huggingface.co/datasets/{PSBENCH_REPO}/resolve/main/"
PSBENCH_API = f"https://huggingface.co/api/datasets/{PSBENCH_REPO}/tree/main?recursive=true"

CATALOGS = [
    Path("/Users/tht0021/Downloads/benchmark-tasks/benchmark_tasks.json"),
    Path("/Users/tht0021/Downloads/benchmark-tasks/dist/benchmark_tasks.json"),
]

SUFFIX_LABEL = {
    "base": "Base (starting design)",
    "target": "Target (goal design)",
    "component": "Component (insert element)",
    "": "Reference design",
}


def fetch_jsonl(path: str) -> list[dict]:
    url = CANVAS_RES + quote(path, safe="/")
    with urllib.request.urlopen(url, timeout=60) as r:
        return [json.loads(line) for line in r.read().decode().splitlines() if line.strip()]


def logical_id(stem: str) -> str:
    return re.sub(r"-(?:base|target|component)$", "", stem)


def suffix_of(stem: str) -> str:
    m = re.search(r"-(base|target|component)$", stem)
    return m.group(1) if m else ""


def res(path: str) -> str:
    return CANVAS_RES + quote(path, safe="/")


def artifact_entry(folder: str, stem: str, figma_url: str) -> dict:
    links = [
        {"text": "PNG", "url": res(f"{folder}/{stem}.png")},
        {"text": "SVG", "url": res(f"{folder}/{stem}.svg")},
        {"text": "Figma JSON", "url": res(f"{folder}/{stem}.json")},
    ]
    return {
        "label": SUFFIX_LABEL[suffix_of(stem)],
        "image_url": res(f"{folder}/{stem}.png"),
        "links": links,
    }


def build_canvas() -> dict[str, dict]:
    out: dict[str, dict] = {}

    # Replication: one reference design per task.
    for row in fetch_jsonl("replication_gt/metadata.jsonl"):
        stem = Path(row["file_name"]).stem
        tid = f"replication/{stem}"
        out[tid] = {
            "design_file_url": row.get("url", ""),
            "artifacts": [artifact_entry("replication_gt", stem, row.get("url", ""))],
        }

    # Modification: base/target (+ component in task-2), grouped by logical id.
    for group in ("task-1", "task-2", "task-3"):
        folder = f"modification_gt/{group}"
        grouped: dict[str, dict] = {}
        for row in fetch_jsonl(f"{folder}/metadata.jsonl"):
            stem = Path(row["file_name"]).stem
            lid = logical_id(stem)
            g = grouped.setdefault(lid, {"url": row.get("url", ""), "stems": []})
            g["stems"].append(stem)
        for lid, g in grouped.items():
            tid = f"modification/{group}/{lid}"
            order = {"base": 0, "component": 1, "target": 2, "": 3}
            stems = sorted(set(g["stems"]), key=lambda s: order[suffix_of(s)])
            out[tid] = {
                "design_file_url": g["url"],
                "artifacts": [artifact_entry(folder, s, g["url"]) for s in stems],
            }
    return out


def build_guide(tasks: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for t in tasks:
        if t["benchmark"] != "GUIDE":
            continue
        links = []
        asset = t.get("task_asset_path")
        if asset:
            links.append({"text": "Task brief (gated) ↗", "url": GUIDE_BLOB + quote(asset, safe="/")})
        links.append({"text": "Paper – task list (Table B2) ↗", "url": GUIDE_PAPER})
        links.append({"text": "Project page ↗", "url": GUIDE_PROJECT})
        video = next((GUIDE_CATEGORY_VIDEO[s] for s in t.get("software", []) if s in GUIDE_CATEGORY_VIDEO), None)
        if video:
            links.append({"text": "Sample session video ↗", "url": GUIDE_VID + video})
        out[t["task_id"]] = {
            "artifacts": [
                {
                    "label": "Task context (screen recording)",
                    "note": (
                        "GUIDE's artifact is a screen recording of a novice user performing this task, "
                        "with think-aloud narration and behavior/intent annotations. Full per-task recordings "
                        "and the task brief require accepting the GuideBench dataset access conditions on "
                        "Hugging Face; the sample session video shows a representative session in the same app family."
                        if video else
                        "GUIDE's artifact is a screen recording of a novice user performing this task, with "
                        "think-aloud narration and behavior/intent annotations. Full per-task recordings and the "
                        "task brief require accepting the GuideBench dataset access conditions on Hugging Face."
                    ),
                    "links": links,
                }
            ]
        }
    return out


def _paginate(url: str) -> list[dict]:
    rows: list[dict] = []
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=60) as r:
            rows.extend(json.loads(r.read().decode()))
            nxt = None
            for part in r.headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    nxt = part[part.find("<") + 1:part.find(">")]
            url = nxt
    return rows


def build_psbench() -> dict[str, dict]:
    """Input (start) and reference output (end) images per task, from the file tree."""
    files = [x["path"] for x in _paginate(PSBENCH_API) if x.get("type") == "file"]
    starts = {p.split("/")[0]: p for p in files if "_start." in p}
    ends = {p.split("/")[0]: p for p in files if "_end." in p}
    out: dict[str, dict] = {}
    for tid in starts:
        arts = []
        if tid in starts:
            arts.append({
                "label": "Input (starting image)",
                "image_url": PSBENCH_RES + quote(starts[tid], safe="/"),
                "links": [{"text": "Download input ↓", "url": PSBENCH_RES + quote(starts[tid], safe="/")}],
            })
        if tid in ends:
            arts.append({
                "label": "Reference output (goal)",
                "image_url": PSBENCH_RES + quote(ends[tid], safe="/"),
                "links": [{"text": "Download reference ↓", "url": PSBENCH_RES + quote(ends[tid], safe="/")}],
            })
        rubric = f"{tid}/{tid}_rubric.json"
        if rubric in files:
            arts[-1]["links"].append({"text": "View rubric ↗", "url": PSBENCH_RES + quote(rubric, safe="/")})
        out[tid] = {"artifacts": arts}
    return out


def build_autocad(tasks: list[dict]) -> dict[str, dict]:
    """Reference drawing (rendered PNG) + gold DWG per task, from catalog fields."""
    out: dict[str, dict] = {}
    for t in tasks:
        if t["benchmark"] != "AutoCAD Bench":
            continue
        ref_url = t.get("reference_image_url")
        if not ref_url:
            continue
        links = [{"text": "View reference PNG ↗", "url": ref_url}]
        gold = t.get("gold_file")
        ref_rel = t.get("reference_image")
        if gold and ref_rel and ref_url.endswith(ref_rel):
            base = ref_url[: -len(ref_rel)]
            links.append({"text": "Download gold DWG ↓", "url": base + quote(gold, safe="/")})
        out[t["task_id"]] = {
            "artifacts": [
                {
                    "label": "Reference drawing (goal)",
                    "image_url": ref_url,
                    "note": t.get("notes") or "Recreate this reference drawing in AutoCAD; the gold DWG is the exact expected result.",
                    "links": links,
                }
            ]
        }
    return out


def main() -> None:
    canvas = build_canvas()
    print(f"CANVAS tasks with artifacts: {len(canvas)}")
    psbench = build_psbench()
    print(f"PSBench tasks with artifacts: {len(psbench)}")

    for catalog_path in CATALOGS:
        catalog = json.loads(catalog_path.read_text())
        guide = build_guide(catalog["tasks"])
        autocad = build_autocad(catalog["tasks"])
        counts = {"CANVAS": 0, "GUIDE": 0, "PSBench": 0, "AutoCAD Bench": 0}
        for t in catalog["tasks"]:
            b = t["benchmark"]
            src = (
                canvas if b == "CANVAS"
                else guide if b == "GUIDE"
                else psbench if b == "PSBench"
                else autocad if b == "AutoCAD Bench"
                else None
            )
            if src is not None and t["task_id"] in src:
                t.update(src[t["task_id"]])
                counts[b] += 1
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
        print(f"  {catalog_path.name}: " + ", ".join(f"{v} {k}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
