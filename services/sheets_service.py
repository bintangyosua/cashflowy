import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import settings
from schemas.models import Transaction

class SheetsService:
    def __init__(self):
        scope = ["https://spreadsheets.google.com/feeds", 
                "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open(settings.google_sheet_name).sheet1
        
    async def add_transaction(self, transaction: Transaction, prompt: str, formatted_time, timestamp):
        # Get current time in WIB timezone
        
        row = [
            formatted_time,  # Use string instead of datetime object
            prompt,
            transaction.category,
            transaction.amount,
            transaction.payment_method,
            transaction.description,
            transaction.type,
        ]
        
        try:
            if not self.is_duplicate_entry(timestamp, prompt):
                self.sheet.append_row(row)
            else:
                print("Duplicate entry detected, skipping.")
        except Exception as e:
            raise ValueError(f"Failed to append row to sheet: {str(e)}")
    
    def is_duplicate_entry(self, timestamp, message):
        records = self.sheet.get_all_values()
        for row in records:
            if row[0] == timestamp and row[1] == message:
                return True
        return False