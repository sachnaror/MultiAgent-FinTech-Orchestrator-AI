from dataclasses import dataclass, field


@dataclass
class DuplicateStore:
    seen: set[tuple[str, str]] = field(default_factory=set)

    def exists(self, vendor: str, invoice_id: str) -> bool:
        return (vendor.casefold(), invoice_id.casefold()) in self.seen

    def mark_seen(self, vendor: str, invoice_id: str) -> None:
        self.seen.add((vendor.casefold(), invoice_id.casefold()))


duplicate_store = DuplicateStore()

