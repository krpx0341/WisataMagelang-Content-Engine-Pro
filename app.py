import streamlit as st
from GoogleNews import GoogleNews
from newspaper import Article, Config
from openai import OpenAI
import requests
import base64
import json
import os
import time
import re  # Tambahkan ini untuk pembersihan teks regex

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="WisataMagelang Content Engine Pro", layout="wide")

# File untuk menyimpan setting
CONFIG_FILE = "config.json"

# --- FUNGSI MANAJEMEN CONFIG ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"openai_key": "", "wp_url": "https://wisatamagelang.id", "wp_user": "", "wp_pass": ""}

def save_config(config_data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f)
    st.success("Konfigurasi tersimpan! Tidak perlu input ulang nanti.")

# Load config saat awal
config = load_config()

# --- SIDEBAR: KREDENSIAL ---
st.sidebar.header("⚙️ Konfigurasi Global")
with st.sidebar.form("config_form"):
    openai_api_key = st.text_input("OpenAI API Key", value=config["openai_key"], type="password")
    wp_url = st.text_input("URL WordPress", value=config["wp_url"])
    wp_user = st.text_input("Username WP", value=config["wp_user"])
    wp_password = st.text_input("App Password WP", value=config["wp_pass"], type="password")
    
    submitted = st.form_submit_button("Simpan Konfigurasi")
    if submitted:
        new_config = {
            "openai_key": openai_api_key,
            "wp_url": wp_url,
            "wp_user": wp_user,
            "wp_pass": wp_password
        }
        save_config(new_config)
        st.rerun()

# Inisialisasi Client OpenAI
client = None
if config["openai_key"]:
    client = OpenAI(api_key=config["openai_key"])

# --- FUNGSI UTAMA (CORE) ---

def search_trending(keyword):
    """Mencari berita terbaru"""
    googlenews = GoogleNews(lang='id', region='ID')
    googlenews.set_period('7d')
    googlenews.search(keyword)
    return googlenews.result()

def get_article_content(url):
    """
    Scraping Cerdas: 
    1. Membersihkan parameter Google
    2. Memaksa mode 'Single Page' (?page=all) agar artikel utuh
    3. Membersihkan iklan sisipan (Baca Juga...)
    """
    
    # 1. BERSIHKAN URL DARI TRACKING GOOGLE
    if '&ved=' in url:
        url = url.split('&ved=')[0]
    if '&usg=' in url:
        url = url.split('&usg=')[0]

    # 2. URL HACKING (PENTING!): Paksa Tampil Semua Halaman
    # Sebagian besar media Indonesia (Tribun, Kompas, dll) menggunakan pola ini
    if '?' in url:
        if 'page=all' not in url:
            url += '&page=all'
    else:
        url += '?page=all'

    try:
        conf = Config()
        conf.browser_user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        
        article = Article(url, config=conf)
        article.download()
        article.parse()
        
        raw_text = article.text

        # 3. TEXT CLEANING (Buang "Baca Juga", "Artikel Terkait", dll)
        # Ini mencegah AI bingung karena ada kalimat iklan di tengah paragraf
        clean_lines = []
        for line in raw_text.split('\n'):
            line_lower = line.lower()
            # Filter baris yang mengandung kata-kata navigasi intrusif
            if not any(
                x in line_lower
                for x in [
                    'baca juga:',
                    'baca selengkapnya',
                    'simak berita',
                    'artikel terkait:',
                    'google news',
                ]
            ):
                if len(line.strip()) > 0:  # Buang baris kosong
                    clean_lines.append(line)
        
        final_text = "\n".join(clean_lines)

        return article.title, final_text

    except Exception as e:
        # Fallback: Jika gagal download (misal server menolak ?page=all), coba url asli tanpa parameter
        if 'page=all' in url:
            try:
                original_url = (
                    url.replace('?page=all', '')
                       .replace('&page=all', '')
                )
                article = Article(original_url, config=conf)
                article.download()
                article.parse()
                return article.title, article.text
            except Exception:
                pass
        return None, None


# --- TAMBAHAN FUNGSI BARU ---
def get_existing_wp_posts():
    """Mengambil daftar artikel yang sudah ada di WP untuk Internal Linking"""
    try:
        api_endpoint = f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/posts?per_page=30&_fields=title,link"
        r = requests.get(api_endpoint)
        if r.status_code == 200:
            posts = r.json()
            # Format menjadi string daftar: "- Judul: Link"
            return "\n".join([f"- {p['title']['rendered']}: {p['link']}" for p in posts])
        return ""
    except:
        return ""


def generate_seo_article_yoast(source_title, source_text, keyword, existing_links_str=""):
    """
    Versi HYBRID: 
    1. Jika teks sumber panjang -> Paraphrase (Aman).
    2. Jika teks sumber pendek -> Expand dengan pengetahuan internal AI (General Knowledge).
    """
    if not client:
        return {"error": "API Key Missing"}

    # Cek apakah konten sumber "tipis" (kurang dari 600 karakter)
    is_thin_content = len(source_text) < 600
    
    # Mode Instruksi
    mode_instruction = ""
    if is_thin_content:
        mode_instruction = """
        PERINGATAN: Sumber teks sangat pendek. 
        TUGASMU: JANGAN hanya memparafrase. KEMBANGKAN topik ini menjadi "Panduan Wisata Lengkap".
        Gunakan pengetahuan umummu tentang Magelang untuk menambahkan bagian:
        1. Rute/Akses menuju lokasi (Sebutkan terminal/kota terdekat).
        2. Estimasi/Kisaran harga tiket (Gunakan kata 'estimasi' jika tidak yakin).
        3. Daya tarik lain di sekitar lokasi.
        4. Tips berkunjung (Waktu terbaik, pakaian, dll).
        """
    else:
        mode_instruction = """
        TUGASMU: Tulis ulang artikel ini dengan gaya bahasa baru yang segar.
        Pertahankan fakta-fakta unik yang ada di teks sumber.
        """

    # Prompt Engineering
    prompt = f"""
    Kamu adalah Local Guide & Travel Blogger spesialis Magelang.
    
    KONTEKS:
    User ingin artikel blog tentang "{keyword}" berdasarkan berita terbaru, tapi isinya harus panjang dan mendalam (Min 500 kata).

    DATA SUMBER (Berita):
    Judul: {source_title}
    Isi: {source_text[:2000]}
    
    REFERENSI INTERNAL (Sisipkan link ini jika relevan):
    {existing_links_str}

    {mode_instruction}

    STRUKTUR ARTIKEL (WAJIB ADA):
    1. **Intro**: Hook menarik + Inti berita/topik.
    2. **Isi Utama**: Detail berita/fakta dari sumber.
    3. **Explorasi (Wajib Ada)**: Sejarah singkat, atau spot foto terbaik, atau kuliner di sekitar (Gunakan pengetahuanmu tentang Magelang).
    4. **Panduan Praktis**: Lokasi (Desa/Kecamatan), Jam Buka.
    5. **Penutup**: Ajakan berkunjung.

    ATURAN SEO (YOAST):
    - Fokus Keyword: "{keyword}" (Muncun di Judul, Paragraf 1, Heading).
    - Panjang: Minimal 500 kata (Meskipun sumbernya pendek, kamu harus mengarang deskripsi suasana/latar belakang secara logis).
    - Gaya Bahasa: Deskriptif, Mengajak, "Storytelling".

    FORMAT OUTPUT (JSON):
    {{
        "seo_title": "Judul Menarik (Ada Keyword)",
        "meta_desc": "Ringkasan memikat (Max 150 chars)",
        "html_content": "<p>...</p><h2>...</h2>..."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # GPT-4o sangat disarankan karena "General Knowledge"-nya luas tentang Indonesia
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert travel writer who can expand short news into full travel guides.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,  # Sedikit kreatif agar bisa mengembangkan deskripsi
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def post_batch_wordpress(articles):
    """Posting batch ke WP"""
    results = []
    
    api_endpoint = f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/posts"
    creds = f"{config['wp_user']}:{config['wp_pass']}"
    token = base64.b64encode(creds.encode())
    headers = {
        'Authorization': f'Basic {token.decode("utf-8")}',
        'Content-Type': 'application/json'
    }

    progress_bar = st.progress(0)
    
    for i, art in enumerate(articles):
        # Post Data
        post_data = {
            'title': art['seo_title'],
            'content': art['html_content'], # Konten HTML dari AI
            'status': 'draft', # Tetap draft untuk safety
            'excerpt': art['meta_desc'] # Meta desc masuk ke excerpt WP
            # Jika ada plugin SEO (Yoast/RankMath), meta desc butuh field khusus (meta_input), 
            # tapi excerpt adalah fallback yang bagus.
        }

        try:
            r = requests.post(api_endpoint, headers=headers, json=post_data)
            if r.status_code == 201:
                link = r.json().get('link')
                results.append(f"✅ Sukses: [{art['seo_title']}]({link})")
            else:
                results.append(f"❌ Gagal ({art['seo_title']}): {r.text[:50]}...")
        except Exception as e:
            results.append(f"❌ Error Koneksi: {str(e)}")
        
        progress_bar.progress((i + 1) / len(articles))
        time.sleep(1) # Delay sopan ke server

    return results

# --- UI UTAMA ---

st.title("🚀 Auto-Blogging: Batch Processor")
st.caption("Scrape Massal -> SEO Rewrite (Yoast Standard) -> WP Draft")

# State Management
if 'search_results' not in st.session_state: st.session_state.search_results = []
if 'processed_articles' not in st.session_state: st.session_state.processed_articles = []

# 1. SEARCH SECTION
col_s1, col_s2 = st.columns([3, 1])
keyword_input = col_s1.text_input("Topik / Keyword", "Wisata Magelang Terbaru")
if col_s2.button("🔍 Cari Berita"):
    with st.spinner("Mencari..."):
        st.session_state.search_results = search_trending(keyword_input)

# 2. SELECTION SECTION
if st.session_state.search_results:
    st.divider()
    st.subheader("Pilih Artikel untuk Diproses")
    
    # Buat list dictionary untuk checkbox
    selected_indices = []
    
    # Grid layout untuk artikel
    for idx, item in enumerate(st.session_state.search_results[:10]): # Batasi 10 agar tidak overload
        chk = st.checkbox(f"{item['title']} ({item['media']})", key=f"chk_{idx}")
        if chk:
            selected_indices.append(item)
    
    st.info(f"Terpilih: {len(selected_indices)} artikel.")

    # 3. PROCESSING SECTION
    if len(selected_indices) > 0 and st.button("⚡ PROSES AI & UPLOAD (BATCH)"):
        st.divider()

        # 1. Ambil data artikel lama SEKALI saja di awal (untuk konteks linking)
        with st.spinner("Mengambil data Internal Link dari blog Anda..."):
            existing_links_str = get_existing_wp_posts()

        st.subheader("Proses Berjalan...")
        processed_data = []

        # Loop Processing
        for index, item in enumerate(selected_indices):
            status_text = st.empty()
            status_text.text(f"Sedang memproses {index+1}/{len(selected_indices)}: {item['title']}...")

            # 1. Scrape Content
            src_title, src_text = get_article_content(item["link"])

            if src_text:
                # 2. Generate AI (Yoast Logic)
                focus_keyword = keyword_input

                # Masukkan existing_links_str ke fungsi generator
                ai_result = generate_seo_article_yoast(
                    src_title, src_text, focus_keyword, existing_links_str
                )

                if "error" not in ai_result:
                    processed_data.append(ai_result)
                    st.success(f"✔️ AI Selesai: {ai_result['seo_title']}")
                else:
                    st.error(f"Gagal AI: {ai_result['error']}")
            else:
                st.warning(f"Gagal Scrape URL: {item['link']}")

        # 4. UPLOADING
        if processed_data:
            st.info("Mengirim ke WordPress...")
            upload_logs = post_batch_wordpress(processed_data)

            st.success("Selesai!")
            st.markdown("### Laporan Upload:")
            for log in upload_logs:
                st.markdown(log)

            # Clear selection after success
            st.balloons()