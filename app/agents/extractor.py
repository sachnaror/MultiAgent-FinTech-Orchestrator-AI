import re
from app.core.models import AgentRun, AgentStatus, ExtractedInvoice, LineItem, WorkflowState


class ExtractorAgent:
    name = "Agent A - Extractor"

    def run(self, state: WorkflowState) -> WorkflowState:
        text = state.source_text
        invoice = ExtractedInvoice(
            vendor=self._field(text, r"Vendor:\s*(.+)"),
            invoice_id=self._field(text, r"Invoice (?:Number|ID):\s*([A-Za-z0-9\-]+)"),
            total_amount=self._money(text, r"Total Amount:\s*([$]?[0-9,]+(?:\.[0-9]{1,2})?)"),
            line_items=self._line_items(text),
            source_refs=self._source_refs(text),
        )
        invoice.confidence = self._confidence(invoice, text)
        state.extracted = invoice
        state.audit.append(
            AgentRun(
                agent=self.name,
                status=AgentStatus.success,
                message="Extracted invoice fields with source references and confidence.",
                data=invoice.model_dump(),
            )
        )
        return state

    def _field(self, text: str, pattern: str) -> str | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _money(self, text: str, pattern: str) -> float | None:
        value = self._field(text, pattern)
        if value is None:
            return None
        return float(value.replace("$", "").replace(",", ""))

    def _line_items(self, text: str) -> list[LineItem]:
        items = []
        pattern = re.compile(
            r"Item:\s*(?P<description>.+?)\s*\|\s*Qty:\s*(?P<quantity>[0-9.]+)\s*\|\s*"
            r"Unit Price:\s*(?P<unit_price>[$]?[0-9,]+(?:\.[0-9]{1,2})?)\s*\|\s*"
            r"Amount:\s*(?P<amount>[$]?[0-9,]+(?:\.[0-9]{1,2})?)",
            flags=re.IGNORECASE,
        )
        for index, match in enumerate(pattern.finditer(text), start=1):
            items.append(
                LineItem(
                    description=match.group("description").strip(),
                    quantity=float(match.group("quantity")),
                    unit_price=self._parse_money(match.group("unit_price")),
                    amount=self._parse_money(match.group("amount")),
                    source_ref=f"line_item_{index}",
                )
            )
        return items

    def _parse_money(self, value: str) -> float:
        return float(value.replace("$", "").replace(",", ""))

    def _source_refs(self, text: str) -> dict[str, str]:
        refs = {}
        for field, pattern in {
            "vendor": r"Vendor:\s*.+",
            "invoice_id": r"Invoice (?:Number|ID):\s*[A-Za-z0-9\-]+",
            "total_amount": r"Total Amount:\s*[$]?[0-9,]+(?:\.[0-9]{1,2})?",
        }.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                refs[field] = match.group(0)
        return refs

    def _confidence(self, invoice: ExtractedInvoice, text: str) -> float:
        score = 0.2
        score += 0.2 if invoice.vendor and "vendor" in invoice.source_refs else 0
        score += 0.2 if invoice.invoice_id and "invoice" in text.casefold() else 0
        score += 0.2 if invoice.total_amount is not None else 0
        score += 0.2 if invoice.line_items else 0
        return round(min(score, 1.0), 2)

