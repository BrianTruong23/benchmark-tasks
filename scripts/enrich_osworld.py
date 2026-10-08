#!/usr/bin/env python3
"""Attach each OSWorld task's initial files (the artifacts the agent opens).

Every OSWorld task config has a `download` step that fetches the starting
file(s) into the VM from the public file cache (xlangai/ubuntu_osworld_file_cache
on Hugging Face) and an `open` step. Those downloaded files are the artifacts
that set up the task context. We read each task's config JSON from the OSWorld
repo (pinned revision), extract the download files, and expose them as artifacts:
images render inline, Office documents get an in-browser viewer plus download,
everything else gets a download link.

Patches both the root and dist copies of benchmark_tasks.json in place.
"""

from __future__ import annotations

import concurrent.futures
import json
import urllib.request
from pathlib import Path
from urllib.parse import quote

REV = "b138d348256078fa634fc3b73567a7337c793e6b"
BASE = f"https://raw.githubusercontent.com/xlang-ai/OSWorld/{REV}/evaluation_examples/examples/"
OFFICE_VIEW = "https://view.officeapps.live.com/op/view.aspx?src="

CATALOGS = [
    Path("/Users/tht0021/Downloads/benchmark-tasks/benchmark_tasks.json"),
    Path("/Users/tht0021/Downloads/benchmark-tasks/dist/benchmark_tasks.json"),
]

IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
MS_OFFICE = {".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".xls"}


def fetch_config(domain: str, tid: str) -> dict | None:
    url = f"{BASE}{quote(domain, safe='')}/{quote(tid, safe='')}.json"
    for _ in range(2):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception:
            continue
    return None


def download_files(cfg: dict) -> list[tuple[str, str]]:
    files = []
    for step in cfg.get("config") or []:
        if step.get("type") == "download":
            for f in step.get("parameters", {}).get("files", []):
                if f.get("url"):
                    files.append((f["url"], f.get("path", "")))
    return files


def ext_of(name: str) -> str:
    return ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""


def build_artifacts(files: list[tuple[str, str]]) -> list[dict]:
    arts = []
    for i, (url, path) in enumerate(files):
        name = (path or url).rsplit("/", 1)[-1]
        ext = ext_of(name)
        entry = {"label": f"Starting file: {name}", "links": []}
        if ext in IMG_EXT:
            entry["image_url"] = url
            entry["links"].append({"text": "Download ↓", "url": url})
        elif ext in MS_OFFICE:
            entry["links"].append({"text": "View in browser ↗", "url": OFFICE_VIEW + quote(url, safe="")})
            entry["links"].append({"text": "Download ↓", "url": url})
        else:
            entry["links"].append({"text": "Download ↓", "url": url})
        if i == 0:
            entry["note"] = "OSWorld downloads this into the VM and opens it as the task's starting state; success is checked by an execution-based evaluator."
        arts.append(entry)
    return arts


def main() -> None:
    # Collect unique (domain, task_id) from the first catalog.
    base_catalog = json.loads(CATALOGS[0].read_text())
    osworld = [(t["task_type"], t["task_id"]) for t in base_catalog["tasks"] if t["benchmark"] == "OSWorld"]
    print(f"OSWorld tasks: {len(osworld)}")

    results: dict[str, list[dict]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        future_map = {ex.submit(fetch_config, d, tid): tid for d, tid in osworld}
        for fut in concurrent.futures.as_completed(future_map):
            tid = future_map[fut]
            cfg = fut.result()
            if not cfg:
                continue
            files = download_files(cfg)
            if files:
                results[tid] = build_artifacts(files)

    with_files = len(results)
    print(f"OSWorld tasks with downloadable artifacts: {with_files} / {len(osworld)}")

    for catalog_path in CATALOGS:
        catalog = json.loads(catalog_path.read_text())
        n = 0
        for t in catalog["tasks"]:
            if t["benchmark"] == "OSWorld" and t["task_id"] in results:
                t["artifacts"] = results[t["task_id"]]
                n += 1
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
        print(f"  {catalog_path.name}: patched {n} OSWorld tasks")


if __name__ == "__main__":
    main()
