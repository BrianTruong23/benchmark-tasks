#!/usr/bin/env python3
"""Build the normalized benchmark task catalog from canonical upstream checkouts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


APP_NAMES = {
    "audacity": "Audacity",
    "blender": "Blender",
    "browser": "Google Chrome",
    "calc": "LibreOffice Calc",
    "chrome": "Google Chrome",
    "gimp": "GIMP",
    "image": "Image Viewer",
    "inkscape": "Inkscape",
    "kdenlive": "Kdenlive",
    "libreoffice": "LibreOffice",
    "libreoffice calc": "LibreOffice Calc",
    "libreoffice_calc": "LibreOffice Calc",
    "libreoffice_impress": "LibreOffice Impress",
    "libreoffice_writer": "LibreOffice Writer",
    "os": "Ubuntu Desktop",
    "pdf": "PDF Viewer",
    "picard": "MusicBrainz Picard",
    "terminal": "GNOME Terminal",
    "thunderbird": "Mozilla Thunderbird",
    "ubuntu_media_player": "VLC media player",
    "vlc": "VLC media player",
    "vs_code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "writer": "LibreOffice Writer",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def revision(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def clean_text(text: str) -> str:
    return " ".join(text.split())


def normalize_apps(apps: Iterable[str], fallback: str | None = None) -> list[str]:
    values = list(apps)
    if not values and fallback:
        values = [fallback]
    normalized: list[str] = []
    for app in values:
        key = app.strip()
        name = APP_NAMES.get(key, APP_NAMES.get(key.lower(), key.replace("_", " ").title()))
        if name not in normalized:
            normalized.append(name)
    return normalized


def task(
    benchmark: str,
    task_id: str,
    software: Iterable[str],
    task_name: str,
    task_type: str,
) -> dict[str, Any]:
    return {
        "benchmark": benchmark,
        "task_id": task_id,
        "software": list(software),
        "task_name": clean_text(task_name),
        "task_type": task_type,
    }


def collect_deskcraft(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "DeskCraft"
    examples = repo / "evaluation_examples" / "examples_per_task"
    task_paths = examples.glob("*/*/task.json")
    by_directory = {
        path.parent.name.rstrip("."): load_json(path)
        for path in task_paths
    }
    rows: list[dict[str, Any]] = []
    suite_counts: dict[str, int] = {}
    for manifest_name, kind in (
        ("standard_task.json", "standard"),
        ("interactive_task.json", "interactive"),
    ):
        manifest = load_json(repo / "evaluation_examples" / manifest_name)
        suite_counts[kind] = sum(len(ids) for ids in manifest.values())
        for domain, task_ids in manifest.items():
            for task_id in task_ids:
                data = by_directory[task_id]
                if kind == "interactive":
                    phases = [
                        f"Phase {phase['phase_id']}: {phase['instruction']}"
                        for phase in data["phases"]
                    ]
                    name = " | ".join(phases)
                else:
                    name = data["instruction"]
                related_apps = data.get("related_apps", [])
                if not related_apps and domain == "multi_app":
                    # DeskCraft's interactive c2w/w2c tasks omit related_apps.
                    # Their IDs and artifacts explicitly encode Writer/Calc flow.
                    related_apps = (
                        ["libreoffice_calc", "libreoffice_writer"]
                        if "_c2w_" in task_id
                        else ["libreoffice_writer", "libreoffice_calc"]
                    )
                rows.append(
                    task(
                        "DeskCraft",
                        task_id,
                        normalize_apps(related_apps, data.get("snapshot", domain)),
                        name,
                        kind,
                    )
                )
    assert suite_counts == {"standard": 386, "interactive": 152}
    assert len(rows) == 538
    return (
        {
            "benchmark": "DeskCraft",
            "source_url": "https://github.com/mrwwk/DeskCraft",
            "paper_url": "https://arxiv.org/abs/2606.03103",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All 386 standard and 152 interactive tasks in the official manifests.",
            "task_name_basis": "Official instruction; interactive tasks concatenate all official phases.",
        },
        rows,
    )


def collect_ppteval(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "ppteval"
    registry = load_json(repo / "task_registry" / "tasks.json")
    rows = [
        task(
            "PPT-Eval",
            task_id,
            ["Microsoft PowerPoint Online"],
            data["goal"],
            f"{data.get('misc', {}).get('difficulty', 'unknown').lower()} task",
        )
        for task_id, data in sorted(registry.items())
    ]
    assert len(rows) == 120
    return (
        {
            "benchmark": "PPT-Eval",
            "source_url": "https://github.com/microsoft/ppteval",
            "paper_url": "https://arxiv.org/abs/2606.31154",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All tasks in the official task registry.",
            "task_name_basis": "Official task goal.",
        },
        rows,
    )


def collect_psbench(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "PSBench-data"
    paths = sorted(
        path
        for path in repo.glob("[0-9][0-9][0-9]/*.json")
        if not path.name.endswith("_rubric.json")
    )
    rows: list[dict[str, Any]] = []
    for path in paths:
        data = load_json(path)
        rows.append(
            task(
                "PSBench",
                data["id"],
                ["Adobe Photoshop"],
                data["instruction"],
                data.get("type", "image editing"),
            )
        )
    assert len(rows) == 600
    return (
        {
            "benchmark": "PSBench",
            "source_url": "https://huggingface.co/datasets/zyn1216/PSBench",
            "code_url": "https://github.com/zyn1216/PSBench",
            "paper_url": "https://openreview.net/forum?id=O93cZGxYB1",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All 600 task JSON files in the official Hugging Face dataset.",
            "task_name_basis": "Official instruction.",
        },
        rows,
    )


def canvas_logical_id(file_name: str) -> str:
    stem = Path(file_name).stem
    return re.sub(r"-(?:base|target|component)$", "", stem)


def collect_canvas(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "CANVAS-data"
    rows: list[dict[str, Any]] = []
    replication = load_jsonl(repo / "replication_gt" / "metadata.jsonl")
    for data in replication:
        task_id = Path(data["file_name"]).stem
        rows.append(
            task(
                "CANVAS",
                f"replication/{task_id}",
                ["Figma"],
                f"Replicate the provided reference UI design ({task_id}).",
                "replication",
            )
        )

    modification_counts: dict[str, int] = {}
    for group in ("task-1", "task-2", "task-3"):
        artifacts = load_jsonl(repo / "modification_gt" / group / "metadata.jsonl")
        logical: dict[str, dict[str, Any]] = {}
        for data in artifacts:
            logical_id = canvas_logical_id(data["file_name"])
            previous = logical.setdefault(logical_id, data)
            assert previous["instruction"] == data["instruction"]
        modification_counts[group] = len(logical)
        for logical_id, data in sorted(logical.items()):
            subtype = data.get("sub_task_type", group)
            rows.append(
                task(
                    "CANVAS",
                    f"modification/{group}/{logical_id}",
                    ["Figma"],
                    data["instruction"],
                    f"modification/{subtype}",
                )
            )
    assert len(replication) == 298
    assert modification_counts == {"task-1": 100, "task-2": 100, "task-3": 100}
    assert len(rows) == 598
    return (
        {
            "benchmark": "CANVAS",
            "source_url": "https://huggingface.co/datasets/seooyxx/canvas",
            "code_url": "https://github.com/kixlab/CANVAS",
            "paper_url": "https://arxiv.org/abs/2511.20737",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All 298 replication and 300 logical modification tasks. Repeated base/target/component artifact rows are deduplicated.",
            "task_name_basis": "Official modification instruction; replication names are derived from the official sample ID because the task is image-specified.",
        },
        rows,
    )


def collect_osworld(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "OSWorld"
    base = repo / "evaluation_examples"
    manifest = load_json(base / "test_all.json")
    examples: dict[str, dict[str, Any]] = {}
    for path in (base / "examples").glob("*/*.json"):
        data = load_json(path)
        examples[data["id"]] = data
    rows: list[dict[str, Any]] = []
    for domain, task_ids in manifest.items():
        for task_id in task_ids:
            data = examples[task_id]
            rows.append(
                task(
                    "OSWorld",
                    task_id,
                    normalize_apps(data.get("related_apps", []), data.get("snapshot", domain)),
                    data["instruction"],
                    domain,
                )
            )
    assert len(rows) == 369
    return (
        {
            "benchmark": "OSWorld",
            "source_url": "https://github.com/xlang-ai/OSWorld",
            "paper_url": "https://arxiv.org/abs/2404.07972",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All 369 tasks in evaluation_examples/test_all.json, including the 8 Google Drive-dependent tasks.",
            "task_name_basis": "Official instruction.",
        },
        rows,
    )


def collect_cadworld(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "CADWORLD"
    base = repo / "evaluation_examples"
    manifest = load_json(base / "test_all.json")
    examples: dict[str, dict[str, Any]] = {}
    for path in (base / "examples").glob("*/*.json"):
        data = load_json(path)
        examples[data["id"]] = data
    rows: list[dict[str, Any]] = []
    for category, task_ids in manifest.items():
        for task_id in task_ids:
            data = examples[task_id]
            rows.append(
                task(
                    "CADWorld",
                    task_id,
                    ["FreeCAD"],
                    data["instruction"],
                    category,
                )
            )
    assert len(rows) == 200
    return (
        {
            "benchmark": "CADWorld",
            "source_url": "https://github.com/Zdong104/CADWORLD",
            "paper_url": "https://arxiv.org/abs/2609.16251",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All 200 tasks in the official test_all manifest.",
            "task_name_basis": "Official instruction.",
        },
        rows,
    )


def collect_autocad_bench(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "autocad-bench"
    manifest = load_jsonl(repo / "tasks" / "manifest.jsonl")
    rows: list[dict[str, Any]] = []
    for data in manifest:
        drawing_type = "3D modeling" if data.get("drawing_type", "2d") == "3d" else "2D recreation"
        name = f"{data['task_id']} — {data['level'].title()} AutoCAD {drawing_type} task"
        rows.append(
            task(
                "AutoCAD Bench",
                data["task_id"],
                ["Autodesk AutoCAD"],
                name,
                data.get("drawing_type", "2d"),
            )
        )
    assert len(rows) == 50
    return (
        {
            "benchmark": "AutoCAD Bench",
            "source_url": "https://github.com/markov-lab/autocad-bench",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All 50 tasks in the canonical manifest (21 2D and 29 3D). Included alongside CADWorld because the requested list named them as alternatives.",
            "task_name_basis": "Derived from the official public task description, level, drawing type, and ID; individual tasks are specified by reference images rather than distinct text prompts.",
        },
        rows,
    )


def build(root: Path) -> dict[str, Any]:
    collectors = (
        collect_deskcraft,
        collect_ppteval,
        collect_psbench,
        collect_cadworld,
        collect_autocad_bench,
        collect_canvas,
        collect_osworld,
    )
    benchmarks: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for collector in collectors:
        metadata, rows = collector(root)
        benchmarks.append(metadata)
        tasks.extend(rows)
    counts = Counter(row["benchmark"] for row in tasks)
    assert all(counts[item["benchmark"]] == item["task_count"] for item in benchmarks)
    return {
        "schema_version": "1.0",
        "generated_on": "2026-10-06",
        "description": "Normalized public task catalog with the primary software and task name for each benchmark task.",
        "field_notes": {
            "software": "A normalized array because some tasks span multiple applications.",
            "task_name": "The official instruction/goal or the closest public task descriptor; see each benchmark's task_name_basis.",
        },
        "benchmark_count": len(benchmarks),
        "task_count": len(tasks),
        "benchmarks": benchmarks,
        "tasks": tasks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("benchmark_tasks.json"))
    args = parser.parse_args()
    catalog = build(args.upstream_root)
    args.output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
