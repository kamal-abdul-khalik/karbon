import streamlit as st
from perplexity import Perplexity
from PIL import Image
import json
import os
import base64
import re
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="EcoScan AI - Analisis Jejak Karbon",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CSS KUSTOM ---
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .skor-box {
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .skor-green { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
    .skor-orange { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
    .skor-red { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; }
    .info-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .debug-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI HELPER ---
def image_to_base64(image):
    """Konversi gambar PIL ke base64 string untuk API"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def extract_json_from_response(text):
    """Extract JSON dari response yang mungkin mengandung teks tambahan"""
    if not text or not text.strip():
        return None
    
    # Coba langsung parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Cari JSON block dalam ``````
    json_match = re.search(r'``````', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Cari objek JSON pertama yang valid
    json_match = re.search(r'\{[^{}]*?(?:\{[^{}]*\}[^{}]*)*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDebug:
            pass
    
    return None

def get_skor_color(skor):
    """Tentukan warna berdasarkan skor"""
    if skor <= 3:
        return "skor-green", "🌟 Luar Biasa!"
    elif skor <= 6:
        return "skor-orange", "⚠️ Cukup Baik"
    else:
        return "skor-red", "🔴 Perlu Perbaikan"

def analyze_with_perplexity(image, api_key, show_debug=False):
    """Analisis gambar struk dengan robust error handling"""
    try:
        # Inisialisasi client
        client = Perplexity(api_key=api_key)
        image_base64 = image_to_base64(image)
        
        # Prompt YANG LEBIH KETAT untuk JSON
        prompt = """KAMU HARUS MENGGUNAKAN FORMAT JSON INI DAN HANYA JSON. JANGAN TULIS TEKS LAIN.

Analisis struk belanja dan berikan assessment jejak karbon. Gunakan sistem scoring berikut:

JAWAB HANYA DENGAN JSON SESUAI FORMAT INI:

{
  "skor": 5,
  "kategori_dominan": "Makanan Olahan",
  "detail_item": "Daftar 3-5 item utama",
  "breakdown_skor": {
    "daging_merah": 2,
    "daging_putih": 1,
    "produk_susu": 1,
    "makanan_olahan": 3,
    "kemasan_plastik": 2,
    "sayuran_buah": 1,
    "produk_organik": 0
  },
  "insight": ["Saran 1 praktis", "Saran 2", "Saran 3"],
  "alternatif": [
    {"item": "Daging Sapi", "pengganti": "Tahu/Tempe", "alasan": "Mengurangi 80% emisi CO2"}
  ],
  "fakta_lingkungan": "1kg daging sapi = 27kg CO2",
  "estimasi_emisi_kg_co2": 4.5,
  "perbandingan": "Setara 20km perjalanan mobil"
}

Scoring: Daging merah +3, Daging putih +1.5, Susu +1, Olahan +2, Plastik +2, Sayur -0.5, Organik -0.5."""

        # Request dengan response_format JSON mode
        response = client.chat.completions.create(
            model="sonar",  # Model vision terbaik
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_base64}}
                    ]
                }
            ],
            temperature=0.1,  # Kurangi randomness untuk JSON konsisten
            max_tokens=2000
        )
        
        raw_response = response.choices[0].message.content
        
        if show_debug:
            st.markdown("### 🔍 Debug Response")
            st.code(raw_response, language="json")
        
        # Extract dan validate JSON
        parsed_data = extract_json_from_response(raw_response)
        
        if parsed_data is None:
            return None, f"❌ Gagal parse JSON dari response:\n``````"
        
        # Validasi struktur minimal
        required_keys = ['skor', 'kategori_dominan']
        missing_keys = [key for key in required_keys if key not in parsed_data]
        if missing_keys:
            return None, f"❌ JSON tidak lengkap, kurang: {missing_keys}"
        
        return parsed_data, None
        
    except Exception as e:
        return None, f"❌ Error API: {str(e)}"

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <h1>🌱 EcoScan AI</h1>
    <p style="font-size: 1.2rem; margin: 0;">Ubah Struk Belanjamu Jadi Aksi Lingkungan!</p>
    <p style="font-size: 0.9rem; opacity: 0.9;">Powered by Perplexity AI | Hackathon SMK AI Innovator 2025</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    # Debug toggle
    show_debug = st.checkbox("🔍 Tampilkan Debug Info (untuk troubleshooting)")
    
    # Info penggunaan
    with st.expander("📖 Panduan Penggunaan", expanded=False):
        st.markdown("""
        **Langkah Mudah:**
        1. Masukkan API Key Perplexity
        2. Ambil foto atau upload struk belanja
        3. Klik tombol analisis
        4. Dapatkan insight dan saran!
        
        **Tips:**
        - Pastikan struk jelas terbaca
        - Cahaya cukup terang
        - Tidak ada bayangan
        """)
    
    # Input API Key
    api_key = st.text_input(
        "Perplexity API Key",
        type="password",
        help="Dapatkan API key di: https://www.perplexity.ai/settings/api",
        placeholder="pplx-..."
    )
    
    # Environment variable fallback
    if not api_key:
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if api_key:
            st.success("✅ Menggunakan API Key dari environment")
    
    st.divider()
    
    st.markdown("""
    ### 🌍 Tahukah Kamu?
    **Fakta Penting:**
    - 1 kg daging sapi = 27 kg CO₂
    - 1 kg sayuran = 2 kg CO₂
    - Plastik sekali pakai butuh 450 tahun terurai
    """)
    
    st.divider()
    st.caption("Dibuat dengan ❤️ untuk Bumi 🌍")

# --- MAIN CONTENT ---
st.markdown("### 📸 Input Struk Belanja")

tab1, tab2 = st.tabs(["📷 Kamera", "⬆️ Upload"])

image = None

with tab1:
    camera_file = st.camera_input("Jepret struk belanjaan Anda")
    if camera_file:
        image = Image.open(camera_file)

with tab2:
    upload_file = st.file_uploader(
        "Pilih foto struk",
        type=['jpg', 'png', 'jpeg']
    )
    if upload_file:
        image = Image.open(upload_file)

# --- PROSES ANALISIS ---
if image is not None:
    st.image(image, caption="✅ Struk siap dianalisis", use_container_width=True)
    
    if st.button("🌍 Analisis Jejak Karbon Sekarang!", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ **API Key diperlukan!** Masukkan API Key Perplexity di sidebar.")
        else:
            with st.spinner('🔍 Menganalisis jejak karbon...'):
                hasil, error = analyze_with_perplexity(image, api_key, show_debug)
                
                if error:
                    st.error(error)
                else:
                    st.success("✅ **Analisis Selesai!**")
                    
                    # Tampilkan hasil
                    st.markdown("### 📊 Skor Jejak Karbon")
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        skor = hasil.get('skor', 0)
                        color_class, status = get_skor_color(skor)
                        st.markdown(f"""
                        <div class="skor-box {color_class}">
                            {skor}/10
                        </div>
                        <p style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">
                            {status}
                        </p>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="info-card">
                            <h4>📦 Kategori Dominan</h4>
                            <p style="font-size: 1.1rem;"><strong>{hasil.get('kategori_dominan', 'N/A')}</strong></p>
                            <h4 style="margin-top: 1rem;">🛒 Item Terdeteksi</h4>
                            <p>{hasil.get('detail_item', 'Tidak ada detail')}</p>
                            <h4 style="margin-top: 1rem;">💨 Estimasi Emisi</h4>
                            <p style="font-size: 1.1rem;"><strong>{hasil.get('estimasi_emisi_kg_co2', 0)} kg CO₂</strong></p>
                            <p style="font-size: 0.9rem; color: #666;">{hasil.get('perbandingan', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Breakdown skor
                    if 'breakdown_skor' in hasil:
                        st.markdown("### 📈 Breakdown Skor")
                        breakdown = hasil['breakdown_skor']
                        cols = st.columns(4)
                        categories = [
                            ("🥩 Daging Merah", breakdown.get('daging_merah', 0)),
                            ("🍗 Daging Putih", breakdown.get('daging_putih', 0)),
                            ("🥛 Produk Susu", breakdown.get('produk_susu', 0)),
                            ("🍕 Makanan Olahan", breakdown.get('makanan_olahan', 0))
                        ]
                        for idx, (label, value) in enumerate(categories):
                            with cols[idx]:
                                st.metric(label, f"{value} poin")
                        
                        cols = st.columns(3)
                        categories2 = [
                            ("♻️ Plastik", breakdown.get('kemasan_plastik', 0)),
                            ("🥬 Sayur/Buah", breakdown.get('sayuran_buah', 0)),
                            ("🌱 Organik", breakdown.get('produk_organik', 0))
                        ]
                        for idx, (label, value) in enumerate(categories2):
                            with cols[idx]:
                                st.metric(label, f"{value} poin")
                    
                    # Insights
                    insights = hasil.get('insight', [])
                    if insights:
                        st.markdown("### 💡 Saran Praktis")
                        for idx, insight in enumerate(insights[:3], 1):
                            st.markdown(f"**{idx}.** {insight}")
                    
                    # Alternatif
                    alternatif = hasil.get('alternatif', [])
                    if alternatif:
                        st.markdown("### 🔄 Alternatif Ramah Lingkungan")
                        for alt in alternatif[:3]:
                            with st.expander(f"🔹 {alt.get('item', 'N/A')} → {alt.get('pengganti', 'N/A')}"):
                                st.success(f"**Alasan:** {alt.get('alasan', '')}")
                    
                    # Fakta
                    if 'fakta_lingkungan' in hasil:
                        st.markdown("### 🌏 Fakta Menarik")
                        st.info(hasil['fakta_lingkungan'])

else:
    st.info("👆 **Silakan ambil foto atau upload struk belanja untuk memulai analisis!**")
    
    # Tampilkan contoh manfaat
    st.markdown("### 🎯 Apa yang Akan Anda Dapatkan?")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 Skor Akurat**
        - Analisis mendalam
        - Breakdown detil
        - Estimasi emisi CO₂
        """)
    
    with col2:
        st.markdown("""
        **💡 Saran Praktis**
        - Tips actionable
        - Alternatif produk
        - Fakta lingkungan
        """)
    
    with col3:
        st.markdown("""
        **🌱 Dampak Nyata**
        - Keputusan lebih baik
        - Kurangi jejak karbon
        - Selamatkan bumi
        """)
