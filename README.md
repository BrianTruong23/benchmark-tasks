# Benchmark task catalog

`benchmark_tasks.json` is a normalized catalog of public tasks from:

- DeskCraft
- PPT-Eval
- PSBench
- CADWorld
- AutoCAD Bench
- CANVAS
- OSWorld

Each row contains the benchmark, canonical task ID, normalized software name(s), task name, and task type. The catalog includes both CADWorld and AutoCAD Bench because they target different applications (FreeCAD and Autodesk AutoCAD) and were presented as alternatives in the request.

## Scope decisions

- **DeskCraft:** all 538 official tasks are included: 386 standard and 152 interactive. Interactive task names concatenate the official phases so no later requirement is lost.
- **CANVAS:** 598 logical tasks are included: 298 replication and 300 modification. The modification metadata repeats each task for its base, target, and sometimes component artifacts; those rows are deduplicated by logical sample ID.
- **OSWorld:** the complete 369-task `test_all` suite is included. This includes 8 Google Drive-dependent tasks; the commonly used no-GDrive subset has 361 tasks.
- **AutoCAD Bench:** its 50 tasks are reference-image-defined and share prompts by drawing type. The task names therefore use the official public description plus level, type, and stable task ID.

Only task metadata is stored here—no benchmark harnesses, application installers, videos, reference images, or other large assets.

## Rebuild

Clone the canonical upstream repositories and datasets into a common directory using the directory names expected by `scripts/build_catalog.py`, then run:

```bash
python3 scripts/build_catalog.py \
  --upstream-root /path/to/benchmark-upstreams \
  --output benchmark_tasks.json
```

The exact upstream commit used for each benchmark is recorded in the generated JSON.
