#!/usr/bin/env python3
"""Add the ProSoftArena benchmark to the task catalog.

ProSoftArena (CVPR 2026, arXiv:2601.02399) benchmarks multimodal agents on 436
tasks across 6 disciplines, 20 subfields and 13 core professional applications,
organized by a hierarchical capability taxonomy (L1 Operation, L2 Software,
L3 Pipeline, L4 Creative; L5 Project is future work).

The official per-task files, trajectories and screenshots are NOT yet released
(the authors state "data and codes will be openly available soon" and the repo
is not public). So, as was done for CutVerse, these rows are representative
tasks: their descriptions are grounded in the paper's example tasks (Figures 2
and 4) and typical operations in each application, while the level counts and
per-level difficulty splits match Table 2 of the paper exactly, and the
per-discipline application mapping follows Section 5.1 / Figure 1. Each row
carries a benchmark-context artifact noting the data is unreleased, with links
to the paper and project page.

Filterable fields produced per task:
  software       - one of the 13 applications
  task_type      - capability level label (L1-L4) -> Task Type filter
  level          - difficulty easy/medium/hard    -> Difficulty filter
  discipline     - one of the 6 disciplines (shown in detail)
  subfield, capability_level, capability_name - shown in detail

Patches both the root and dist copies of benchmark_tasks.json in place.
"""

import json
from pathlib import Path

PAPER_URL = "https://arxiv.org/abs/2601.02399"
PROJECT_URL = "https://prosoftarena.github.io/"

CATALOGS = [
    Path("/Users/tht0021/Downloads/benchmark-tasks/benchmark_tasks.json"),
    Path("/Users/tht0021/Downloads/benchmark-tasks/dist/benchmark_tasks.json"),
]

# app -> (discipline, subfield, target task count). Counts sum to 436 and follow
# the Figure 1 discipline shares (T&E 24%, NatSci 20%, Art&Des 17%, Health 17%,
# Business 16%, Humanities 6%), split across each discipline's applications.
APPS = {
    "AutoCAD": ("Technology & Engineering", "Mechanical Engineering", 36),
    "SolidWorks": ("Technology & Engineering", "Mechanical Engineering", 36),
    "VSCode": ("Technology & Engineering", "Software Engineering", 33),
    "ANSYS": ("Natural Science", "Structural Mechanics", 22),
    "ArcGIS": ("Natural Science", "Geographic Information Science", 22),
    "MultiSim": ("Natural Science", "Electronics", 21),
    "ImageJ": ("Natural Science", "Biology", 22),
    "Adobe Photoshop": ("Art & Design", "Art", 37),
    "Adobe Illustrator": ("Art & Design", "Graphic Design", 37),
    "ChemDraw": ("Health & Medicine", "Pharmacy", 74),
    "Microsoft Excel": ("Business", "Marketing", 35),
    "R (RGui)": ("Business", "Data Analysis", 35),
    "NVivo": ("Humanities & Social Science", "Sociology", 26),
}

CAPABILITY = {
    "L1": "Operation Level",
    "L2": "Software Level",
    "L3": "Pipeline Level",
    "L4": "Creative Level",
}

# Per-level difficulty splits from Table 2 (Simple/Middle/Hard -> easy/medium/hard).
LEVEL_DIFFICULTY = {
    "L1": {"easy": 173, "medium": 67, "hard": 12},   # 252
    "L2": {"easy": 48, "medium": 86, "hard": 30},    # 164
    "L3": {"hard": 10},                               # 10
    "L4": {"hard": 10},                               # 10
}

# L1 (atomic single-operation) task templates per application.
L1_TEMPLATES = {
    "AutoCAD": [
        "Set the current layer to 'Dimensions' and change its color to red.",
        "Draw a 100 x 60 mm rectangle starting at the origin.",
        "Change the active dimension style to use 2.5 mm text height.",
        "Offset the selected polyline by 10 mm to the inside.",
    ],
    "SolidWorks": [
        "Create a new part and set the document units to millimeters (MMGS).",
        "Sketch a 50 mm diameter circle on the front plane.",
        "Apply a 5 mm fillet to the selected edge of the block.",
        "Change the part material to 'Plain Carbon Steel'.",
    ],
    "VSCode": [
        "Enable format-on-save in the workspace settings.",
        "Switch the color theme to 'Dark+ (default dark)'.",
        "Open the integrated terminal and set the default profile to bash.",
        "Install the Python extension from the marketplace.",
    ],
    "ANSYS": [
        "Apply a fixed support to the selected face of the model.",
        "Set the mesh element size to 5 mm for the body.",
        "Add a 500 N force to the top face in the -Y direction.",
        "Insert a 'Total Deformation' result under the solution.",
    ],
    "ArcGIS": [
        "Add a north arrow to the current map layout.",
        "Change the coordinate system of the data frame to WGS 1984.",
        "Add a scale bar in kilometers to the layout.",
        "Symbolize the district layer with a single blue fill.",
    ],
    "MultiSim": [
        "Place a 1 kohm resistor and a 10 uF capacitor on the schematic.",
        "Add a DC power supply set to 5 V to the circuit.",
        "Wire a ground symbol to the negative terminal.",
        "Place a voltmeter across the output node.",
    ],
    "ImageJ": [
        "Set the measurement scale to 1.5 pixels per micron.",
        "Convert the image to 8-bit grayscale.",
        "Apply a Gaussian blur with sigma 2 to the image.",
        "Measure the mean gray value inside the rectangular ROI.",
    ],
    "Adobe Photoshop": [
        "Adjust the brightness of the image to 100.",
        "Crop the image to a 1:1 square aspect ratio.",
        "Add a new adjustment layer for Hue/Saturation.",
        "Flatten all layers and export the image as PNG.",
    ],
    "Adobe Illustrator": [
        "Set the fill of the selected shape to a 50% gray.",
        "Create a new 800 x 600 px artboard.",
        "Apply a 2 pt black stroke to the selected path.",
        "Convert the selected text to outlines.",
    ],
    "ChemDraw": [
        "Draw a benzene ring using the ring template.",
        "Add a hydroxyl (-OH) group to the selected carbon.",
        "Generate the molecular formula for the drawn structure.",
        "Label the selected atom as nitrogen.",
    ],
    "Microsoft Excel": [
        "Add a slicer for the 'Region' column to the table.",
        "Format the 'Sales' column as currency with two decimals.",
        "Freeze the top row of the worksheet.",
        "Apply a conditional-formatting color scale to the values column.",
    ],
    "R (RGui)": [
        "Load the CSV file into a data frame named df.",
        "Print the summary statistics of the numeric columns.",
        "Compute the mean of the 'sales' column.",
        "Create a histogram of the response variable.",
    ],
    "NVivo": [
        "Create a new node named 'barriers' in the project.",
        "Import the interview transcript into the sources.",
        "Run a word-frequency query on the selected source.",
        "Code the highlighted passage to the 'wellbeing' node.",
    ],
}

# L2 (software-level, multi-step) task templates per application.
L2_TEMPLATES = {
    "AutoCAD": [
        "Draw a standard outdoor badminton court with regulation dimensions on dedicated layers.",
        "Create an A3 title block with a border and a dimension style, then annotate the part.",
        "Model the floor plan of a single room with walls, a door, and a window, fully dimensioned.",
    ],
    "SolidWorks": [
        "Model three components of a syringe: a barrel, a plunger, and a needle.",
        "Create a revolved shaft with a keyway and a chamfer, then apply steel material.",
        "Build a bracket and generate a drawing sheet with front, top, and section views.",
    ],
    "VSCode": [
        "Set up a Python virtual environment, install requests, and run the active script.",
        "Create a launch configuration to debug the Node.js app and hit a breakpoint.",
        "Configure tasks.json to build the project and bind it to Ctrl+Shift+B.",
    ],
    "ANSYS": [
        "Add a 'Total Deformation' result to the current Static Structural analysis and solve.",
        "Apply a fixed support and a 500 N load, mesh the body, and solve for equivalent stress.",
        "Set up a steady-state thermal analysis with a 100 C boundary and plot temperature.",
    ],
    "ArcGIS": [
        "Classify the land-use raster into five categories and export a styled map.",
        "Join census attributes to the district layer and create a choropleth of population.",
        "Buffer the roads layer by 500 m and clip the parcels within the buffer.",
    ],
    "MultiSim": [
        "Build an RC low-pass filter and run an AC sweep to plot the frequency response.",
        "Simulate a full-wave rectifier and measure the output ripple with a transient analysis.",
        "Design an inverting op-amp amplifier with gain 10 and verify the output waveform.",
    ],
    "ImageJ": [
        "Measure the angles of four leaf veins from top to bottom and export the results.",
        "Threshold the cell image, count particles above 50 square microns, and save the summary.",
        "Measure the area and circularity of each ROI and export the measurements to CSV.",
    ],
    "Adobe Photoshop": [
        "Remove all birds from the photo, then adjust the brightness of the image to 100.",
        "Replace the sky with a sunset image and match the foreground color grading.",
        "Retouch the portrait with frequency separation and dodge-and-burn, then export.",
    ],
    "Adobe Illustrator": [
        "Trace the sketch with the pen tool and apply a three-color flat palette.",
        "Create a repeating pattern swatch and apply it to a packaging shape.",
        "Design a two-color icon set of three pictograms on a shared grid.",
    ],
    "ChemDraw": [
        "Draw and analyze the molecular structure information of Acetylsalicylic acid (Aspirin).",
        "Draw the esterification reaction scheme with reagents and conditions above the arrow.",
        "Draw ibuprofen, then generate its IUPAC name and exact mass.",
    ],
    "Microsoft Excel": [
        "Build a PivotTable summarizing revenue by quarter and product, then add a slicer.",
        "Create a clustered column chart of monthly sales and add a linear trendline.",
        "Clean the dataset with Text-to-Columns and compute a weighted average per region.",
    ],
    "R (RGui)": [
        "Fit a linear regression of sales on advertising and print the model summary.",
        "Aggregate the data by group, compute group means, and plot them as a bar chart.",
        "Run a t-test between two groups and report the p-value and confidence interval.",
    ],
    "NVivo": [
        "Compare the perspectives of different respondents on the various aspects of 'wellbeing'.",
        "Code three transcripts into 'barriers' and 'enablers' nodes and run a matrix query.",
        "Run a word-frequency query, build a tag cloud, and export the top 50 terms.",
    ],
}

# L3 (cross-application pipeline) tasks — each spans two applications. All Hard.
L3_TASKS = [
    (["ArcGIS", "Microsoft Excel"], "Aggregate street-level population in ArcGIS and derive distributional statistics in Excel for spatial demographic analysis."),
    (["ImageJ", "Microsoft Excel"], "Measure cell areas for each sample in ImageJ, then summarize and chart the distributions in Excel."),
    (["ChemDraw", "Microsoft Excel"], "Draw a series of analogues in ChemDraw, export their properties, and tabulate them in Excel."),
    (["ANSYS", "Microsoft Excel"], "Run a parametric structural sweep in ANSYS and compile the deformation results into an Excel report."),
    (["R (RGui)", "Microsoft Excel"], "Fit a forecasting model in R, export the predictions, and build a dashboard chart in Excel."),
    (["AutoCAD", "SolidWorks"], "Create a 2D profile in AutoCAD, import it into SolidWorks, and extrude it into a 3D part."),
    (["Adobe Photoshop", "Adobe Illustrator"], "Mask and color-grade a product photo in Photoshop, then lay it out with vector type in Illustrator."),
    (["MultiSim", "Microsoft Excel"], "Sweep a filter circuit in MultiSim, export the frequency response, and plot the Bode curve in Excel."),
    (["NVivo", "Microsoft Excel"], "Code survey responses in NVivo, export the coding matrix, and visualize theme frequencies in Excel."),
    (["ImageJ", "R (RGui)"], "Extract intensity measurements in ImageJ and run a statistical comparison across conditions in R."),
]

# L4 (open-ended creative) tasks. All Hard.
L4_TASKS = [
    (["Adobe Illustrator"], "Design a cartoon-style logo for a pediatric dentistry clinic that incorporates sun and smile elements."),
    (["Adobe Photoshop"], "Create a promotional poster for a campus music festival with a cohesive color theme and typography."),
    (["Adobe Illustrator"], "Design a three-icon brand pictogram set for a sustainable coffee shop."),
    (["Adobe Photoshop"], "Compose a surreal double-exposure portrait blending a cityscape and a face."),
    (["SolidWorks"], "Design an ergonomic desk-lamp concept with an articulated arm and a weighted base."),
    (["Adobe Illustrator"], "Create a flat-style infographic layout summarizing a product's three key features."),
    (["Adobe Photoshop"], "Design a social-media banner for a book launch with a clear focal hierarchy."),
    (["AutoCAD"], "Design a small community pavilion floor plan with seating and circulation."),
    (["Adobe Illustrator"], "Design a playful mascot character for a children's science museum."),
    (["Adobe Photoshop"], "Create a magazine cover concept with a hero image, masthead, and cover lines."),
]


def artifact_block():
    return [
        {
            "label": "Task context",
            "note": (
                "ProSoftArena runs each task in an executable Windows 11 VM with the professional "
                "software pre-installed; every task ships an initialization script, input files, a "
                "demonstration trajectory, and an execution-based evaluator. The per-task files and "
                "trajectories are not yet publicly released (the authors state the data and code are "
                "coming soon), so no per-task screenshot is available here."
            ),
            "links": [
                {"text": "Paper (CVPR 2026) ↗", "url": PAPER_URL},
                {"text": "Project page ↗", "url": PROJECT_URL},
            ],
        }
    ]


def build_rows():
    rows = []
    n = 0

    def add(software, discipline, subfield, cap, difficulty, name):
        nonlocal n
        n += 1
        rows.append({
            "benchmark": "ProSoftArena",
            "task_id": f"prosoftarena-{n:03d}",
            "software": software if isinstance(software, list) else [software],
            "task_name": name,
            "task_type": f"{cap} {CAPABILITY[cap]}",
            "level": difficulty,
            "discipline": discipline,
            "subfield": subfield,
            "capability_level": cap,
            "capability_name": CAPABILITY[cap],
            "artifacts": artifact_block(),
        })

    # L1 and L2: distribute per-app target counts, split by that level's difficulty mix.
    for cap, templates in (("L1", L1_TEMPLATES), ("L2", L2_TEMPLATES)):
        # Build the per-difficulty bucket of app slots for this level.
        diff_counts = LEVEL_DIFFICULTY[cap]
        # proportion of each app's tasks that belong to this level
        level_total = sum(diff_counts.values())
        l1l2_total = sum(LEVEL_DIFFICULTY["L1"].values()) + sum(LEVEL_DIFFICULTY["L2"].values())
        # app-level allocation for this capability level, proportional to level size
        app_alloc = {}
        for app, (_, _, target) in APPS.items():
            app_alloc[app] = round(target * level_total / l1l2_total)
        # fix rounding to match level_total
        drift = level_total - sum(app_alloc.values())
        apps_cycle = list(APPS.keys())
        i = 0
        while drift != 0:
            app = apps_cycle[i % len(apps_cycle)]
            app_alloc[app] += 1 if drift > 0 else -1
            drift += -1 if drift > 0 else 1
            i += 1
        # flat list of apps for this level
        app_slots = []
        for app, c in app_alloc.items():
            app_slots.extend([app] * max(0, c))
        # difficulty slots for this level
        diff_slots = []
        for d, c in diff_counts.items():
            diff_slots.extend([d] * c)
        # pair them up
        for idx, app in enumerate(app_slots):
            if idx >= len(diff_slots):
                break
            difficulty = diff_slots[idx]
            discipline, subfield, _ = APPS[app]
            pool = templates[app]
            name = pool[idx % len(pool)]
            add(app, discipline, subfield, cap, difficulty, name)

    # L3: cross-application, all hard.
    for software, name in L3_TASKS:
        disciplines = sorted({APPS[a][0] for a in software})
        add(software, " + ".join(disciplines), "Cross-application workflow", "L3", "hard", name)

    # L4: creative, all hard.
    for software, name in L4_TASKS:
        app = software[0]
        discipline, subfield, _ = APPS[app]
        add(software, discipline, subfield, "L4", "hard", name)

    return rows


def metadata(count):
    return {
        "benchmark": "ProSoftArena",
        "source_url": PROJECT_URL,
        "paper_url": PAPER_URL,
        "source_revision": "arxiv-2601.02399v1",
        "task_count": count,
        "scope": (
            "All 436 tasks across 6 disciplines, 20 subfields and 13 core professional applications, "
            "organized by the hierarchical capability taxonomy (L1 Operation 252, L2 Software 164, "
            "L3 Pipeline 10, L4 Creative 10)."
        ),
        "task_name_basis": (
            "Representative task descriptions grounded in the paper's example tasks (Figures 2 and 4) "
            "and typical operations per application. The capability-level counts and per-level "
            "difficulty splits match Table 2 of the paper exactly; the per-discipline application "
            "mapping follows Section 5.1. Official per-task files and trajectories are not yet "
            "publicly released."
        ),
    }


def main():
    rows = build_rows()
    assert len(rows) == 436, f"expected 436, got {len(rows)}"
    meta = metadata(len(rows))

    from collections import Counter
    caps = Counter(r["capability_level"] for r in rows)
    diffs = Counter(r["level"] for r in rows)
    print("Capability levels:", dict(caps))
    print("Difficulty:", dict(diffs))

    for catalog_path in CATALOGS:
        catalog = json.loads(catalog_path.read_text())
        catalog["benchmarks"] = [b for b in catalog["benchmarks"] if b["benchmark"] != "ProSoftArena"]
        catalog["tasks"] = [t for t in catalog["tasks"] if t["benchmark"] != "ProSoftArena"]
        catalog["benchmarks"].append(meta)
        catalog["tasks"].extend(rows)
        catalog["benchmark_count"] = len(catalog["benchmarks"])
        catalog["task_count"] = len(catalog["tasks"])
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
        print(f"  {catalog_path.name}: added {len(rows)} ProSoftArena tasks "
              f"(total {catalog['task_count']} tasks, {catalog['benchmark_count']} benchmarks)")


if __name__ == "__main__":
    main()
