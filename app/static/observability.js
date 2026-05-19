const runsContainer = document.querySelector("#runs");
const runCount = document.querySelector("#run-count");
const refreshButton = document.querySelector("#refresh-runs");

function money(value) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function badgeClass(decision) {
  if (decision === "AUTO_APPROVE") return "approve";
  if (decision === "HUMAN_REVIEW") return "review";
  if (decision === "REJECT") return "reject";
  if (decision === "STOPPED") return "stopped";
  return "";
}

function renderIssue(issue) {
  const item = document.createElement("li");
  item.className = issue.severity;
  item.textContent = `${issue.severity.toUpperCase()} ${issue.code}: ${issue.message}`;
  return item;
}

function renderCheckpoint(checkpoint) {
  const item = document.createElement("li");
  const title = document.createElement("p");
  title.textContent = `${checkpoint.agent} - ${checkpoint.status}`;
  const detail = document.createElement("p");
  detail.className = "checkpoint-meta";
  detail.textContent = checkpoint.message;
  item.append(title, detail);
  return item;
}

function renderRun(run) {
  const card = document.createElement("article");
  card.className = "run-card";

  const summary = document.createElement("div");
  summary.className = "run-summary";
  summary.innerHTML = `
    <div><p class="label">Workflow ID</p><p>${run.workflow_id}</p></div>
    <div><p class="label">Decision</p><p><span class="status-pill ${badgeClass(run.decision)}">${run.decision || "-"}</span></p></div>
    <div><p class="label">Vendor</p><p>${run.vendor || "-"}</p></div>
    <div><p class="label">Invoice ID</p><p>${run.invoice_id || "-"}</p></div>
    <div><p class="label">Total</p><p>${money(run.total_amount)}</p></div>
  `;

  const reason = document.createElement("div");
  reason.className = "run-section";
  reason.innerHTML = `<h3>Decision Reason</h3><p>${run.decision_reason || "-"}</p>`;

  const issuesSection = document.createElement("div");
  issuesSection.className = "run-section";
  const issuesTitle = document.createElement("h3");
  issuesTitle.textContent = "Validation Issues";
  const issues = document.createElement("ul");
  issues.className = "issues";
  if (!run.validation_issues.length) {
    const item = document.createElement("li");
    item.textContent = "No validation issues.";
    issues.appendChild(item);
  }
  run.validation_issues.forEach((issue) => issues.appendChild(renderIssue(issue)));
  issuesSection.append(issuesTitle, issues);

  const checkpointsSection = document.createElement("div");
  checkpointsSection.className = "run-section";
  const checkpointsTitle = document.createElement("h3");
  checkpointsTitle.textContent = "Stateful Checkpoints";
  const checkpoints = document.createElement("ol");
  checkpoints.className = "checkpoint-list";
  run.stateful_checkpoints.forEach((checkpoint) => checkpoints.appendChild(renderCheckpoint(checkpoint)));
  checkpointsSection.append(checkpointsTitle, checkpoints);

  card.append(summary, reason, issuesSection, checkpointsSection);
  return card;
}

async function loadRuns() {
  runsContainer.textContent = "Loading runs...";
  const response = await fetch("/api/observability/runs");
  const data = await response.json();
  runCount.textContent = `${data.total_runs} run${data.total_runs === 1 ? "" : "s"}`;
  runsContainer.innerHTML = "";
  if (!data.runs.length) {
    runsContainer.textContent = "No workflow runs yet. Process an invoice first.";
    return;
  }
  data.runs.forEach((run) => runsContainer.appendChild(renderRun(run)));
}

refreshButton.addEventListener("click", loadRuns);
loadRuns();

