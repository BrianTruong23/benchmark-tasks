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
from urllib.parse import quote


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


def _ppteval_deck_urls(repo: Path) -> dict[str, str]:
    """Map a normalized deck name to its archive.org download URL."""
    from urllib.parse import quote, unquote

    def key(name: str) -> str:
        name = unquote(name).strip()
        while name.lower().endswith(".pptx"):
            name = name[: -len(".pptx")]
        return name

    def normalize(url: str) -> str:
        head, _, path = url.partition("://")
        host, slash, rest = path.partition("/")
        return f"{head}://{host}{slash}{quote(unquote(rest), safe='/')}"

    manifest = (repo / "data" / "files" / "PowerPoint" / "files.txt").read_text()
    urls = {}
    for line in manifest.splitlines():
        line = line.strip()
        if line:
            urls[key(line.rsplit("/", 1)[-1])] = normalize(line)
    return urls


def collect_ppteval(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "ppteval"
    registry = load_json(repo / "task_registry" / "tasks.json")
    rev = revision(repo)
    gh_base = f"https://github.com/microsoft/ppteval/blob/{rev}/"
    deck_urls = _ppteval_deck_urls(repo)

    def deck_key(name: str) -> str:
        name = name.strip()
        while name.lower().endswith(".pptx"):
            name = name[: -len(".pptx")]
        return name

    rows = []
    for task_id, data in sorted(registry.items()):
        row = task(
            "PPT-Eval",
            task_id,
            ["Microsoft PowerPoint Online"],
            data["goal"],
            f"{data.get('misc', {}).get('difficulty', 'unknown').lower()} task",
        )
        deck_file = Path(data["file_path"]).name
        row["resource_url"] = deck_urls[deck_key(deck_file)]
        row["rubric_url"] = gh_base + quote(data["rubric_path"], safe="/")
        row["deck_name"] = Path(data["file_path"]).stem
        rows.append(row)
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
    descriptive_names = {
        "task-001": "Symmetric two-hole bracket with central rounded slot",
    }
    rows: list[dict[str, Any]] = []
    for data in manifest:
        drawing_type = "3D modeling" if data.get("drawing_type", "2d") == "3d" else "2D recreation"
        description = descriptive_names.get(
            data["task_id"],
            f"{data['level'].title()} AutoCAD {drawing_type} task",
        )
        name = f"{data['task_id']} — {description}"
        rows.append(
            task(
                "AutoCAD Bench",
                data["task_id"],
                ["Autodesk AutoCAD"],
                name,
                data.get("drawing_type", "2d"),
            )
        )
        rows[-1].update(
            {
                "level": data["level"],
                "split": data.get("split"),
                "units": data.get("units"),
                "time_limit_s": data.get("time_limit_s"),
                "max_actions": data.get("max_actions"),
                "notes": data.get("notes"),
                "reference_image": data.get("image_path"),
                "gold_file": data.get("gold_path"),
                "reference_image_url": f"https://raw.githubusercontent.com/markov-lab/autocad-bench/{revision(repo)}/{data['image_path']}",
            }
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


def paraguibench_software(task_id: str) -> list[str]:
    if task_id.startswith((
        "InformationRetrieval-WebSearch",
        "InformationRetrieval-VisualSearch",
        "Operation-OnlineShopping",
        "Operation-WebOperate",
    )):
        return ["Google Chrome"]
    if "ReadonlyPPT" in task_id or "BatchOperationPPT" in task_id:
        return ["LibreOffice Impress"]
    if "ReadonlyWord" in task_id or "BatchOperationWord" in task_id:
        return ["LibreOffice Writer"]
    if "BatchOperationExcel" in task_id:
        return ["LibreOffice Calc"]
    if "CombinationDocs" in task_id:
        return ["LibreOffice Writer", "LibreOffice Calc", "LibreOffice Impress"]
    if "SearchAndWrite" in task_id:
        return ["Google Chrome", "LibreOffice"]
    if "Settings" in task_id:
        return ["Ubuntu Desktop"]
    return ["Ubuntu Desktop", "LibreOffice"]


def collect_paraguibench(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "ParaGUIBench"
    rows: list[dict[str, Any]] = []
    for path in sorted((repo / "benchmark" / "tasks").glob("*.json")):
        data = load_json(path)
        instruction = data.get("instruction") or data.get("instruction_template")
        if not instruction:
            raise ValueError(f"ParaGUIBench task has no instruction: {path}")
        row = task(
            "ParaGUIBench",
            data["task_id"],
            paraguibench_software(data["task_id"]),
            instruction,
            data.get("task_tag") or data.get("task_type") or "unknown",
        )
        row.update(
            {
                "task_uid": data.get("task_uid"),
                "task_source": data.get("task_source"),
                "canonical_task_path": str(path.relative_to(repo)),
            }
        )
        rows.append(row)
    assert len(rows) == 233
    return (
        {
            "benchmark": "ParaGUIBench",
            "source_url": "https://github.com/pkgunboat/ParaGUIBench",
            "paper_url": "https://arxiv.org/abs/2607.22689",
            "source_revision": revision(repo),
            "task_count": len(rows),
            "scope": "All 233 canonical tasks in benchmark/tasks across six categories and two domains.",
            "task_name_basis": "Official canonical instruction, or the official instruction template for fixture-backed checkout tasks.",
        },
        rows,
    )


def collect_guide(_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    categories = (
        (
            "photo-editing",
            (("Photoshop", "Adobe Photoshop"), ("GIMP", "GIMP")),
            (
                "Create a composite from two images.",
                "Create a bakery logo with a warm, friendly identity.",
                "Replace a photo's background with a custom-designed pattern.",
                "Design a movie poster.",
            ),
        ),
        (
            "graphic-design",
            (("Figma", "Figma"), ("Canva", "Canva")),
            (
                "Design a mobile sign-up screen for a fictional app.",
                "Design a custom 404 error page with a visual and animated element.",
                "Design compact profile cards that display personal user details.",
                "Design an event poster for a music festival.",
            ),
        ),
        (
            "presentation-design",
            (("PowerPoint", "Microsoft PowerPoint"), ("Google_Slides", "Google Slides")),
            (
                "Create a product pitch deck that highlights the MacBook's key features.",
                "Create an interactive timeline presenting a company's history.",
                "Create a 5-slide nature-themed shape-masked photo scrapbook.",
                "Create a quiz deck with 3 multiple-choice questions.",
            ),
        ),
        (
            "video-editing",
            (("Premiere_Pro", "Adobe Premiere Pro"), ("CapCut", "CapCut")),
            (
                "Edit a short interview to improve clarity and engagement.",
                "Design a creative intro using animated text.",
                "Edit a short instructional video to clearly guide a process.",
                "Transform a long video into a highly engaging short-form clip.",
            ),
        ),
        (
            "data-analysis",
            (("Excel", "Microsoft Excel"), ("Google_Sheets", "Google Sheets")),
            (
                "Design a Gantt chart for a mini project.",
                "Summarize and visualize responses from a survey.",
                "Visualize student performance across subjects.",
                "Summarize and visualize product sales by category or region.",
            ),
        ),
    )
    rows: list[dict[str, Any]] = []
    task_slots = (("A", 1), ("A", 2), ("B", 1), ("B", 2))
    for category, applications, descriptions in categories:
        for app_id, software in applications:
            for (group, number), description in zip(task_slots, descriptions):
                task_id = f"{app_id}_{group}_Task_{number}"
                row = task("GUIDE", task_id, [software], description, category)
                row.update(
                    {
                        "group": group,
                        "task_number": number,
                        "category": category,
                        "task_asset_path": f"tasks/{task_id}.md",
                        "evaluation_tracks": [
                            "behavior-state-detection",
                            "intent-prediction",
                            "help-prediction",
                        ],
                    }
                )
                rows.append(row)
    assert len(rows) == 40
    return (
        {
            "benchmark": "GUIDE",
            "source_url": "https://huggingface.co/datasets/kixlab/GuideBench",
            "project_url": "https://guide-bench.github.io/",
            "paper_url": "https://arxiv.org/abs/2603.25864",
            "source_revision": "783caa868dc3a929ef99702731a1e0b27add48f1",
            "task_count": len(rows),
            "scope": "All 40 open-ended software task conditions (20 unique goals across paired applications) underlying 120 demonstrations. Segment-level evaluation sets are recorded in metadata rather than expanded into catalog rows.",
            "task_name_basis": "Official public task descriptions in Table B2 of the paper; full task Markdown and annotations require accepting the dataset access conditions.",
            "evaluation_sample_counts": {
                "behavior_state_detection": 1800,
                "intent_prediction": 1300,
                "help_prediction": 1000,
            },
        },
        rows,
    )


SCRATCHWORLD_EASY = {
    # Create: one narrow event/response or presentation behavior.
    "ask_and_echo",
    "backdrop_cycler",
    "hide_show_sprite",
    "keyboard_ball",
    "mouse_follower",
    "say_hello",
    "size_pulse",
    # Debug: a localized event, visibility, position, or motion defect.
    "coordinate_reporter_broadcast_missing_error",
    "coordinate_reporter_button_visibility_error",
    "maze_starter_movement_mapping_error",
    "maze_starter_start_position_error",
    "party_costume",
    "pong_starter_pong_not_moving_error",
    # Compute: direct formulas, comparisons, scans, or simple transformations.
    "celsius_to_fahrenheit",
    "check_equality",
    "count_even_digits",
    "count_vowels",
    "even_or_double",
    "largest_digit_in_number",
    "perfect_square_check",
    "reverse_string",
    "sum_of_list",
}

SCRATCHWORLD_HARD = {
    # Create: several interacting scripts, state transitions, or clones.
    "gravity_ball",
    "multi_scene_story",
    "random_walk_explorer",
    "space_shooter_clone",
    # Debug: defects involving collision, repeated state, or interacting systems.
    "math_game_inadequate_repeat_error",
    "math_game_invalid_randomness_error",
    "maze_starter_overshoot_collision_error",
    "maze_starter_wall_collision_detection_error",
    "simple_circuit_switch_immediate_turn_off_error",
    # Compute: nested iteration or comparatively involved algorithms.
    "find_largest_prime_factor",
    "perfect_number_check",
    "sort_numbers_in_list",
    # Extend: multi-system features, clones, progression, or sustained state.
    "make_it_fly_endless_scrolling_and_scoring_modify",
    "make_it_fly_gravity_flap_mode_modify",
    "make_it_fly_power_ups_modify",
    "maze_starter_footstep_trail_with_fading_clones_modify",
    "maze_starter_multi_level_maze_progression_modify",
    "maze_starter_patrolling_obstacles_modify",
    "maze_starter_sprint_and_stamina_mechanic_modify",
    "maze_starter_timed_maze_challenge_modify",
    "mouse_trail_glide_to_goal_modify",
    "simple_circuit_auto_snap_connectors_modify",
    "simple_circuit_timed_assembly_challenge_modify",
}


def scratchworld_difficulty(name: str) -> tuple[str, str]:
    """Return a transparent catalog-derived level, not an upstream label."""
    if name in SCRATCHWORLD_EASY:
        return (
            "easy",
            "Narrow behavior, localized defect, or direct calculation with limited control-flow depth.",
        )
    if name in SCRATCHWORLD_HARD:
        return (
            "hard",
            "Multiple interacting behaviors, sustained state or clones, deeper debugging scope, or a comparatively involved algorithm.",
        )
    return (
        "medium",
        "Several coordinated steps, non-trivial control flow, or diagnosis within an existing project.",
    )


def collect_scratchworld(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = root / "ScratchWorld"
    manifest = load_json(repo / "tasks" / "all_tasks.json")
    rev = revision(repo)
    rows: list[dict[str, Any]] = []
    category_counts: dict[str, int] = {}
    for category in ("create", "debug", "extend", "compute"):
        files = manifest[category]
        category_counts[category] = len(files)
        for file_name in files:
            path = repo / "tasks" / category / file_name
            data = load_json(path)
            assert data["type"] == category
            level, rationale = scratchworld_difficulty(data["name"])
            row = task(
                "ScratchWorld",
                f"{category}/{data['name']}",
                ["MIT Scratch"],
                data["instruction"],
                category,
            )
            row.update(
                {
                    "level": level,
                    "difficulty_source": "catalog-derived",
                    "difficulty_rationale": rationale,
                    "description": clean_text(data.get("description", "")),
                    "initial_project": data.get("initial_project"),
                    "evaluation_timeout_s": data.get("evaluation", {}).get("timeout"),
                    "evaluation_description": clean_text(
                        data.get("evaluation", {}).get("description", "")
                    ),
                    "canonical_task_path": str(path.relative_to(repo)),
                    "task_definition_url": (
                        "https://github.com/astarforbae/ScratchWorld/blob/"
                        f"{rev}/{quote(str(path.relative_to(repo)), safe='/')}"
                    ),
                }
            )
            rows.append(row)
    assert category_counts == {"create": 20, "debug": 20, "extend": 18, "compute": 25}
    assert len(rows) == 83
    assert {row["level"] for row in rows} == {"easy", "medium", "hard"}
    return (
        {
            "benchmark": "ScratchWorld",
            "source_url": "https://github.com/astarforbae/ScratchWorld",
            "paper_url": "https://arxiv.org/abs/2602.10814",
            "source_revision": rev,
            "task_count": len(rows),
            "scope": "All 83 curated tasks in the official manifest: 20 Create, 20 Debug, 18 Extend, and 25 Compute.",
            "task_name_basis": "Official task instruction.",
            "difficulty_basis": "Catalog-derived Easy, Medium, and Hard labels based on behavioral interaction, debugging scope, control-flow depth, and algorithmic complexity; ScratchWorld does not publish official per-task difficulty labels.",
            "interaction_modes": ["primitive", "composite"],
            "category_counts": category_counts,
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
        collect_paraguibench,
        collect_guide,
        collect_scratchworld,
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
            "level": "Difficulty when supplied by the benchmark or explicitly marked as catalog-derived in difficulty_source.",
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
