import requests
import google.generativeai as genai
import sys

# Windows terminal encoding fix
sys.stdout.reconfigure(encoding='utf-8')

GEMINI_API_KEY = "AIzaSyAVWtGOdaHjtJCdjnWZbviXjPzs-SdYi7w"

def test_fixed_logic():
    print("--- YENI MANTIK TESTI ---")
    
    # 1. Model Secimi Testi
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Eski hatali mantik: "gemini-1.5-flash" in models
            # Yeni mantik:
            flash_model = next((m for m in models if 'gemini-1.5-flash' in m), None)
            selected = flash_model if flash_model else models[0]
            
            print(f"✅ Secilen Model: {selected}")
            
            # Test istegi
            m = genai.GenerativeModel(selected)
            resp = m.generate_content("Test")
            print("✅ Gemini Cevap Verdi!")
        except Exception as e:
            print(f"❌ Gemini Hatasi: {e}")

    # 2. Arama Mantigi (Ozet)
    print("\n--- Arama Testi ---")
    # Burada request mantigini tekrar kopyalamiyorum, zaten request calisiyordu.
    # Onemli olan Gemini'nin cevap verebilmesiydi cunku app.py Google bulsa bile Gemini ozeti icin API'ye gidiyor.
    # Eger API calismazsa "Ozet Hatasi" donuyor ve kitap gosterilmiyor.
    
if __name__ == "__main__":
    test_fixed_logic()
