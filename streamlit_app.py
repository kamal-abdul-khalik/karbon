import streamlit as st
from perplexity import Perplexity
from PIL import Image
import json
import os
import base64
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px;
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

def get_skor_color(skor):
    """Tentukan warna berdasarkan skor"""
    if skor <= 3:
        return "skor-green", "🌟 Luar Biasa!"
    elif skor <= 6:
        return "skor-orange", "⚠️ Cukup Baik"
    else:
        return "skor-red", "🔴 Perlu Perbaikan"

def analyze_with_perplexity(image, api_key):
    """Analisis gambar struk menggunakan Perplexity API dengan web-grounded research"""
    try:
        # Inisialisasi client
        client = Perplexity(api_key=api_key)
        
        # Konversi gambar ke base64
        image_base64 = image_to_base64(image)
        
        # Prompt yang lebih komprehensif dan informatif
        prompt = """
Kamu adalah Ahli Lingkungan dan Analis Jejak Karbon yang berpengalaman. 

TUGAS: Analisis struk belanja pada gambar dan berikan assessment jejak karbon yang mendalam.

LANGKAH ANALISIS:
1. **Identifikasi Item**: Deteksi semua produk yang dibeli dari struk
2. **Kategori Produk**: Kelompokkan produk (Daging Merah, Daging Putih, Produk Susu, Sayuran/Buah, Makanan Olahan, Kemasan Plastik, Produk Organik)
3. **Skor Jejak Karbon**: Hitung total skor 1-10 berdasarkan:
   - Daging merah (sapi, kambing): +3 poin
   - Daging putih (ayam, ikan): +1.5 poin
   - Produk susu: +1 poin
   - Makanan ultra-processed: +2 poin
   - Kemasan plastik berlebihan: +2 poin
   - Sayuran/buah lokal: -0.5 poin
   - Produk organik: -0.5 poin
4. **Eco-Insight**: Berikan 3-5 saran konkret dan actionable
5. **Alternatif Ramah Lingkungan**: Sarankan pengganti untuk item dengan jejak karbon tinggi
6. **Fakta Lingkungan**: Tambahkan 1 fakta menarik terkait jejak karbon

OUTPUT FORMAT (JSON tanpa markdown):
{
    "skor": 0,
    "kategori_dominan": "Kategori utama",
    "detail_item": "Daftar item terdeteksi",
    "breakdown_skor": {
        "daging_merah": 0,
        "daging_putih": 0,
        "produk_susu": 0,
        "makanan_olahan": 0,
        "kemasan_plastik": 0,
        "sayuran_buah": 0,
        "produk_organik": 0
    },
    "insight": [
        "Saran 1",
        "Saran 2",
        "Saran 3"
    ],
    "alternatif": [
        {"item": "Produk X", "pengganti": "Produk Y", "alasan": "Mengapa lebih baik"}
    ],
    "fakta_lingkungan": "Fakta menarik",
    "estimasi_emisi_kg_co2": 0,
    "perbandingan": "Setara dengan X km perjalanan mobil"
}
"""
        
        # Request ke Perplexity API dengan vision
        response = client.chat.completions.create(
            model="sonar",  # Model sonar mendukung image analysis
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_base64}}
                    ]
                }
            ]
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        return result, None
        
    except json.JSONDecodeError as e:
        return None, f"Error parsing response: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

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
    
    # Gunakan environment variable jika tersedia
    if not api_key:
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if api_key:
            st.success("✅ Menggunakan API Key dari environment")
    
    st.divider()
    
    # Informasi tentang jejak karbon
    st.markdown("""
    ### 🌍 Tahukah Kamu?
    
    **Jejak Karbon** adalah total emisi gas rumah kaca yang dihasilkan dari aktivitas kita.
    
    **Fakta Penting:**
    - 1 kg daging sapi = 27 kg CO₂
    - 1 kg sayuran = 2 kg CO₂
    - Plastik sekali pakai butuh 450 tahun terurai
    """)
    
    st.divider()
    st.caption("Dibuat dengan ❤️ untuk Bumi 🌍")

# --- MAIN CONTENT ---
st.markdown("### 📸 Input Struk Belanja")

# Tabs untuk input gambar
col1, col2 = st.columns(2)

with col1:
    st.info("💡 **Ambil Foto Langsung**\nGunakan kamera untuk foto struk")
with col2:
    st.info("💡 **Upload dari Galeri**\nPilih foto yang sudah ada")

tab1, tab2 = st.tabs(["📷 Kamera", "⬆️ Upload"])

image = None

with tab1:
    camera_file = st.camera_input("Jepret struk belanjaan Anda")
    if camera_file:
        image = Image.open(camera_file)

with tab2:
    upload_file = st.file_uploader(
        "Pilih foto struk",
        type=['jpg', 'png', 'jpeg'],
        help="Format: JPG, PNG, JPEG (Maks 200MB)"
    )
    if upload_file:
        image = Image.open(upload_file)

# --- PROSES ANALISIS ---
if image is not None:
    # Tampilkan preview gambar
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(image, caption="✅ Struk siap dianalisis", use_container_width=True)
    
    # Tombol Analisis
    if st.button("🌍 Analisis Jejak Karbon Sekarang!", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ **API Key diperlukan!** Masukkan API Key Perplexity di sidebar.")
        else:
            with st.spinner('🔍 Sedang menganalisis jejak karbon... Mohon tunggu!'):
                hasil, error = analyze_with_perplexity(image, api_key)
                
                if error:
                    st.error(f"❌ {error}")
                else:
                    # Tampilkan hasil dengan UI menarik
                    st.success("✅ **Analisis Selesai!** Berikut adalah hasil assessment jejak karbon Anda:")
                    
                    # --- SKOR UTAMA ---
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
                    
                    # --- BREAKDOWN SKOR ---
                    if 'breakdown_skor' in hasil:
                        st.markdown("### 📈 Breakdown Skor Detil")
                        breakdown = hasil['breakdown_skor']
                        cols = st.columns(4)
                        categories = [
                            ("🥩 Daging Merah", breakdown.get('daging_merah', 0)),
                            ("🍗 Daging Putih", breakdown.get('daging_putih', 0)),
                            ("🥛 Produk Susu", breakdown.get('produk_susu', 0)),
                            ("🍕 Makanan Olahan", breakdown.get('makanan_olahan', 0)),
                            ("♻️ Kemasan Plastik", breakdown.get('kemasan_plastik', 0)),
                            ("🥬 Sayuran/Buah", breakdown.get('sayuran_buah', 0)),
                            ("🌱 Produk Organik", breakdown.get('produk_organik', 0))
                        ]
                        
                        for idx, (label, value) in enumerate(categories):
                            with cols[idx % 4]:
                                st.metric(label, f"{value} poin")
                    
                    # --- ECO-INSIGHT ---
                    st.markdown("### 💡 Eco-Insight & Saran")
                    insights = hasil.get('insight', [])
                    for idx, insight in enumerate(insights, 1):
                        st.markdown(f"""
                        <div class="info-card">
                            <strong>{idx}.</strong> {insight}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # --- ALTERNATIF RAMAH LINGKUNGAN ---
                    if 'alternatif' in hasil and hasil['alternatif']:
                        st.markdown("### 🔄 Alternatif Ramah Lingkungan")
                        for alt in hasil['alternatif']:
                            with st.expander(f"🔹 {alt.get('item', 'N/A')} → {alt.get('pengganti', 'N/A')}"):
                                st.write(f"**Alasan:** {alt.get('alasan', 'Tidak ada informasi')}")
                    
                    # --- FAKTA LINGKUNGAN ---
                    if 'fakta_lingkungan' in hasil:
                        st.markdown("### 🌏 Fakta Lingkungan")
                        st.info(hasil['fakta_lingkungan'])
                    
                    # --- CALL TO ACTION ---
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-top: 2rem;">
                        <h3>🌟 Mulai Langkah Kecilmu untuk Bumi!</h3>
                        <p>Setiap pilihan belanja yang ramah lingkungan adalah kontribusi nyata untuk masa depan yang lebih hijau.</p>
                    </div>
                    """, unsafe_allow_html=True)

else:
    # Info jika belum ada gambar
    st.info("👆 **Silakan ambil foto atau upload struk belanja Anda untuk memulai analisis jejak karbon!**")
    
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
