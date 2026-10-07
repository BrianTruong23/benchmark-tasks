# Benchmark task catalog

`benchmark_tasks.json` is a normalized catalog of public tasks from:

- DeskCraft
- PPT-Eval
- PSBench
- CADWorld
- AutoCAD Bench
- ParaGUIBench
- GUIDE
- ScratchWorld
- CANVAS
- OSWorld

Each row contains the benchmark, canonical task ID, normalized software name(s), task name, and task type. The catalog includes both CADWorld and AutoCAD Bench because they target different applications (FreeCAD and Autodesk AutoCAD) and were presented as alternatives in the request.

## Scope decisions

- **DeskCraft:** all 538 official tasks are included: 386 standard and 152 interactive. Interactive task names concatenate the official phases so no later requirement is lost.
- **CANVAS:** 598 logical tasks are included: 298 replication and 300 modification. The modification metadata repeats each task for its base, target, and sometimes component artifacts; those rows are deduplicated by logical sample ID.
- **OSWorld:** the complete 369-task `test_all` suite is included. This includes 8 Google Drive-dependent tasks; the commonly used no-GDrive subset has 361 tasks.
- **AutoCAD Bench:** its 50 tasks are reference-image-defined and share prompts by drawing type. The task names therefore use the official public description plus level, type, and stable task ID.
- **ParaGUIBench:** all 233 canonical tasks are included from the official `benchmark/tasks` definitions. This covers six categories across information retrieval and operation/manipulation, using the official instruction or fixture-backed instruction template as the task name.
- **GUIDE:** all 40 open-ended software task conditions are included (20 unique goals, each used in two paired applications). GUIDE's roughly 4,100 segment-level examples evaluate behavior-state detection, intent prediction, and help prediction; they are summarized in benchmark metadata rather than expanded as duplicate catalog rows.
- **ScratchWorld:** all 83 official tasks are included: 20 Create, 20 Debug, 18 Extend, and 25 Compute. ScratchWorld does not publish per-task difficulty, so the catalog adds explicitly marked derived Easy, Medium, and Hard labels based on behavioral interaction, debugging scope, control-flow depth, and algorithmic complexity.

Only task metadata is stored here—no benchmark harnesses, application installers, videos, reference images, or other large assets.

## Dataset viewer

The static viewer in `dist/` supports full-text search, benchmark/software/task-type filters, sorting, pagination, task JSON copying, and filtered JSON exports. It is published privately with OpenAI Sites and can also be run locally:

Shared-canvas candidates are curated separately in `shared_canvas_candidates.json`. A candidate must naturally split into concurrent regions, layers, tracks, views, or components of one artifact while still requiring global visual or temporal coherence. The dedicated **Shared-canvas** tab provides benchmark, difficulty, software, and decision filters; each candidate can be approved or rejected. Tasks with Chinese-language instructions are excluded from this approval queue. Each candidate includes a concrete saved-note draft with explicit `Agent A`, `Agent B`, and additional region assignments plus a final coordination checklist. Approved tasks are added to the existing browser-local saved collection and included in saved-task exports, while rejected decisions are also retained locally for later reconsideration.

```bash
python3 -m http.server 8000 --directory dist
```

Then open `http://localhost:8000`.

## Rebuild

Clone the canonical upstream repositories and datasets into a common directory using the directory names expected by `scripts/build_catalog.py`, then run:

```bash
python3 scripts/build_catalog.py \
  --upstream-root /path/to/benchmark-upstreams \
  --output benchmark_tasks.json
```

The exact upstream commit used for each benchmark is recorded in the generated JSON.
