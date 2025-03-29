from fastapi import HTTPException
import requests
from schemas.models import Transaction
from config import settings

class WhatsAppService:
    @staticmethod
    def format_response(transaction: Transaction, timestamp) -> str:
        return (
            f"✅ Transaksi tercatat!\n"
            f"Waktu: {timestamp}\n"
            f"Deskripsi: {transaction.description}\n"
            f"Jumlah: Rp{transaction.amount:,}\n"
            f"Kategori: {transaction.category}\n"
            f"Metode: {transaction.payment_method}\n"
            f"Tipe: {transaction.type}"
        )
    
    @staticmethod
    def async_send_message(phone_number_id: str, message: str):
        response = requests.post(
            f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": phone_number_id,  # Nomor yang sudah di-allowlist
                "type": "text",
                "text": {"body": message}
            }
        )
        
    @staticmethod
    def validate_whatsapp_request(body: dict):
        if not body.get("Body"):
            raise HTTPException(status_code=400, detail="Pesan tidak valid")