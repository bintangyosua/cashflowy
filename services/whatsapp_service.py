from fastapi import HTTPException
import requests
from schemas.models import Transaction
import config
import httpx

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
    async def send_whatsapp_message(to, message):
        url = f"https://graph.facebook.com/v17.0/{config.settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {config.settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        print('sampe sini cok hahaha')
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
        
        print(response.text)

    @staticmethod
    def validate_whatsapp_request(body: dict):
        if not body.get("Body"):
            raise HTTPException(status_code=400, detail="Pesan tidak valid")