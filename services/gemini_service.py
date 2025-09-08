import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
import google.generativeai as genai
from config import settings

class GeminiService:
    """Service untuk mengelola Gemini AI"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def get_current_timestamp(self) -> str:
        """Mendapatkan timestamp saat ini dalam timezone Jakarta"""
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        current_time = datetime.now(jakarta_tz)
        return current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def encode_image_to_base64(self, image_data: bytes) -> str:
        """Mengconvert image data ke base64 untuk Gemini AI"""
        return base64.b64encode(image_data).decode('utf-8')
    
    def create_prompt(self) -> str:
        """Membuat prompt untuk Gemini AI"""
        return """
Saya akan memberikan Anda teks atau gambar yang berkaitan dengan transaksi keuangan. 
Tolong analisis dan ekstrak informasi berikut dalam format JSON yang VALID:

{
  "timestamp": "YYYY-MM-DD HH:MM:SS (jika ada waktu di gambar, gunakan itu. Jika tidak, gunakan waktu saat ini)",
  "prompt_text": "teks yang diberikan atau deskripsi gambar",
  "category": "kategori transaksi (entertainment, transfer, billings, food, shopping, transport, dll)",
  "amount": "total jumlah uang (angka saja, tanpa mata uang)",
  "payment_method": "metode pembayaran (cash, dana, gopay, shopeepay, ovo, bca, bni, dll)",
  "type": "jenis transaksi (income/expense/transfer)",
  "summary": "ringkasan singkat transaksi",
  "items": [
    {
      "name": "nama item",
      "quantity": "jumlah item (angka)",
      "price": "harga per item (angka)"
    }
  ]
}

Aturan penting:
1. Berikan HANYA JSON yang valid, tanpa penjelasan tambahan
2. Untuk amount, gunakan angka saja (contoh: 50000, bukan "Rp 50.000")
3. Jika tidak ada informasi spesifik, gunakan nilai default yang masuk akal
4. Untuk timestamp, jika ada tanggal/waktu di gambar, gunakan itu. Jika tidak, biarkan kosong
5. Items hanya diisi jika ada daftar pembelian yang jelas (seperti struk belanja)
6. Category harus spesifik (contoh: food, transport, entertainment, shopping, transfer, billings)
7. Type: "expense" untuk pengeluaran, "income" untuk pemasukan, "transfer" untuk transfer antar akun

Analisis data berikut:
"""
    
    async def process_financial_data(self, text_content: str = None, image_data: bytes = None) -> Dict[str, Any]:
        """Memproses teks atau gambar dengan Gemini AI"""
        try:
            prompt = self.create_prompt()
            
            if image_data and text_content:
                # Jika ada gambar dan teks
                image_base64 = self.encode_image_to_base64(image_data)
                prompt += f"\n\nTeks: {text_content}\nGambar: [Gambar terlampir]"
                
                response = self.model.generate_content([
                    prompt,
                    {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }
                ])
                
            elif image_data:
                # Hanya gambar
                image_base64 = self.encode_image_to_base64(image_data)
                prompt += "\n\nGambar: [Gambar terlampir]"
                
                response = self.model.generate_content([
                    prompt,
                    {
                        "mime_type": "image/jpeg", 
                        "data": image_base64
                    }
                ])
                
            elif text_content:
                # Hanya teks
                prompt += f"\n\nTeks: {text_content}"
                response = self.model.generate_content(prompt)
                
            else:
                return {"error": "Tidak ada teks atau gambar yang diberikan"}
            
            # Parse response JSON
            response_text = response.text.strip()
            
            # Membersihkan response jika ada markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            financial_data = json.loads(response_text)
            
            # Jika timestamp kosong, gunakan waktu saat ini
            if not financial_data.get("timestamp"):
                financial_data["timestamp"] = self.get_current_timestamp()

            return financial_data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response_text}")
            return {"error": f"Invalid JSON response from Gemini: {str(e)}"}
        except Exception as e:
            print(f"Error processing with Gemini: {e}")
            return {"error": str(e)}
