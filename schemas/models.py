from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class Transaction(BaseModel):
    timestamp: str
    prompt_text: str
    summary_text: str
    amount: float
    type: str  # expense/income
    category: str