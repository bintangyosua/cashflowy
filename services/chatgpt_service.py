import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
import openai
from config import settings

class ChatGPTService:
    """
    Service untuk mengelola ChatGPT/OpenAI
    
    Model yang digunakan: GPT-4o (model terbaru dengan vision capability)
    Note: GPT-5 belum tersedia secara publik dari OpenAI (September 2025)
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_name = "gpt-4o"  # Model terbaru yang available
    
    def get_current_timestamp(self) -> str:
        """Mendapatkan timestamp saat ini dalam timezone Jakarta"""
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        current_time = datetime.now(jakarta_tz)
        return current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def encode_image_to_base64(self, image_data: bytes) -> str:
        """Mengconvert image data ke base64 untuk OpenAI"""
        return base64.b64encode(image_data).decode('utf-8')
    
    def create_prompt(self) -> str:
        """Membuat prompt untuk ChatGPT"""
        return """
Saya akan memberikan Anda teks atau gambar yang berkaitan dengan transaksi keuangan. 
Tolong analisis dan ekstrak informasi berikut dalam format JSON yang VALID:

{
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
4. Items hanya diisi jika ada daftar pembelian yang jelas (seperti struk belanja)
5. Category harus spesifik (contoh: food, transport, entertainment, shopping, transfer, billings)
6. Type: "expense" untuk pengeluaran, "income" untuk pemasukan, "transfer" untuk transfer antar akun

Analisis data berikut:
"""
    
    async def process_financial_data(self, text_content: str = None, image_data: bytes = None) -> Dict[str, Any]:
        """Memproses teks atau gambar dengan ChatGPT"""
        try:
            prompt = self.create_prompt()
            messages = []
            
            if image_data and text_content:
                # Jika ada gambar dan teks
                image_base64 = self.encode_image_to_base64(image_data)
                prompt += f"\n\nTeks: {text_content}\nGambar: [Gambar terlampir]"
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
                
            elif image_data:
                # Hanya gambar
                image_base64 = self.encode_image_to_base64(image_data)
                prompt += "\n\nGambar: [Gambar terlampir]"
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
                
            elif text_content:
                # Hanya teks
                prompt += f"\n\nTeks: {text_content}"
                messages = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
            else:
                return {"error": "Tidak ada teks atau gambar yang diberikan"}
            
            # Panggil OpenAI API dengan model terbaru
            response = self.client.chat.completions.create(
                model=self.model_name,  # GPT-4o (model terbaru, GPT-5 belum tersedia)
                messages=messages,
                temperature=0.1,  # Low temperature for consistent financial data extraction
                max_tokens=1500,  # Increased for detailed transaction analysis
                top_p=0.9,       # Slightly focused responses
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Parse response JSON
            response_text = response.choices[0].message.content.strip()
            
            # Membersihkan response jika ada markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            financial_data = json.loads(response_text)
            
            # Timestamp akan ditambahkan di level service yang lebih tinggi
            # berdasarkan waktu pesan dari user
            
            return financial_data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response_text}")
            return {"error": f"Invalid JSON response from ChatGPT: {str(e)}"}
        except Exception as e:
            print(f"Error processing with ChatGPT: {e}")
            return {"error": str(e)}
