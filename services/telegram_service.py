import requests
import io
from typing import Optional, Dict, Any
from PIL import Image
from config import settings

class TelegramService:
    """Service untuk mengelola Telegram Bot API"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> Optional[Dict[str, Any]]:
        """Mengirim pesan ke Telegram menggunakan Bot API"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def get_file_url(self, file_id: str) -> Optional[str]:
        """Mendapatkan URL file dari Telegram"""
        url = f"{self.base_url}/getFile"
        payload = {"file_id": file_id}
        
        try:
            response = requests.post(url, json=payload)
            result = response.json()
            
            if result.get("ok"):
                file_path = result["result"]["file_path"]
                file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                return file_url
            return None
        except Exception as e:
            print(f"Error getting file URL: {e}")
            return None
    
    def download_image(self, file_url: str) -> Optional[bytes]:
        """Mengunduh gambar dari URL"""
        try:
            response = requests.get(file_url)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def process_image(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """Memproses gambar dan mendapatkan informasi dasar"""
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            format_img = image.format
            mode = image.mode
            
            return {
                "width": width,
                "height": height,
                "format": format_img,
                "mode": mode,
                "size_bytes": len(image_data)
            }
        except Exception as e:
            print(f"Error processing image: {e}")
            return None
    
    def get_webhook_info(self) -> Optional[Dict[str, Any]]:
        """Mendapatkan informasi webhook yang sudah diset"""
        url = f"{self.base_url}/getWebhookInfo"
        
        try:
            response = requests.get(url)
            return response.json()
        except Exception as e:
            print(f"Error getting webhook info: {e}")
            return {"error": str(e)}
    
    def set_webhook(self, webhook_url: str) -> Optional[Dict[str, Any]]:
        """Mengatur webhook Telegram"""
        url = f"{self.base_url}/setWebhook"
        payload = {"url": webhook_url}
        
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            print(f"Error setting webhook: {e}")
            return {"error": str(e)}
    
    def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """Mendapatkan informasi bot"""
        url = f"{self.base_url}/getMe"
        
        try:
            response = requests.get(url)
            return response.json()
        except Exception as e:
            print(f"Error getting bot info: {e}")
            return {"error": str(e)}
