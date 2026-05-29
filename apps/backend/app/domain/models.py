from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class ImportBatchStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchStatus(StrEnum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    UNMATCHED = "unmatched"


@dataclass(frozen=True)
class FlowRecord:
    id: UUID
    source_platform_id: UUID
    import_batch_id: UUID
    flow_date: date
    raw_customer_name: str
    raw_product_name: str
    quantity: Decimal
    amount: Decimal | None
    match_status: MatchStatus
    created_at: datetime
