import google.generativeai as genai
from schemas.models import Transaction
from config import settings

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    async def parse_transaction(self, message: str) -> Transaction:
        prompt = f"""
        Anda adalah asisten pencatatan keuangan. Ekstrak informasi transaksi dari pesan berikut dalam format JSON dengan field:
        - description (string)
        - amount (float)
        - category (string: Makanan, Transportasi, Belanja, dll)
        - type (string: 'expense', 'income', 'internal transfer')
        - payment_method. hanya pilihan ini saja (string: cash, bank, e-wallet)

        Contoh Output:
        {{
            "description": "nasi padang",
            "amount": 15000,
            "category": "Makanan",
            "type": "expense",
            "payment_method": "cash"
        }}

        Pesan: {message}

        Hanya kembalikan JSON tanpa penjelasan tambahan.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Bersihkan response dan ekstrak JSON
            json_str = self._clean_response(response.text)
            return Transaction.model_validate_json(json_str)
            
        except Exception as e:
            raise ValueError(f"Gagal memproses transaksi: {str(e)}")
    
    def weekly_recommendation(self, message):
        prompt = f"""
        Anda adalah asisten pencatatan keuangan. Buat rekomendasi keuangan untuk minggu ini. Berikut adalah data agregasinya:
        
        {message}
        """
        try:
            response = self.model.generate_content(prompt)
            
            # Bersihkan response dan ekstrak JSON
            return response.text
            
        except Exception as e:
            raise ValueError(f"Gagal memproses transaksi: {str(e)}")
        

    def _clean_response(self, text: str) -> str:
        """Bersihkan response Gemini untuk ekstrak JSON"""
        # Hapus markdown code block jika ada
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Cari substring JSON
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise ValueError("Format response tidak valid")
            
        return text[start:end]