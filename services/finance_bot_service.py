from typing import Dict, Any, Optional
from datetime import datetime
import pytz
from .gemini_service import GeminiService
from .chatgpt_service import ChatGPTService
from .google_sheets_service import GoogleSheetsService
from .telegram_service import TelegramService
from .message_formatter_service import MessageFormatterService
from config import settings

class FinanceBotService:
    """Service utama yang menggabungkan semua service"""
    
    def __init__(self):
        self.gemini = GeminiService()
        self.chatgpt = ChatGPTService()
        self.sheets = GoogleSheetsService()
        self.telegram = TelegramService()
        self.formatter = MessageFormatterService()
    
    def get_ai_service(self):
        """Mendapatkan AI service yang aktif berdasarkan konfigurasi"""
        if settings.ai_provider.lower() == "gemini":
            return self.gemini
        else:
            return self.chatgpt
    
    def get_timestamp_from_unix(self, unix_timestamp: int) -> str:
        """Konversi Unix timestamp ke format string dengan timezone Jakarta"""
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        dt = datetime.fromtimestamp(unix_timestamp, tz=jakarta_tz)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    async def process_text_message(self, chat_id: int, user_name: str, text_content: str, message_timestamp: int):
        """Memproses pesan teks"""
        # Kirim pesan sedang memproses
        self.telegram.send_message(chat_id, self.formatter.format_processing_message())
        
        # Proses dengan AI service yang aktif
        ai_service = self.get_ai_service()
        financial_data = await ai_service.process_financial_data(text_content=text_content)
        
        if "error" in financial_data:
            # Kirim pesan error
            error_msg = self.formatter.format_error_message(financial_data['error'])
            self.telegram.send_message(chat_id, error_msg)
        else:
            # Tambahkan timestamp berdasarkan waktu pesan user
            financial_data["timestamp"] = self.get_timestamp_from_unix(message_timestamp)
            
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
    
    async def process_image_message(self, chat_id: int, user_name: str, file_id: str, message_timestamp: int, caption: str = ""):
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
        
        # Proses dengan AI service yang aktif
        ai_service = self.get_ai_service()
        financial_data = await ai_service.process_financial_data(
            text_content=caption if caption else None,
            image_data=image_data
        )
        
        if "error" in financial_data:
            # Kirim pesan error
            error_msg = self.formatter.format_error_message(financial_data['error'])
            self.telegram.send_message(chat_id, error_msg)
        else:
            # Tambahkan timestamp berdasarkan waktu pesan user
            financial_data["timestamp"] = self.get_timestamp_from_unix(message_timestamp)
            
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
