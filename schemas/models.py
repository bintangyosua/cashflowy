from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class TransactionItem(BaseModel):
    name: str
    quantity: Optional[int] = 1
    price: Optional[float] = 0

class Transaction(BaseModel):
    timestamp: str
    prompt_text: str
    summary_text: str
    amount: float
    type: str  # expense/income
    category: str
    payment_method: str  # cash/debit/credit/ewallet/transfer/other
    items: Optional[List[TransactionItem]] = []  # Detail items untuk nota belanja
    image_url: Optional[str] = None  # URL gambar yang diupload ke Google Drive