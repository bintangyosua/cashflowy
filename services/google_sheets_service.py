import json
from typing import Dict, Any
import gspread
from gspread.exceptions import SpreadsheetNotFound
from google.oauth2.service_account import Credentials
from config import settings

class GoogleSheetsService:
    """Service untuk mengelola Google Sheets"""
    
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.service_account_file = 'credentials.json'
        self._client = None
    
    def get_client(self):
        """Membuat koneksi ke Google Sheets"""
        if not self._client:
            credentials = Credentials.from_service_account_file(
                self.service_account_file, scopes=self.scopes)
            self._client = gspread.authorize(credentials)
        return self._client
    
    def create_spreadsheet_if_not_exists(self, client):
        """Buat spreadsheet baru jika belum ada"""
        try:
            spreadsheet = client.open(settings.google_sheet_name)
            print(f"✅ Spreadsheet '{settings.google_sheet_name}' ditemukan")
            return spreadsheet
        except SpreadsheetNotFound:
            print(f"❌ Spreadsheet '{settings.google_sheet_name}' tidak ditemukan")
            print("🔄 Membuat spreadsheet baru...")
            
            # Buat spreadsheet baru
            spreadsheet = client.create(settings.google_sheet_name)
            
            # Share dengan anyone (optional, bisa dihapus jika tidak perlu)
            try:
                spreadsheet.share(None, perm_type='anyone', role='writer')
                print(f"🔗 Spreadsheet dibagikan untuk akses publik")
            except Exception as share_error:
                print(f"⚠️ Warning: Tidak bisa share spreadsheet: {share_error}")
            
            print(f"✅ Spreadsheet '{settings.google_sheet_name}' berhasil dibuat")
            return spreadsheet
    
    def test_connection(self) -> Dict[str, Any]:
        """Test koneksi ke Google Sheets"""
        try:
            client = self.get_client()
            
            # Test dengan membuat spreadsheet temporary
            test_name = f"Test Connection - {settings.google_sheet_name}"
            
            try:
                # Coba akses spreadsheet utama
                spreadsheet = client.open(settings.google_sheet_name)
                return {
                    "status": "success",
                    "message": f"Berhasil mengakses spreadsheet '{settings.google_sheet_name}'",
                    "spreadsheet_id": spreadsheet.id,
                    "url": spreadsheet.url
                }
            except SpreadsheetNotFound:
                return {
                    "status": "not_found",
                    "message": f"Spreadsheet '{settings.google_sheet_name}' tidak ditemukan, akan dibuat saat pertama kali menyimpan data"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing connection: {str(e)}"
            }
    
    def save_financial_data(self, financial_data: Dict[str, Any]) -> bool:
        """Menyimpan data keuangan ke Google Sheets"""
        try:
            client = self.get_client()
            
            # Buat atau buka spreadsheet
            spreadsheet = self.create_spreadsheet_if_not_exists(client)
            worksheet = spreadsheet.sheet1  # Menggunakan sheet pertama
            
            # Siapkan data untuk disimpan sesuai urutan kolom JSON
            row_data = [
                financial_data.get('timestamp', ''),
                financial_data.get('prompt_text', ''),
                financial_data.get('category', ''),
                financial_data.get('amount', 0),
                financial_data.get('payment_method', ''),
                financial_data.get('type', ''),
                financial_data.get('summary', ''),
                json.dumps(financial_data.get('items', []), ensure_ascii=False)  # Items sebagai JSON string
            ]
            
            # Cek apakah ada header, jika tidak ada maka buat header
            try:
                existing_headers = worksheet.row_values(1)
                if not existing_headers:
                    raise Exception("No headers found")
                print(f"✅ Headers ditemukan: {existing_headers}")
            except:
                print("🔄 Menambahkan headers...")
                headers = [
                    'timestamp',
                    'prompt_text', 
                    'category',
                    'amount',
                    'payment_method',
                    'type',
                    'summary',
                    'items'
                ]
                worksheet.append_row(headers)
                print(f"✅ Headers berhasil ditambahkan: {headers}")
            
            # Tambahkan data baru
            worksheet.append_row(row_data)
            
            print(f"✅ Data berhasil disimpan ke Google Sheets: {settings.google_sheet_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error menyimpan ke Google Sheets: {e}")
            return False
