#!/usr/bin/env python3
"""Add or refresh ParaGUIBench in an existing generated task catalog."""

import argparse
import json
from pathlib import Path

from build_catalog import collect_paraguibench


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=Path("benchmark_tasks.json"))
    args = parser.parse_args()

    metadata, rows = collect_paraguibench(args.repo.parent)
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    catalog["benchmarks"] = [
        item for item in catalog["benchmarks"] if item["benchmark"] != "ParaGUIBench"
    ]
    catalog["tasks"] = [
        item for item in catalog["tasks"] if item["benchmark"] != "ParaGUIBench"
    ]
    catalog["benchmarks"].append(metadata)
    catalog["tasks"].extend(rows)
    catalog["benchmark_count"] = len(catalog["benchmarks"])
    catalog["task_count"] = len(catalog["tasks"])
    args.catalog.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
