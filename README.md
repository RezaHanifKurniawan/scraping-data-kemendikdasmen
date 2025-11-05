# Scraper Data Sekolah SD/MI Kabupaten Semarang

Proyek ini adalah sistem scraping data sekolah jenjang SD/MI di Kabupaten Semarang menggunakan **Selenium**, **Requests**, dan **BeautifulSoup**. Data diambil dari situs Kemendikdasmen dan disimpan dalam format CSV.

## Fitur
- **Scraping Daftar Kecamatan**: Mengambil kode dan nama kecamatan.
- **Scraping Data Sekolah**: Nama sekolah, NPSN, status, alamat, kepala sekolah, kontak, dll.
- **Antarmuka Gradio**: Memudahkan pengguna memilih kecamatan dan kolom data.
- **Dua Versi Scraper**:
  - **Versi 1**: Full Selenium (akurasi tinggi, lebih lambat).
  - **Versi 2**: Hybrid (Selenium + Requests, lebih cepat).

**Instalasi**:
   ```bash
   pip install selenium undetected-chromedriver beautifulsoup4 requests gradio
   ```
   
**Teknologi**:
- Selenium: Scraping dinamis.
- Requests: HTTP
- BeautifulSoup: Parsing HTML.
- Thread Pool : 25 workers
- Gradio: Antarmuka pengguna.

## DETAILNYA ADA DI FILE IPYNB