import google.generativeai as genai
from schemas.models import Transaction
from config import settings
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    async def parse_transaction(self, message, system_prompt=None, is_image=False):
        # Gunakan system_prompt jika disediakan, jika tidak gunakan prompt default
        if system_prompt:
            prompt = f"{system_prompt}\n\nUser input: {message}"
        else:
            prompt = f"""
            You are a finance extraction assistant for a Telegram bot. Users send SHORT TEXT or IMAGES (e.g., minimarket/gas station receipts). Your job is to convert any input into ONE structured record for a Google Sheet.

            # OUTPUT
            Return ONLY a single-line JSON object with these exact keys in this order:
            {{
              "timestamp": "<ISO 8601 in Asia/Jakarta, e.g., 2025-08-31T20:15:00+07:00>",
              "prompt_text": "<the raw user text or a compact OCR summary from the image>",
              "summary_text": "<clean human summary of the transaction in Indonesian>",
              "amount": <number, use dot as decimal separator>,
              "type": "expense" | "income",
              "category": "<one of: food|beverage|grocery|transport|fuel|bill|utility|health|personal|entertainment|education|gift|transfer|salary|other>"
            }}

            Rules:
            - Timezone: Asia/Jakarta. If the user text includes a specific date/time, use it; otherwise use "now" in Asia/Jakarta.
            - If input is an IMAGE: do OCR, prefer the largest "Total"/"Grand Total" number; ignore loyalty points, VAT lines unless they change total.
            - If input is TEXT: detect currency if present (Rp/IDR/ID), otherwise assume IDR. Normalize amount to number (strip separators).
            - Infer type:
              - Words like "beli", "bayar", "top up game", "isi bensin", "cash", "debet", or receipts → "expense"
              - Words like "gaji", "refund", "diterima", "transfer masuk", "jualan" → "income"
            - Infer category (best guess):
              - bensin, pertalite, shell, spbu → "fuel" (transport related)
              - gojek/grab/angkot/parkir/tol → "transport"
              - indomaret/alfamart/minimarket groceries → "grocery"
              - makan, restoran, warteg, warung, cafe → "food"
              - listrik, air, pulsa, paket data, wifi → "utility"
              - sekolah, kursus, buku → "education"
              - netflix, spotify, hiburan → "entertainment"
              - dokter, apotek, obat → "health"
              - hadiah, traktir → "gift"
              - gaji, salary, upah → "salary"
              - lain-lain → "other"
            - If amount is not explicitly given, try to compute from OCR/keywords; if still unknown, set amount: 0 and keep category/type guess.
            - Never include extra keys or text outside the JSON. No markdown.

            User input: {message}
            """
        
        try:
            if is_image and isinstance(message, bytes):
                # Jika input adalah gambar (bytes), kirim ke Gemini vision
                if not PIL_AVAILABLE:
                    raise ValueError("PIL library tidak tersedia. Install dengan: pip install Pillow")
                
                from io import BytesIO
                image = Image.open(BytesIO(message))
                response = self.model.generate_content([prompt, image])
            else:
                # Jika input adalah teks
                response = self.model.generate_content(prompt)
            
            # Bersihkan response dan ekstrak JSON
            json_str = self._clean_response(response.text)
            
            # Parse JSON dan return sebagai dict (bukan Transaction object)
            import json
            return json.loads(json_str)
            
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