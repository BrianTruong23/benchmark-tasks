import json
import pathlib
import subprocess

catalog_path = pathlib.Path("benchmark_tasks.json")
manifest_path = pathlib.Path("/tmp/autocad-bench/tasks/manifest.jsonl")
catalog = json.loads(catalog_path.read_text())
manifest = [json.loads(line) for line in manifest_path.read_text().splitlines() if line]
by_id = {item["task_id"]: item for item in manifest}
revision = subprocess.check_output(["git", "-C", "/tmp/autocad-bench", "rev-parse", "HEAD"], text=True).strip()
descriptive_names = {
    "task-001": "task-001 — Symmetric two-hole bracket with central rounded slot",
}

for row in catalog["tasks"]:
    if row["benchmark"] != "AutoCAD Bench":
        continue
    source = by_id[row["task_id"]]
    if row["task_id"] in descriptive_names:
        row["task_name"] = descriptive_names[row["task_id"]]
    row.update({
        "level": source["level"],
        "split": source.get("split"),
        "units": source.get("units"),
        "time_limit_s": source.get("time_limit_s"),
        "max_actions": source.get("max_actions"),
        "notes": source.get("notes"),
        "reference_image": source.get("image_path"),
        "gold_file": source.get("gold_path"),
        "reference_image_url": f"https://raw.githubusercontent.com/markov-lab/autocad-bench/{revision}/{source['image_path']}",
    })

catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")
