import streamlit as st
import base64
import requests
import json
import time

# --- Konfigurasi Halaman Streamlit ---
# Pengaturan tampilan halaman
st.set_page_config(
    page_title="EcoScan AI: Pemindai Jejak Karbon Struk",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Variabel Global dan Konfigurasi API ---
# Gunakan kunci API kosong sesuai instruksi. Lingkungan Canvas akan mengisinya saat runtime.
API_KEY = "" 
GEMINI_MODEL_NAME = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent?key={API_KEY}"

# Fungsi untuk mengonversi gambar ke base64 (untuk payload API)
def image_to_base64(uploaded_file):
    """Mengkonversi objek file upload Streamlit ke string base64."""
    bytes_data = uploaded_file.getvalue()
    return base64.b64encode(bytes_data).decode('utf-8')

# Fungsi untuk memanggil Gemini API (Multimodal/Vision)
def get_eco_analysis(base64_image):
    """Menganalisis struk dan menghitung skor karbon."""
    
    # Prompt System: Mengarahkan peran dan format output AI
    system_prompt = (
        "Anda adalah AI Analis Karbon. Tugas Anda adalah: "
        "1. Lakukan OCR dan ekstrak daftar item, harganya, dan kategorikan dampaknya (misal: 'Daging Merah', 'Lokal Sayuran', 'Kemasan Plastik'). "
        "2. Berikan 'Skor Dampak Karbon' total (dari 1 hingga 10, di mana 10 adalah dampak tertinggi) berdasarkan item yang paling berdampak. "
        "3. Berikan 'Eco-Insight' sederhana: satu tips yang dapat ditindaklanjuti untuk mengurangi skor di masa depan."
        "4. Format SEMUA output Anda sebagai JSON untuk parsing yang andal. Jika struk tidak terbaca jelas, kembalikan JSON dengan status 'Error'."
    )
    
    user_query = "Tolong analisis struk belanja ini untuk menghitung jejak karbon dan berikan tips sederhana."

    # Payload API dengan struktur JSON Schema untuk respons terstruktur
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_query},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",  # Asumsi tipe JPEG
                            "data": base64_image
                        }
                    }
                ]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "skor_karbon": {"type": "NUMBER", "description": "Skor dampak karbon total, 1-10."},
                    "kategori_terdampak": {"type": "STRING", "description": "Kategori pembelian dengan dampak terbesar."},
                    "eco_insight": {"type": "STRING", "description": "Tips sederhana yang direkomendasikan AI."},
                    "items_terekstrak": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "item": {"type": "STRING"},
                                "kategori": {"type": "STRING"},
                                "harga": {"type": "STRING"} 
                            }
                        }
                    },
                    "status": {"type": "STRING", "description": "Status hasil: OK atau Error."}
                }
            }
        }
    }

    # Implementasi Exponential Backoff untuk retry API
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
            response.raise_for_status() # Cek status HTTP
            
            result = response.json()
            
            # Ekstraksi dan parsing respons JSON
            if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                json_string = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(json_string)
            else:
                st.error("Gagal mendapatkan konten dari AI. Respons tidak terstruktur.")
                return None

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt # Exponential backoff (1s, 2s, 4s...)
                st.warning(f"Kesalahan API ({e}). Mencoba lagi dalam {wait_time} detik... (Percobaan ke {attempt + 1})")
                time.sleep(wait_time)
            else:
                st.error(f"Gagal memanggil API setelah {max_retries} percobaan: {e}")
                return None
        except json.JSONDecodeError:
            st.error("AI mengembalikan format JSON yang tidak valid. Coba lagi dengan gambar struk yang lebih jelas.")
            return {"status": "Error", "eco_insight": "Format respons AI tidak valid."}
        except Exception as e:
            st.error(f"Terjadi kesalahan tak terduga: {e}")
            return None
    
    return None

# --- Tampilan Streamlit Utama ---

st.title("🌱 EcoScan AI: Pemindai Jejak Karbon")
st.markdown("Aplikasi *simple, kreatif, dan solutif* untuk menganalisis struk belanja, menghitung jejak karbon, dan memberikan tips ramah lingkungan.")

# Pilihan input: Kamera atau Upload File
input_method = st.radio(
    "Pilih sumber gambar struk:",
    ("📸 Ambil Foto Langsung", "⬆️ Unggah File Gambar"),
    key="input_method",
    horizontal=True
)

uploaded_file = None

if input_method == "📸 Ambil Foto Langsung":
    # Streamlit memiliki widget kamera
    st.info("Pastikan struk berada di tempat yang terang dan rata.")
    uploaded_file = st.camera_input("Ambil Foto Struk")
elif input_method == "⬆️ Unggah File Gambar":
    # Widget upload file
    uploaded_file = st.file_uploader(
        "Unggah foto struk belanja (.jpg, .png)",
        type=["jpg", "jpeg", "png"]
    )

# --- Logika Pemrosesan ---
if uploaded_file is not None:
    st.image(uploaded_file, caption='Struk yang akan dianalisis.', use_column_width=True)

    # Tombol untuk memicu Analisis
    if st.button("🚀 Analisis Jejak Karbon", type="primary"):
        with st.spinner("⏳ AI sedang menganalisis teks dan menghitung skor..."):
            
            # 1. Konversi ke Base64
            base64_data = image_to_base64(uploaded_file)
            
            # 2. Panggil API Gemini
            analysis_result = get_eco_analysis(base64_data)

        # 3. Tampilkan Hasil
        if analysis_result and analysis_result.get("status") == "OK":
            
            skor = analysis_result.get("skor_karbon", 0)
            kategori = analysis_result.get("kategori_terdampak", "Tidak teridentifikasi")
            insight = analysis_result.get("eco_insight", "Maaf, insight tidak tersedia.")
            items = analysis_result.get("items_terekstrak", [])

            st.subheader("✅ Hasil Analisis EcoScan")
            
            # Tampilan Skor Karbon (Skor 10 berarti dampak lingkungan sangat tinggi)
            st.metric(
                label="Skor Dampak Karbon Harian (1-10)",
                value=f"{skor}/10",
                delta_color="off" 
            )
            
            # Visualisasi Sederhana (Eco-Gauge)
            progress_value = min(1.0, skor / 10.0) # Pastikan tidak lebih dari 1.0
            
            if skor >= 7:
                 st.progress(progress_value, text=f"🔴 *Dampak Tinggi:* Fokus pada *{kategori}*")
            elif skor >= 4:
                 st.progress(progress_value, text=f"🟠 *Dampak Sedang:* Fokus pada *{kategori}*")
            else:
                 st.progress(progress_value, text="🟢 *Dampak Rendah:* Pertahankan pola belanja ini!")

            
            # Eco-Insight (Tips Solutif)
            st.success(f"💡 *Eco-Insight Sederhana:* {insight}")
            st.markdown("---")
            
            # Detail Item yang Diekstrak
            st.subheader("🛒 Detail Item Terekstrak")
            if items:
                # Membuat list untuk ditampilkan dalam tabel Streamlit
                data_to_show = [{"Item": item['item'], "Kategori Karbon": item['kategori'], "Harga": item['harga']} for item in items]
                st.dataframe(data_to_show, use_container_width=True, hide_index=True)
            else:
                st.warning("Tidak ada item spesifik yang dapat diekstrak oleh AI.")

        elif analysis_result and analysis_result.get("status") == "Error":
             st.error(f"❌ Analisis Gagal. Pesan AI: {analysis_result.get('eco_insight')}. Coba dengan foto struk yang lebih jelas dan resolusi tinggi.")
        elif analysis_result is None:
             st.error("❌ Analisis Gagal. Silakan periksa koneksi atau coba lagi.")


st.caption("Proyek AI untuk Lingkungan - Ditenagai oleh Gemini 2.5 Flash")