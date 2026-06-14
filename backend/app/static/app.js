const state = {
  route: "datasets",
  datasets: [],
  selectedDatasetId: null,
  selectedDataset: null,
  selectedCheck: null,
  issues: [],
  severity: "all",
  agentResult: null,
  edaResult: null,
  activeEdaPlotMode: "box",
  cleaningSuggestions: [],
  cleaningPreview: null,
  cleaningRuns: [],
  latestCleaningResult: null,
  queryHistory: [],
  workspaceContext: null,
  reports: [],
  jobs: [],
  events: [],
};

const els = {
  apiStatus: document.querySelector("#api-status"),
  refreshButton: document.querySelector("#refresh-button"),
  navLinks: document.querySelectorAll(".nav-link"),
  views: document.querySelectorAll(".route-view"),
  uploadForm: document.querySelector("#upload-form"),
  uploadButton: document.querySelector("#upload-button"),
  csvFile: document.querySelector("#csv-file"),
  fileTitle: document.querySelector("#file-title"),
  fileHint: document.querySelector("#file-hint"),
  datasetTable: document.querySelector("#dataset-table"),
  datasetEmpty: document.querySelector("#dataset-empty"),
  datasetCount: document.querySelector("#dataset-count"),
  selectedTitle: document.querySelector("#selected-title"),
  runStatus: document.querySelector("#run-status"),
  columnHealth: document.querySelector("#column-health"),
  issueList: document.querySelector("#issue-list"),
  issuesEmpty: document.querySelector("#issues-empty"),
  severityFilter: document.querySelector("#severity-filter"),
  briefingButton: document.querySelector("#briefing-button"),
  briefing: document.querySelector("#briefing"),
  toast: document.querySelector("#toast"),
  metricDatasets: document.querySelector("#metric-datasets"),
  metricRows: document.querySelector("#metric-rows"),
  metricIssues: document.querySelector("#metric-issues"),
  metricHigh: document.querySelector("#metric-high"),
  profileRows: document.querySelector("#profile-rows"),
  profileColumns: document.querySelector("#profile-columns"),
  profileNullHeavy: document.querySelector("#profile-null-heavy"),
  agentForm: document.querySelector("#agent-form"),
  agentDatasetSelect: document.querySelector("#agent-dataset-select"),
  agentQuestion: document.querySelector("#agent-question"),
  agentSubmit: document.querySelector("#agent-submit"),
  agentSource: document.querySelector("#agent-source"),
  agentSql: document.querySelector("#agent-sql"),
  agentExplanation: document.querySelector("#agent-explanation"),
  agentRowCount: document.querySelector("#agent-row-count"),
  agentResultTable: document.querySelector("#agent-result-table"),
  agentResultEmpty: document.querySelector("#agent-result-empty"),
  manualSqlInput: document.querySelector("#manual-sql-input"),
  manualSqlSubmit: document.querySelector("#manual-sql-submit"),
  queryHistoryRefresh: document.querySelector("#query-history-refresh"),
  queryHistoryList: document.querySelector("#query-history-list"),
  queryHistoryEmpty: document.querySelector("#query-history-empty"),
  cleaningDatasetSelect: document.querySelector("#cleaning-dataset-select"),
  cleaningSuggestionList: document.querySelector("#cleaning-suggestion-list"),
  cleaningSuggestionsEmpty: document.querySelector("#cleaning-suggestions-empty"),
  cleaningAiButton: document.querySelector("#cleaning-ai-button"),
  cleaningPreviewButton: document.querySelector("#cleaning-preview-button"),
  cleaningApplyButton: document.querySelector("#cleaning-apply-button"),
  cleaningRefreshButton: document.querySelector("#cleaning-refresh-button"),
  cleaningPreviewSummary: document.querySelector("#cleaning-preview-summary"),
  cleaningStepDetails: document.querySelector("#cleaning-step-details"),
  cleaningBeforeTable: document.querySelector("#cleaning-before-table"),
  cleaningAfterTable: document.querySelector("#cleaning-after-table"),
  cleaningRunList: document.querySelector("#cleaning-run-list"),
  cleaningRunsEmpty: document.querySelector("#cleaning-runs-empty"),
  cleaningDownload: document.querySelector("#cleaning-download"),
  cleaningOpenDataset: document.querySelector("#cleaning-open-dataset"),
  
  // EDA View Selectors
  edaDatasetSelect: document.querySelector("#eda-dataset-select"),
  edaInsightsList: document.querySelector("#eda-insights-list"),
  edaInsightsEmpty: document.querySelector("#eda-insights-empty"),
  edaPosCorrelations: document.querySelector("#eda-pos-correlations"),
  edaNegCorrelations: document.querySelector("#eda-neg-correlations"),
  edaCorrelationsEmpty: document.querySelector("#eda-correlations-empty"),
  edaMissingRows: document.querySelector("#eda-missing-rows"),
  edaCoMissingColumns: document.querySelector("#eda-co-missing-columns"),
  edaMissingnessEmpty: document.querySelector("#eda-missingness-empty"),
  edaColumnSearch: document.querySelector("#eda-col-search"),
  edaNumericPills: document.querySelector("#eda-numeric-pills"),
  edaCategoricalPills: document.querySelector("#eda-categorical-pills"),
  edaActiveColType: document.querySelector("#eda-active-col-type"),
  edaActiveColName: document.querySelector("#eda-active-col-name"),
  edaActiveColBadge: document.querySelector("#eda-active-col-badge"),
  edaActiveColProfile: document.querySelector("#eda-active-col-profile"),
  workspaceRefresh: document.querySelector("#workspace-refresh"),
  workspaceSummary: document.querySelector("#workspace-summary"),
  ruleBuilderDataset: document.querySelector("#rule-builder-dataset"),
  ruleBuilderInput: document.querySelector("#rule-builder-input"),
  ruleBuilderPreview: document.querySelector("#rule-builder-preview"),
  ruleBuilderCreate: document.querySelector("#rule-builder-create"),
  ruleBuilderOutput: document.querySelector("#rule-builder-output"),
  reportDataset: document.querySelector("#report-dataset"),
  reportExportButton: document.querySelector("#report-export-button"),
  reportsRefresh: document.querySelector("#reports-refresh"),
  reportsList: document.querySelector("#reports-list"),
  jobsRefresh: document.querySelector("#jobs-refresh"),
  jobsList: document.querySelector("#jobs-list"),
  eventsRefresh: document.querySelector("#events-refresh"),
  eventsList: document.querySelector("#events-list"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatBytes(bytes) {
  const value = Number(bytes || 0);
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function datasetVersionLabel(dataset) {
  const version = dataset.version || 1;
  const source = dataset.source === "cleaned" ? "Cleaned" : "Uploaded";
  const parent = dataset.parent_dataset_id ? ` | from #${dataset.parent_dataset_id}` : "";
  return `${source} | v${version}${parent}`;
}

function datasetOptionLabel(dataset) {
  return `${dataset.filename} (${dataset.source === "cleaned" ? "cleaned" : "raw"} v${dataset.version || 1})`;
}

function formatDecimal(value, digits = 2, fallback = "-") {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : fallback;
}

function formatPercent(value, digits = 1, fallback = "-") {
  const number = Number(value);
  return Number.isFinite(number) ? `${(number * 100).toFixed(digits)}%` : fallback;
}

function asArray(value) {
  if (Array.isArray(value)) return value;
  if (value === null || value === undefined || value === "") return [];
  return [value];
}

function clampPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  return Math.max(0, Math.min(100, number));
}

function scalePercent(value, min, max) {
  const current = Number(value);
  const lower = Number(min);
  const upper = Number(max);

  if (!Number.isFinite(current) || !Number.isFinite(lower) || !Number.isFinite(upper) || lower === upper) {
    return 50;
  }

  return clampPercent(((current - lower) / (upper - lower)) * 100);
}

function renderEdaHistogramPlot(counts, bins) {
  const safeCounts = Array.isArray(counts) ? counts.map((count) => Number(count) || 0) : [];
  const safeBins = Array.isArray(bins) ? bins : [];
  const maxCount = Math.max(...safeCounts, 1);
  const bars = safeCounts
    .map((count, index) => {
      const pct = (count / maxCount) * 100;
      const left = formatDecimal(safeBins[index], 2, "");
      const right = formatDecimal(safeBins[index + 1], 2, "");
      const label = left && right ? `${left} to ${right}: ${count} rows` : `${count} rows`;
      return `<div class="histogram-bar" style="height: ${Math.max(2, pct)}%" title="${escapeHtml(label)}"></div>`;
    })
    .join("");

  return `
    <div class="histogram-container eda-plot-card">
      <div class="histogram-visual eda-histogram-large">${bars}</div>
      <div class="histogram-labels">
        <span><strong>Min:</strong> ${formatDecimal(safeBins[0], 2, "Min")}</span>
        <span><strong>Max:</strong> ${formatDecimal(safeBins[safeBins.length - 1], 2, "Max")}</span>
      </div>
    </div>
  `;
}

function renderEdaBoxPlot({bins, quantiles, outliers}) {
  const safeBins = Array.isArray(bins) ? bins : [];
  const min = Number(safeBins[0]);
  const max = Number(safeBins[safeBins.length - 1]);
  const q1 = Number(quantiles.p25);
  const median = Number(quantiles.p50);
  const q3 = Number(quantiles.p75);
  const lowerFence = Number(outliers.lower_bound);
  const upperFence = Number(outliers.upper_bound);
  const whiskerLow = Number.isFinite(lowerFence) ? Math.max(lowerFence, min) : min;
  const whiskerHigh = Number.isFinite(upperFence) ? Math.min(upperFence, max) : max;

  const lowPct = scalePercent(whiskerLow, min, max);
  const highPct = scalePercent(whiskerHigh, min, max);
  const q1Pct = scalePercent(q1, min, max);
  const q3Pct = scalePercent(q3, min, max);
  const medianPct = scalePercent(median, min, max);
  const boxLeft = Math.min(q1Pct, q3Pct);
  const boxWidth = Math.max(1, Math.abs(q3Pct - q1Pct));

  return `
    <div class="boxplot-card eda-plot-card">
      <div class="boxplot-stage">
        <div class="boxplot-axis"></div>
        <div class="boxplot-whisker-line" style="left: ${lowPct}%; width: ${Math.max(1, highPct - lowPct)}%;"></div>
        <div class="boxplot-whisker left" style="left: ${lowPct}%;"></div>
        <div class="boxplot-whisker right" style="left: ${highPct}%;"></div>
        <div class="boxplot-box" style="left: ${boxLeft}%; width: ${boxWidth}%;"></div>
        <div class="boxplot-median" style="left: ${medianPct}%;"></div>
        <div class="boxplot-fence low" style="left: ${scalePercent(lowerFence, min, max)}%;" title="Lower IQR fence"></div>
        <div class="boxplot-fence high" style="left: ${scalePercent(upperFence, min, max)}%;" title="Upper IQR fence"></div>
      </div>
      <div class="boxplot-labels">
        <span>Min ${formatDecimal(min)}</span>
        <span>Q1 ${formatDecimal(q1)}</span>
        <span>Median ${formatDecimal(median)}</span>
        <span>Q3 ${formatDecimal(q3)}</span>
        <span>Max ${formatDecimal(max)}</span>
      </div>
      <div class="eda-outliers-box compact">
        <div>
          <span>IQR outlier fences</span>
          <p>${formatDecimal(outliers.lower_bound)} to ${formatDecimal(outliers.upper_bound)}</p>
        </div>
        <strong class="${Number(outliers.rate || 0) > 0.05 ? "bad" : "ok"}">${escapeHtml(outliers.num_outliers ?? 0)} rows (${formatPercent(outliers.rate || 0)})</strong>
      </div>
    </div>
  `;
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    els.toast.classList.add("hidden");
  }, 3600);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof payload === "object" ? payload.detail : payload;
    const message = typeof detail === "string" ? detail : JSON.stringify(detail);
    if (!path.startsWith("/observability")) {
      fetch("/observability/events", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          level: "error",
          source: "frontend_api",
          message: message || `Request failed with ${response.status}`,
          context: {path, status: response.status},
        }),
      }).catch(() => {});
    }
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return payload;
}

const apiEndpoints = {
  upload: {
    method: "POST",
    path: "/datasets/upload",
    payload: `Multipart Form-Data:
- file: File (CSV data)`,
    response: `{
  "dataset_id": 1,
  "quality_check_id": 1,
  "file_info": {
    "filename": "orders.csv",
    "storage_path": "storage/uploads/x.csv",
    "size": 1048576
  },
  "profile": {
    "num_rows": 1000,
    "num_columns": 5
  },
  "quality_issues": []
}`
  },
  eda: {
    method: "GET",
    path: "/datasets/{dataset_id}/eda",
    payload: `URL Parameters:
- dataset_id: Integer (Unique dataset ID)`,
    response: `{
  "dataset_id": 1,
  "eda": {
    "numeric_distributions": {
      "amount": {
        "quantiles": { "p50": 150.25 },
        "outliers": { "rate": 0.02 }
      }
    },
    "categorical_distributions": {
      "status": { "unique_values": 4 }
    },
    "correlations": {
      "top_pos": [
        { "columns": ["price", "qty"], "correlation": 0.82 }
      ]
    },
    "missingness": {},
    "insights": []
  }
}`
  },
  agent: {
    method: "POST",
    path: "/agent/query",
    payload: `{
  "dataset_id": 1,
  "question": "Show top 5 largest orders",
  "limit": 50
}`,
    response: `{
  "dataset": {
    "id": 1,
    "filename": "orders.csv"
  },
  "sql": "SELECT * FROM data ORDER BY amount DESC LIMIT 5",
  "explanation": "Query returning the highest purchase amounts.",
  "columns": ["order_id", "amount", "customer"],
  "rows": [
    { "order_id": "1004", "amount": 950.0, "customer": "Alice" }
  ],
  "row_count": 1,
  "generated_by": "llm"
}`
  },
  rules: {
    method: "POST",
    path: "/rules",
    payload: `{
  "name": "Positive Amount",
  "description": "Order amounts must be greater than zero",
  "column": "amount",
  "condition": "amount > 0",
  "severity": "high",
  "is_active": true
}`,
    response: `{
  "id": 5,
  "name": "Positive Amount",
  "column": "amount",
  "condition": "amount > 0",
  "severity": "high",
  "is_active": true,
  "created_at": "2026-05-28T22:54:00Z"
}`
  }
};

function setupApiTabSwitcher() {
  const tabs = document.querySelectorAll(".api-tab");
  if (!tabs.length) return;

  tabs.forEach(tab => {
    if (tab.dataset.bound) return;
    tab.dataset.bound = "true";

    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const endpoint = tab.dataset.endpoint;
      const data = apiEndpoints[endpoint];
      if (!data) return;

      const pathEl = document.querySelector("#api-display-path");
      const methodEl = document.querySelector(".api-method");
      const reqEl = document.querySelector("#api-request-code");
      const resEl = document.querySelector("#api-response-code");

      if (pathEl) pathEl.textContent = data.path;
      if (methodEl) {
        methodEl.textContent = data.method;
        methodEl.className = `api-method ${data.method}`;
      }
      if (reqEl) reqEl.textContent = data.payload;
      if (resEl) resEl.textContent = data.response;
    });
  });
}

function currentRoute() {
  const route = window.location.hash.replace(/^#\/?/, "");
  if (route === "datasets") return "datasets";
  if (route === "ask") return "ask";
  if (route === "eda") return "eda";
  if (route === "cleaning") return "cleaning";
  if (route === "operations") return "operations";
  return "home";
}

function renderRoute() {
  state.route = currentRoute();

  els.views.forEach((view) => {
    view.classList.toggle("hidden", view.dataset.view !== state.route);
  });

  els.navLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.route === state.route);
  });

  if (state.route === "home") {
    setupApiTabSwitcher();
  } else if (state.route === "ask") {
    renderAgentDatasetOptions();
    loadQueryHistory();
  } else if (state.route === "eda") {
    renderEdaDatasetOptions();
    if (state.datasets.length) {
      loadEdaData();
    } else {
      renderEdaEmpty();
    }
  } else if (state.route === "cleaning") {
    renderCleaningDatasetOptions();
    if (state.datasets.length) {
      loadCleaningData();
    } else {
      renderCleaningEmpty();
    }
  } else if (state.route === "operations") {
    renderOperationsDatasetOptions();
    loadOperationsData();
  }
}

async function loadDatasets(preferredDatasetId = null) {
  try {
    els.apiStatus.textContent = "Connected";
    state.datasets = await api("/datasets");
    state.selectedDatasetId =
      preferredDatasetId || state.selectedDatasetId || state.datasets[0]?.id || null;

    if (!state.datasets.some((dataset) => dataset.id === state.selectedDatasetId)) {
      state.selectedDatasetId = state.datasets[0]?.id || null;
    }

    renderDatasetTable();
    renderAgentDatasetOptions();
    renderEdaDatasetOptions();
    renderCleaningDatasetOptions();
    renderOperationsDatasetOptions();
    await loadSelectedDataset();
  } catch (error) {
    els.apiStatus.textContent = "Connection issue";
    showToast(error.message);
  }
}

async function refreshDatasetRegistry(preferredDatasetId = state.selectedDatasetId) {
  state.datasets = await api("/datasets");
  state.selectedDatasetId = preferredDatasetId;

  if (!state.datasets.some((dataset) => dataset.id === state.selectedDatasetId)) {
    state.selectedDatasetId = state.datasets[0]?.id || null;
  }

  renderDatasetTable();
  renderAgentDatasetOptions();
  renderEdaDatasetOptions();
  renderCleaningDatasetOptions();
  renderOperationsDatasetOptions();
  renderMetrics();
}

async function loadSelectedDataset() {
  state.selectedDataset =
    state.datasets.find((dataset) => dataset.id === state.selectedDatasetId) || null;
  state.selectedCheck = null;
  state.issues = [];

  if (!state.selectedDataset) {
    renderEmptySelection();
    return;
  }

  const checks = await api(`/datasets/${state.selectedDataset.id}/checks`);
  state.selectedCheck = checks[0] || null;

  if (state.selectedCheck) {
    state.issues = await api(`/datasets/checks/${state.selectedCheck.id}/issues`);
  }

  renderAll();
  if (state.route === "eda") {
    await loadEdaData();
  } else if (state.route === "cleaning") {
    await loadCleaningData();
  } else if (state.route === "ask") {
    await loadQueryHistory();
  }
}

function renderAll() {
  renderDatasetTable();
  renderAgentDatasetOptions();
  renderEdaDatasetOptions();
  renderCleaningDatasetOptions();
  renderOperationsDatasetOptions();
  renderMetrics();
  renderProfile();
  renderIssues();
  renderBriefingDefault();
}

function renderDatasetTable() {
  els.metricDatasets.textContent = state.datasets.length;
  els.datasetCount.textContent = `${state.datasets.length} item${state.datasets.length === 1 ? "" : "s"}`;
  els.datasetEmpty.classList.toggle("hidden", state.datasets.length > 0);

  els.datasetTable.innerHTML = state.datasets
    .map((dataset) => {
      const active = dataset.id === state.selectedDatasetId ? " active" : "";
      return `
        <tr class="dataset-row${active}" data-id="${dataset.id}">
          <td>
            <div class="dataset-name">
              <strong>${escapeHtml(dataset.filename)}</strong>
              <span>ID ${dataset.id} | ${escapeHtml(datasetVersionLabel(dataset))}</span>
            </div>
          </td>
          <td>${formatBytes(dataset.size)}</td>
          <td>${formatDate(dataset.created_at)}</td>
        </tr>
      `;
    })
    .join("");

  document.querySelectorAll(".dataset-row").forEach((row) => {
    row.addEventListener("click", async () => {
      state.selectedDatasetId = Number(row.dataset.id);
      await loadSelectedDataset();
    });
  });
}

function renderAgentDatasetOptions() {
  if (!els.agentDatasetSelect) return;

  if (!state.datasets.length) {
    els.agentDatasetSelect.innerHTML = `<option value="">No datasets available</option>`;
    els.agentDatasetSelect.disabled = true;
    return;
  }

  els.agentDatasetSelect.disabled = false;
  els.agentDatasetSelect.innerHTML = state.datasets
    .map((dataset) => {
      const selected = dataset.id === state.selectedDatasetId ? " selected" : "";
      return `<option value="${dataset.id}"${selected}>${escapeHtml(datasetOptionLabel(dataset))}</option>`;
    })
    .join("");
}

function renderEdaDatasetOptions() {
  if (!els.edaDatasetSelect) return;

  if (!state.datasets.length) {
    els.edaDatasetSelect.innerHTML = `<option value="">No datasets available</option>`;
    els.edaDatasetSelect.disabled = true;
    return;
  }

  els.edaDatasetSelect.disabled = false;
  els.edaDatasetSelect.innerHTML = state.datasets
    .map((dataset) => {
      const selected = dataset.id === state.selectedDatasetId ? " selected" : "";
      return `<option value="${dataset.id}"${selected}>${escapeHtml(datasetOptionLabel(dataset))}</option>`;
    })
    .join("");
}

function renderCleaningDatasetOptions() {
  if (!els.cleaningDatasetSelect) return;

  if (!state.datasets.length) {
    els.cleaningDatasetSelect.innerHTML = `<option value="">No datasets available</option>`;
    els.cleaningDatasetSelect.disabled = true;
    return;
  }

  els.cleaningDatasetSelect.disabled = false;
  els.cleaningDatasetSelect.innerHTML = state.datasets
    .map((dataset) => {
      const selected = dataset.id === state.selectedDatasetId ? " selected" : "";
      return `<option value="${dataset.id}"${selected}>${escapeHtml(datasetOptionLabel(dataset))}</option>`;
    })
    .join("");
}

function renderOperationsDatasetOptions() {
  [els.ruleBuilderDataset, els.reportDataset].forEach((select) => {
    if (!select) return;

    if (!state.datasets.length) {
      select.innerHTML = `<option value="">No datasets available</option>`;
      select.disabled = true;
      return;
    }

    select.disabled = false;
    select.innerHTML = state.datasets
      .map((dataset) => {
        const selected = dataset.id === state.selectedDatasetId ? " selected" : "";
        return `<option value="${dataset.id}"${selected}>${escapeHtml(datasetOptionLabel(dataset))}</option>`;
      })
      .join("");
  });
}

function renderCleaningEmpty() {
  state.cleaningSuggestions = [];
  state.cleaningPreview = null;
  state.cleaningRuns = [];
  state.latestCleaningResult = null;

  if (els.cleaningSuggestionList) els.cleaningSuggestionList.innerHTML = "";
  if (els.cleaningSuggestionsEmpty) els.cleaningSuggestionsEmpty.classList.remove("hidden");
  if (els.cleaningPreviewSummary) {
    els.cleaningPreviewSummary.innerHTML = `
      <div class="empty-state">
        <strong>No preview yet</strong>
        <span>Select cleaning steps and preview the result.</span>
      </div>
    `;
  }
  if (els.cleaningStepDetails) els.cleaningStepDetails.innerHTML = "";
  if (els.cleaningBeforeTable) els.cleaningBeforeTable.innerHTML = "";
  if (els.cleaningAfterTable) els.cleaningAfterTable.innerHTML = "";
  if (els.cleaningRunList) els.cleaningRunList.innerHTML = "";
  if (els.cleaningRunsEmpty) els.cleaningRunsEmpty.classList.remove("hidden");
  if (els.cleaningDownload) {
    els.cleaningDownload.classList.add("hidden");
    els.cleaningDownload.removeAttribute("href");
  }
  if (els.cleaningOpenDataset) {
    els.cleaningOpenDataset.classList.add("hidden");
    delete els.cleaningOpenDataset.dataset.datasetId;
  }
}

function selectedCleaningSteps() {
  return [...document.querySelectorAll(".cleaning-step-checkbox:checked")]
    .map((checkbox) => state.cleaningSuggestions[Number(checkbox.dataset.index)])
    .filter((step) => step && step.type !== "no_op");
}

function riskClass(risk) {
  if (risk === "high") return "bad";
  if (risk === "medium") return "warn";
  return "ok";
}

function cleanedColumnsFromPreview(preview) {
  const diff = preview?.diff || {};
  const columns = [
    ...asArray(diff.cleaned_columns),
    ...asArray(diff.columns_changed),
    ...asArray(diff.columns_removed),
  ];

  (preview?.step_details || []).forEach((detail) => {
    if (detail.column) columns.push(detail.column);
    columns.push(...asArray(detail.columns_changed));
    columns.push(...asArray(detail.columns_removed));
  });

  return [...new Set(columns.filter(Boolean))];
}

function renderCleanedColumnChips(columns, removedColumns = []) {
  columns = asArray(columns);
  removedColumns = asArray(removedColumns);

  if (!columns.length) {
    return `
      <div class="cleaned-column-chips">
        <span class="column-chip muted">No column-level changes</span>
      </div>
    `;
  }

  const removed = new Set(removedColumns || []);
  return `
    <div class="cleaned-column-chips">
      ${columns
        .map((column) => `
          <span class="column-chip ${removed.has(column) ? "removed" : ""}">
            ${escapeHtml(column)}${removed.has(column) ? " removed" : ""}
          </span>
        `)
        .join("")}
    </div>
  `;
}

function renderDataSampleTable(rows, priorityColumns = []) {
  if (!rows?.length) {
    return `
      <div class="empty-state">
        <strong>No rows</strong>
        <span>The sample is empty.</span>
      </div>
    `;
  }

  const availableColumns = Object.keys(rows[0]);
  const prioritized = priorityColumns.filter((column) => availableColumns.includes(column));
  const contextColumns = availableColumns
    .filter((column) => !prioritized.includes(column))
    .slice(0, Math.max(0, 8 - prioritized.length));
  const columns = [...prioritized, ...contextColumns];
  const hiddenCount = Math.max(0, availableColumns.length - columns.length);
  const prioritySet = new Set(prioritized);
  const header = columns
    .map((column) => `<th class="${prioritySet.has(column) ? "cleaned-col" : ""}">${escapeHtml(column)}</th>`)
    .join("");
  const body = rows
    .map((row) => `
      <tr>
        ${columns
          .map((column) => `<td class="${prioritySet.has(column) ? "cleaned-col" : ""}">${escapeHtml(row[column])}</td>`)
          .join("")}
      </tr>
    `)
    .join("");

  return `
    <table>
      <thead><tr>${header}</tr></thead>
      <tbody>${body}</tbody>
    </table>
    ${prioritized.length ? `<p class="table-note">Showing cleaned column${prioritized.length === 1 ? "" : "s"} first: ${prioritized.map(escapeHtml).join(", ")}.</p>` : ""}
    ${hiddenCount ? `<p class="table-note">${hiddenCount} additional column${hiddenCount === 1 ? "" : "s"} hidden in preview.</p>` : ""}
  `;
}

function datasetAuditLabel(dataset, fallback = "Dataset unavailable") {
  if (!dataset) return fallback;
  return `#${dataset.id} | v${dataset.version || 1} | ${dataset.source || "uploaded"} | ${dataset.filename || "dataset"}`;
}

function renderAuditLog(preview) {
  const audit = preview.audit;
  if (!audit) return "";
  const history = audit.history || {};
  const columnsTouched = asArray(history.columns_touched);

  return `
    <div class="audit-log-block">
      <div class="audit-log-header">
        <div>
          <span>Audit log</span>
          <strong>Run #${escapeHtml(audit.run_id || "-")}</strong>
        </div>
        <span class="severity ok">${escapeHtml(audit.status || "applied")}</span>
      </div>
      <div class="audit-log-grid">
        <div>
          <span>Previous version</span>
          <strong>${escapeHtml(datasetAuditLabel(audit.previous_dataset, "Previous dataset unavailable"))}</strong>
        </div>
        <div>
          <span>Current version</span>
          <strong>${escapeHtml(datasetAuditLabel(audit.current_dataset, "Cleaned file only"))}</strong>
        </div>
        <div>
          <span>Applied at</span>
          <strong>${escapeHtml(formatDate(audit.created_at))}</strong>
        </div>
        <div>
          <span>Affected row events</span>
          <strong>${escapeHtml(history.total_affected_rows ?? "-")}</strong>
        </div>
        <div>
          <span>Steps applied</span>
          <strong>${escapeHtml(history.steps_applied ?? "-")}</strong>
        </div>
        <div>
          <span>Columns touched</span>
          <strong>${escapeHtml(columnsTouched.length ? columnsTouched.join(", ") : "-")}</strong>
        </div>
      </div>
    </div>
  `;
}

function renderStepParams(params) {
  if (!params || (typeof params === "object" && !Object.keys(params).length)) {
    return `<span class="history-param muted">No params</span>`;
  }

  if (typeof params === "string") {
    return `<span class="history-param">${escapeHtml(params)}</span>`;
  }

  return Object.entries(params)
    .map(([key, value]) => {
      const renderedValue = typeof value === "object" && value !== null
        ? JSON.stringify(value)
        : value;
      return `<span class="history-param">${escapeHtml(key)}: ${escapeHtml(renderedValue)}</span>`;
    })
    .join("");
}

function renderRiskChips(riskCounts = {}) {
  const entries = Object.entries(riskCounts).filter(([, count]) => Number(count) > 0);
  if (!entries.length) return `<span class="history-param muted">No risk flags</span>`;

  return entries
    .map(([risk, count]) => `<span class="severity ${riskClass(risk)}">${escapeHtml(risk)} ${escapeHtml(count)}</span>`)
    .join("");
}

function renderActionChips(actionCounts = {}) {
  const entries = Object.entries(actionCounts);
  if (!entries.length) return `<span class="history-param muted">No action log</span>`;

  return entries
    .slice(0, 4)
    .map(([action, count]) => `<span class="history-param">${escapeHtml(action)} x${escapeHtml(count)}</span>`)
    .join("");
}

function renderTouchedColumns(columns) {
  const values = asArray(columns);
  if (!values.length) return `<span class="history-param muted">No column-level changes</span>`;
  const visible = values.slice(0, 5);
  const hidden = values.length - visible.length;

  return `
    ${visible.map((column) => `<span class="column-chip">${escapeHtml(column)}</span>`).join("")}
    ${hidden > 0 ? `<span class="column-chip muted">+${hidden} more</span>` : ""}
  `;
}

function buildRunPreview(runDetail) {
  const summary = runDetail.summary || {};
  const comparison = runDetail.comparison || {};
  const before = comparison.before || summary.before || {};
  const after = comparison.after || summary.after || {};
  const diff = comparison.diff || {};
  const stepDetails = comparison.step_details?.length
    ? comparison.step_details
    : (summary.step_details || runDetail.steps?.map((step) => step.preview || step) || []);
  const summaryColumnsRemoved = asArray(summary.columns_removed);
  const summaryColumnsChanged = asArray(summary.columns_changed);
  const summaryCleanedColumns = asArray(summary.cleaned_columns);
  const columnsRemoved = summaryColumnsRemoved.length ? summaryColumnsRemoved : asArray(diff.columns_removed);
  const columnsChanged = summaryColumnsChanged.length ? summaryColumnsChanged : asArray(diff.columns_changed);
  const cleanedColumns = summaryCleanedColumns.length ? summaryCleanedColumns : asArray(diff.cleaned_columns);

  return {
    before: {
      ...before,
      sample: before.sample || summary.before_sample || [],
    },
    after: {
      ...after,
      sample: after.sample || summary.after_sample || summary.sample || [],
    },
    diff: {
      rows_removed: summary.rows_removed ?? diff.rows_removed ?? 0,
      columns_removed: columnsRemoved,
      columns_changed: columnsChanged,
      cleaned_columns: cleanedColumns,
      missing_cells_delta: diff.missing_cells_delta,
    },
    cleaned_dataset: runDetail.current_dataset || summary.cleaned_dataset || null,
    audit: {
      run_id: runDetail.id,
      status: runDetail.status,
      created_at: runDetail.created_at,
      previous_dataset: runDetail.previous_dataset || null,
      current_dataset: runDetail.current_dataset || summary.cleaned_dataset || null,
      history: runDetail.history || null,
    },
    step_details: stepDetails,
  };
}

async function loadCleaningData() {
  if (!state.selectedDatasetId) {
    renderCleaningEmpty();
    return;
  }

  try {
    if (els.cleaningSuggestionList) {
      els.cleaningSuggestionList.innerHTML = `
        <div class="empty-state">
          <strong>Loading suggestions</strong>
          <span>Scanning dataset for safe cleaning actions.</span>
        </div>
      `;
    }

    const [suggestionsPayload, runs] = await Promise.all([
      api(`/cleaning/datasets/${state.selectedDatasetId}/suggestions`),
      api(`/cleaning/datasets/${state.selectedDatasetId}/runs`),
    ]);

    state.cleaningSuggestions = suggestionsPayload.suggestions || [];
    state.cleaningRuns = runs || [];
    state.cleaningPreview = null;
    state.latestCleaningResult = null;
    if (els.cleaningDownload) {
      els.cleaningDownload.classList.add("hidden");
      els.cleaningDownload.removeAttribute("href");
    }
    if (els.cleaningOpenDataset) {
      els.cleaningOpenDataset.classList.add("hidden");
      delete els.cleaningOpenDataset.dataset.datasetId;
    }
    renderCleaningSuggestions();
    renderCleaningPreview();
    renderCleaningRuns();
  } catch (error) {
    showToast(error.message);
    renderCleaningEmpty();
    if (els.cleaningPreviewSummary) {
      els.cleaningPreviewSummary.innerHTML = `
        <div class="empty-state">
          <strong>Cleaning could not be loaded</strong>
          <span>${escapeHtml(error.message)}</span>
        </div>
      `;
    }
  }
}

function renderCleaningSuggestions() {
  const suggestions = state.cleaningSuggestions || [];
  if (!els.cleaningSuggestionList) return;

  els.cleaningSuggestionsEmpty.classList.toggle("hidden", suggestions.length > 0);

  els.cleaningSuggestionList.innerHTML = suggestions
    .map((step, index) => `
      <label class="cleaning-step ${riskClass(step.risk)}">
        <input class="cleaning-step-checkbox" type="checkbox" data-index="${index}" ${step.type === "no_op" ? "disabled" : "checked"} />
        <span class="cleaning-step-body">
          <span class="cleaning-step-title">
            <strong>${escapeHtml(step.type)}</strong>
            <span class="severity ${riskClass(step.risk)}">${escapeHtml(step.risk || "safe")}</span>
          </span>
          <span>${escapeHtml(step.message || "Apply this cleaning step.")}</span>
          ${step.why ? `<span>${escapeHtml(step.why)}</span>` : ""}
          <span class="cleaning-step-meta">
            ${step.column ? `Column: ${escapeHtml(step.column)}` : "Dataset-level"}
            ${Number.isFinite(Number(step.affected_rows)) ? ` · Affected rows: ${escapeHtml(step.affected_rows)}` : ""}
          </span>
        </span>
      </label>
    `)
    .join("");
}

function renderCleaningSuggestions() {
  const suggestions = state.cleaningSuggestions || [];
  if (!els.cleaningSuggestionList) return;

  els.cleaningSuggestionsEmpty.classList.toggle("hidden", suggestions.length > 0);

  els.cleaningSuggestionList.innerHTML = suggestions
    .map((step, index) => `
      <label class="cleaning-step ${riskClass(step.risk)}">
        <input class="cleaning-step-checkbox" type="checkbox" data-index="${index}" ${step.type === "no_op" ? "disabled" : "checked"} />
        <span class="cleaning-step-body">
          <span class="cleaning-step-title">
            <strong>${escapeHtml(step.type)}</strong>
            <span class="severity ${riskClass(step.risk)}">${escapeHtml(step.risk || "safe")}</span>
          </span>
          <span>${escapeHtml(step.message || "Apply this cleaning step.")}</span>
          ${step.why ? `<span>${escapeHtml(step.why)}</span>` : ""}
          <span class="cleaning-step-meta">
            ${step.column ? `Column: ${escapeHtml(step.column)}` : "Dataset-level"}
            ${Number.isFinite(Number(step.affected_rows)) ? ` | Affected rows: ${escapeHtml(step.affected_rows)}` : ""}
            ${Number.isFinite(Number(step.confidence)) ? ` | Confidence: ${escapeHtml(Math.round(Number(step.confidence) * 100))}%` : ""}
            ${step.review_required ? " | Review required" : ""}
          </span>
        </span>
      </label>
    `)
    .join("");
}

async function loadAiCleaningSuggestions() {
  if (!state.selectedDatasetId) {
    showToast("Choose a dataset first.");
    return;
  }

  try {
    els.cleaningAiButton.disabled = true;
    els.cleaningAiButton.textContent = "Thinking";
    const payload = await api(`/cleaning/datasets/${state.selectedDatasetId}/ai-suggestions`);
    state.cleaningSuggestions = payload.suggestions || [];
    state.cleaningPreview = null;
    renderCleaningSuggestions();
    renderCleaningPreview();
    showToast(`LLM cleaning suggestions loaded${payload.model ? ` from ${payload.model}` : ""}.`);
  } catch (error) {
    showToast(error.message);
  } finally {
    els.cleaningAiButton.disabled = false;
    els.cleaningAiButton.textContent = "LLM suggestions";
  }
}

function renderCleaningPreview() {
  const preview = state.cleaningPreview?.preview || state.cleaningPreview;

  if (!preview) {
    if (els.cleaningPreviewSummary) {
      els.cleaningPreviewSummary.innerHTML = `
        <div class="empty-state">
          <strong>No preview yet</strong>
          <span>Select cleaning steps and preview the result.</span>
        </div>
      `;
    }
    if (els.cleaningStepDetails) els.cleaningStepDetails.innerHTML = "";
    if (els.cleaningBeforeTable) els.cleaningBeforeTable.innerHTML = "";
    if (els.cleaningAfterTable) els.cleaningAfterTable.innerHTML = "";
    return;
  }

  const before = preview.before || {};
  const after = preview.after || {};
  const diff = preview.diff || {};

  els.cleaningPreviewSummary.innerHTML = `
    <div class="cleaning-metrics">
      <div><span>Rows</span><strong>${escapeHtml(before.num_rows ?? 0)} → ${escapeHtml(after.num_rows ?? 0)}</strong></div>
      <div><span>Columns</span><strong>${escapeHtml(before.num_columns ?? 0)} → ${escapeHtml(after.num_columns ?? 0)}</strong></div>
      <div><span>Missing Cells</span><strong>${escapeHtml(before.missing_cells ?? 0)} → ${escapeHtml(after.missing_cells ?? 0)}</strong></div>
      <div><span>Rows Removed</span><strong>${escapeHtml(diff.rows_removed ?? 0)}</strong></div>
    </div>
  `;

  els.cleaningStepDetails.innerHTML = (preview.step_details || [])
    .map((detail) => `
      <article class="cleaning-detail">
        <strong>${escapeHtml(detail.type)}</strong>
        <span>${detail.column ? `Column: ${escapeHtml(detail.column)}` : "Dataset-level"} · affected rows: ${escapeHtml(detail.affected_rows ?? 0)}</span>
      </article>
    `)
    .join("");

  els.cleaningBeforeTable.innerHTML = renderDataSampleTable(before.sample || []);
  els.cleaningAfterTable.innerHTML = renderDataSampleTable(after.sample || []);
}

function renderCleaningPreview() {
  const preview = state.cleaningPreview?.preview || state.cleaningPreview;

  if (!preview) {
    if (els.cleaningPreviewSummary) {
      els.cleaningPreviewSummary.innerHTML = `
        <div class="empty-state">
          <strong>No preview yet</strong>
          <span>Select cleaning steps and preview the result.</span>
        </div>
      `;
    }
    if (els.cleaningStepDetails) els.cleaningStepDetails.innerHTML = "";
    if (els.cleaningBeforeTable) els.cleaningBeforeTable.innerHTML = "";
    if (els.cleaningAfterTable) els.cleaningAfterTable.innerHTML = "";
    return;
  }

  const before = preview.before || {};
  const after = preview.after || {};
  const diff = preview.diff || {};
  const cleanedColumns = cleanedColumnsFromPreview(preview);
  const removedColumns = diff.columns_removed || [];
  const cleanedDataset = preview.cleaned_dataset || state.latestCleaningResult?.cleaned_dataset || null;

  els.cleaningPreviewSummary.innerHTML = `
    <div class="cleaning-metrics">
      <div><span>Rows</span><strong>${escapeHtml(before.num_rows ?? 0)} -> ${escapeHtml(after.num_rows ?? 0)}</strong></div>
      <div><span>Columns</span><strong>${escapeHtml(before.num_columns ?? 0)} -> ${escapeHtml(after.num_columns ?? 0)}</strong></div>
      <div><span>Missing Cells</span><strong>${escapeHtml(before.missing_cells ?? 0)} -> ${escapeHtml(after.missing_cells ?? 0)}</strong></div>
      <div><span>Rows Removed</span><strong>${escapeHtml(diff.rows_removed ?? 0)}</strong></div>
    </div>
    ${renderAuditLog(preview)}
    <div class="cleaned-columns-block">
      <span>Cleaned columns</span>
      ${renderCleanedColumnChips(cleanedColumns, removedColumns)}
    </div>
    ${cleanedDataset ? `
      <div class="cleaned-columns-block">
        <span>Saved dataset version</span>
        <div class="cleaned-column-chips">
          <span class="column-chip">Dataset #${escapeHtml(cleanedDataset.id)}</span>
          <span class="column-chip">v${escapeHtml(cleanedDataset.version || 1)}</span>
          <span class="column-chip muted">${escapeHtml(cleanedDataset.filename || "cleaned dataset")}</span>
        </div>
      </div>
    ` : ""}
  `;

  const details = preview.step_details || [];
  els.cleaningStepDetails.innerHTML = details.length
    ? details.map((detail, index) => `
      <article class="cleaning-detail">
        <div class="cleaning-detail-head">
          <strong>Step ${escapeHtml(index + 1)} | ${escapeHtml(detail.type || "cleaning_step")}</strong>
          <span class="severity ${riskClass(detail.risk)}">${escapeHtml(detail.risk || "safe")}</span>
        </div>
        <span>${detail.column ? `Column: ${escapeHtml(detail.column)}` : "Dataset-level"} | affected rows: ${escapeHtml(detail.affected_rows ?? 0)}</span>
        <div class="history-step-metrics">
          <span>Rows: ${escapeHtml(detail.before_rows ?? "-")} -> ${escapeHtml(detail.after_rows ?? "-")}</span>
          <span>Status: ${escapeHtml(detail.status || "applied")}</span>
        </div>
        <div class="history-chip-row">
          ${renderStepParams(detail.params)}
        </div>
        ${renderCleanedColumnChips([
          detail.column,
          ...asArray(detail.columns_changed),
          ...asArray(detail.columns_removed),
        ].filter(Boolean), asArray(detail.columns_removed))}
      </article>
    `)
    .join("")
    : `
      <div class="empty-state">
        <strong>No step log</strong>
        <span>This run does not have saved cleaning step metadata.</span>
      </div>
    `;

  els.cleaningBeforeTable.innerHTML = renderDataSampleTable(before.sample || [], cleanedColumns);
  els.cleaningAfterTable.innerHTML = renderDataSampleTable(after.sample || [], cleanedColumns);
}

function renderCleaningRuns() {
  const runs = state.cleaningRuns || [];
  if (!els.cleaningRunList) return;

  els.cleaningRunsEmpty.classList.toggle("hidden", runs.length > 0);
  els.cleaningRunList.innerHTML = runs
    .map((run) => {
      const summary = run.summary || {};
      const history = run.history || {};
      const after = summary.after || {};
      const cleanedDataset = run.current_dataset || summary.cleaned_dataset || {};
      const previousDataset = run.previous_dataset || history.previous_dataset || null;
      const currentDataset = run.current_dataset || history.current_dataset || cleanedDataset || null;
      const steps = run.steps || [];
      const downloadUrl = `/cleaning/runs/${run.id}/download`;
      return `
        <article class="cleaning-run">
          <div>
            <strong>Run #${escapeHtml(run.id)}</strong>
            <span>${formatDate(run.created_at)} · ${escapeHtml(run.status)}</span>
          </div>
          <div class="cleaning-run-meta">
            <span>${escapeHtml(after.num_rows ?? "-")} rows</span>
            <span>${escapeHtml(summary.steps_applied ?? 0)} steps</span>
            ${cleanedDataset.id ? `<span>Dataset #${escapeHtml(cleanedDataset.id)} v${escapeHtml(cleanedDataset.version || 1)}</span>` : ""}
            <button class="secondary-button compact cleaning-run-preview" type="button" data-run-id="${escapeHtml(run.id)}">Preview</button>
            <a class="secondary-button compact" href="${downloadUrl}">Download</a>
          </div>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll(".cleaning-run-preview").forEach((button) => {
    button.addEventListener("click", () => previewCleaningRun(Number(button.dataset.runId)));
  });
}

function renderCleaningRuns() {
  const runs = state.cleaningRuns || [];
  if (!els.cleaningRunList) return;

  els.cleaningRunsEmpty.classList.toggle("hidden", runs.length > 0);
  els.cleaningRunList.innerHTML = runs
    .map((run) => {
      const summary = run.summary || {};
      const history = run.history || {};
      const after = summary.after || {};
      const cleanedDataset = run.current_dataset || summary.cleaned_dataset || {};
      const previousDataset = run.previous_dataset || history.previous_dataset || null;
      const currentDataset = run.current_dataset || history.current_dataset || cleanedDataset || null;
      const steps = run.steps || [];
      const downloadUrl = `/cleaning/runs/${run.id}/download`;

      return `
        <article class="cleaning-run">
          <div class="cleaning-run-head">
            <div>
              <strong>Run #${escapeHtml(run.id)}</strong>
              <span>${formatDate(run.created_at)} | ${escapeHtml(run.status)}</span>
            </div>
            <div class="history-risk-strip">
              ${renderRiskChips(history.risk_counts || {})}
            </div>
          </div>

          <div class="cleaning-run-history">
            <div><span>Affected row events</span><strong>${escapeHtml(history.total_affected_rows ?? "-")}</strong></div>
            <div><span>Rows</span><strong>${escapeHtml(history.rows_before ?? summary.before?.num_rows ?? "-")} -> ${escapeHtml(history.rows_after ?? after.num_rows ?? "-")}</strong></div>
            <div><span>Columns</span><strong>${escapeHtml(history.columns_before ?? summary.before?.num_columns ?? "-")} -> ${escapeHtml(history.columns_after ?? after.num_columns ?? "-")}</strong></div>
            <div><span>Missing cells</span><strong>${escapeHtml(history.missing_cells_before ?? summary.before?.missing_cells ?? "-")} -> ${escapeHtml(history.missing_cells_after ?? after.missing_cells ?? "-")}</strong></div>
          </div>

          <div class="run-lineage">
            <span>From ${escapeHtml(datasetAuditLabel(previousDataset, `Dataset #${run.dataset_id}`))}</span>
            <span>To ${escapeHtml(datasetAuditLabel(currentDataset, "Cleaned file"))}</span>
          </div>

          <div class="history-chip-row">
            ${renderActionChips(history.action_counts || {})}
          </div>

          <div class="cleaned-column-chips">
            ${renderTouchedColumns(history.columns_touched || summary.cleaned_columns || summary.columns_changed || [])}
          </div>

          ${steps.length ? `
            <div class="history-step-list">
              ${steps.slice(0, 3).map((step, index) => `
                <div class="history-step-item">
                  <strong>${escapeHtml(index + 1)}. ${escapeHtml(step.type)}</strong>
                  <span>${step.column ? `Column: ${escapeHtml(step.column)}` : "Dataset-level"} | affected rows: ${escapeHtml(step.affected_rows ?? 0)}</span>
                </div>
              `).join("")}
              ${steps.length > 3 ? `<div class="history-step-item muted">+${escapeHtml(steps.length - 3)} more steps</div>` : ""}
            </div>
          ` : ""}

          <div class="cleaning-run-meta">
            <span>${escapeHtml(history.steps_applied ?? summary.steps_applied ?? 0)} steps</span>
            ${cleanedDataset.id ? `<span>Dataset #${escapeHtml(cleanedDataset.id)} v${escapeHtml(cleanedDataset.version || 1)}</span>` : ""}
            <button class="secondary-button compact cleaning-run-preview" type="button" data-run-id="${escapeHtml(run.id)}">Preview</button>
            <a class="secondary-button compact" href="${downloadUrl}">Download</a>
          </div>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll(".cleaning-run-preview").forEach((button) => {
    button.addEventListener("click", () => previewCleaningRun(Number(button.dataset.runId)));
  });
}

async function previewCleaningRun(runId) {
  if (!runId) return;

  try {
    const runDetail = await api(`/cleaning/runs/${runId}`);
    const preview = buildRunPreview(runDetail);
    state.cleaningPreview = {preview};
    state.latestCleaningResult = {
      cleaned_dataset_id: preview.cleaned_dataset?.id,
      cleaned_dataset: preview.cleaned_dataset,
      download_url: runDetail.download_url,
    };

    if (els.cleaningDownload) {
      els.cleaningDownload.href = runDetail.download_url;
      els.cleaningDownload.classList.remove("hidden");
    }
    if (els.cleaningOpenDataset && preview.cleaned_dataset?.id) {
      els.cleaningOpenDataset.dataset.datasetId = preview.cleaned_dataset.id;
      els.cleaningOpenDataset.classList.remove("hidden");
    } else if (els.cleaningOpenDataset) {
      els.cleaningOpenDataset.classList.add("hidden");
      delete els.cleaningOpenDataset.dataset.datasetId;
    }

    renderCleaningPreview();
    showToast(`Loaded preview for cleaning run #${runId}.`);
  } catch (error) {
    showToast(error.message);
  }
}

async function previewCleaningSteps() {
  const steps = selectedCleaningSteps();
  if (!state.selectedDatasetId) {
    showToast("Choose a dataset first.");
    return;
  }
  if (!steps.length) {
    showToast("Select at least one cleaning step.");
    return;
  }

  try {
    els.cleaningPreviewButton.disabled = true;
    els.cleaningPreviewButton.textContent = "Previewing";
    state.cleaningPreview = await api(`/cleaning/datasets/${state.selectedDatasetId}/preview`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({steps}),
    });
    renderCleaningPreview();
  } catch (error) {
    showToast(error.message);
  } finally {
    els.cleaningPreviewButton.disabled = false;
    els.cleaningPreviewButton.textContent = "Preview";
  }
}

async function applyCleaningSteps() {
  const steps = selectedCleaningSteps();
  if (!state.selectedDatasetId) {
    showToast("Choose a dataset first.");
    return;
  }
  if (!steps.length) {
    showToast("Select at least one cleaning step.");
    return;
  }

  try {
    els.cleaningApplyButton.disabled = true;
    els.cleaningApplyButton.textContent = "Applying";
    state.latestCleaningResult = await api(`/cleaning/datasets/${state.selectedDatasetId}/apply`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({steps}),
    });
    state.cleaningPreview = {preview: {
      before: {
        ...(state.latestCleaningResult.result?.before || {}),
        sample: state.latestCleaningResult.result?.before_sample || state.cleaningPreview?.preview?.before?.sample || [],
      },
      after: {
        ...(state.latestCleaningResult.result?.after || {}),
        sample: state.latestCleaningResult.result?.after_sample || state.latestCleaningResult.result?.sample || [],
      },
      diff: {
        rows_removed: state.latestCleaningResult.result?.rows_removed || 0,
        columns_removed: state.latestCleaningResult.result?.columns_removed || [],
        columns_changed: state.latestCleaningResult.result?.columns_changed || [],
        cleaned_columns: state.latestCleaningResult.result?.cleaned_columns || [],
      },
      cleaned_dataset: state.latestCleaningResult.cleaned_dataset || state.latestCleaningResult.result?.cleaned_dataset || null,
      step_details: state.latestCleaningResult.result?.step_details || [],
    }};
    if (els.cleaningDownload) {
      els.cleaningDownload.href = state.latestCleaningResult.download_url;
      els.cleaningDownload.classList.remove("hidden");
    }
    if (els.cleaningOpenDataset && state.latestCleaningResult.cleaned_dataset_id) {
      els.cleaningOpenDataset.dataset.datasetId = state.latestCleaningResult.cleaned_dataset_id;
      els.cleaningOpenDataset.classList.remove("hidden");
    }
    await refreshDatasetRegistry(state.selectedDatasetId);
    showToast("Cleaning applied. Cleaned dataset version is ready.");
    const runs = await api(`/cleaning/datasets/${state.selectedDatasetId}/runs`);
    state.cleaningRuns = runs || [];
    renderCleaningPreview();
    renderCleaningRuns();
  } catch (error) {
    showToast(error.message);
  } finally {
    els.cleaningApplyButton.disabled = false;
    els.cleaningApplyButton.textContent = "Apply and save";
  }
}

async function loadEdaData() {
  if (!state.selectedDatasetId) {
    renderEdaEmpty();
    return;
  }

  try {
    els.edaInsightsEmpty.classList.add("hidden");
    els.edaCorrelationsEmpty.classList.add("hidden");
    els.edaMissingnessEmpty.classList.add("hidden");

    els.edaNumericPills.innerHTML = `<span style="font-size: 12px; color: var(--faint); padding-left: 4px;">Loading numerical columns...</span>`;
    els.edaCategoricalPills.innerHTML = `<span style="font-size: 12px; color: var(--faint); padding-left: 4px;">Loading categorical columns...</span>`;
    els.edaActiveColName.textContent = "Analyzing dataset";
    els.edaActiveColType.textContent = "Active Profile";
    els.edaActiveColBadge.textContent = "Loading";
    els.edaActiveColBadge.className = "status-pill";
    els.edaActiveColProfile.innerHTML = `
      <div class="empty-state">
        <strong>Compiling EDA</strong>
        <span>Analyzing distributions, correlations, and missingness patterns.</span>
      </div>
    `;
    
    const result = await api(`/datasets/${state.selectedDatasetId}/eda`);
    state.edaResult = result.eda;
    renderEda();
  } catch (error) {
    showToast("Failed to load EDA data: " + error.message);
    renderEdaError(error.message);
  }
}

function renderEdaEmpty() {
  state.edaResult = null;
  els.edaInsightsList.innerHTML = "";
  els.edaInsightsEmpty.classList.remove("hidden");
  els.edaPosCorrelations.innerHTML = "";
  els.edaNegCorrelations.innerHTML = "";
  els.edaCorrelationsEmpty.classList.remove("hidden");
  els.edaMissingRows.innerHTML = "";
  els.edaCoMissingColumns.innerHTML = "";
  els.edaMissingnessEmpty.classList.remove("hidden");
  els.edaNumericPills.innerHTML = "";
  els.edaCategoricalPills.innerHTML = "";
  els.edaActiveColType.textContent = "Active Profile";
  els.edaActiveColName.textContent = "No column selected";
  els.edaActiveColBadge.textContent = "Select a feature";
  els.edaActiveColBadge.className = "status-pill";
  els.edaActiveColProfile.innerHTML = `
    <div class="empty-state">
      <strong>Select a dataset</strong>
      <span>Choose or upload a dataset to inspect EDA.</span>
    </div>
  `;
}

function renderEdaError(message) {
  state.edaResult = null;
  const safeMessage = escapeHtml(message || "Unknown error while loading EDA.");

  els.edaInsightsList.innerHTML = `
    <article class="insight-card warn">
      <div>
        <strong>EDA could not be loaded</strong>
        <p style="margin: 4px 0 0;">${safeMessage}</p>
      </div>
    </article>
  `;
  els.edaInsightsEmpty.classList.add("hidden");

  els.edaPosCorrelations.innerHTML = "";
  els.edaNegCorrelations.innerHTML = "";
  els.edaCorrelationsEmpty.classList.remove("hidden");
  els.edaMissingRows.innerHTML = "";
  els.edaCoMissingColumns.innerHTML = "";
  els.edaMissingnessEmpty.classList.remove("hidden");

  els.edaNumericPills.innerHTML = "";
  els.edaCategoricalPills.innerHTML = "";
  els.edaActiveColType.textContent = "EDA Error";
  els.edaActiveColName.textContent = "Unable to render EDA";
  els.edaActiveColBadge.textContent = "Failed";
  els.edaActiveColBadge.className = "status-pill";
  els.edaActiveColProfile.innerHTML = `
    <div class="empty-state">
      <strong>Unable to render EDA</strong>
      <span>${safeMessage}</span>
    </div>
  `;
}

function renderEda() {
  const eda = state.edaResult;
  if (!eda) {
    renderEdaEmpty();
    return;
  }

  // 1. Insights
  const insights = eda.insights || [];
  els.edaInsightsEmpty.classList.toggle("hidden", insights.length > 0);
  els.edaInsightsList.innerHTML = insights
    .map((insight) => {
      const tone = insight.type === "outlier_heavy" ? "warn" : "info";
      return `
        <article class="insight-card ${tone}">
          <div>
            <strong>${escapeHtml(insight.column || "Dataset")}</strong>
            <p style="margin: 4px 0 0;">${escapeHtml(insight.message)}</p>
          </div>
        </article>
      `;
    })
    .join("");

  // 2. Correlations
  const correlations = eda.correlations || {};
  const topPos = correlations.top_pos || [];
  const topNeg = correlations.top_neg || [];
  const hasCorrelations = topPos.length > 0 || topNeg.length > 0;
  els.edaCorrelationsEmpty.classList.toggle("hidden", hasCorrelations);
  
  els.edaPosCorrelations.innerHTML = topPos
    .map(item => {
      const columns = Array.isArray(item.columns) ? item.columns : [];
      return `
        <div class="correlation-item">
          <div class="correlation-cols">
            <span>${escapeHtml(columns[0] || "Column A")}</span>
            <span style="color: var(--muted); font-size: 11px; font-weight: normal;">and ${escapeHtml(columns[1] || "Column B")}</span>
          </div>
          <div class="correlation-val pos">+${formatDecimal(item.correlation)}</div>
        </div>
      `;
    }).join("");

  els.edaNegCorrelations.innerHTML = topNeg
    .map(item => {
      const columns = Array.isArray(item.columns) ? item.columns : [];
      return `
        <div class="correlation-item">
          <div class="correlation-cols">
            <span>${escapeHtml(columns[0] || "Column A")}</span>
            <span style="color: var(--muted); font-size: 11px; font-weight: normal;">and ${escapeHtml(columns[1] || "Column B")}</span>
          </div>
          <div class="correlation-val neg">${formatDecimal(item.correlation)}</div>
        </div>
      `;
    }).join("");

  // 3. Missingness
  const missingness = eda.missingness || {};
  const missingRows = missingness.row_missing_distribution || [];
  const coMissing = missingness.column_pairs || [];
  const hasMissing = missingRows.some(r => r.missing_columns > 0) || coMissing.length > 0;
  els.edaMissingnessEmpty.classList.toggle("hidden", hasMissing);

  els.edaMissingRows.innerHTML = missingRows
    .map(r => `
      <div class="missing-dist-item">
        <span>Rows missing <strong>${r.missing_columns}</strong> cols</span>
        <strong>${r.row_count} rows</strong>
      </div>
    `).join("");

  els.edaCoMissingColumns.innerHTML = coMissing
    .map(item => `
      <div class="missing-dist-item">
        <span>${escapeHtml(Array.isArray(item.columns) ? item.columns.join(" & ") : "Column pair")}</span>
        <strong>${item.both_missing_count} rows (${formatPercent(item.both_missing_rate)})</strong>
      </div>
    `).join("");

  // 4. Render interactive column explorer sidebar registry
  const numerics = eda.numeric_distributions || {};
  const categoricals = eda.categorical_distributions || {};
  
  const numericKeys = Object.keys(numerics);
  const categoricalKeys = Object.keys(categoricals);

  // Apply filtering based on search term
  const filterTerm = (state.edaSearchTerm || "").toLowerCase().trim();
  const filteredNumerics = numericKeys.filter(k => k.toLowerCase().includes(filterTerm));
  const filteredCategoricals = categoricalKeys.filter(k => k.toLowerCase().includes(filterTerm));

  // Determine active column
  if (!state.activeEdaColumn || (!numerics[state.activeEdaColumn] && !categoricals[state.activeEdaColumn])) {
    state.activeEdaColumn = numericKeys[0] || categoricalKeys[0] || null;
  }

  const activeColNameEl = document.querySelector("#eda-active-col-name");
  const activeColTypeEl = document.querySelector("#eda-active-col-type");
  const activeColBadgeEl = document.querySelector("#eda-active-col-badge");
  const activeProfileEl = document.querySelector("#eda-active-col-profile");

  const numericPillsEl = document.querySelector("#eda-numeric-pills");
  const categoricalPillsEl = document.querySelector("#eda-categorical-pills");

  // Render Numeric pills
  if (numericPillsEl) {
    if (filteredNumerics.length === 0) {
      numericPillsEl.innerHTML = `<span style="font-size: 12px; color: var(--faint); padding-left: 4px;">No matching numeric columns</span>`;
    } else {
      numericPillsEl.innerHTML = filteredNumerics
        .map(col => {
          const activeClass = col === state.activeEdaColumn ? "active" : "";
          return `<button class="col-pill ${activeClass}" data-col="${escapeHtml(col)}"><span>${escapeHtml(col)}</span><span class="type-badge num">123</span></button>`;
        })
        .join("");
    }
  }

  // Render Categorical pills
  if (categoricalPillsEl) {
    if (filteredCategoricals.length === 0) {
      categoricalPillsEl.innerHTML = `<span style="font-size: 12px; color: var(--faint); padding-left: 4px;">No matching categorical columns</span>`;
    } else {
      categoricalPillsEl.innerHTML = filteredCategoricals
        .map(col => {
          const activeClass = col === state.activeEdaColumn ? "active" : "";
          return `<button class="col-pill ${activeClass}" data-col="${escapeHtml(col)}"><span>${escapeHtml(col)}</span><span class="type-badge cat">abc</span></button>`;
        })
        .join("");
    }
  }

  // Add click listeners to all pills
  document.querySelectorAll(".col-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      state.activeEdaColumn = pill.dataset.col;
      renderEda();
    });
  });

  // Render the detailed profile of the active column
  if (!state.activeEdaColumn) {
    if (activeColNameEl) activeColNameEl.textContent = "No column selected";
    if (activeColTypeEl) activeColTypeEl.textContent = "Active Profile";
    if (activeColBadgeEl) {
      activeColBadgeEl.textContent = "Select a feature";
      activeColBadgeEl.className = "status-pill";
    }
    if (activeProfileEl) {
      activeProfileEl.innerHTML = `
        <div class="empty-state">
          <strong>No columns available</strong>
          <span>This dataset appears to be empty.</span>
        </div>
      `;
    }
    return;
  }

  const activeCol = state.activeEdaColumn;
  if (activeColNameEl) activeColNameEl.textContent = activeCol;

  if (numerics[activeCol]) {
    // Numeric Active Column Detailed Render
    if (activeColTypeEl) activeColTypeEl.textContent = "Numerical Feature Profile";
    if (activeColBadgeEl) {
      activeColBadgeEl.textContent = "Numeric";
      activeColBadgeEl.className = "status-pill";
    }

    const info = numerics[activeCol];
    const quantiles = info.quantiles || {};
    const outliers = info.outliers || {};
    const hist = info.histogram || { bins: [], counts: [] };
    const counts = Array.isArray(hist.counts) ? hist.counts.map((count) => Number(count) || 0) : [];
    const bins = Array.isArray(hist.bins) ? hist.bins : [];
    const outlierRate = Number(outliers.rate || 0);
    const outlierClass = outlierRate > 0.05 ? "bad" : "ok";
    const plotMode = state.activeEdaPlotMode === "histogram" ? "histogram" : "box";
    const plotHtml = plotMode === "histogram"
      ? renderEdaHistogramPlot(counts, bins)
      : renderEdaBoxPlot({bins, quantiles, outliers});
    const totalHistogramRows = counts.reduce((sum, count) => sum + count, 0);
    const peakIndex = counts.reduce(
      (bestIndex, count, index) => (count > (counts[bestIndex] || 0) ? index : bestIndex),
      0,
    );
    const peakBinLabel = bins.length > peakIndex + 1
      ? `${formatDecimal(bins[peakIndex])} to ${formatDecimal(bins[peakIndex + 1])}`
      : "-";
    const metricHtml = plotMode === "histogram"
      ? `
          <div>
            <h4 class="eda-sub-title" style="margin-top: 0;">Histogram Summary</h4>
            <div class="eda-stats-grid">
              <div class="eda-stat-box"><span>Rows plotted</span><strong>${escapeHtml(totalHistogramRows)}</strong></div>
              <div class="eda-stat-box"><span>Bins</span><strong>${escapeHtml(counts.length)}</strong></div>
              <div class="eda-stat-box"><span>Peak bin</span><strong>${escapeHtml(peakBinLabel)}</strong></div>
              <div class="eda-stat-box"><span>Peak rows</span><strong>${escapeHtml(counts[peakIndex] || 0)}</strong></div>
            </div>
          </div>
        `
      : `
          <div>
            <h4 class="eda-sub-title" style="margin-top: 0;">Statistical Quantiles</h4>
            <div class="eda-stats-grid">
              <div class="eda-stat-box"><span>p25 (Q1)</span><strong>${formatDecimal(quantiles.p25)}</strong></div>
              <div class="eda-stat-box"><span>p50 (Median)</span><strong>${formatDecimal(quantiles.p50)}</strong></div>
              <div class="eda-stat-box"><span>p75 (Q3)</span><strong>${formatDecimal(quantiles.p75)}</strong></div>
              <div class="eda-stat-box"><span>p95</span><strong>${formatDecimal(quantiles.p95)}</strong></div>
              <div class="eda-stat-box"><span>p99</span><strong>${formatDecimal(quantiles.p99)}</strong></div>
            </div>
          </div>

          <div class="eda-outliers-box">
            <div>
              <span>Potential Anomaly Outliers (IQR Method)</span>
              <p style="margin: 4px 0 0; font-size: 11px; color: var(--faint);">Outer limits: [${formatDecimal(outliers.lower_bound)} to ${formatDecimal(outliers.upper_bound)}]</p>
            </div>
            <strong class="${outlierClass}" style="font-size: 15px;">${escapeHtml(outliers.num_outliers ?? 0)} rows (${formatPercent(outlierRate)})</strong>
          </div>
        `;

    if (activeProfileEl) {
      activeProfileEl.innerHTML = `
        <div style="display: grid; gap: 18px;">
          <div class="eda-plot-header">
            <div>
              <h4 class="eda-sub-title" style="margin: 0;">Distribution View</h4>
            </div>
            <div class="eda-plot-toggle-group" role="group" aria-label="Numeric plot type">
              <button class="eda-plot-toggle ${plotMode === "box" ? "active" : ""}" type="button" data-plot="box">Box plot</button>
              <button class="eda-plot-toggle ${plotMode === "histogram" ? "active" : ""}" type="button" data-plot="histogram">Histogram</button>
            </div>
          </div>

          ${plotHtml}

          ${metricHtml}
        </div>
      `;

      document.querySelectorAll(".eda-plot-toggle").forEach((button) => {
        button.addEventListener("click", () => {
          state.activeEdaPlotMode = button.dataset.plot || "box";
          renderEda();
        });
      });
    }
  } else if (categoricals[activeCol]) {
    // Categorical Active Column Detailed Render
    if (activeColTypeEl) activeColTypeEl.textContent = "Categorical Feature Profile";
    if (activeColBadgeEl) {
      activeColBadgeEl.textContent = "Category";
      activeColBadgeEl.className = "status-pill";
      activeColBadgeEl.style.borderColor = "#e3d1fc";
      activeColBadgeEl.style.color = "var(--purple)";
      activeColBadgeEl.style.background = "var(--purple-soft)";
    }

    const info = categoricals[activeCol];
    const topValues = info.top_values || [];
    
    const rows = topValues
      .map(val => {
        const pct = Math.max(0, Math.min(100, Math.round(Number(val.percentage || 0) * 100)));
        return `
          <div class="cat-row" style="grid-template-columns: minmax(140px, 0.5fr) minmax(100px, 1fr) 52px; min-height: 28px;">
            <span class="cat-name" title="${escapeHtml(val.value)}" style="font-size: 13px; font-weight: 700;">${escapeHtml(val.value)}</span>
            <div class="bar-track" style="margin: 0; height: 10px; background: hsl(210, 20%, 93%);">
              <div class="bar-fill" style="width: ${pct}%; background: linear-gradient(90deg, var(--purple), #b38dfd);"></div>
            </div>
            <span class="bar-value" style="font-size: 12px; font-weight: 800; color: var(--muted);">${pct}%</span>
          </div>
        `;
      })
      .join("");

    if (activeProfileEl) {
      activeProfileEl.innerHTML = `
        <div style="display: grid; gap: 18px;">
          <div>
            <h4 class="eda-sub-title" style="margin-top: 0; margin-bottom: 12px;">Top 10 Value Counts (Density)</h4>
            <div class="cat-dist-list" style="gap: 10px;">
              ${rows}
            </div>
          </div>

          <div class="cat-info-summary" style="border-top: 1px solid var(--line); padding-top: 14px; margin-top: 6px; font-size: 13px; color: var(--muted);">
            <span>Unique labels: <strong style="color: var(--ink);">${info.unique_values}</strong></span>
            <span>Rare entries (x1): <strong style="color: var(--ink);">${info.rare_values}</strong></span>
            <span>Cardinality ratio: <strong style="color: var(--ink);">${formatPercent(info.cardinality_ratio)}</strong></span>
          </div>
        </div>
      `;
    }
  }

  // Setup column explorer search event listener once
  const searchInput = document.querySelector("#eda-col-search");
  if (searchInput && !searchInput.dataset.bound) {
    searchInput.dataset.bound = "true";
    searchInput.value = state.edaSearchTerm || "";
    searchInput.addEventListener("input", () => {
      state.edaSearchTerm = searchInput.value;
      renderEda();
      
      const reSearch = document.querySelector("#eda-col-search");
      if (reSearch) {
        reSearch.focus();
        // Move cursor to the end of search term
        const len = reSearch.value.length;
        reSearch.setSelectionRange(len, len);
      }
    });
  }
}

function renderMetrics() {
  const profile = state.selectedCheck?.profile || {};
  const highCount = state.issues.filter((issue) => issue.severity === "high").length;

  els.metricRows.textContent = profile.num_rows ?? 0;
  els.metricIssues.textContent = state.issues.length;
  els.metricHigh.textContent = highCount;
}

function renderProfile() {
  const profile = state.selectedCheck?.profile || {};
  const columns = profile.columns_details || [];
  const nullHeavy = columns.filter((column) => Number(column.null_ratio || 0) > 0.2);

  els.selectedTitle.textContent = state.selectedDataset
    ? `${state.selectedDataset.filename} (${datasetVersionLabel(state.selectedDataset)})`
    : "No dataset selected";
  els.runStatus.textContent = state.selectedCheck?.status || "No run";
  els.profileRows.textContent = profile.num_rows ?? 0;
  els.profileColumns.textContent = profile.num_columns ?? 0;
  els.profileNullHeavy.textContent = nullHeavy.length;

  if (!columns.length) {
    els.columnHealth.innerHTML = `
      <div class="empty-state">
        <strong>No profile data</strong>
        <span>Run a quality check to inspect column health.</span>
      </div>
    `;
    return;
  }

  els.columnHealth.innerHTML = columns
    .map((column) => {
      const ratio = Number(column.null_ratio || 0);
      const pct = Math.round(ratio * 100);
      const tone = ratio > 0.35 ? "bad" : ratio > 0.1 ? "warn" : "";
      return `
        <div class="column-row" title="${escapeHtml(column.name)}">
          <div class="column-name">${escapeHtml(column.name)}</div>
          <div class="bar-track">
            <div class="bar-fill ${tone}" style="width: ${Math.min(100, pct)}%"></div>
          </div>
          <div class="bar-value">${pct}% null</div>
        </div>
      `;
    })
    .join("");
}

function renderIssues() {
  const filtered =
    state.severity === "all"
      ? state.issues
      : state.issues.filter((issue) => issue.severity === state.severity);

  els.issuesEmpty.classList.toggle("hidden", filtered.length > 0);

  els.issueList.innerHTML = filtered
    .map((issue) => {
      const evidence = Object.entries(issue.evidence || {})
        .map(([key, value]) => {
          const display = typeof value === "number" ? Number(value.toFixed?.(3) ?? value) : value;
          return `<span class="evidence-chip">${escapeHtml(key)}: ${escapeHtml(display)}</span>`;
        })
        .join("");

      return `
        <article class="issue-item">
          <div class="issue-title">
            <strong>${escapeHtml(issue.type)}</strong>
            <span class="severity ${escapeHtml(issue.severity)}">${escapeHtml(issue.severity)}</span>
          </div>
          <p>${escapeHtml(issue.message)}</p>
          <div class="evidence-grid">
            <span class="evidence-chip">column: ${escapeHtml(issue.column || "dataset")}</span>
            ${evidence}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderEmptySelection() {
  els.selectedTitle.textContent = "No dataset selected";
  els.runStatus.textContent = "Idle";
  els.metricRows.textContent = "0";
  els.metricIssues.textContent = "0";
  els.metricHigh.textContent = "0";
  els.profileRows.textContent = "0";
  els.profileColumns.textContent = "0";
  els.profileNullHeavy.textContent = "0";
  els.columnHealth.innerHTML = "";
  els.issueList.innerHTML = "";
  els.issuesEmpty.classList.remove("hidden");
  renderBriefingDefault();
  renderAgentDatasetOptions();
}

function renderBriefingDefault() {
  if (!state.selectedDataset) {
    els.briefing.innerHTML = `
      <strong>Ready for review</strong>
      <p>Select a dataset or upload a CSV.</p>
    `;
    return;
  }

  els.briefing.innerHTML = `
    <strong>${escapeHtml(state.selectedDataset.filename)}</strong>
    <p>${state.issues.length} issue${state.issues.length === 1 ? "" : "s"} found in the latest check.</p>
  `;
}

function generateBriefing() {
  if (!state.selectedDataset || !state.selectedCheck) {
    renderBriefingDefault();
    return;
  }

  const profile = state.selectedCheck.profile || {};
  const high = state.issues.filter((issue) => issue.severity === "high");
  const medium = state.issues.filter((issue) => issue.severity === "medium");
  const topColumns = [...new Set(state.issues.map((issue) => issue.column).filter(Boolean))].slice(0, 4);
  const priority = high[0] || medium[0] || state.issues[0];

  els.briefing.innerHTML = `
    <strong>${escapeHtml(state.selectedDataset.filename)}</strong>
    <p>The latest run scanned ${escapeHtml(profile.num_rows ?? 0)} rows and ${escapeHtml(profile.num_columns ?? 0)} columns. It found ${state.issues.length} open issue${state.issues.length === 1 ? "" : "s"}, including ${high.length} high severity item${high.length === 1 ? "" : "s"}.</p>
    <ul>
      <li>Primary risk: ${escapeHtml(priority?.message || "No blocking issue detected.")}</li>
      <li>Affected columns: ${escapeHtml(topColumns.join(", ") || "none")}</li>
      <li>Next step: review evidence and confirm the expected business rule.</li>
    </ul>
  `;
}

function renderAgentResult(result) {
  state.agentResult = result;
  els.agentSource.textContent = result.generated_by || "agent";
  els.agentSql.textContent = result.sql || "";
  els.agentRowCount.textContent = `${result.row_count || 0} row${result.row_count === 1 ? "" : "s"}`;

  const statusText =
    result.generated_by === "llm"
      ? "LLM generated this SQL."
      : "SQL generation did not complete through the configured LLM.";

  els.agentExplanation.innerHTML = `
    <strong>${escapeHtml(result.dataset?.filename || "Selected dataset")}</strong>
    <p>${escapeHtml(result.explanation || "SQL generated and executed successfully.")}</p>
    <p>${escapeHtml(statusText)}</p>
  `;

  if (!result.rows?.length) {
    els.agentResultTable.innerHTML = "";
    els.agentResultEmpty.classList.remove("hidden");
    return;
  }

  els.agentResultEmpty.classList.add("hidden");
  const columns = result.columns?.length ? result.columns : Object.keys(result.rows[0]);

  const header = `
    <thead>
      <tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
    </thead>
  `;
  const body = `
    <tbody>
      ${result.rows
        .map(
          (row) => `
            <tr>
              ${columns.map((column) => `<td>${escapeHtml(row[column])}</td>`).join("")}
            </tr>
          `,
        )
        .join("")}
    </tbody>
  `;

  els.agentResultTable.innerHTML = header + body;
}

function renderAgentError(message) {
  state.agentResult = null;
  els.agentSource.textContent = "Error";
  els.agentSql.textContent = "-- SQL generation failed";
  els.agentRowCount.textContent = "0 rows";
  els.agentExplanation.innerHTML = `
    <strong>Agent request failed</strong>
    <p>${escapeHtml(message || "Unknown error while generating SQL.")}</p>
  `;
  els.agentResultTable.innerHTML = "";
  els.agentResultEmpty.classList.remove("hidden");
}

function renderQueryHistory() {
  if (!els.queryHistoryList) return;
  const items = state.queryHistory || [];
  els.queryHistoryEmpty?.classList.toggle("hidden", items.length > 0);
  els.queryHistoryList.innerHTML = items
    .map((item) => `
      <article class="history-card">
        <div>
          <strong>${escapeHtml(item.mode === "manual_sql" ? "Manual SQL" : "AI SQL Agent")}</strong>
          <span>${formatDate(item.created_at)} | ${escapeHtml(item.status)} | ${escapeHtml(item.row_count || 0)} rows</span>
        </div>
        ${item.question ? `<p>${escapeHtml(item.question)}</p>` : ""}
        <pre class="mini-sql">${escapeHtml(item.sql || "-- no SQL captured")}</pre>
        ${item.error ? `<span class="severity bad">${escapeHtml(item.error)}</span>` : ""}
      </article>
    `)
    .join("");
}

async function loadQueryHistory() {
  if (!state.selectedDatasetId) return;
  state.queryHistory = await api(`/agent/history?dataset_id=${state.selectedDatasetId}`);
  renderQueryHistory();
}

async function runManualSql() {
  const datasetId = Number(els.agentDatasetSelect.value);
  const sql = els.manualSqlInput.value.trim();
  if (!datasetId || !sql) {
    showToast("Choose a dataset and enter SQL first.");
    return;
  }

  try {
    els.manualSqlSubmit.disabled = true;
    els.manualSqlSubmit.textContent = "Running";
    const result = await api("/agent/sql", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({dataset_id: datasetId, sql, limit: 500}),
    });
    renderAgentResult(result);
    await loadQueryHistory();
  } catch (error) {
    showToast(error.message);
    renderAgentError(error.message);
  } finally {
    els.manualSqlSubmit.disabled = false;
    els.manualSqlSubmit.textContent = "Run SQL";
  }
}

async function loadOperationsData() {
  renderOperationsDatasetOptions();
  await Promise.allSettled([
    loadWorkspaceSummary(),
    loadReports(),
    loadJobs(),
    loadEvents(),
  ]);
}

function renderWorkspaceSummary() {
  if (!els.workspaceSummary) return;
  const context = state.workspaceContext;
  if (!context) {
    els.workspaceSummary.innerHTML = `<div class="empty-state"><strong>No workspace loaded</strong><span>Refresh workspace context.</span></div>`;
    return;
  }
  els.workspaceSummary.innerHTML = `
    <div class="ops-metrics">
      <div><span>Workspace</span><strong>${escapeHtml(context.workspace.name)}</strong></div>
      <div><span>User</span><strong>${escapeHtml(context.user.display_name)}</strong></div>
      <div><span>Role</span><strong>${escapeHtml(context.user.role)}</strong></div>
      <div><span>Datasets</span><strong>${escapeHtml(context.dataset_count)}</strong></div>
    </div>
    <p class="table-note">Auth mode: ${escapeHtml(context.auth_mode)}. Use X-Workspace-Id for API workspace routing.</p>
  `;
}

async function loadWorkspaceSummary() {
  state.workspaceContext = await api("/workspace/current");
  renderWorkspaceSummary();
}

function renderReports() {
  if (!els.reportsList) return;
  const reports = state.reports || [];
  els.reportsList.innerHTML = reports.length
    ? reports.map((report) => `
        <article class="history-card">
          <div>
            <strong>Report #${escapeHtml(report.id)}</strong>
            <span>${formatDate(report.created_at)} | Dataset #${escapeHtml(report.dataset_id)}</span>
          </div>
          <p>${escapeHtml(report.summary?.issue_count ?? 0)} issues | ${escapeHtml(report.summary?.eda_insight_count ?? 0)} insights</p>
          <a class="secondary-button compact" href="${escapeHtml(report.download_url)}" target="_blank" rel="noreferrer">Open report</a>
        </article>
      `).join("")
    : `<div class="empty-state"><strong>No reports</strong><span>Export a dataset report to create one.</span></div>`;
}

async function loadReports() {
  const datasetId = Number(els.reportDataset?.value || state.selectedDatasetId || 0);
  state.reports = await api(datasetId ? `/reports?dataset_id=${datasetId}` : "/reports");
  renderReports();
}

async function exportReport() {
  const datasetId = Number(els.reportDataset.value);
  if (!datasetId) {
    showToast("Choose a dataset first.");
    return;
  }

  try {
    els.reportExportButton.disabled = true;
    els.reportExportButton.textContent = "Exporting";
    const result = await api(`/reports/datasets/${datasetId}/export`, {method: "POST"});
    showToast(`Report #${result.report.id} exported.`);
    await Promise.all([loadReports(), loadJobs()]);
  } catch (error) {
    showToast(error.message);
  } finally {
    els.reportExportButton.disabled = false;
    els.reportExportButton.textContent = "Export HTML report";
  }
}

function renderJobs() {
  if (!els.jobsList) return;
  const jobs = state.jobs || [];
  els.jobsList.innerHTML = jobs.length
    ? jobs.map((job) => `
        <article class="history-card">
          <div>
            <strong>${escapeHtml(job.type)} #${escapeHtml(job.id)}</strong>
            <span>${formatDate(job.created_at)} | ${escapeHtml(job.status)} | ${escapeHtml(job.progress)}%</span>
          </div>
          ${job.error ? `<span class="severity bad">${escapeHtml(job.error)}</span>` : ""}
        </article>
      `).join("")
    : `<div class="empty-state"><strong>No jobs</strong><span>Report exports and future long-running tasks will appear here.</span></div>`;
}

async function loadJobs() {
  state.jobs = await api("/jobs");
  renderJobs();
}

function renderEvents() {
  if (!els.eventsList) return;
  const events = state.events || [];
  els.eventsList.innerHTML = events.length
    ? events.map((event) => `
        <article class="history-card">
          <div>
            <strong>${escapeHtml(event.level)} | ${escapeHtml(event.source)}</strong>
            <span>${formatDate(event.created_at)}</span>
          </div>
          <p>${escapeHtml(event.message)}</p>
          <pre class="mini-sql">${escapeHtml(JSON.stringify(event.context || {}, null, 2))}</pre>
        </article>
      `).join("")
    : `<div class="empty-state"><strong>No events</strong><span>Backend and frontend errors will appear here.</span></div>`;
}

async function loadEvents() {
  state.events = await api("/observability/events");
  renderEvents();
}

async function buildRuleFromNaturalLanguage(create = false) {
  const datasetId = Number(els.ruleBuilderDataset.value);
  const instruction = els.ruleBuilderInput.value.trim();
  if (!datasetId || !instruction) {
    showToast("Choose a dataset and enter a rule instruction.");
    return;
  }

  const button = create ? els.ruleBuilderCreate : els.ruleBuilderPreview;
  try {
    button.disabled = true;
    button.textContent = create ? "Creating" : "Previewing";
    const result = await api("/rules/from-natural-language", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({dataset_id: datasetId, instruction, create}),
    });
    const rule = result.rule || result.candidate;
    els.ruleBuilderOutput.innerHTML = `
      <div class="ops-output-card">
        <strong>${escapeHtml(rule.name)}</strong>
        <span>Column: ${escapeHtml(rule.column)} | Severity: ${escapeHtml(rule.severity)}</span>
        <pre class="mini-sql">${escapeHtml(rule.condition)}</pre>
        <p>${escapeHtml(result.created ? "Rule created and activated." : "Preview only. Create when ready.")}</p>
      </div>
    `;
    showToast(result.created ? "Rule created." : "Rule preview generated.");
  } catch (error) {
    showToast(error.message);
    els.ruleBuilderOutput.innerHTML = `<div class="empty-state"><strong>Rule builder failed</strong><span>${escapeHtml(error.message)}</span></div>`;
  } finally {
    button.disabled = false;
    button.textContent = create ? "Create rule" : "Preview rule";
  }
}

els.csvFile.addEventListener("change", () => {
  const file = els.csvFile.files[0];
  els.fileTitle.textContent = file ? file.name : "Choose CSV file";
  els.fileHint.textContent = file ? `${formatBytes(file.size)} ready to upload` : "No file selected";
});

els.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = els.csvFile.files[0];

  if (!file) {
    showToast("Choose a CSV file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    els.uploadButton.disabled = true;
    els.uploadButton.textContent = "Running";
    const result = await api("/datasets/upload", {
      method: "POST",
      body: formData,
    });
    showToast(`Completed check for ${file.name}`);
    els.uploadForm.reset();
    els.fileTitle.textContent = "Choose CSV file";
    els.fileHint.textContent = "No file selected";
    await loadDatasets(result.dataset_id);
  } catch (error) {
    showToast(error.message);
    renderAgentError(error.message);
  } finally {
    els.uploadButton.disabled = false;
    els.uploadButton.textContent = "Run check";
  }
});

els.refreshButton.addEventListener("click", () => loadDatasets());

els.severityFilter.addEventListener("change", () => {
  state.severity = els.severityFilter.value;
  renderIssues();
});

els.briefingButton.addEventListener("click", generateBriefing);

els.agentDatasetSelect.addEventListener("change", async () => {
  state.selectedDatasetId = Number(els.agentDatasetSelect.value);
  await loadSelectedDataset();
});

els.edaDatasetSelect.addEventListener("change", async () => {
  state.selectedDatasetId = Number(els.edaDatasetSelect.value);
  await loadSelectedDataset();
});

els.cleaningDatasetSelect.addEventListener("change", async () => {
  state.selectedDatasetId = Number(els.cleaningDatasetSelect.value);
  await loadSelectedDataset();
});

els.cleaningRefreshButton.addEventListener("click", loadCleaningData);
els.cleaningAiButton.addEventListener("click", loadAiCleaningSuggestions);
els.cleaningPreviewButton.addEventListener("click", previewCleaningSteps);
els.cleaningApplyButton.addEventListener("click", applyCleaningSteps);
els.cleaningOpenDataset.addEventListener("click", async () => {
  const datasetId = Number(els.cleaningOpenDataset.dataset.datasetId);
  if (!datasetId) return;

  state.selectedDatasetId = datasetId;
  window.location.hash = "#/datasets";
  await loadSelectedDataset();
  showToast("Opened cleaned dataset version.");
});

els.agentForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const datasetId = Number(els.agentDatasetSelect.value);
  const question = els.agentQuestion.value.trim();

  if (!datasetId) {
    showToast("Choose a dataset first.");
    return;
  }

  if (!question) {
    showToast("Type a question first.");
    return;
  }

  try {
    els.agentSubmit.disabled = true;
    els.agentSubmit.textContent = "Running agent";
    const result = await api("/agent/query", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        dataset_id: datasetId,
        question,
        limit: 200,
      }),
    });
    renderAgentResult(result);
    await loadQueryHistory();
  } catch (error) {
    showToast(error.message);
    renderAgentError(error.message);
  } finally {
    els.agentSubmit.disabled = false;
    els.agentSubmit.textContent = "Translate and run";
  }
});

els.manualSqlSubmit.addEventListener("click", runManualSql);
els.queryHistoryRefresh.addEventListener("click", loadQueryHistory);
els.workspaceRefresh.addEventListener("click", loadWorkspaceSummary);
els.ruleBuilderPreview.addEventListener("click", () => buildRuleFromNaturalLanguage(false));
els.ruleBuilderCreate.addEventListener("click", () => buildRuleFromNaturalLanguage(true));
els.reportExportButton.addEventListener("click", exportReport);
els.reportsRefresh.addEventListener("click", loadReports);
els.jobsRefresh.addEventListener("click", loadJobs);
els.eventsRefresh.addEventListener("click", loadEvents);
els.reportDataset.addEventListener("change", loadReports);

document.querySelectorAll(".example-chip").forEach((button) => {
  button.addEventListener("click", () => {
    els.agentQuestion.value = button.dataset.question || "";
    els.agentQuestion.focus();
  });
});

window.addEventListener("hashchange", renderRoute);

if (!window.location.hash) {
  window.location.hash = "#/home";
}

renderRoute();
loadDatasets();
