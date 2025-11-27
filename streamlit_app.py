import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import time

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="EcoScan AI",
    page_icon="🌱",
    layout="centered"
)

# --- CSS KUSTOM (Untuk Tampilan Lebih Cantik) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #2E8B57;
        color: white;
        border-radius: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- JUDUL & HEADER ---
st.title("🌱 EcoScan AI")
st.subheader("Ubah struk belanjamu jadi skor jejak karbon!")
st.caption("Hackathon SMK AI Innovator 2025 - AI untuk Lingkungan")

# --- SIDEBAR: KONFIGURASI API ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    st.markdown("""
    **Cara Pakai:**
    1. Masukkan API Key Google Gemini.
    2. Foto/Upload struk belanjaan.
    3. Klik 'Analisis Jejak Karbon!'.
    """)

    # Input API Key
    api_key = st.text_input("Masukkan Google Gemini API Key", type="password", help="Dapatkan di aistudio.google.com")

    st.divider()
    st.info("Dibuat dengan ❤️ untuk Bumi")

# --- FITUR UTAMA: INPUT GAMBAR ---
st.markdown("### 📸 Masukkan Struk Belanja")
tab1, tab2 = st.tabs(["📷 Ambil Foto", "⬆️ Upload Gambar"])

image = None

with tab1:
    camera_file = st.camera_input("Jepret struk belanjaan")
    if camera_file:
        image = Image.open(camera_file)

with tab2:
    upload_file = st.file_uploader("Upload foto struk", type=['jpg', 'png', 'jpeg'])
    if upload_file:
        image = Image.open(upload_file)

# --- PROSES AI ---
if image is not None:
    st.image(image, caption="Struk yang akan dianalisis", use_column_width=True)

    # Tombol Aksi
    if st.button("🌍 Analisis Jejak Karbon!", type="primary"):
        if not api_key:
            st.error("⚠️ Waduh! API Key belum diisi di menu sebelah kiri (Sidebar).")
        else:
            try:
                with st.spinner('Sedang menghitung emisi karbon... Tunggu sebentar!'):
                    # 1. Konfigurasi Gemini
                    genai.configure(api_key=api_key)
                    
                    # Gunakan model gemini-1.5-flash untuk kecepatan dan stabilitas
                    # (Bisa diganti gemini-2.0-flash-exp jika akses tersedia)
                    model = genai.GenerativeModel('gemini-1.5-flash')

                    # 2. Prompt Khusus EcoScan
                    prompt_ecoscan = """
                    Peran: Kamu adalah Ahli Lingkungan dan AI Analis Data.
                    Tugas: Analisis gambar struk belanja ini.
                    
                    Lakukan langkah berikut:
                    1. Identifikasi item belanjaan yang ada di struk.
                    2. Tentukan 'Skor Jejak Karbon' total dari 1-10 (10 = Sangat Buruk bagi lingkungan, 1 = Sangat Ramah).
                    3. Berikan 'Eco-Insight' atau tips ramah lingkungan berdasarkan item yang dibeli.
                    4. Kategorikan pembelian dominan (misal: Daging, Plastik, Sayuran).
                    
                    Output Wajib dalam format JSON murni tanpa markdown code block:
                    {
                        "skor": 0,
                        "kategori_dominan": "Nama Kategori",
                        "insight": "Saran singkat...",
                        "detail_item": "Ringkasan item yang terdeteksi"
                    }
                    """

                    # 3. Request ke AI
                    response = model.generate_content(
                        [prompt_ecoscan, image],
                        generation_config={"response_mime_type": "application/json"}
                    )

                    # 4. Parsing Hasil JSON
                    hasil = json.loads(response.text)
                    
                    # 5. Tampilkan Hasil (UI yang Menarik)
                    st.success("Analisis Selesai! Ini jejak karbonmu:")
                    
                    # Layout Kolom untuk Skor
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        skor = hasil.get('skor', 0)
                        warna_skor = "green" if skor < 5 else "orange" if skor < 8 else "red"
                        st.markdown(f"""
                        <div style="text-align: center; border: 2px solid {warna_skor}; border-radius: 10px; padding: 10px;">
                            <h2 style="color: {warna_skor}; margin:0;">{skor}/10</h2>
                            <p>Skor Karbon</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>🔍 Kategori Dominan: {hasil.get('kategori_dominan')}</h4>
                            <p><i>"{hasil.get('detail_item')}"</i></p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Insight / Saran
                    st.markdown(f"""
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #2E8B57; margin-top: 10px;">
                        <strong>💡 Eco-Insight:</strong><br>
                        {hasil.get('insight')}
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Yah error bro: {e}. Coba foto struk lebih jelas ya!")

else:
    st.info("👈 Silakan ambil foto atau upload gambar struk dulu ya di tab atas.")