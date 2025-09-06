import requests
from config import settings

class TelegramClient:
    """Class untuk menangani komunikasi dengan Telegram Bot API."""
    BASE_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    @staticmethod
    def send_message(chat_id: str, text: str):
        url = f"{TelegramClient.BASE_URL}/sendMessage"
        # Hilangkan parse_mode agar tidak error jika ada karakter spesial
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=payload)
        if not response.ok:
            raise Exception(response.text)
        return response.json()
