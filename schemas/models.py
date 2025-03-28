from typing import Optional
from pydantic import BaseModel

class Transaction(BaseModel):
    description: str
    amount: float
    category: str = "Lainnya"
    type: str  # expense/income/transfer
    payment_method: str = "cash"