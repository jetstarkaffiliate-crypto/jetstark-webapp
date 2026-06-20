from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class PayoutRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    note: Optional[str] = None
    bank_name: str = Field(min_length=1, max_length=255)
    account_number: str = Field(min_length=10, max_length=20)
    account_name: str = Field(min_length=1, max_length=255)


class PayoutResponse(BaseModel):
    id: str
    amount: Decimal
    fee: Decimal
    status: str
    payment_method: str
    bank_name: Optional[str]
    account_number: Optional[str]
    account_name: Optional[str]
    transaction_reference: Optional[str]
    note: Optional[str]
    requested_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PayoutBalanceResponse(BaseModel):
    available_balance: Decimal
    pending_balance: Decimal
    total_earned: Decimal
    total_paid_out: Decimal
