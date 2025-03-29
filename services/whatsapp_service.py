from datetime import datetime, timedelta
from io import StringIO
from fastapi import HTTPException
import requests
from schemas.models import Transaction
from config import settings
from services.sheets_service import SheetsService

import pandas as pd

class WhatsAppClient:
    """Class untuk menangani komunikasi dengan WhatsApp API."""
    
    BASE_URL = "https://graph.facebook.com/v19.0"

    @staticmethod
    def send_request(endpoint: str, payload: dict):
        """Mengirim request ke WhatsApp API."""
        url = f"{WhatsAppClient.BASE_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.json())

        return response.json()

    @staticmethod
    def send_text_message(recipient_id: str, message: str):
        """Mengirim pesan teks ke WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": message},
        }
        return WhatsAppClient.send_request("messages", payload)

    @staticmethod
    def send_buttons(recipient_id: str, text: str, buttons: list):
        """Mengirim pesan dengan action buttons."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {
                    "buttons": [btn.to_dict() for btn in buttons],
                },
            },
        }
        return WhatsAppClient.send_request("messages", payload)


class WhatsAppMessageFormatter:
    """Class untuk menangani format pesan WhatsApp."""

    @staticmethod
    def format_transaction(transaction: Transaction, timestamp: str) -> str:
        """Memformat pesan konfirmasi transaksi."""
        return (
            f"✅ Transaksi tercatat!\n"
            f"Waktu: {timestamp}\n"
            f"Deskripsi: {transaction.description}\n"
            f"Jumlah: Rp{transaction.amount:,}\n"
            f"Kategori: {transaction.category}\n"
            f"Metode: {transaction.payment_method}\n"
            f"Tipe: {transaction.type}"
        )


class WhatsAppService:
    """Class utama yang mengatur pengiriman pesan WhatsApp."""

    @staticmethod
    def send_transaction_confirmation(recipient_id: str, transaction: Transaction, timestamp: str):
        """Mengirim pesan konfirmasi transaksi."""
        message = WhatsAppMessageFormatter.format_transaction(transaction, timestamp)
        return WhatsAppClient.send_text_message(recipient_id, message)

    @staticmethod
    def send_action_buttons(recipient_id: str, text: str, buttons: list):
        """Mengirim tombol aksi ke pengguna."""
        return WhatsAppClient.send_buttons(recipient_id, text, buttons)

    @staticmethod
    def get_recent_transactions(sheet, limit=5):
        """Mengambil transaksi terbaru dengan format rapi untuk WhatsApp"""
        transactions = sheet.get_all_values()
        
        if not transactions:
            return "No transactions found."

        formatted_transactions = [] 
        for row in transactions[-limit:][::-1]:
            timestamp, category, total, method, desc = row[0], row[2], row[3], row[4], row[5]
            emoji = "🛒" if "Belanja" in category else "🍽️" if "Makanan" in category else "💰" if "Transfer" in category else "💳"
            formatted_transactions.append(f"{timestamp}\n{emoji} *{category}* - {total} ({method})\n   {desc}")

        return f"📌 *Transaksi Terbaru:*\n\n" + "\n\n".join(formatted_transactions) + "\n"
    
    @staticmethod
    def get_weekly_report(sheet: SheetsService):
        df = SheetsService.sheet_to_dataframe(sheet)

        # Konversi Timestamp ke datetime
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%Y-%m-%d %H:%M:%S")

        # Filter transaksi seminggu terakhir
        one_week_ago = datetime.now() - timedelta(days=7)
        weekly_df = df[df["Timestamp"] >= one_week_ago]

        if weekly_df.empty:
            return "Tidak ada transaksi dalam seminggu terakhir.", "Tidak ada data untuk disimpan."

        # Tambah kolom 'Tanggal' biar lebih mudah dikelompokkan per hari
        weekly_df["Tanggal"] = weekly_df["Timestamp"].dt.date

        # Agregasi berdasarkan Tanggal, Kategori, Metode, dan Tipe
        agg_df = (weekly_df.groupby(["Tanggal", "Kategori", "Metode", "Tipe"])
                            .agg({"Total Harga": "sum", "Deskripsi": lambda x: ", ".join(x)})
                            .reset_index())

        # **Convert DataFrame ke CSV (tanpa header & index biar lebih clean)**
        csv_output = StringIO()
        agg_df.to_csv(csv_output, index=False)
        csv_text = csv_output.getvalue()

        # **Format laporan untuk WhatsApp**
        formatted_report = []
        for tanggal, daily_df in agg_df.groupby("Tanggal"):
            formatted_report.append(f"📅 *{tanggal}*")
            for _, row in daily_df.iterrows():
                emoji = "🛒" if "Belanja" in row["Kategori"] else "🍽️" if "Makanan" in row["Kategori"] else "💰" if "Transfer" in row["Kategori"] else "💳"
                formatted_report.append(f"{emoji} *{row['Kategori']}* - Rp{row['Total Harga']} ({row['Metode']})\n   {row['Deskripsi']}")

        whatsapp_text = "\n\n".join(formatted_report)

        return csv_text, whatsapp_text