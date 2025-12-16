import streamlit as st
import numpy as np
from PIL import Image
import requests
import google.generativeai as genai
import time

# ==============================================================================
# 🔑 API ANAHTARI BÖLÜMÜ
# ==============================================================================
GEMINI_API_KEY = "AIzaSyADWLhw8kH0iOTRDMRjbS8af6g1ZgxOjJM"  # <-- API Anahtarını buraya yapıştır (Tırnakların içine)

# --- GEMINI BAĞLANTISI ---
gemini_aktif = False
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_aktif = True
except:
    pass

st.set_page_config(page_title="Sınırsız Büyülü Kütüphane", page_icon="🧙‍♂️", layout="wide")

# --- SESSION STATE ---
if 'favoriler' not in st.session_state: st.session_state['favoriler'] = []
if 'son_kitap' not in st.session_state: st.session_state['son_kitap'] = None
if 'chat_history' not in st.session_state: st.session_state['chat_history'] = []
if 'muzik_onerileri' not in st.session_state: st.session_state['muzik_onerileri'] = []
if 'vibe_onerileri' not in st.session_state: st.session_state['vibe_onerileri'] = None

# --- CSS (Tasarım) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400;700&display=swap');
    .stApp { background: linear-gradient(135deg, #1a0b2e 0%, #2d1b4e 50%, #0f0c29 100%); color: #e0d4fc; font-family: 'Lato', sans-serif; }
    h1, h2, h3 { font-family: 'Cinzel', serif; color: #ffd700 !important; text-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
    .stButton>button { background: linear-gradient(45deg, #4b0082, #800080); color: #ffd700; border: 2px solid #ffd700; border-radius: 15px; height: 50px; font-family: 'Cinzel', serif; font-weight: bold; transition: all 0.3s ease; box-shadow: 0 0 15px rgba(128, 0, 128, 0.5); }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 0 25px rgba(255, 215, 0, 0.8); background: linear-gradient(45deg, #800080, #4b0082); }
    .stTextInput>div>div>input { background-color: rgba(255, 255, 255, 0.1); color: #ffd700; border: 1px solid #4b0082; border-radius: 10px; }
    .stChatMessage { background-color: rgba(0, 0, 0, 0.3); border-radius: 10px; border: 1px solid #4b0082; }
    .vibe-box { background-color: rgba(255, 215, 0, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ffd700; margin-top: 10px;}
    .kitap-ozet { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border: 1px solid #4b0082; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- MODEL ---
def en_iyi_modeli_bul():
    if not gemini_aktif: return None
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return "gemini-1.5-flash" if "gemini-1.5-flash" in models else models[0]
    except: return None

AKTIF_MODEL = en_iyi_modeli_bul()

# ==========================================================
# 🛑 KATMAN 1: MANUEL KİTAP KASASI (DEV ARŞİV)
# ==========================================================
MANUEL_KITAPLAR = {
    "bab-i esrar": {
        "baslik": "Bab-ı Esrar", "yazar": "Ahmet Ümit",
        "ozet": """🎭 **Karakterler:** Karen Kimya Greenwood, Şems-i Tebrizi, Mennan, Poyraz Bey, Ziya Bey.
📖 **Hikaye:** Londra'dan gelen Karen Kimya, Konya'daki Yakut Otel yangınını araştırırken kendini mistik bir sırrın ortasında bulur. Esrarengiz bir dervişin verdiği yüzük onu babasının geçmişine ve Şems-i Tebrizi cinayetine götürür.
🌟 **Tema:** Tasavvuf, gizem ve içsel yolculuk.""",
        "durum": "✅ Özel Hafıza"
    },
    "afacanlar cetesi": {
        "baslik": "Afacanlar Çetesi", "yazar": "İpek Ongun",
        "ozet": """🎭 **Karakterler:** Asena, Sinan, Defne, Zeynep, Berk, Ahbap.
📖 **Hikaye:** Okullarına kütüphane kazandırmak isteyen mahalle grubunun maceraları.
🌟 **Tema:** Dostluk ve dayanışma.""",
        "durum": "✅ Özel Hafıza"
    }
}

# --- YARDIMCI FONKSİYONLAR ---

def text_normalize(text):
    if not text: return ""
    text = text.lower()
    mapping = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', 'İ': 'i'}
    for k, v in mapping.items(): text = text.replace(k, v)
    return text

def gemini_ile_goruntu_oku(image):
    if not AKTIF_MODEL: return "HATA", None
    try:
        model = genai.GenerativeModel(AKTIF_MODEL)
        prompt = "Bu kitap kapağındaki Kitap Adı ve Yazarını yaz. Sadece 'Kitap Adı - Yazar' formatında yaz."
        response = model.generate_content([prompt, image])
        text = response.text.strip()
        if "|" in text:
            tur, icerik = text.split("|", 1)
            return tur.strip(), icerik.strip()
        return "KITAP", text 
    except Exception as e:
        return "HATA", str(e)

def benzer_kitaplar_bul(kitap_adi, yazar_adi=""):
    if not AKTIF_MODEL: return []
    try:
        model = genai.GenerativeModel(AKTIF_MODEL)
        prompt = f'"{kitap_adi}" ({yazar_adi}) kitabını sevenler için 5 benzer kitap öner. Sadece liste halinde yaz.'
        response = model.generate_content(prompt)
        return [s.strip().replace("*", "") for s in response.text.split('\n') if '-' in s][:5]
    except: return []

# 🔥 YENİLENMİŞ MÜZİK ÖNERİSİ
def muzik_onerileri_bul(kitap_adi, yazar_adi="", kitap_ozet=""):
    if not AKTIF_MODEL: return []
    try:
        model = genai.GenerativeModel(AKTIF_MODEL)
        prompt = f"""
        "{kitap_adi}" ({yazar_adi}) kitabının atmosferine ve duygusuna tam uyan 3 tane GERÇEK şarkı öner.
        
        KURALLAR:
        1. Sadece şarkı adı ve sanatçı ver.
        2. Tür adı verme (Örn: "Rock" deme, "Metallica - One" de).
        3. Format: "Sanatçı - Şarkı Adı"
        """
        response = model.generate_content(prompt)
        # Gelen cevabı satır satır böl ve temizle
        sarkilar = [s.strip().replace("*", "").replace("- ", "") for s in response.text.split('\n') if len(s) > 5]
        return sarkilar[:3] # İlk 3 şarkıyı al
    except: 
        return ["Klasik Müzik - Kitap Okuma Listesi"]

# 🔥 RUH HALİ (VIBE) ÖNERİSİ
def gemini_ruh_hali_onerisi(vibe):
    if not AKTIF_MODEL: return "⚠️ Hata: API Anahtarı eksik."
    try:
        model = genai.GenerativeModel(AKTIF_MODEL)
        prompt = f"""
        Kullanıcının Ruh Hali: {vibe}
        GÖREV: Bu ruh haline tam olarak uyan 3 kitap öner.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Hata: {str(e)}"

# --- GEMINI GENEL ÖZET (GÜÇLENDİRİLMİŞ) ---
def gemini_ile_ozetle(kitap_adi, yazar_adi="", google_ozeti=""):
    if not AKTIF_MODEL: 
        # API yoksa Google özetini döndür
        if google_ozeti and len(google_ozeti) > 50:
            return google_ozeti, "⚠️ API Yok - Google Özeti"
        return "Özet oluşturulamadı. Lütfen API anahtarı ekleyin.", "⚠️ API Gerekli"
    
    try:
        model = genai.GenerativeModel(AKTIF_MODEL)
        
        google_temiz = ""
        if google_ozeti and len(google_ozeti) > 50:
            spam = ['sex', 'porn', 'erotik', 'xxx', 'casino', 'seo', 'taktikleri', 'teknikleri']
            if not any(k in google_ozeti.lower() for k in spam):
                google_temiz = google_ozeti

        prompt = f"""
        Sen edebiyat profesörüsün.
        Kitap: "{kitap_adi}" {f'- {yazar_adi}' if yazar_adi else ''}
        {f'Referans Özet: {google_temiz}' if google_temiz else ''}
        
        GÖREV: Bu kitabı Türkçe olarak, OKUYUCUYU DOYURACAK ŞEKİLDE UZUN VE DETAYLI anlat (en az 400 kelime).
        FORMAT: 
        🎭 **Karakterler:** Ana karakterleri ve özelliklerini yaz
        📖 **Hikaye:** Konuyu detaylı anlat
        🌟 **Tema:** Ana temaları belirt
        """
        response = model.generate_content(prompt)
        return response.text.strip(), "✅ Büyücü Hafızası"
    except Exception as e:
        # Hata durumunda Google özetini döndür
        if google_ozeti and len(google_ozeti) > 50:
            return google_ozeti, f"⚠️ API Hatası - Google Özeti"
        return f"Özet oluşturulamadı. Hata: {str(e)}", "❌ Hata"

# --- ASİSTAN ---
def gemini_sohbet(soru, kitap_bilgisi):
    if not AKTIF_MODEL: return "Büyü zayıf... API anahtarı gerekli."
    try:
        model = genai.GenerativeModel(AKTIF_MODEL)
        prompt = f"Kitap: {kitap_bilgisi['baslik']} - {kitap_bilgisi['yazar']}. Soru: {soru}. Cevapla:"
        return model.generate_content(prompt).text.strip()
    except: return "Hata oluştu."

# --- ARAMA MOTORU ---
def search_book_universal(query):
    query_clean = text_normalize(query)
    
    # 1. MANUEL VERİ KONTROLÜ
    for key, data in MANUEL_KITAPLAR.items():
        if key in query_clean or query_clean in key:
            return {
                "baslik": data["baslik"], "yazar": data["yazar"], "ozet": data["ozet"],
                "durum": data["durum"], "resim": None
            }

    # 2. GOOGLE BOOKS
    try:
        r = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1", timeout=5)
        if r.status_code == 200 and "items" in r.json():
            info = r.json()["items"][0]["volumeInfo"]
            baslik = info.get("title", query)
            yazar = ", ".join(info.get("authors", ["Bilinmiyor"]))
            resim = info.get("imageLinks", {}).get("thumbnail")
            if resim: resim = resim.replace("zoom=1", "zoom=2")
            
            google_ozet = info.get("description", "")
            
            # Gemini ile özetle (BURASI KRİTİK)
            ozet, durum = gemini_ile_ozetle(baslik, yazar, google_ozet)
            
            return {"baslik": baslik, "yazar": yazar, "ozet": ozet, "durum": durum, "resim": resim}
    except Exception as e:
        st.sidebar.warning(f"⚠️ Google Kitaplar hatası: {str(e)[:100]}")

    # 3. GEMINI SON ŞANS (Google bulamazsa)
    if gemini_aktif:
        ozet, durum = gemini_ile_ozetle(query)
        if ozet and "oluşturulamadı" not in ozet:
            return {"baslik": query.title(), "yazar": "Bilinmiyor", "ozet": ozet, "durum": durum, "resim": None}

    return None

# --- ARAYÜZ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3330/3330314.png", width=100)
    st.title("⚙️ Ayarlar")
    if AKTIF_MODEL: st.success("✨ Büyü Aktif")
    else: st.error("🌑 API Key Girilmedi")
    st.markdown(f"**📚 Favoriler:** {len(st.session_state['favoriler'])}")
    
    st.divider()
    st.subheader("🧠 Ruh Hali (Vibe) Seç")
    selected_vibe = st.selectbox("Bugün nasıl hissediyorsun?", 
        ["Seçiniz...", "Hüzünlü & Melankolik", "Gizemli & Meraklı", "Korkmak İstiyorum", "İlham Verici", "Aşık & Romantik"])
    
    if selected_vibe != "Seçiniz...":
        if st.button("🔮 Bana Kitap Öner"):
            with st.spinner("Ruhuna uygun kitaplar aranıyor..."):
                st.session_state['vibe_onerileri'] = gemini_ruh_hali_onerisi(selected_vibe)

st.title("🧙‍♂️ Sınırsız Büyülü Kütüphane")
st.markdown("*İster 'Bab-ı Esrar' de, ister 'Suç ve Ceza'... Büyücü hepsini bilir!*")

# VIBE SONUÇLARI
if st.session_state['vibe_onerileri']:
    if "Hata" in st.session_state['vibe_onerileri']:
        st.error(st.session_state['vibe_onerileri'])
    else:
        st.markdown(f"<div class='vibe-box'><h3>✨ {selected_vibe} Modu İçin Öneriler:</h3>{st.session_state['vibe_onerileri']}</div>", unsafe_allow_html=True)
    if st.button("Temizle"): 
        st.session_state['vibe_onerileri'] = None
        st.rerun()

tab1, tab2, tab3 = st.tabs(["✍️ İsimle Çağır", "📸 Gözle Tara", "⭐ Sandık"])

# TAB 1: ARAMA
with tab1:
    with st.form("arama_form"):
        col1, col2 = st.columns([4, 1])
        query = col1.text_input("Kitap Adı:", placeholder="Örn: Bab-ı Esrar, Harry Potter")
        btn = col2.form_submit_button("🔮 Keşfet")
    
    if btn and query:
        with st.spinner("Büyücü küresine bakılıyor..."):
            sonuc = search_book_universal(query)
            if sonuc:
                st.session_state['son_kitap'] = {**sonuc, "benzer_kitaplar": []}
                st.session_state['chat_history'] = [] 
                st.session_state['muzik_onerileri'] = []
                st.rerun()
            else:
                st.error("❌ Kitap Bulunamadı. Lütfen farklı bir isim deneyin.")

# TAB 2: KAMERA
with tab2:
    img_file = st.file_uploader("Kapak Resmi Yükle", type=['jpg','png','jpeg'])
    if img_file:
        img = Image.open(img_file)
        st.image(img, width=200)
        if st.button("📸 Tara ve Bul"):
            with st.spinner("Görsel okunuyor..."):
                tur, icerik = gemini_ile_goruntu_oku(img)
                if tur == "KITAP":
                    st.info(f"Algılanan: {icerik}")
                    sonuc = search_book_universal(icerik)
                    if sonuc:
                        st.session_state['son_kitap'] = {**sonuc, "benzer_kitaplar": []}
                        st.session_state['chat_history'] = []
                        st.session_state['muzik_onerileri'] = []
                        st.rerun()
                    else: st.warning(f"⚠️ Kitap bulunamadı")
                else: st.error("Görsel okunamadı")

# SONUÇ EKRANI
if st.session_state['son_kitap']:
    st.divider()
    k = st.session_state['son_kitap']
    
    c1, c2, c3 = st.columns([1, 2, 2])
    
    with c1:
        if k.get('resim'): 
            st.image(k['resim'], use_container_width=True)
        else: 
            st.info("🖼️ Kapak Resmi Yok")
        st.caption(k.get('durum', ''))
        
        # 🔥 YENİLENMİŞ MÜZİK BUTONU
        if st.button("🎵 Bu Kitaba Uygun Şarkılar Öner", use_container_width=True):
            with st.spinner("Notalar aranıyor..."):
                sarkilar = muzik_onerileri_bul(k['baslik'], k['yazar'], k['ozet'])
                st.session_state['muzik_onerileri'] = sarkilar
        
        # Şarkı Listesini Göster
        if st.session_state['muzik_onerileri']:
            st.success("🎧 **Senin İçin Seçtiklerim:**")
            for sarki in st.session_state['muzik_onerileri']:
                # YouTube arama linki oluştur
                link = f"https://www.youtube.com/results?search_query={sarki.replace(' ', '+')}"
                st.markdown(f"🎵 [{sarki}]({link})", unsafe_allow_html=True)

        if st.button("❤️ Favorilere Ekle", use_container_width=True):
            if k not in st.session_state['favoriler']:
                st.session_state['favoriler'].append(k.copy())
                st.toast("✅ Eklendi!")
            else: st.toast("⚠️ Zaten var.")
    
    # KİTAP BAŞLIĞI VE ÖZETİ (c2'de gösterilecek)
    with c2:
        st.markdown(f"### 📚 {k['baslik']}")
        st.markdown(f"**✍️ Yazar:** {k['yazar']}")
        
        # ÖZETİ BELİRGİN ŞEKİLDE GÖSTER
        if k.get('ozet'):
            st.markdown("<div class='kitap-ozet'>", unsafe_allow_html=True)
            st.markdown(k['ozet'])
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ Özet bulunamadı.")

    with c3:
        st.markdown("### 🧙‍♂️ Büyücüye Sor")
        chat_container = st.container(height=400)
        for msg in st.session_state['chat_history']:
            chat_container.chat_message(msg["role"]).write(msg["content"])
        
        if prompt := st.chat_input("Sorunu sor..."):
            st.session_state['chat_history'].append({"role": "user", "content": prompt})
            chat_container.chat_message("user").write(prompt)
            with chat_container.chat_message("assistant"):
                with st.spinner("🔮 Cevaplanıyor..."):
                    cevap = gemini_sohbet(prompt, k)
                    st.write(cevap)
            st.session_state['chat_history'].append({"role": "assistant", "content": cevap})
            st.rerun()

# --- FAVORİLER ---
with tab3:
    st.subheader("⭐ Hazine Sandığım")
    if not st.session_state['favoriler']:
        st.info("Henüz favori kitap eklemediniz.")
    else:
        for i, fav in enumerate(st.session_state['favoriler']):
            with st.expander(f"📜 {fav['baslik']} - {fav['yazar']}", expanded=False):
                c1, c2 = st.columns([1,4])
                if fav.get('resim'): 
                    c1.image(fav['resim'], width=80)
                if fav.get('ozet'):
                    c2.markdown(f"**Özet:** {fav['ozet'][:300]}...")
                if c2.button("📖 Tekrar Aç", key=f"open_{i}"):
                    st.session_state['son_kitap'] = fav.copy()
                    st.session_state['chat_history'] = []
                    st.rerun()
                if c2.button("🗑️ Sil", key=f"del_{i}"):
                    st.session_state['favoriler'].pop(i)
                    st.rerun()