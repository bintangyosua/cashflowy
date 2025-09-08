from typing import Dict, Any, Optional
from .gemini_service import GeminiService
from .google_sheets_service import GoogleSheetsService
from .telegram_service import TelegramService
from .message_formatter_service import MessageFormatterService

class FinanceBotService:
    """Service utama yang menggabungkan semua service"""
    
    def __init__(self):
        self.gemini = GeminiService()
        self.sheets = GoogleSheetsService()
        self.telegram = TelegramService()
        self.formatter = MessageFormatterService()
    
    async def process_text_message(self, chat_id: int, user_name: str, text_content: str):
        """Memproses pesan teks"""
        # Kirim pesan sedang memproses
        self.telegram.send_message(chat_id, self.formatter.format_processing_message())
        
        # Proses dengan Gemini AI
        financial_data = await self.gemini.process_financial_data(text_content=text_content)
        
        if "error" in financial_data:
            # Kirim pesan error
            error_msg = self.formatter.format_error_message(financial_data['error'])
            self.telegram.send_message(chat_id, error_msg)
        else:
            # Simpan ke Google Sheets
            sheet_saved = self.sheets.save_financial_data(financial_data)
            
            # Format dan kirim pesan hasil analisis
            analysis_msg = self.formatter.format_financial_analysis(
                financial_data, user_name, sheet_saved, is_image=False
            )
            self.telegram.send_message(chat_id, analysis_msg)
            
            # Kirim JSON response
            # json_msg = self.formatter.format_json_response(financial_data)
            # self.telegram.send_message(chat_id, json_msg)
    
    async def process_image_message(self, chat_id: int, user_name: str, file_id: str, caption: str = ""):
        """Memproses pesan gambar"""
        # Kirim pesan sedang memproses
        self.telegram.send_message(chat_id, self.formatter.format_processing_message(is_image=True))
        
        # Mendapatkan URL file dan mengunduh gambar
        file_url = self.telegram.get_file_url(file_id)
        
        if not file_url:
            error_msg = f"❌ Gagal mendapatkan URL gambar dari {user_name}"
            self.telegram.send_message(chat_id, error_msg)
            return
        
        image_data = self.telegram.download_image(file_url)
        
        if not image_data:
            error_msg = f"❌ Gagal mengunduh gambar dari {user_name}"
            self.telegram.send_message(chat_id, error_msg)
            return
        
        # Proses dengan Gemini AI
        financial_data = await self.gemini.process_financial_data(
            text_content=caption if caption else None,
            image_data=image_data
        )
        
        if "error" in financial_data:
            # Kirim pesan error
            error_msg = self.formatter.format_error_message(financial_data['error'])
            self.telegram.send_message(chat_id, error_msg)
        else:
            # Simpan ke Google Sheets
            sheet_saved = self.sheets.save_financial_data(financial_data)
            
            # Format dan kirim pesan hasil analisis
            analysis_msg = self.formatter.format_financial_analysis(
                financial_data, user_name, sheet_saved, is_image=True, caption=caption
            )
            self.telegram.send_message(chat_id, analysis_msg)
            
            # Kirim JSON response
            # json_msg = self.formatter.format_json_response(financial_data)
            # self.telegram.send_message(chat_id, json_msg)
    
    def process_unsupported_message(self, chat_id: int, user_name: str):
        """Memproses pesan yang tidak didukung"""
        unsupported_msg = self.formatter.format_unsupported_message(user_name)
        self.telegram.send_message(chat_id, unsupported_msg)
