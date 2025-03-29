import csv
from datetime import datetime, timedelta
from io import StringIO
from fastapi import HTTPException
import requests
from schemas.models import Transaction
from config import settings
from services.sheets_service import SheetsService

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
        raw_data = sheet.get_all_values()
        
        if not raw_data or len(raw_data) < 2:
            return "Sheet kosong atau tidak ada data yang cukup.", "Tidak ada data untuk disimpan."

        # Ambil header dan ubah ke list of dicts
        headers = raw_data[0]
        data = [dict(zip(headers, row)) for row in raw_data[1:] if any(row)]  # Hindari baris kosong
        
        # Konversi timestamp ke datetime dengan validasi
        for row in data:
            try:
                row["Timestamp"] = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                row["Timestamp"] = None  # Jika format salah, biarkan None

        # Filter transaksi seminggu terakhir
        one_week_ago = datetime.now() - timedelta(days=7)
        weekly_data = [row for row in data if row["Timestamp"] and row["Timestamp"] >= one_week_ago]
        
        if not weekly_data:
            return "Tidak ada transaksi dalam seminggu terakhir.", "Tidak ada data untuk disimpan."

        # Tambah kolom 'Tanggal'
        for row in weekly_data:
            row["Tanggal"] = row["Timestamp"].date()

        # Agregasi berdasarkan Tanggal, Kategori, Metode, dan Tipe
        aggregated = {}
        for row in weekly_data:
            key = (row["Tanggal"], row.get("Kategori", "Unknown"), row.get("Metode", "Unknown"), row.get("Tipe", "Unknown"))
            if key not in aggregated:
                aggregated[key] = {"Total Harga": 0, "Deskripsi": []}
            
            # FIX: Parsing harga dengan validasi ketat
            harga_str = row.get("Total Harga", "").replace("Rp", "").replace(",", "").replace(".", "").strip()  # Hapus Rp, koma, titik
            try:
                harga = int(harga_str) if harga_str.isdigit() else 0  # Cek apakah angka valid sebelum parse
            except ValueError:
                print(f"⚠️ Gagal parse harga: {row.get('Total Harga')} (set 0)")
                harga = 0  # Jika gagal parse, set 0

            aggregated[key]["Total Harga"] += harga
            aggregated[key]["Deskripsi"].append(row.get("Deskripsi", "No description"))

        # Buat CSV
        csv_output = StringIO()
        writer = csv.writer(csv_output)
        writer.writerow(["Tanggal", "Kategori", "Metode", "Tipe", "Total Harga", "Deskripsi"])
        for (tanggal, kategori, metode, tipe), values in aggregated.items():
            writer.writerow([tanggal, kategori, metode, tipe, values["Total Harga"], ", ".join(values["Deskripsi"])])
        csv_text = csv_output.getvalue()

        # Format laporan untuk WhatsApp
        formatted_report = []
        sorted_keys = sorted(aggregated.keys())
        for tanggal, kategori, metode, tipe in sorted_keys:
            total_harga = aggregated[(tanggal, kategori, metode, tipe)]["Total Harga"]
            deskripsi = ", ".join(aggregated[(tanggal, kategori, metode, tipe)]["Deskripsi"])
            emoji = "🛒" if "Belanja" in kategori else "🍽️" if "Makanan" in kategori else "💰" if "Transfer" in kategori else "💳"
            formatted_report.append(f"📅 *{tanggal}*\n{emoji} *{kategori}* - Rp{total_harga:,} ({metode})\n   {deskripsi}")

        whatsapp_text = "\n\n".join(formatted_report)

        return csv_text, whatsapp_text