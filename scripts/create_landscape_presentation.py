#!/usr/bin/env python3
"""Adapt the updated benchmark-landscape report into the Multi-Cursor deck style."""

from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

TEMPLATE = Path("/Users/tht0021/Downloads/Multi-Cursor (1).pptx")
REPORT = Path("/Users/tht0021/Downloads/Domains & Tasks (Updated) (1).docx")
OUTPUT = Path("/Users/tht0021/Downloads/benchmark-tasks/Computer-Use_Benchmark_Landscape.pptx")

NAVY = RGBColor(12, 35, 64)
ORANGE = RGBColor(232, 119, 34)
INK = RGBColor(37, 37, 37)
MUTED = RGBColor(107, 107, 107)
LIGHT = RGBColor(245, 246, 247)
PALE_ORANGE = RGBColor(253, 238, 226)
PALE_BLUE = RGBColor(232, 239, 246)
WHITE = RGBColor(255, 255, 255)
BORDER = RGBColor(218, 222, 226)
FONT = "Urbanist"


def delete_shape(shape):
    shape._element.getparent().remove(shape._element)


def clear_slide(slide, keep_title=True):
    kept = None
    if keep_title:
        candidates = [s for s in slide.shapes if s.has_text_frame and s.top < Inches(1.35)]
        if candidates:
            kept = min(candidates, key=lambda s: s.top)
    for shape in list(slide.shapes):
        if shape is not kept:
            delete_shape(shape)
    return kept


def set_title(slide, text):
    title = next((s for s in slide.shapes if s.has_text_frame and s.top < Inches(1.35)), None)
    if title is None:
        title = slide.shapes.add_textbox(Inches(.69), Inches(.3), Inches(8.62), Inches(1.0))
    title.text_frame.clear()
    p = title.text_frame.paragraphs[0]
    p.text = text
    p.font.name = FONT
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = INK
    p.space_after = Pt(0)
    title.text_frame.word_wrap = True
    title.text_frame.margin_left = 0
    title.text_frame.margin_right = 0
    return title


def add_text(slide, text, x, y, w, h, size=13, color=INK, bold=False,
             align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=.06, font=FONT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.name = font
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.space_after = Pt(0)
    return box


def add_rich_text(slide, blocks, x, y, w, h, fill=WHITE, line=BORDER, margin=.15):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(.8)
    tf = shape.text_frame
    tf.clear(); tf.word_wrap = True
    tf.margin_left = Inches(margin); tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin)
    for i, block in enumerate(blocks):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = block.get("text", "")
        p.alignment = PP_ALIGN.LEFT
        p.font.name = FONT
        p.font.size = Pt(block.get("size", 11))
        p.font.bold = block.get("bold", False)
        p.font.color.rgb = block.get("color", INK)
        p.space_before = Pt(block.get("before", 0))
        p.space_after = Pt(block.get("after", 4))
        if block.get("bullet"):
            p.text = "•  " + p.text
            p.level = 0
    return shape


def add_rule(slide, x, y, w, color=ORANGE, height=.035):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(height))
    shape.fill.solid(); shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_image_contain(slide, path, x, y, w, h, border=True):
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px, py = x + (w - pw) / 2, y + (h - ph) / 2
    if border:
        frame = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        frame.fill.solid(); frame.fill.fore_color.rgb = WHITE
        frame.line.color.rgb = BORDER; frame.line.width = Pt(.6)
    return slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))


def extract_report_images(folder):
    doc = Document(REPORT)
    paths = []
    for i, inline in enumerate(doc.inline_shapes):
        blip = inline._inline.graphic.graphicData.pic.blipFill.blip
        part = doc.part.related_parts[blip.embed]
        ext = Path(part.partname).suffix or ".png"
        path = folder / f"report-{i:02d}{ext}"
        path.write_bytes(part.blob)
        paths.append(path)
    return paths


def add_kpi(slide, number, label, x, y, w=1.95):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(.9))
    card.fill.solid(); card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = BORDER
    add_text(slide, number, x+.12, y+.08, w-.24, .38, size=23, color=ORANGE, bold=True)
    add_text(slide, label, x+.12, y+.48, w-.24, .25, size=10.2, color=NAVY, bold=True)


def slide_2(slide, images):
    set_title(slide, "The landscape spans 13 benchmarks and 4,353 tasks")
    add_image_contain(slide, images[0], .72, 1.43, 5.7, 3.5, border=False)
    add_kpi(slide, "13", "benchmarks", 6.67, 1.45, 1.15)
    add_kpi(slide, "4,353", "tasks", 7.98, 1.45, 1.3)
    add_rich_text(slide, [
        {"text": "WHY THIS REVIEW", "size": 10, "bold": True, "color": ORANGE, "after": 7},
        {"text": "Map domains and operation types", "size": 12, "bold": True, "color": NAVY},
        {"text": "Identify tasks that fit concurrent work on one shared artifact", "size": 11},
        {"text": "Design a benchmark spanning professional, creative, office, engineering and OS software", "size": 11},
    ], 6.67, 2.55, 2.61, 2.38, fill=PALE_BLUE, line=PALE_BLUE)
    add_text(slide, "Source: updated Domains & Tasks report, October 2026.", .75, 5.12, 8.5, .22, size=8.5, color=MUTED)


def benchmark_cards(slide):
    set_title(slide, "The catalog covers creative, office, engineering and desktop work")
    items = [
        ("PSBench", "600 · Photoshop", "24 High"), ("CANVAS", "598 · Figma", "23 High"),
        ("ProSoftArena", "436 · 13 professional apps", "78 High"), ("GUIDE", "40 · 10 creative/office apps", "32 High"),
        ("PPT-Eval", "120 · PowerPoint Online", "Reviewed"), ("OSWorld", "369 · Ubuntu / LibreOffice", "14 High"),
        ("ScratchWorld", "83 · MIT Scratch", "6 High"), ("DeskCraft", "538 · Linux creative tools", "59 High"),
        ("DesignBench", "900 · Web frameworks", "529 High"), ("ParaGUIBench", "233 · Ubuntu / LibreOffice", "Not flagged"),
        ("CADWorld", "200 · FreeCAD", "12 High"), ("CutVerse", "186 · Media production", "6 High"),
        ("AutoCAD Bench", "50 · AutoCAD", "1 Medium"),
    ]
    left, right = items[:7], items[7:]
    for col, group in enumerate((left, right)):
        x = .78 + col * 4.55
        for row, (name, meta, fit) in enumerate(group):
            y = 1.42 + row * .52
            add_rule(slide, x, y+.02, .045, ORANGE, .38)
            add_text(slide, name, x+.12, y, 1.32, .24, size=11.2, color=NAVY, bold=True)
            add_text(slide, meta, x+1.47, y, 1.88, .24, size=9.4, color=INK)
            add_text(slide, fit, x+3.39, y, .78, .24, size=9.4, color=ORANGE, bold=True, align=PP_ALIGN.RIGHT)
            if row < len(group)-1:
                add_rule(slide, x+.12, y+.43, 4.05, BORDER, .008)
    add_text(slide, "Shared-canvas column reports the source document’s classified fit.", .78, 5.16, 8.4, .2, size=8.5, color=MUTED)


def shared_canvas_slide(slide):
    set_title(slide, "Shared-canvas work splits cleanly but still produces one artifact")
    add_rich_text(slide, [
        {"text": "WORKING DEFINITION", "size": 10, "bold": True, "color": ORANGE, "after": 8},
        {"text": "Different agents own clean regions of the same canvas and work concurrently.", "size": 18, "bold": True, "color": NAVY, "after": 10},
        {"text": "The result remains one coherent slide, design, image, document, project or timeline.", "size": 12, "color": INK},
    ], .78, 1.48, 3.45, 3.45, fill=NAVY, line=NAVY)
    # recolor text manually for dark card
    card = slide.shapes[-1]
    for p in card.text_frame.paragraphs:
        if p.text != "WORKING DEFINITION": p.font.color.rgb = WHITE
    rows = [
        ("PPT-Eval", "PowerPoint Online"), ("CANVAS", "Figma"), ("PSBench", "Photoshop"),
        ("GUIDE", "Canva, Slides, Office, media"), ("ProSoftArena", "Photoshop, Illustrator, CAD"),
        ("CutVerse", "Premiere, AE, Resolve"), ("DeskCraft", "GIMP, Inkscape, Kdenlive"),
        ("DesignBench", "React, Vue, Angular, HTML/CSS"),
    ]
    x, y, w = 4.55, 1.48, 4.72
    add_text(slide, "Best-fit software", x, y, w, .28, size=13, color=NAVY, bold=True)
    for i, (bench, software) in enumerate(rows):
        yy = y+.42+i*.43
        fill = PALE_ORANGE if i % 2 == 0 else WHITE
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(yy), Inches(w), Inches(.39))
        box.fill.solid(); box.fill.fore_color.rgb = fill; box.line.fill.background()
        add_text(slide, bench, x+.1, yy+.055, 1.2, .22, size=9.5, color=NAVY, bold=True)
        add_text(slide, software, x+1.35, yy+.055, 3.22, .22, size=9.5, color=INK)


def ppt_eval_slide(slide, images):
    set_title(slide, "PPT-Eval divides naturally by slide region and diagram component")
    add_text(slide, "TASK 1  ·  COMBINE SLIDES", .78, 1.35, 4.35, .22, size=10, color=ORANGE, bold=True)
    add_text(slide, "Combine slides 2 and 3 into one new slide with male and female clothing tables and both images.", .78, 1.62, 4.35, .64, size=12, color=NAVY, bold=True)
    add_image_contain(slide, images[1], .8, 2.34, 2.02, 1.5)
    add_image_contain(slide, images[2], 2.92, 2.34, 2.12, 1.5)
    add_rich_text(slide, [
        {"text": "Agent A", "size": 10, "bold": True, "color": ORANGE},
        {"text": "Male clothing table", "size": 10.5, "bold": True, "color": NAVY},
        {"text": "Agent B", "size": 10, "bold": True, "color": ORANGE, "before": 4},
        {"text": "Female clothing table", "size": 10.5, "bold": True, "color": NAVY},
    ], .8, 4.02, 4.24, .95, fill=PALE_BLUE, line=PALE_BLUE)

    add_text(slide, "TASK 2  ·  REBUILD A FLOWCHART", 5.35, 1.35, 3.85, .22, size=10, color=ORANGE, bold=True)
    add_text(slide, "Replace the slide 11 diagram with: Browser → HTTP Request → Web Server → HTTP Response → Browser.", 5.35, 1.62, 3.85, .8, size=12, color=NAVY, bold=True)
    add_image_contain(slide, images[3], 5.38, 2.45, 3.82, 2.08)
    add_text(slide, "Five components can be built concurrently, then aligned as one flow.", 5.38, 4.66, 3.82, .38, size=10, color=INK)


def canvas_slide(slide, images):
    set_title(slide, "CANVAS exposes independent UI components on one Figma screen")
    tasks = [
        ("Contact list recolor", "Change minus buttons and missed-call names from green to red.", images[4], images[5], "Buttons and contact names can be owned separately."),
        ("Commerce UI recolor", "Change Shop, forward arrows and bottom navigation from pink to blue.", images[6], images[7], "Button, arrows and navigation icons can change in parallel."),
    ]
    for i, (name, task, before, after, rationale) in enumerate(tasks):
        y = 1.38 + i*1.92
        add_text(slide, f"0{i+1}", .78, y, .52, .28, size=18, color=ORANGE, bold=True)
        add_text(slide, name, 1.34, y, 1.96, .28, size=13, color=NAVY, bold=True)
        add_text(slide, task, 1.34, y+.34, 1.96, .62, size=10.5, color=INK)
        add_text(slide, rationale, 1.34, y+1.02, 1.96, .5, size=9.5, color=MUTED)
        add_image_contain(slide, before, 3.58, y, 2.05, 1.58)
        add_image_contain(slide, after, 5.77, y, 2.05, 1.58)
        add_text(slide, "STARTING", 3.58, y+1.61, 2.05, .18, size=8.5, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, "TARGET", 5.77, y+1.61, 2.05, .18, size=8.5, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
        add_rich_text(slide, [{"text": "Shared artifact", "size": 9, "bold": True, "color": ORANGE}, {"text": "One Figma screen", "size": 11, "bold": True, "color": NAVY}], 8.05, y, 1.18, 1.58, fill=PALE_ORANGE, line=PALE_ORANGE)


def psbench_slide(slide, images):
    set_title(slide, "PSBench separates subject treatment from background treatment")
    tasks = [
        ("Luminous flowers", "Keep flowers vivid and glowing while converting the surrounding scene to black and white.", images[8], images[9], "A  Flowers and glow", "B  Monochrome scene"),
        ("Sharp tree, blurred background", "Keep the tree sharp and dark blue-black; make the background grayscale with strong Gaussian blur.", images[10], images[11], "A  Foreground tree", "B  Background treatment"),
    ]
    for i, (name, task, before, after, a, b) in enumerate(tasks):
        x = .78 + i*4.51
        add_text(slide, f"0{i+1}  {name}", x, 1.36, 4.16, .28, size=13, color=NAVY, bold=True)
        add_text(slide, task, x, 1.7, 4.16, .58, size=10.5, color=INK)
        add_image_contain(slide, before, x, 2.4, 1.98, 1.52)
        add_image_contain(slide, after, x+2.16, 2.4, 1.98, 1.52)
        add_text(slide, "STARTING", x, 3.95, 1.98, .18, size=8.5, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, "TARGET", x+2.16, 3.95, 1.98, .18, size=8.5, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
        add_rich_text(slide, [{"text": a, "size": 10, "bold": True, "color": NAVY}, {"text": b, "size": 10, "bold": True, "color": NAVY}], x, 4.28, 4.14, .7, fill=PALE_BLUE, line=PALE_BLUE)


def scratch_prosoft_slide(slide):
    set_title(slide, "ScratchWorld and ProSoftArena split work by module or document region")
    add_text(slide, "SCRATCHWORLD", .78, 1.35, 4.15, .22, size=10, color=ORANGE, bold=True)
    add_rich_text(slide, [
        {"text": "Maze timer and scoring", "size": 14, "bold": True, "color": NAVY},
        {"text": "Add timeLeft and score; enforce countdown, wall penalties and a +50 goal bonus.", "size": 10.5},
        {"text": "A  Stage — initialize and enforce timeout", "size": 9.8, "bold": True, "color": NAVY, "before": 5},
        {"text": "B  Ball — wall-contact penalties", "size": 9.8, "bold": True, "color": NAVY},
        {"text": "C  Goal — award bonus and stop timer", "size": 9.8, "bold": True, "color": NAVY},
    ], .78, 1.68, 4.15, 1.55, fill=WHITE)
    add_rich_text(slide, [
        {"text": "Voltage-aware circuit", "size": 14, "bold": True, "color": NAVY},
        {"text": "Cycle a Battery between 3V and 6V and map voltage to Lightbulb brightness when the circuit is complete and ON.", "size": 10.5},
        {"text": "A  Battery", "size": 9.8, "bold": True, "color": NAVY, "before": 5},
        {"text": "B  Lightbulb", "size": 9.8, "bold": True, "color": NAVY},
        {"text": "C  Circuit integration", "size": 9.8, "bold": True, "color": NAVY},
    ], .78, 3.38, 4.15, 1.55, fill=WHITE)

    add_text(slide, "PROSOFTARENA", 5.22, 1.35, 4.05, .22, size=10, color=ORANGE, bold=True)
    add_rich_text(slide, [
        {"text": "Microsoft Excel", "size": 11, "bold": True, "color": ORANGE},
        {"text": "Build a PivotTable summarizing revenue by quarter and product, then add a slicer.", "size": 14, "bold": True, "color": NAVY},
        {"text": "A  Quarter summary", "size": 10, "bold": True, "color": NAVY, "before": 7},
        {"text": "B  Product dimension", "size": 10, "bold": True, "color": NAVY},
        {"text": "C  Slicer", "size": 10, "bold": True, "color": NAVY},
    ], 5.22, 1.68, 4.05, 2.06, fill=PALE_ORANGE, line=PALE_ORANGE)
    add_rich_text(slide, [
        {"text": "Adobe Illustrator", "size": 11, "bold": True, "color": ORANGE},
        {"text": "Design a three-icon brand pictogram set for a sustainable coffee shop.", "size": 14, "bold": True, "color": NAVY},
    ], 5.22, 3.9, 4.05, 1.03, fill=PALE_BLUE, line=PALE_BLUE)


def osworld_slide(slide):
    set_title(slide, "OSWorld assigns independent worksheet or slide regions")
    add_rich_text(slide, [
        {"text": "LIBREOFFICE CALC", "size": 10, "bold": True, "color": ORANGE},
        {"text": "Create separate monthly-cost column charts for 2019 and 2020.", "size": 16, "bold": True, "color": NAVY, "after": 9},
        {"text": "Agent A", "size": 10, "bold": True, "color": ORANGE},
        {"text": "2019 table and chart", "size": 11.5, "bold": True, "color": INK},
        {"text": "Agent B", "size": 10, "bold": True, "color": ORANGE, "before": 6},
        {"text": "2020 table and chart", "size": 11.5, "bold": True, "color": INK},
    ], .78, 1.42, 4.12, 3.45, fill=PALE_BLUE, line=PALE_BLUE)
    add_rich_text(slide, [
        {"text": "LIBREOFFICE IMPRESS", "size": 10, "bold": True, "color": ORANGE},
        {"text": "Set the three slide-1 textboxes to yellow, red and green from top to bottom.", "size": 16, "bold": True, "color": NAVY, "after": 9},
        {"text": "Agent A  Top textbox — yellow", "size": 11, "bold": True, "color": INK},
        {"text": "Agent B  Middle textbox — red", "size": 11, "bold": True, "color": INK},
        {"text": "Agent C  Bottom textbox — green", "size": 11, "bold": True, "color": INK},
    ], 5.17, 1.42, 4.12, 3.45, fill=PALE_ORANGE, line=PALE_ORANGE)
    add_text(slide, "One file, multiple clean regions, one integrated deliverable.", .78, 5.03, 8.5, .25, size=11, color=MUTED, bold=True, align=PP_ALIGN.CENTER)


def concerns_next_slide(slide):
    set_title(slide, "Four constraints shape the rollout—and three actions come next")
    concerns = [
        ("01", "Licensing", "Commercial apps make execution and verification hard to scale."),
        ("02", "Taxonomy", "Benchmarks use incompatible labels for task and operation types."),
        ("03", "Environments", "Windows, Ubuntu, web apps and code/render harnesses need different runners."),
        ("04", "Evaluation", "One harness must compare all tasks, benchmarks and final artifacts."),
    ]
    add_text(slide, "MAIN CONCERNS", .78, 1.38, 4.08, .2, size=10, color=ORANGE, bold=True)
    for i, (num, name, desc) in enumerate(concerns):
        y = 1.72 + i*.75
        add_text(slide, num, .78, y, .4, .28, size=15, color=ORANGE, bold=True)
        add_text(slide, name, 1.24, y, 1.18, .24, size=10.8, color=NAVY, bold=True)
        add_text(slide, desc, 2.39, y, 2.43, .49, size=9.6, color=INK)
    add_text(slide, "NEXT STEPS", 5.18, 1.38, 4.08, .2, size=10, color=ORANGE, bold=True)
    steps = [
        ("1", "Finalize the task list", "Export the approved set as the benchmark seed."),
        ("2", "Prefer open software", "Use Figma, GIMP, FreeCAD, LibreOffice, Inkscape, Scratch and web frameworks where possible."),
        ("3", "Build one harness", "Run the shared-canvas agent across every selected task and benchmark."),
    ]
    for i, (num, title, desc) in enumerate(steps):
        y = 1.7 + i*1.03
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(5.18), Inches(y), Inches(.43), Inches(.43))
        circle.fill.solid(); circle.fill.fore_color.rgb = ORANGE if i == 0 else NAVY
        circle.line.fill.background()
        add_text(slide, num, 5.18, y+.04, .43, .24, size=11, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, title, 5.78, y, 3.45, .25, size=12, color=NAVY, bold=True)
        add_text(slide, desc, 5.78, y+.31, 3.45, .48, size=10, color=INK)


def build():
    prs = Presentation(TEMPLATE)
    with TemporaryDirectory() as tmp:
        images = extract_report_images(Path(tmp))

        # Cover: retain template artwork and typography.
        cover = prs.slides[0]
        text_shapes = [s for s in cover.shapes if s.has_text_frame]
        text_shapes[0].text = "Computer-Use Benchmark Landscape"
        text_shapes[1].text = "Domains, software and shared-canvas suitability  ·  October 2026"
        text_shapes[2].text = "FINAL REPORT  ·  Benchmark planning"
        for index, shape in enumerate(text_shapes):
            paragraph = shape.text_frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.CENTER
            paragraph.font.name = FONT
            paragraph.font.color.rgb = ORANGE if index == 2 else WHITE
            paragraph.font.bold = index == 2
            paragraph.font.size = Pt(30 if index == 0 else 13 if index == 1 else 11)

        for slide_index in range(1, 10):
            clear_slide(prs.slides[slide_index], keep_title=True)

        slide_2(prs.slides[1], images)
        benchmark_cards(prs.slides[2])
        shared_canvas_slide(prs.slides[3])
        ppt_eval_slide(prs.slides[4], images)
        canvas_slide(prs.slides[5], images)
        psbench_slide(prs.slides[6], images)
        scratch_prosoft_slide(prs.slides[7])
        osworld_slide(prs.slides[8])
        concerns_next_slide(prs.slides[9])

        closing = prs.slides[10]
        for s in closing.shapes:
            if s.has_text_frame:
                s.text = "Thank you. Questions?"

        prs.core_properties.title = "Computer-Use Benchmark Landscape"
        prs.core_properties.subject = "Domains, software, and shared-canvas suitability"
        prs.core_properties.author = "Benchmark Tasks Project"
        prs.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
