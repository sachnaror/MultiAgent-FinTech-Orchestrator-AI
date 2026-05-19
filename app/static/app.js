const sample = `Vendor: ABC Ltd
Invoice Number: INV123
Item: Cloud hosting | Qty: 2 | Unit Price: 1500 | Amount: 3000
Item: Support retainer | Qty: 1 | Unit Price: 2000 | Amount: 2000
Total Amount: 5000`;

const form = document.querySelector("#invoice-form");
const textArea = document.querySelector("#invoice-text");
const loadSample = document.querySelector("#load-sample");
const decisionBadge = document.querySelector("#decision-badge");
const decisionReason = document.querySelector("#decision-reason");
const issues = document.querySelector("#issues");
const audit = document.querySelector("#audit");

function money(value) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function setDecision(decision) {
  decisionBadge.className = "";
  decisionBadge.textContent = decision || "Idle";
  if (decision === "AUTO_APPROVE") decisionBadge.classList.add("approve");
  if (decision === "HUMAN_REVIEW") decisionBadge.classList.add("review");
  if (decision === "REJECT") decisionBadge.classList.add("reject");
  if (decision === "STOPPED") decisionBadge.classList.add("stopped");
}

function render(data) {
  setDecision(data.decision);
  decisionReason.textContent = data.decision_reason || "-";
  document.querySelector("#vendor").textContent = data.extracted?.vendor || "-";
  document.querySelector("#invoice-id").textContent = data.extracted?.invoice_id || "-";
  document.querySelector("#total").textContent = money(data.extracted?.total_amount);
  document.querySelector("#confidence").textContent = data.extracted ? `${Math.round(data.extracted.confidence * 100)}%` : "-";

  issues.innerHTML = "";
  const validationIssues = data.validation?.issues || [];
  if (!validationIssues.length) {
    const item = document.createElement("li");
    item.textContent = "No validation issues.";
    issues.appendChild(item);
  }
  validationIssues.forEach((issue) => {
    const item = document.createElement("li");
    item.className = issue.severity;
    item.textContent = `${issue.severity.toUpperCase()} ${issue.code}: ${issue.message}`;
    issues.appendChild(item);
  });

  audit.innerHTML = "";
  data.audit.forEach((entry) => {
    const item = document.createElement("li");
    item.textContent = `${entry.agent} - ${entry.status}: ${entry.message}`;
    audit.appendChild(item);
  });
}

loadSample.addEventListener("click", () => {
  textArea.value = sample;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setDecision("Running");
  const response = await fetch("/api/process-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: textArea.value }),
  });
  const data = await response.json();
  render(data);
});

fetch("/api/health")
  .then((response) => response.json())
  .then((data) => {
    document.querySelector("#health").textContent = data.status === "ok" ? "Ready" : "Check";
  });

textArea.value = sample;

