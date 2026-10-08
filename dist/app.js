const PAGE_SIZE = 40;
const SHARED_PAGE_SIZE = 24;
const SAVED_TASKS_KEY = "benchmark-task-saves-v1";
const REJECTED_TASKS_KEY = "benchmark-shared-canvas-rejections-v1";

const state = {
  catalog: null,
  filtered: [],
  page: 1,
  benchmark: "",
  software: "",
  type: "",
  level: "",
  sharedCanvas: "",
  sharedReviewBenchmark: "",
  sharedReviewLevel: "",
  sharedReviewPage: 1,
  sharedReviewSoftware: "",
  sharedReviewStatus: "pending",
  view: "",
  search: "",
  sort: "benchmark",
  saves: {},
  rejections: {},
};

const elements = {
  benchmarkFilter: document.querySelector("#benchmarkFilter"),
  benchmarkStrip: document.querySelector("#benchmarkStrip"),
  catalogShell: document.querySelector(".catalog-shell"),
  clearSaved: document.querySelector("#clearSavedButton"),
  closeResearch: document.querySelector("#closeResearch"),
  closeSavedDrawer: document.querySelector("#closeSavedDrawer"),
  closeSharedCanvas: document.querySelector("#closeSharedCanvas"),
  error: document.querySelector("#errorState"),
  exportButton: document.querySelector("#exportButton"),
  exportSaved: document.querySelector("#exportSavedButton"),
  generatedDate: document.querySelector("#generatedDate"),
  hero: document.querySelector(".hero"),
  loading: document.querySelector("#loadingState"),
  next: document.querySelector("#nextPage"),
  pageStatus: document.querySelector("#pageStatus"),
  pagination: document.querySelector("#pagination"),
  previous: document.querySelector("#previousPage"),
  reset: document.querySelector("#resetFilters"),
  resultCount: document.querySelector("#resultCount"),
  resultLabel: document.querySelector("#resultLabel"),
  researchButton: document.querySelector("#researchButton"),
  researchDrawer: document.querySelector("#researchDrawer"),
  researchNotes: document.querySelector("#researchNotes"),
  results: document.querySelector("#results"),
  savedCount: document.querySelector("#savedCount"),
  savedDrawer: document.querySelector("#savedDrawer"),
  savedEmpty: document.querySelector("#savedEmpty"),
  savedGrid: document.querySelector("#savedGrid"),
  savedTasksButton: document.querySelector("#savedTasksButton"),
  search: document.querySelector("#searchInput"),
  sectionKicker: document.querySelector("#sectionKicker"),
  sharedApprovedTotal: document.querySelector("#sharedApprovedTotal"),
  sharedBenchmarkFilter: document.querySelector("#sharedBenchmarkFilter"),
  sharedBenchmarkTabs: document.querySelector("#sharedBenchmarkTabs"),
  sharedCandidateTotal: document.querySelector("#sharedCandidateTotal"),
  sharedCanvasButton: document.querySelector("#sharedCanvasButton"),
  sharedCanvasEmpty: document.querySelector("#sharedCanvasEmpty"),
  sharedCanvasEmptyCopy: document.querySelector("#sharedCanvasEmptyCopy"),
  sharedCanvasFilter: document.querySelector("#sharedCanvasFilter"),
  sharedCanvasTaskGrid: document.querySelector("#sharedCanvasTaskGrid"),
  sharedCanvasView: document.querySelector("#sharedCanvasView"),
  sharedDifficultyFilter: document.querySelector("#sharedDifficultyFilter"),
  sharedNextPage: document.querySelector("#sharedNextPage"),
  sharedPageStatus: document.querySelector("#sharedPageStatus"),
  sharedPagination: document.querySelector("#sharedPagination"),
  sharedPendingTotal: document.querySelector("#sharedPendingTotal"),
  sharedPreviousPage: document.querySelector("#sharedPreviousPage"),
  sharedQueueCount: document.querySelector("#sharedQueueCount"),
  sharedQueueTitle: document.querySelector("#sharedQueueTitle"),
  sharedSoftwareFilter: document.querySelector("#sharedSoftwareFilter"),
  sharedStatusFilter: document.querySelector("#sharedStatusFilter"),
  softwareFilter: document.querySelector("#softwareFilter"),
  sort: document.querySelector("#sortSelect"),
  template: document.querySelector("#taskTemplate"),
  toast: document.querySelector("#toast"),
  totalBenchmarks: document.querySelector("#totalBenchmarks"),
  totalSoftware: document.querySelector("#totalSoftware"),
  totalTasks: document.querySelector("#totalTasks"),
  typeFilter: document.querySelector("#typeFilter"),
  levelFilter: document.querySelector("#levelFilter"),
};

const number = new Intl.NumberFormat("en-US");

const DIFFICULTY_ORDER = ["easy", "medium", "hard", "basic", "intermediate", "advanced", "project"];

function taskDifficulty(item) {
  if (item.level) return item.level.toLowerCase();
  const tt = (item.task_type || "").toLowerCase();
  const match = tt.match(/^(easy|medium|hard)\s*task$/);
  if (match) return match[1];
  return "";
}

function option(value, label = value) {
  const item = document.createElement("option");
  item.value = value;
  item.textContent = label;
  return item;
}

function badge(text, className) {
  const item = document.createElement("span");
  item.className = `badge ${className}`;
  item.textContent = text;
  return item;
}

function agentLabel(index) {
  return index < 26 ? `Agent ${String.fromCharCode(65 + index)}` : `Agent ${index + 1}`;
}

function candidateNote(item) {
  return item.shared_canvas_note || item.shared_canvas_rationale || "Shared-canvas task approved during benchmark review.";
}

function artifactsSection(item) {
  if (!item.artifacts?.length && !item.design_file_url) return null;
  const section = document.createElement("div");
  section.className = "task-artifacts";
  const heading = document.createElement("p");
  heading.className = "task-artifacts-heading";
  heading.textContent = "Artifacts the agent works with";
  section.append(heading);
  if (item.design_file_url) {
    const figma = document.createElement("a");
    figma.className = "artifact-design-link";
    figma.href = item.design_file_url;
    figma.target = "_blank";
    figma.rel = "noreferrer";
    figma.textContent = "Open source design file (Figma) ↗";
    section.append(figma);
  }
  if (item.artifacts?.length) {
    const grid = document.createElement("div");
    grid.className = "artifact-grid";
    item.artifacts.forEach((a) => {
      const cardEl = document.createElement("div");
      cardEl.className = "artifact-card";
      const lab = document.createElement("p");
      lab.className = "artifact-label";
      lab.textContent = a.label;
      cardEl.append(lab);
      if (a.image_url) {
        const link = document.createElement("a");
        link.href = a.image_url;
        link.target = "_blank";
        link.rel = "noreferrer";
        const img = document.createElement("img");
        img.className = "artifact-thumb";
        img.loading = "lazy";
        img.alt = a.label;
        img.src = a.image_url;
        link.append(img);
        cardEl.append(link);
      }
      if (a.note) {
        const n = document.createElement("p");
        n.className = "artifact-note";
        n.textContent = a.note;
        cardEl.append(n);
      }
      if (a.links?.length) {
        const linkRow = document.createElement("div");
        linkRow.className = "artifact-links";
        a.links.forEach((l) => {
          const el = document.createElement("a");
          el.href = l.url;
          el.target = "_blank";
          el.rel = "noreferrer";
          el.textContent = l.text;
          linkRow.append(el);
        });
        cardEl.append(linkRow);
      }
      grid.append(cardEl);
    });
    section.append(grid);
  }
  return section;
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    elements.toast.classList.remove("visible");
  }, 1800);
}

function savedKey(item) {
  return `${item.benchmark}::${item.task_id}`;
}

function loadSaves() {
  try {
    const saved = JSON.parse(localStorage.getItem(SAVED_TASKS_KEY) || "{}");
    state.saves = saved && typeof saved === "object" && !Array.isArray(saved) ? saved : {};
  } catch {
    state.saves = {};
  }
  try {
    const rejected = JSON.parse(localStorage.getItem(REJECTED_TASKS_KEY) || "{}");
    state.rejections = rejected && typeof rejected === "object" && !Array.isArray(rejected) ? rejected : {};
  } catch {
    state.rejections = {};
  }
}

function persistSaves() {
  localStorage.setItem(SAVED_TASKS_KEY, JSON.stringify(state.saves));
  updateSavedNav();
  if (!elements.savedDrawer.hidden) renderSavedDrawer();
  if (!elements.sharedCanvasView.hidden) renderSharedCanvasView();
}

function updateSavedNav() {
  const count = Object.keys(state.saves).length;
  elements.savedCount.textContent = number.format(count);
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.search) params.set("q", state.search);
  if (state.benchmark) params.set("benchmark", state.benchmark);
  if (state.software) params.set("software", state.software);
  if (state.type) params.set("type", state.type);
  if (state.level) params.set("level", state.level);
  if (state.sharedCanvas) params.set("shared_canvas", state.sharedCanvas);
  if (state.view) params.set("view", state.view);
  if (state.sort !== "benchmark") params.set("sort", state.sort);
  const query = params.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
}

function readUrl() {
  const params = new URLSearchParams(location.search);
  state.search = params.get("q") || "";
  state.benchmark = params.get("benchmark") || "";
  state.software = params.get("software") || "";
  state.type = params.get("type") || "";
  state.level = params.get("level") || "";
  state.sharedCanvas = params.get("shared_canvas") || "";
  state.view = params.get("view") || "";
  state.sort = params.get("sort") || "benchmark";
}

function updateDependentFilters() {
  const tasks = state.benchmark
    ? state.catalog.tasks.filter((item) => item.benchmark === state.benchmark)
    : state.catalog.tasks;

  const software = [...new Set(tasks.flatMap((item) => item.software))].sort();
  const types = [...new Set(tasks.map((item) => item.task_type))].sort();
  const levels = DIFFICULTY_ORDER.filter((l) => tasks.some((item) => taskDifficulty(item) === l));

  while (elements.softwareFilter.options.length > 1) elements.softwareFilter.remove(1);
  while (elements.typeFilter.options.length > 1) elements.typeFilter.remove(1);
  while (elements.softwareFilter.options.length > 1) elements.softwareFilter.remove(1);
  while (elements.typeFilter.options.length > 1) elements.typeFilter.remove(1);

  software.forEach((value) => elements.softwareFilter.append(option(value)));
  types.forEach((value) => elements.typeFilter.append(option(value)));

  if (!software.includes(state.software)) state.software = "";
  elements.softwareFilter.value = state.software;

  if (!types.includes(state.type)) state.type = "";
  elements.typeFilter.value = state.type;

  if (elements.levelFilter) {
    while (elements.levelFilter.options.length > 1) elements.levelFilter.remove(1);
    levels.forEach((value) => elements.levelFilter.append(option(value, value.charAt(0).toUpperCase() + value.slice(1))));
    if (!levels.includes(state.level)) state.level = "";
    elements.levelFilter.value = state.level;
  }
}

function populateFilters() {
  const tasks = state.catalog.tasks;
  const benchmarks = state.catalog.benchmarks.map((item) => item.benchmark);

  benchmarks.forEach((value) => elements.benchmarkFilter.append(option(value)));

  elements.search.value = state.search;
  elements.benchmarkFilter.value = state.benchmark;
  elements.sort.value = state.sort;
  elements.sharedCanvasFilter.value = state.sharedCanvas;

  updateDependentFilters();

  state.catalog.benchmarks.forEach((item) => {
    const chip = document.createElement("div");
    chip.className = "benchmark-chip-group";

    const button = document.createElement("button");
    button.className = "benchmark-chip";
    button.type = "button";
    button.dataset.benchmark = item.benchmark;
    button.append(document.createTextNode(item.benchmark));
    const count = document.createElement("span");
    count.textContent = number.format(item.task_count);
    button.append(count);
    button.addEventListener("click", () => {
      state.benchmark = state.benchmark === item.benchmark ? "" : item.benchmark;
      elements.benchmarkFilter.value = state.benchmark;
      updateDependentFilters();
      state.page = 1;
      applyFilters();
      document.querySelector("#catalog-title").scrollIntoView({ behavior: "smooth" });
    });
    chip.append(button);

    const links = document.createElement("span");
    links.className = "benchmark-links";
    if (item.paper_url) {
      const paper = document.createElement("a");
      paper.href = item.paper_url;
      paper.target = "_blank";
      paper.rel = "noreferrer";
      paper.className = "benchmark-link";
      paper.title = "Paper";
      paper.textContent = "paper";
      links.append(paper);
    }
    if (item.source_url) {
      const source = document.createElement("a");
      source.href = item.source_url;
      source.target = "_blank";
      source.rel = "noreferrer";
      source.className = "benchmark-link";
      source.title = "Source";
      source.textContent = "source";
      links.append(source);
    }
    if (item.code_url) {
      const code = document.createElement("a");
      code.href = item.code_url;
      code.target = "_blank";
      code.rel = "noreferrer";
      code.className = "benchmark-link";
      code.title = "Code";
      code.textContent = "code";
      links.append(code);
    }
    if (links.children.length) chip.append(links);
    elements.benchmarkStrip.append(chip);
  });

  const softwareCount = new Set(tasks.flatMap((item) => item.software)).size;
  elements.totalTasks.textContent = number.format(tasks.length);
  elements.totalBenchmarks.textContent = number.format(benchmarks.length);
  elements.totalSoftware.textContent = number.format(softwareCount);
  elements.generatedDate.textContent = `Catalog generated ${state.catalog.generated_on}`;
  updateSavedNav();
}

function compareTasks(a, b) {
  if (state.sort === "task_id") {
    return a.task_id.localeCompare(b.task_id, undefined, { numeric: true });
  }
  if (state.sort === "software") {
    return a.software.join(", ").localeCompare(b.software.join(", ")) ||
      a.benchmark.localeCompare(b.benchmark);
  }
  return a.benchmark.localeCompare(b.benchmark) ||
    a.task_id.localeCompare(b.task_id, undefined, { numeric: true });
}

function applyFilters() {
  const query = state.search.trim().toLocaleLowerCase();
  state.filtered = state.catalog.tasks
    .filter((item) => !state.benchmark || item.benchmark === state.benchmark)
    .filter((item) => !state.software || item.software.includes(state.software))
    .filter((item) => !state.type || item.task_type === state.type)
    .filter((item) => !state.level || taskDifficulty(item) === state.level)
    .filter((item) => {
      if (state.sharedCanvas === "candidate") return Boolean(item.shared_canvas_candidate);
      if (state.sharedCanvas === "accepted") return Boolean(state.saves[savedKey(item)]);
      return true;
    })
    .filter((item) => {
      if (!query) return true;
      const haystack = [
        item.benchmark,
        item.task_id,
        item.task_name,
        item.task_type,
        item.level || "",
        item.difficulty_rationale || "",
        item.shared_canvas_rationale || "",
        ...(item.shared_canvas_regions || []),
        state.saves[savedKey(item)]?.note || "",
        ...item.software,
      ].join(" ").toLocaleLowerCase();
      return haystack.includes(query);
    })
    .sort(compareTasks);

  const pageCount = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
  state.page = Math.min(state.page, pageCount);
  elements.resultCount.textContent = number.format(state.filtered.length);
  elements.resultLabel.textContent = state.sharedCanvas === "candidate"
    ? "shared-canvas candidates to review"
    : state.sharedCanvas === "accepted"
      ? "accepted shared-canvas tasks"
      : "matching tasks";
  elements.sectionKicker.textContent = state.sharedCanvas ? "Shared canvas review" : "Task explorer";
  document.querySelectorAll(".benchmark-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.benchmark === state.benchmark);
  });
  syncUrl();
  renderResults();
}

function sourceFor(benchmark) {
  const metadata = state.catalog.benchmarks.find((item) => item.benchmark === benchmark);
  return metadata?.source_url || metadata?.code_url || "#";
}

function renderResults() {
  elements.results.replaceChildren();
  if (!state.filtered.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No tasks match these filters. Try a broader search.";
    elements.results.append(empty);
    elements.pagination.hidden = true;
    return;
  }

  const start = (state.page - 1) * PAGE_SIZE;
  const pageTasks = state.filtered.slice(start, start + PAGE_SIZE);
  const fragment = document.createDocumentFragment();

  pageTasks.forEach((item, offset) => {
    const node = elements.template.content.cloneNode(true);
    node.querySelector(".task-index").textContent = String(start + offset + 1).padStart(4, "0");
    const badges = node.querySelector(".task-badges");
    badges.append(badge(item.benchmark, "badge-benchmark"));
    item.software.slice(0, 2).forEach((name) => badges.append(badge(name, "badge-software")));
    if (item.shared_canvas_candidate) {
      badges.append(badge(`shared canvas · ${item.shared_canvas_confidence}`, "badge-shared-canvas"));
      const review = node.querySelector(".shared-canvas-review");
      review.hidden = false;
      node.querySelector(".shared-canvas-confidence").textContent = `${item.shared_canvas_confidence} confidence`;
      node.querySelector(".shared-canvas-rationale").textContent = item.shared_canvas_rationale;
      const regions = node.querySelector(".shared-canvas-regions");
      item.shared_canvas_regions.forEach((region, index) => {
        const chip = document.createElement("span");
        chip.textContent = `${agentLabel(index)}: ${region}`;
        regions.append(chip);
      });
    }
    node.querySelector(".task-preview").textContent = item.task_name;
    node.querySelector(".task-full-name").textContent = item.task_name;
    node.querySelector(".task-id").textContent = item.task_id;
    node.querySelector(".task-software").textContent = item.software.join(", ");
    node.querySelector(".task-type").textContent = item.task_type;
    const difficulty = taskDifficulty(item);
    node.querySelector(".task-difficulty").textContent = difficulty
      ? `${difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}${item.difficulty_source ? ` (${item.difficulty_source})` : ""}`
      : "Not assigned";
    if (item.difficulty_rationale) {
      const difficultyNote = node.querySelector(".task-difficulty-note");
      difficultyNote.hidden = false;
      difficultyNote.textContent = `Difficulty basis: ${item.difficulty_rationale}`;
    }
    const isAutoCAD = item.benchmark === "AutoCAD Bench";
    node.querySelectorAll(".autocad-meta").forEach((element) => { element.hidden = !isAutoCAD; });
    if (isAutoCAD) {
      node.querySelector(".task-level-split").textContent = `${item.level} / ${item.split}`;
      node.querySelector(".task-units-limit").textContent = `${item.units} / ${item.time_limit_s}s`;
      node.querySelector(".task-notes").textContent = item.notes || "Reference-image recreation task.";
      const reference = node.querySelector(".reference-button");
      reference.href = item.reference_image_url;
    }
    const key = savedKey(item);
    const saved = state.saves[key];
    const card = node.querySelector(".task-card");
    if (saved) {
      card.classList.add("is-saved");
      badges.append(badge("saved", "badge-saved"));
    }
    const noteInput = node.querySelector(".save-note-input");
    const noteLabel = node.querySelector(".save-label");
    const saveButton = node.querySelector(".save-task-button");
    const removeButton = node.querySelector(".remove-saved-button");
    const savedStatus = node.querySelector(".saved-status");
    noteInput.id = `save-note-${start + offset}`;
    noteLabel.htmlFor = noteInput.id;
    noteInput.value = saved?.note || (item.shared_canvas_candidate ? candidateNote(item) : "");
    if (saved) {
      saveButton.textContent = "Update note";
      removeButton.hidden = false;
      savedStatus.textContent = `Saved ${new Date(saved.savedAt).toLocaleDateString()}`;
    } else if (item.shared_canvas_candidate) {
      saveButton.textContent = "Accept candidate & save";
      savedStatus.textContent = "Review before accepting";
    }
    saveButton.addEventListener("click", () => {
      const note = noteInput.value.trim();
      if (!note) {
        savedStatus.textContent = "Add a note before saving.";
        noteInput.focus();
        return;
      }
      state.saves[key] = {
        note,
        savedAt: state.saves[key]?.savedAt || new Date().toISOString(),
        ...(item.shared_canvas_candidate ? { sharedCanvasAccepted: true } : {}),
      };
      delete state.rejections[key];
      localStorage.setItem(REJECTED_TASKS_KEY, JSON.stringify(state.rejections));
      persistSaves();
      saveButton.textContent = "Update note";
      removeButton.hidden = false;
      savedStatus.textContent = "Saved with note";
      showToast("Task saved");
    });
    removeButton.addEventListener("click", () => {
      delete state.saves[key];
      persistSaves();
      showToast("Removed from saved tasks");
      applyFilters();
    });
    const source = node.querySelector(".source-button");
    source.href = sourceFor(item.benchmark);
    if (item.task_definition_url) {
      const taskDefinition = document.createElement("a");
      taskDefinition.className = "source-button resource-link";
      taskDefinition.href = item.task_definition_url;
      taskDefinition.target = "_blank";
      taskDefinition.rel = "noreferrer";
      taskDefinition.textContent = "Open task definition ↗";
      node.querySelector(".task-actions").append(taskDefinition);
    }
    if (item.resource_url) {
      const actions = node.querySelector(".task-actions");
      const viewDeck = document.createElement("a");
      viewDeck.className = "source-button resource-link";
      viewDeck.href = `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(item.resource_url)}`;
      viewDeck.target = "_blank";
      viewDeck.rel = "noreferrer";
      viewDeck.textContent = "View slides ↗";
      actions.append(viewDeck);

      const downloadDeck = document.createElement("a");
      downloadDeck.className = "source-button resource-link";
      downloadDeck.href = item.resource_url;
      downloadDeck.target = "_blank";
      downloadDeck.rel = "noreferrer";
      downloadDeck.textContent = "Download slides ↓";
      actions.append(downloadDeck);
      if (item.rubric_url) {
        const rubric = document.createElement("a");
        rubric.className = "source-button";
        rubric.href = item.rubric_url;
        rubric.target = "_blank";
        rubric.rel = "noreferrer";
        rubric.textContent = "View rubric ↗";
        actions.append(rubric);
      }
      if (item.deck_name) {
        const deckRow = document.createElement("div");
        const dt = document.createElement("dt");
        dt.textContent = "Source deck";
        const dd = document.createElement("dd");
        dd.textContent = `${item.deck_name}.pptx`;
        deckRow.append(dt, dd);
        node.querySelector("dl").append(deckRow);
      }
    }
    const artifactEl = artifactsSection(item);
    if (artifactEl) {
      const detail = node.querySelector(".task-detail");
      const dl = detail.querySelector("dl");
      detail.insertBefore(artifactEl, dl.nextSibling);
    }
    const benchMeta = state.catalog.benchmarks.find((b) => b.benchmark === item.benchmark);
    if (benchMeta?.paper_url) {
      const paperLink = document.createElement("a");
      paperLink.className = "source-button";
      paperLink.href = benchMeta.paper_url;
      paperLink.target = "_blank";
      paperLink.rel = "noreferrer";
      paperLink.textContent = "Read paper ↗";
      node.querySelector(".task-actions").prepend(paperLink);
    }
    node.querySelector(".copy-button").addEventListener("click", async () => {
      await navigator.clipboard.writeText(JSON.stringify(item, null, 2));
      showToast("Task JSON copied");
    });
    fragment.append(node);
  });

  elements.results.append(fragment);
  const pageCount = Math.ceil(state.filtered.length / PAGE_SIZE);
  elements.pagination.hidden = pageCount <= 1;
  elements.pageStatus.textContent = `Page ${number.format(state.page)} of ${number.format(pageCount)}`;
  elements.previous.disabled = state.page === 1;
  elements.next.disabled = state.page === pageCount;
}

function resetFilters() {
  Object.assign(state, { page: 1, benchmark: "", software: "", type: "", level: "", sharedCanvas: "", search: "", sort: "benchmark" });
  elements.search.value = "";
  elements.benchmarkFilter.value = "";
  elements.sharedCanvasFilter.value = "";
  elements.sort.value = "benchmark";
  updateDependentFilters();
  applyFilters();
}

function renderSavedDrawer() {
  const keys = Object.keys(state.saves);
  const hasSaved = keys.length > 0;
  elements.savedEmpty.hidden = hasSaved;
  elements.savedGrid.hidden = !hasSaved;
  elements.exportSaved.hidden = !hasSaved;
  elements.clearSaved.hidden = !hasSaved;

  if (!hasSaved) {
    elements.savedGrid.replaceChildren();
    return;
  }

  const tasks = state.catalog.tasks;
  const fragment = document.createDocumentFragment();

  const savedTasks = keys
    .map((key) => {
      const task = tasks.find((t) => savedKey(t) === key);
      return task ? { task, save: state.saves[key] } : null;
    })
    .filter(Boolean)
    .sort((a, b) => new Date(b.save.savedAt) - new Date(a.save.savedAt));

  savedTasks.forEach(({ task, save }) => {
    const card = document.createElement("article");
    card.className = "saved-card";

    const top = document.createElement("div");
    top.className = "saved-card-top";
    top.append(badge(task.benchmark, "badge-benchmark"));
    task.software.slice(0, 2).forEach((s) => top.append(badge(s, "badge-software")));
    if (task.shared_canvas_candidate) top.append(badge("shared canvas", "badge-shared-canvas"));

    const body = document.createElement("div");
    body.className = "saved-card-body";
    const name = document.createElement("div");
    name.className = "saved-card-name";
    name.textContent = task.task_name;
    const id = document.createElement("div");
    id.className = "saved-card-id";
    id.textContent = task.task_id;
    body.append(name, id);

    const note = document.createElement("div");
    note.className = "saved-card-note";
    note.textContent = save.note;

    const footer = document.createElement("div");
    footer.className = "saved-card-footer";
    const date = document.createElement("span");
    date.className = "saved-card-date";
    date.textContent = `Saved ${new Date(save.savedAt).toLocaleDateString()}`;
    const actions = document.createElement("div");
    actions.className = "saved-card-actions";

    const copyBtn = document.createElement("button");
    copyBtn.className = "saved-card-action";
    copyBtn.type = "button";
    copyBtn.textContent = "Copy JSON";
    copyBtn.addEventListener("click", async () => {
      await navigator.clipboard.writeText(JSON.stringify({
        ...task,
        saved_note: save.note,
        saved_at: save.savedAt,
        shared_canvas_accepted: Boolean(save.sharedCanvasAccepted),
      }, null, 2));
      showToast("Task JSON copied");
    });

    const removeBtn = document.createElement("button");
    removeBtn.className = "saved-card-action remove";
    removeBtn.type = "button";
    removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", () => {
      delete state.saves[savedKey(task)];
      persistSaves();
      renderSavedDrawer();
      applyFilters();
      showToast("Removed from saved tasks");
    });

    actions.append(copyBtn, removeBtn);
    footer.append(date, actions);
    card.append(top, body, note, footer);
    fragment.append(card);
  });

  elements.savedGrid.replaceChildren(fragment);
}

function toggleSavedDrawer(open) {
  const show = open !== undefined ? open : elements.savedDrawer.hidden;
  elements.savedDrawer.hidden = !show;
  elements.savedTasksButton.classList.toggle("active", show);
  elements.savedTasksButton.setAttribute("aria-pressed", String(show));
  if (show) {
    renderSavedDrawer();
    elements.savedDrawer.scrollIntoView({ behavior: "smooth" });
  }
}

function sharedDecision(item) {
  const key = savedKey(item);
  if (state.saves[key]) return "approved";
  if (state.rejections[key]) return "rejected";
  return "pending";
}

function confidenceRank(item) {
  const order = { high: 0, medium: 1, low: 2 };
  return item.shared_canvas_confidence in order ? order[item.shared_canvas_confidence] : 3;
}

function renderSharedCanvasCriteria(data) {
  const criterion = document.querySelector("#sharedCriterion");
  if (criterion && data?.criterion) criterion.textContent = data.criterion;
  const list = document.querySelector("#sharedExclusions");
  if (list && Array.isArray(data?.exclusions)) {
    list.replaceChildren();
    data.exclusions.forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      list.append(li);
    });
  }
}

function sharedReviewItems() {
  return state.catalog.tasks.filter((item) => {
    const key = savedKey(item);
    return item.shared_canvas_candidate || state.saves[key] || state.rejections[key];
  });
}

function persistSharedReview() {
  localStorage.setItem(SAVED_TASKS_KEY, JSON.stringify(state.saves));
  localStorage.setItem(REJECTED_TASKS_KEY, JSON.stringify(state.rejections));
  updateSavedNav();
  renderSharedCanvasView();
  if (!elements.savedDrawer.hidden) renderSavedDrawer();
}

function renderSharedCanvasView() {
  const reviewItems = sharedReviewItems();
  const candidates = reviewItems.filter((item) => item.shared_canvas_candidate);
  const approved = reviewItems.filter((item) => sharedDecision(item) === "approved");
  const pending = candidates.filter((item) => sharedDecision(item) === "pending");

  elements.sharedCandidateTotal.textContent = number.format(candidates.length);
  elements.sharedApprovedTotal.textContent = number.format(approved.length);
  elements.sharedPendingTotal.textContent = number.format(pending.length);

  const benchmarkStats = state.catalog.benchmarks.map((metadata) => {
    const tasks = reviewItems.filter((item) => item.benchmark === metadata.benchmark);
    return {
      name: metadata.benchmark,
      total: tasks.length,
      pending: tasks.filter((item) => sharedDecision(item) === "pending").length,
      approved: tasks.filter((item) => sharedDecision(item) === "approved").length,
      rejected: tasks.filter((item) => sharedDecision(item) === "rejected").length,
    };
  });

  if (state.sharedReviewBenchmark && !benchmarkStats.some((item) => item.name === state.sharedReviewBenchmark)) {
    state.sharedReviewBenchmark = "";
  }

  while (elements.sharedBenchmarkFilter.options.length > 1) elements.sharedBenchmarkFilter.remove(1);
  benchmarkStats.forEach((stats) => elements.sharedBenchmarkFilter.append(option(stats.name, `${stats.name} (${stats.total})`)));
  elements.sharedBenchmarkFilter.value = state.sharedReviewBenchmark;

  const benchScoped = state.sharedReviewBenchmark
    ? reviewItems.filter((item) => item.benchmark === state.sharedReviewBenchmark)
    : reviewItems;

  const levels = DIFFICULTY_ORDER.filter((level) => benchScoped.some((item) => taskDifficulty(item) === level));
  while (elements.sharedDifficultyFilter.options.length > 1) elements.sharedDifficultyFilter.remove(1);
  levels.forEach((level) => elements.sharedDifficultyFilter.append(option(level, level.charAt(0).toUpperCase() + level.slice(1))));
  if (state.sharedReviewLevel && !levels.includes(state.sharedReviewLevel)) state.sharedReviewLevel = "";
  elements.sharedDifficultyFilter.value = state.sharedReviewLevel;

  const software = [...new Set(benchScoped.flatMap((item) => item.software))].sort();
  while (elements.sharedSoftwareFilter.options.length > 1) elements.sharedSoftwareFilter.remove(1);
  software.forEach((name) => elements.sharedSoftwareFilter.append(option(name)));
  if (state.sharedReviewSoftware && !software.includes(state.sharedReviewSoftware)) state.sharedReviewSoftware = "";
  elements.sharedSoftwareFilter.value = state.sharedReviewSoftware;

  elements.sharedBenchmarkTabs.replaceChildren();
  const allTab = document.createElement("button");
  allTab.type = "button";
  allTab.className = "shared-benchmark-tab";
  allTab.setAttribute("role", "tab");
  allTab.setAttribute("aria-selected", String(!state.sharedReviewBenchmark));
  if (!state.sharedReviewBenchmark) allTab.classList.add("active");
  const allName = document.createElement("strong");
  allName.textContent = "All benchmarks";
  const allProgress = document.createElement("span");
  allProgress.textContent = `${approved.length} approved · ${pending.length} pending`;
  allTab.append(allName, allProgress);
  allTab.addEventListener("click", () => {
    state.sharedReviewBenchmark = "";
    state.sharedReviewPage = 1;
    renderSharedCanvasView();
  });
  elements.sharedBenchmarkTabs.append(allTab);

  benchmarkStats.forEach((stats) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "shared-benchmark-tab";
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", String(stats.name === state.sharedReviewBenchmark));
    if (stats.name === state.sharedReviewBenchmark) button.classList.add("active");
    const name = document.createElement("strong");
    name.textContent = stats.name;
    const progress = document.createElement("span");
    progress.textContent = `${stats.approved} approved · ${stats.pending} pending${stats.rejected ? ` · ${stats.rejected} rejected` : ""}`;
    button.append(name, progress);
    button.addEventListener("click", () => {
      state.sharedReviewBenchmark = stats.name;
      state.sharedReviewPage = 1;
      renderSharedCanvasView();
    });
    elements.sharedBenchmarkTabs.append(button);
  });

  elements.sharedStatusFilter.value = state.sharedReviewStatus;
  const filteredQueue = reviewItems
    .filter((item) => !state.sharedReviewBenchmark || item.benchmark === state.sharedReviewBenchmark)
    .filter((item) => !state.sharedReviewLevel || taskDifficulty(item) === state.sharedReviewLevel)
    .filter((item) => !state.sharedReviewSoftware || item.software.includes(state.sharedReviewSoftware))
    .filter((item) => state.sharedReviewStatus === "all" || sharedDecision(item) === state.sharedReviewStatus)
    .sort((a, b) =>
      confidenceRank(a) - confidenceRank(b)
      || a.benchmark.localeCompare(b.benchmark)
      || a.task_id.localeCompare(b.task_id, undefined, { numeric: true })
    );
  const pageCount = Math.max(1, Math.ceil(filteredQueue.length / SHARED_PAGE_SIZE));
  state.sharedReviewPage = Math.min(state.sharedReviewPage, pageCount);
  const queueStart = (state.sharedReviewPage - 1) * SHARED_PAGE_SIZE;
  const queue = filteredQueue.slice(queueStart, queueStart + SHARED_PAGE_SIZE);

  elements.sharedQueueTitle.textContent = state.sharedReviewBenchmark || "All benchmarks";
  elements.sharedQueueCount.textContent = `${number.format(filteredQueue.length)} ${state.sharedReviewStatus === "all" ? "tasks" : state.sharedReviewStatus}`;
  elements.sharedCanvasEmpty.hidden = filteredQueue.length > 0;
  elements.sharedCanvasTaskGrid.hidden = filteredQueue.length === 0;
  elements.sharedPagination.hidden = pageCount <= 1;
  elements.sharedPageStatus.textContent = `Page ${number.format(state.sharedReviewPage)} of ${number.format(pageCount)}`;
  elements.sharedPreviousPage.disabled = state.sharedReviewPage === 1;
  elements.sharedNextPage.disabled = state.sharedReviewPage === pageCount;
  elements.sharedCanvasEmptyCopy.textContent = state.sharedReviewStatus === "pending"
    ? "All matching candidates have been approved or rejected."
    : `No matching ${state.sharedReviewStatus} tasks.`;

  const fragment = document.createDocumentFragment();
  queue.forEach((item) => {
    const key = savedKey(item);
    const decision = sharedDecision(item);
    const card = document.createElement("article");
    card.className = `shared-approval-card is-${decision}`;

    const badges = document.createElement("div");
    badges.className = "task-badges";
    badges.append(badge(item.benchmark, "badge-benchmark"));
    item.software.slice(0, 2).forEach((name) => badges.append(badge(name, "badge-software")));
    if (item.shared_canvas_candidate) badges.append(badge(`${item.shared_canvas_confidence} confidence`, "badge-shared-canvas"));
    badges.append(badge(decision, `badge-decision badge-${decision}`));

    const title = document.createElement("h3");
    title.textContent = item.task_name;
    const id = document.createElement("div");
    id.className = "shared-approval-id";
    id.textContent = item.task_id;

    const rationale = document.createElement("p");
    rationale.className = "shared-approval-rationale";
    rationale.textContent = item.shared_canvas_rationale || state.saves[key]?.note || "Previously saved as a shared-canvas task.";

    const regions = document.createElement("div");
    regions.className = "shared-canvas-regions";
    (item.shared_canvas_regions || []).forEach((region, index) => {
      const chip = document.createElement("span");
      chip.textContent = `${agentLabel(index)}: ${region}`;
      regions.append(chip);
    });

    const noteLabel = document.createElement("label");
    noteLabel.className = "save-label";
    noteLabel.textContent = "Saved-task note";
    const note = document.createElement("textarea");
    note.className = "save-note-input shared-approval-note";
    note.rows = 3;
    note.maxLength = 600;
    note.value = state.saves[key]?.note || candidateNote(item);
    noteLabel.append(note);

    const actions = document.createElement("div");
    actions.className = "shared-approval-actions";
    const approve = document.createElement("button");
    approve.type = "button";
    approve.className = "save-task-button";
    approve.textContent = decision === "approved" ? "Update saved note" : "Approve & save";
    approve.addEventListener("click", () => {
      const value = note.value.trim();
      if (!value) {
        note.focus();
        showToast("Add a note before approving");
        return;
      }
      delete state.rejections[key];
      state.saves[key] = {
        note: value,
        savedAt: state.saves[key]?.savedAt || new Date().toISOString(),
        sharedCanvasAccepted: true,
      };
      persistSharedReview();
      showToast(decision === "approved" ? "Saved note updated" : "Task approved and saved");
    });

    const reject = document.createElement("button");
    reject.type = "button";
    reject.className = "shared-reject-button";
    reject.textContent = decision === "rejected" ? "Return to queue" : "Reject";
    reject.addEventListener("click", () => {
      if (decision === "rejected") {
        delete state.rejections[key];
        persistSharedReview();
        showToast("Task returned to approval queue");
        return;
      }
      delete state.saves[key];
      state.rejections[key] = { rejectedAt: new Date().toISOString() };
      persistSharedReview();
      showToast("Task rejected");
    });

    const source = document.createElement("a");
    source.className = "source-button";
    source.href = sourceFor(item.benchmark);
    source.target = "_blank";
    source.rel = "noreferrer";
    source.textContent = "Open source ↗";
    actions.append(approve, reject, source);
    card.append(badges, title, id, rationale);
    if (regions.children.length) card.append(regions);
    const reviewArtifacts = artifactsSection(item);
    if (reviewArtifacts) card.append(reviewArtifacts);
    card.append(noteLabel, actions);
    fragment.append(card);
  });
  elements.sharedCanvasTaskGrid.replaceChildren(fragment);
}

function toggleSharedCanvasView(open) {
  const show = open !== undefined ? open : elements.sharedCanvasView.hidden;
  state.view = show ? "shared-canvas" : "";
  elements.sharedCanvasView.hidden = !show;
  elements.hero.hidden = show;
  elements.catalogShell.hidden = show;
  elements.savedDrawer.hidden = true;
  elements.researchDrawer.hidden = true;
  elements.savedTasksButton.classList.remove("active");
  elements.researchButton.classList.remove("active");
  elements.sharedCanvasButton.classList.toggle("active", show);
  elements.sharedCanvasButton.setAttribute("aria-pressed", String(show));
  if (show) renderSharedCanvasView();
  syncUrl();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function exportSaved() {
  const tasks = state.catalog.tasks;
  const savedTasks = Object.entries(state.saves)
    .map(([key, save]) => {
      const task = tasks.find((t) => savedKey(t) === key);
      return task ? {
        ...task,
        saved_note: save.note,
        saved_at: save.savedAt,
        shared_canvas_accepted: Boolean(save.sharedCanvasAccepted),
      } : null;
    })
    .filter(Boolean);
  const payload = {
    exported_on: new Date().toISOString(),
    task_count: savedTasks.length,
    tasks: savedTasks,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "saved_benchmark_tasks.json";
  link.click();
  URL.revokeObjectURL(url);
  showToast(`Exported ${number.format(savedTasks.length)} saved tasks`);
}

function exportFiltered() {
  const tasks = state.filtered.map((item) => {
    const saved = state.saves[savedKey(item)];
    return saved ? { ...item, saved_note: saved.note, saved_at: saved.savedAt } : item;
  });
  const payload = {
    exported_on: new Date().toISOString(),
    filters: {
      search: state.search,
      benchmark: state.benchmark,
      software: state.software,
      task_type: state.type,
      difficulty: state.level,
      shared_canvas: state.sharedCanvas,
    },
    task_count: state.filtered.length,
    tasks,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "benchmark_tasks_filtered.json";
  link.click();
  URL.revokeObjectURL(url);
  showToast(`Exported ${number.format(state.filtered.length)} tasks`);
}

const RESEARCH_BENCHMARKS = [
  {
    name: "ScratchWorld",
    tasks: "83 tasks",
    meta: "MIT Scratch · Create, Debug, Extend, Compute",
    desc: "Program-by-construction tasks in Scratch with primitive drag-and-drop and composite interaction modes. The catalog adds transparent derived difficulty labels because the benchmark does not publish per-task levels.",
    tags: [["block programming","rt-2d"],["in catalog","rt-catalog"]],
    links: {paper:"https://arxiv.org/abs/2602.10814",code:"https://github.com/astarforbae/ScratchWorld"},
    shared: "med", multi: null, inCatalog: true,
  },
  {
    name: "CANVAS",
    tasks: "598 tasks",
    meta: "Figma · Replication + modification",
    desc: "Tool-based Figma design tasks. Multiple agents could each handle different components on the same canvas.",
    tags: [["shared canvas","rt-shared"],["2D design","rt-2d"],["in catalog","rt-catalog"]],
    links: {paper:"https://arxiv.org/abs/2511.20737",code:"https://github.com/kixlab/CANVAS",data:"https://huggingface.co/datasets/seooyxx/canvas"},
    shared: "high", multi: null, inCatalog: true,
  },
  {
    name: "PSBench",
    tasks: "600 tasks",
    meta: "Adobe Photoshop · Image editing",
    desc: "Large Photoshop editing set. Multi-cursor potential: independent layer operations could run in parallel (masking + color correction).",
    tags: [["2D editing","rt-2d"],["multi-cursor","rt-multi"],["in catalog","rt-catalog"]],
    links: {paper:"https://openreview.net/forum?id=O93cZGxYB1",code:"https://github.com/zyn1216/PSBench"},
    shared: "med", multi: "med", inCatalog: true,
  },
  {
    name: "CutVerse",
    tasks: "186 tasks",
    meta: "Premiere Pro, After Effects, Photoshop, DaVinci, JianYing, ComfyUI, Keling",
    desc: "Media post-production. Timeline is a shared canvas: one agent on audio, another on VFX, another on masking—all on the same timeline.",
    tags: [["shared canvas","rt-shared"],["in catalog","rt-catalog"]],
    links: {paper:"https://arxiv.org/abs/2605.19484",code:"https://github.com/CUC-MIPG/CutVerse"},
    shared: "high", multi: null, inCatalog: true,
  },
  {
    name: "ParaGUIBench",
    tasks: "233 tasks",
    meta: "Chrome, LibreOffice, Ubuntu · Parallel multi-device",
    desc: "The only benchmark purpose-built for parallel GUI agent execution. Multiple agents on separate desktop instances working on coordinated tasks.",
    tags: [["multi-cursor native","rt-multi"],["in catalog","rt-catalog"]],
    links: {paper:"https://arxiv.org/abs/2607.22689",code:"https://github.com/pkgunboat/ParaGUIBench"},
    shared: null, multi: "high", inCatalog: true,
  },
  {
    name: "DeskCraft",
    tasks: "538 tasks",
    meta: "Multi-app desktop · Standard + interactive",
    desc: "Desktop agent workflows across multiple apps. Interactive multi-phase flows could be parallelized: one agent per app.",
    tags: [["multi-cursor","rt-multi"],["in catalog","rt-catalog"]],
    links: {paper:"https://arxiv.org/abs/2606.03103",code:"https://github.com/mrwwk/DeskCraft"},
    shared: null, multi: "med", inCatalog: true,
  },
  {
    name: "OSWorld",
    tasks: "369 tasks",
    meta: "Full Ubuntu desktop · Multi-app",
    desc: "Full desktop environment. Multi-app tasks can be decomposed to parallel agents.",
    tags: [["multi-cursor","rt-multi"],["in catalog","rt-catalog"]],
    links: {paper:"https://arxiv.org/abs/2404.07972",code:"https://github.com/xlang-ai/OSWorld"},
    shared: null, multi: "med", inCatalog: true,
  },
  {
    name: "GUIDE",
    tasks: "40 tasks",
    meta: "Figma, Canva, PowerPoint, Google Slides, Photoshop, and more",
    desc: "Open-ended creative tasks across paired design apps. Tasks like “design a poster” can be split among agents working on the same canvas.",
    tags: [["shared canvas","rt-shared"],["2D design","rt-2d"],["in catalog","rt-catalog"]],
    links: {paper:"https://arxiv.org/abs/2603.25864",data:"https://huggingface.co/datasets/kixlab/GuideBench",project:"https://guide-bench.github.io/"},
    shared: "med", multi: null, inCatalog: true,
  },
  {
    name: "GraphicBench",
    tasks: "1,079 tasks",
    meta: "Web-based design · Book covers, business cards, postcards, posters",
    desc: "Multi-agent planning benchmark with 3 design experts (Photo Editor, Vector Graphic Editor, Layout Designer) + supervisor on one canvas. Closest existing benchmark to multi-agent shared canvas.",
    tags: [["shared canvas","rt-shared"],["2D design","rt-2d"],["to add","rt-new"]],
    links: {paper:"https://arxiv.org/abs/2504.11571"},
    shared: "high", multi: "med", inCatalog: false,
    fit: "Shared canvas: High — multi-agent framework already built in. Multi-cursor: Medium — shared canvas, not separate instances.",
  },
  {
    name: "Cua-Bench",
    tasks: "130+ tasks",
    meta: "42 environments · 5 platforms (Linux, Windows, Android, browser, simulated)",
    desc: "MIT-licensed framework for parallel computer use. Multi-player is first-class: separate synthetic cursors per agent, separate sessions and recordings.",
    tags: [["multi-cursor native","rt-multi"],["to add","rt-new"]],
    links: {docs:"https://cua.ai/docs/concepts/what-is-cua-bench",code:"https://github.com/hami-sh/cua",blog:"https://cua.ai/blog/computer-use-2-ai-engineer-worlds-fair"},
    shared: null, multi: "high", inCatalog: false,
    fit: "Multi-cursor: Very high — purpose-built for parallel CU. Shared canvas: Low — agents get separate windows.",
  },
  {
    name: "MMBench-GUI",
    tasks: "8,123 tasks",
    meta: "6 platforms (Windows, macOS, Linux, iOS, Android, Web) · 4 levels · CVPR 2026",
    desc: "Massive hierarchical benchmark. L4 “Task Collaboration” (248 tasks) evaluates cross-app coordination and information flow. Full L1–L4 hierarchy from understanding to multi-app orchestration.",
    tags: [["shared canvas","rt-shared"],["multi-cursor","rt-multi"],["to add","rt-new"]],
    links: {paper:"https://arxiv.org/abs/2507.19478",code:"https://github.com/open-compass/mmbench-gui"},
    shared: "med", multi: "high", inCatalog: false,
    fit: "Shared canvas: Medium-High (L4 cross-app coordination). Multi-cursor: High (L3–L4 tasks decompose across parallel cursors).",
  },
  {
    name: "ProSoftArena",
    tasks: "436 tasks",
    meta: "13 professional applications · 6 disciplines · CVPR 2026",
    desc: "Professional software benchmark. L3 tasks require multi-software workflows. Dense pro app canvases (CAD, scientific visualization) are the hardest shared-observation test.",
    tags: [["shared canvas","rt-shared"],["2D / professional","rt-2d"],["to add","rt-new"]],
    links: {paper:"https://arxiv.org/abs/2601.02399"},
    shared: "high", multi: "med", inCatalog: false,
    fit: "Shared canvas: High — dense professional canvases. Multi-cursor: Medium — L3 multi-software tasks could parallelize.",
  },
  {
    name: "WindowsWorld",
    tasks: "181 tasks",
    meta: "17 desktop apps · 78% multi-application · ACL 2026 Findings",
    desc: "Cross-application Windows workflows with sub-goals. 78% of tasks span multiple apps, making it natural to assign one cursor per app.",
    tags: [["multi-cursor","rt-multi"],["to add","rt-new"]],
    links: {paper:"https://arxiv.org/abs/2604.27776",code:"https://github.com/HITsz-TMG/WindowsWorld"},
    shared: null, multi: "high", inCatalog: false,
    fit: "Multi-cursor: High — multi-app tasks decompose to one agent per window. Shared canvas: Low.",
  },
  {
    name: "AUI-Gym",
    tasks: "1,560 tasks",
    meta: "52 applications · NeurIPS 2025",
    desc: "GUI design benchmark: Coder generates websites, CUA (Computer-Use Agent) evaluates them. Inherently multi-agent on a shared artifact (the generated UI).",
    tags: [["2D / UI design","rt-2d"],["shared canvas","rt-shared"],["to add","rt-new"]],
    links: {paper:"https://arxiv.org/abs/2511.15567"},
    shared: "high", multi: null, inCatalog: false,
    fit: "Shared canvas: High — both agents observe the same 2D artifact. Multi-cursor: Low — designer vs. judge roles, not parallel cursors.",
  },
  {
    name: "DesignBench",
    tasks: "900 tasks",
    meta: "React, Vue, Angular, HTML/CSS · Generation, edit, repair",
    desc: "Front-end engineering benchmark across 4 frameworks and 3 task types. Agents generate, edit, and repair web UIs. Relevant for multi-agent workflows by framework or task type.",
    tags: [["2D / front-end","rt-2d"],["to add","rt-new"]],
    links: {paper:"https://arxiv.org/abs/2506.06251"},
    shared: "med", multi: "med", inCatalog: false,
    fit: "Shared canvas: Medium — shared UI, but editing is code-level. Multi-cursor: Medium — edit and repair can run in parallel.",
  },
];

function createResearchCard(b) {
  const card = document.createElement("article");
  card.className = "research-card";

  const head = document.createElement("div");
  head.className = "research-card-head";
  const name = document.createElement("p");
  name.className = "research-card-name";
  name.textContent = b.name;
  const tags = document.createElement("div");
  tags.className = "research-card-tags";
  b.tags.forEach(([label, cls]) => {
    const t = document.createElement("span");
    t.className = `research-tag ${cls}`;
    t.textContent = label;
    tags.append(t);
  });
  head.append(name, tags);

  const meta = document.createElement("p");
  meta.className = "research-card-meta";
  meta.textContent = `${b.tasks} · ${b.meta}`;

  const desc = document.createElement("p");
  desc.className = "research-card-desc";
  desc.textContent = b.desc;

  const links = document.createElement("div");
  links.className = "research-card-links";
  Object.entries(b.links).forEach(([label, href]) => {
    const a = document.createElement("a");
    a.href = href;
    a.target = "_blank";
    a.rel = "noreferrer";
    a.textContent = label;
    links.append(a);
  });

  card.append(head, meta, desc, links);

  if (b.fit) {
    const fit = document.createElement("div");
    fit.className = "research-card-fit";
    fit.innerHTML = b.fit.replace(/(High|Very high)/g, '<strong>$1</strong>').replace(/(Medium(?:-High)?|Medium)/g, '<strong>$1</strong>').replace(/(Low)/g, '<strong>$1</strong>');
    card.append(fit);
  }

  return card;
}

function renderResearch() {
  const shared = document.querySelector("#sharedCanvasGrid");
  const multi = document.querySelector("#multiCursorGrid");
  const toAdd = document.querySelector("#toAddGrid");
  shared.replaceChildren();
  multi.replaceChildren();
  toAdd.replaceChildren();

  const sharedBenches = RESEARCH_BENCHMARKS.filter((b) => b.shared === "high").sort((a, b) => a.inCatalog - b.inCatalog);
  const multiBenches = RESEARCH_BENCHMARKS.filter((b) => b.multi === "high" || b.multi === "med" && !b.inCatalog).sort((a, b) => (b.multi === "high" ? 1 : 0) - (a.multi === "high" ? 1 : 0));
  const toAddBenches = RESEARCH_BENCHMARKS.filter((b) => !b.inCatalog);

  sharedBenches.forEach((b) => shared.append(createResearchCard(b)));
  multiBenches.forEach((b) => multi.append(createResearchCard(b)));
  toAddBenches.forEach((b) => toAdd.append(createResearchCard(b)));
}

function toggleResearch(open) {
  const show = open !== undefined ? open : elements.researchDrawer.hidden;
  elements.researchDrawer.hidden = !show;
  elements.researchButton.classList.toggle("active", show);
  elements.researchButton.setAttribute("aria-pressed", String(show));
  if (show) {
    renderResearch();
    elements.researchDrawer.scrollIntoView({ behavior: "smooth" });
  }
}

function wireEvents() {
  let searchTimer;
  elements.search.addEventListener("input", (event) => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
      state.search = event.target.value;
      state.page = 1;
      applyFilters();
    }, 120);
  });
  elements.benchmarkFilter.addEventListener("change", (event) => {
    state.benchmark = event.target.value;
    updateDependentFilters();
    state.page = 1;
    applyFilters();
  });
  elements.softwareFilter.addEventListener("change", (event) => {
    state.software = event.target.value;
    state.page = 1;
    applyFilters();
  });
  elements.typeFilter.addEventListener("change", (event) => {
    state.type = event.target.value;
    state.page = 1;
    applyFilters();
  });
  if (elements.levelFilter) {
    elements.levelFilter.addEventListener("change", (event) => {
      state.level = event.target.value;
      state.page = 1;
      applyFilters();
    });
  }
  elements.sharedCanvasFilter.addEventListener("change", (event) => {
    state.sharedCanvas = event.target.value;
    state.page = 1;
    applyFilters();
  });
  elements.sort.addEventListener("change", (event) => {
    state.sort = event.target.value;
    state.page = 1;
    applyFilters();
  });
  elements.reset.addEventListener("click", resetFilters);
  elements.exportButton.addEventListener("click", exportFiltered);
  elements.sharedCanvasButton.addEventListener("click", () => toggleSharedCanvasView());
  elements.closeSharedCanvas.addEventListener("click", () => toggleSharedCanvasView(false));
  elements.sharedBenchmarkFilter.addEventListener("change", (event) => {
    state.sharedReviewBenchmark = event.target.value;
    state.sharedReviewPage = 1;
    renderSharedCanvasView();
  });
  elements.sharedDifficultyFilter.addEventListener("change", (event) => {
    state.sharedReviewLevel = event.target.value;
    state.sharedReviewPage = 1;
    renderSharedCanvasView();
  });
  elements.sharedSoftwareFilter.addEventListener("change", (event) => {
    state.sharedReviewSoftware = event.target.value;
    state.sharedReviewPage = 1;
    renderSharedCanvasView();
  });
  elements.sharedStatusFilter.addEventListener("change", (event) => {
    state.sharedReviewStatus = event.target.value;
    state.sharedReviewPage = 1;
    renderSharedCanvasView();
  });
  elements.sharedPreviousPage.addEventListener("click", () => {
    state.sharedReviewPage -= 1;
    renderSharedCanvasView();
    elements.sharedCanvasView.scrollIntoView({ behavior: "smooth" });
  });
  elements.sharedNextPage.addEventListener("click", () => {
    state.sharedReviewPage += 1;
    renderSharedCanvasView();
    elements.sharedCanvasView.scrollIntoView({ behavior: "smooth" });
  });
  elements.researchButton.addEventListener("click", () => {
    if (state.view === "shared-canvas") toggleSharedCanvasView(false);
    toggleResearch();
  });
  elements.closeResearch.addEventListener("click", () => toggleResearch(false));
  try {
    const savedNotes = localStorage.getItem("benchmark-research-notes");
    if (savedNotes) elements.researchNotes.value = savedNotes;
  } catch {}
  elements.researchNotes.addEventListener("input", () => {
    try { localStorage.setItem("benchmark-research-notes", elements.researchNotes.value); } catch {}
  });
  elements.savedTasksButton.addEventListener("click", () => {
    if (state.view === "shared-canvas") toggleSharedCanvasView(false);
    toggleSavedDrawer();
  });
  elements.closeSavedDrawer.addEventListener("click", () => toggleSavedDrawer(false));
  elements.exportSaved.addEventListener("click", exportSaved);
  elements.clearSaved.addEventListener("click", () => {
    if (!Object.keys(state.saves).length) return;
    if (!confirm("Remove all saved tasks? This cannot be undone.")) return;
    state.saves = {};
    persistSaves();
    renderSavedDrawer();
    applyFilters();
    showToast("All saved tasks cleared");
  });
  elements.previous.addEventListener("click", () => {
    state.page -= 1;
    renderResults();
    document.querySelector("#catalog-title").scrollIntoView({ behavior: "smooth" });
  });
  elements.next.addEventListener("click", () => {
    state.page += 1;
    renderResults();
    document.querySelector("#catalog-title").scrollIntoView({ behavior: "smooth" });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement !== elements.search) {
      event.preventDefault();
      elements.search.focus();
    }
    if (event.key === "Escape" && document.activeElement === elements.search) {
      elements.search.blur();
    }
  });
}

async function init() {
  loadSaves();
  readUrl();
  try {
    const [catalogResponse, candidatesResponse] = await Promise.all([
      fetch("./benchmark_tasks.json?v=17"),
      fetch("./shared_canvas_candidates.json?v=5"),
    ]);
    if (!catalogResponse.ok) throw new Error(`Dataset request failed (${catalogResponse.status})`);
    if (!candidatesResponse.ok) throw new Error(`Candidate review data failed (${candidatesResponse.status})`);
    state.catalog = await catalogResponse.json();
    const candidateData = await candidatesResponse.json();
    renderSharedCanvasCriteria(candidateData);
    const candidates = new Map(candidateData.tasks.map((item) => [`${item.benchmark}::${item.task_id}`, item]));
    state.catalog.tasks.forEach((item) => {
      const candidate = candidates.get(savedKey(item));
      if (!candidate) return;
      item.shared_canvas_candidate = true;
      item.shared_canvas_confidence = candidate.confidence;
      item.shared_canvas_rationale = candidate.rationale;
      item.shared_canvas_regions = candidate.regions;
      item.shared_canvas_note = candidate.suggested_note;
    });
    populateFilters();
    wireEvents();
    applyFilters();
    elements.loading.hidden = true;
    if (state.view === "shared-canvas") toggleSharedCanvasView(true);
  } catch (error) {
    elements.loading.hidden = true;
    elements.error.hidden = false;
    elements.error.textContent = `Could not load the task catalog: ${error.message}`;
  }
}

init();
