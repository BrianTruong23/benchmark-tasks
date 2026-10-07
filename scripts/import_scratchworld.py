#!/usr/bin/env python3
"""Add or refresh ScratchWorld in an existing generated task catalog."""

import argparse
import json
from pathlib import Path

from build_catalog import collect_scratchworld


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("benchmark_tasks.json"))
    parser.add_argument("--upstream-root", type=Path, required=True)
    args = parser.parse_args()

    metadata, rows = collect_scratchworld(args.upstream_root)
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    catalog["benchmarks"] = [
        item for item in catalog["benchmarks"] if item["benchmark"] != "ScratchWorld"
    ]
    catalog["tasks"] = [
        item for item in catalog["tasks"] if item["benchmark"] != "ScratchWorld"
    ]
    catalog["benchmarks"].append(metadata)
    catalog["tasks"].extend(rows)
    catalog["benchmark_count"] = len(catalog["benchmarks"])
    catalog["task_count"] = len(catalog["tasks"])
    catalog["generated_on"] = "2026-10-07"
    catalog.setdefault("field_notes", {})["level"] = (
        "Difficulty when supplied by the benchmark or explicitly marked as "
        "catalog-derived in difficulty_source."
    )
    args.catalog.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
