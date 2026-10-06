const PAGE_SIZE = 40;

const state = {
  catalog: null,
  filtered: [],
  page: 1,
  benchmark: "",
  software: "",
  type: "",
  search: "",
  sort: "benchmark",
};

const elements = {
  benchmarkFilter: document.querySelector("#benchmarkFilter"),
  benchmarkStrip: document.querySelector("#benchmarkStrip"),
  error: document.querySelector("#errorState"),
  exportButton: document.querySelector("#exportButton"),
  generatedDate: document.querySelector("#generatedDate"),
  loading: document.querySelector("#loadingState"),
  next: document.querySelector("#nextPage"),
  pageStatus: document.querySelector("#pageStatus"),
  pagination: document.querySelector("#pagination"),
  previous: document.querySelector("#previousPage"),
  reset: document.querySelector("#resetFilters"),
  resultCount: document.querySelector("#resultCount"),
  results: document.querySelector("#results"),
  search: document.querySelector("#searchInput"),
  softwareFilter: document.querySelector("#softwareFilter"),
  sort: document.querySelector("#sortSelect"),
  template: document.querySelector("#taskTemplate"),
  toast: document.querySelector("#toast"),
  totalBenchmarks: document.querySelector("#totalBenchmarks"),
  totalSoftware: document.querySelector("#totalSoftware"),
  totalTasks: document.querySelector("#totalTasks"),
  typeFilter: document.querySelector("#typeFilter"),
};

const number = new Intl.NumberFormat("en-US");

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

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    elements.toast.classList.remove("visible");
  }, 1800);
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.search) params.set("q", state.search);
  if (state.benchmark) params.set("benchmark", state.benchmark);
  if (state.software) params.set("software", state.software);
  if (state.type) params.set("type", state.type);
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
  state.sort = params.get("sort") || "benchmark";
}

function populateFilters() {
  const tasks = state.catalog.tasks;
  const benchmarks = state.catalog.benchmarks.map((item) => item.benchmark);
  const software = [...new Set(tasks.flatMap((item) => item.software))].sort();
  const types = [...new Set(tasks.map((item) => item.task_type))].sort();

  benchmarks.forEach((value) => elements.benchmarkFilter.append(option(value)));
  software.forEach((value) => elements.softwareFilter.append(option(value)));
  types.forEach((value) => elements.typeFilter.append(option(value)));

  elements.search.value = state.search;
  elements.benchmarkFilter.value = state.benchmark;
  elements.softwareFilter.value = state.software;
  elements.typeFilter.value = state.type;
  elements.sort.value = state.sort;

  state.catalog.benchmarks.forEach((item) => {
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
      state.page = 1;
      applyFilters();
      document.querySelector("#catalog-title").scrollIntoView({ behavior: "smooth" });
    });
    elements.benchmarkStrip.append(button);
  });

  elements.totalTasks.textContent = number.format(tasks.length);
  elements.totalBenchmarks.textContent = number.format(benchmarks.length);
  elements.totalSoftware.textContent = number.format(software.length);
  elements.generatedDate.textContent = `Catalog generated ${state.catalog.generated_on}`;
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
    .filter((item) => {
      if (!query) return true;
      const haystack = [
        item.benchmark,
        item.task_id,
        item.task_name,
        item.task_type,
        ...item.software,
      ].join(" ").toLocaleLowerCase();
      return haystack.includes(query);
    })
    .sort(compareTasks);

  const pageCount = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
  state.page = Math.min(state.page, pageCount);
  elements.resultCount.textContent = number.format(state.filtered.length);
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
    node.querySelector(".task-preview").textContent = item.task_name;
    node.querySelector(".task-full-name").textContent = item.task_name;
    node.querySelector(".task-id").textContent = item.task_id;
    node.querySelector(".task-software").textContent = item.software.join(", ");
    node.querySelector(".task-type").textContent = item.task_type;
    const source = node.querySelector(".source-button");
    source.href = sourceFor(item.benchmark);
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
  Object.assign(state, { page: 1, benchmark: "", software: "", type: "", search: "", sort: "benchmark" });
  elements.search.value = "";
  elements.benchmarkFilter.value = "";
  elements.softwareFilter.value = "";
  elements.typeFilter.value = "";
  elements.sort.value = "benchmark";
  applyFilters();
}

function exportFiltered() {
  const payload = {
    exported_on: new Date().toISOString(),
    filters: {
      search: state.search,
      benchmark: state.benchmark,
      software: state.software,
      task_type: state.type,
    },
    task_count: state.filtered.length,
    tasks: state.filtered,
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
  elements.sort.addEventListener("change", (event) => {
    state.sort = event.target.value;
    state.page = 1;
    applyFilters();
  });
  elements.reset.addEventListener("click", resetFilters);
  elements.exportButton.addEventListener("click", exportFiltered);
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
  readUrl();
  try {
    const response = await fetch("./benchmark_tasks.json");
    if (!response.ok) throw new Error(`Dataset request failed (${response.status})`);
    state.catalog = await response.json();
    populateFilters();
    wireEvents();
    applyFilters();
    elements.loading.hidden = true;
  } catch (error) {
    elements.loading.hidden = true;
    elements.error.hidden = false;
    elements.error.textContent = `Could not load the task catalog: ${error.message}`;
  }
}

init();
