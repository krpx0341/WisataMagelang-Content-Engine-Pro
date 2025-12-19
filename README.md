## WisataMagelang Content Engine Pro

Streamlit-based auto-blogging tool that turns trending news about Magelang tourism into SEO‑optimized WordPress drafts in bulk.

The app will:
- **Search news** via `GoogleNews` based on your keyword (Indonesian news, 7‑day range).
- **Scrape & clean** the full article text (removes tracking params and “Baca Juga” style noise).
- **Rewrite/expand** it into long‑form, Yoast‑style SEO content using **OpenAI GPT‑4o**.
- **Batch‑upload** the generated posts to your **WordPress** site as **drafts** via the REST API (Basic Auth).

---

## Features

- **Trending news fetcher** – uses `GoogleNews` (lang=`id`, region=`ID`) for fresh topics.
- **Smart scraping** – uses `newspaper3k` with custom user‑agent and `?page=all` hack.
- **Content cleaning** – removes promo/navigation lines that can confuse the model.
- **Hybrid SEO writer**:
  - If source text is **short** → expands into a **full travel guide** (routes, ticket estimates, tips, etc.).
  - If source text is **long** → paraphrases while keeping unique facts.
- **Internal linking helper** – fetches your latest WP posts and passes them as link suggestions to the model.
- **Batch WordPress drafts** – send multiple AI‑generated posts at once, all as drafts for manual review.

---

## Requirements

- **Python** 3.9+ (recommended)
- A valid **OpenAI API key**
- A **WordPress** site with:
  - REST API enabled (default on modern WordPress)
  - Username + **Application Password** (for Basic Auth)

Python dependencies (install via `pip`):
- `streamlit`
- `GoogleNews`
- `newspaper3k`
- `openai`
- `requests`

You can also put them in a `requirements.txt`:

```txt
streamlit
GoogleNews
newspaper3k
openai
requests
```

---

## Setup & Configuration

1. **Clone or copy this project**
   - Place `app.py` (and `config.json` if you already have one) in your project folder.

2. **Create virtual environment (optional but recommended)**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # on Windows
   # source .venv/bin/activate  # on macOS / Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   or, if you don’t use `requirements.txt`:

   ```bash
   pip install streamlit GoogleNews newspaper3k openai requests
   ```

4. **First‑time configuration in the app UI**
   - Run the app (see next section) and open it in your browser.
   - In the **left sidebar** (`⚙️ Konfigurasi Global`), fill in:
     - **OpenAI API Key**
     - **URL WordPress** (e.g. `https://wisatamagelang.id`)
     - **Username WP**
     - **App Password WP**
   - Click **“Simpan Konfigurasi”**.
   - These settings are saved to `config.json` so you don’t need to re‑enter them.

---

## How to Run

From the project directory (where `app.py` lives), run:

```bash
streamlit run app.py
```

Streamlit will print a local URL (e.g. `http://localhost:8501`) – open it in your browser.

---

## How to Use the App

1. **Configure credentials**
   - Use the sidebar to set your OpenAI key and WordPress credentials, then save.

2. **Search for news**
   - In the main page, enter a **topic/keyword** (default: `Wisata Magelang Terbaru`).
   - Click **“🔍 Cari Berita”**.
   - The app fetches recent articles from Google News.

3. **Select articles to process**
   - A list of articles (max 10) appears with checkboxes.
   - Tick the ones you want to convert into blog posts.

4. **Process with AI & upload**
   - Click **“⚡ PROSES AI & UPLOAD (BATCH)”**.
   - The app:
     - Fetches your latest WP posts for internal linking context.
     - Scrapes and cleans the selected news articles.
     - Calls OpenAI GPT‑4o to generate SEO‑ready content (JSON: `seo_title`, `meta_desc`, `html_content`).
     - Sends each result to WordPress as a **draft** post.
   - Progress and per‑article status are shown live; at the end you’ll see a simple upload report.

5. **Review in WordPress**
   - Log into your WordPress admin.
   - Go to **Posts → All Posts**, filter by **Draft**.
   - Open each draft, review/edit as needed, set featured image, categories, tags, and publish.

---

## Notes & Limitations

- All posts are created as **drafts** (not published) for safety.
- Internal linking relies on the latest posts fetched from `wp-json/wp/v2/posts`.
- If scraping fails for some sites (paywalled, heavy anti‑bot, etc.), the app will skip that article and show a warning.
- OpenAI usage will incur costs on your account; monitor your API usage/limits.

---

## (ID) Ringkasan Singkat

**WisataMagelang Content Engine Pro** adalah aplikasi Streamlit untuk:
- Mencari berita wisata Magelang terbaru.
- Scrape dan bersihkan artikel sumber.
- Menulis ulang / mengembangkan artikel menjadi konten SEO (standar Yoast) dengan OpenAI (GPT‑4o).
- Mengirim banyak artikel sekaligus sebagai **draft** ke WordPress.

Sangat cocok untuk pemilik blog wisata yang ingin mempercepat produksi konten namun tetap bisa review manual sebelum terbit.
