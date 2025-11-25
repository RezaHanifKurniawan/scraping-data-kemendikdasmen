#  Scraper SD/MI Kabupaten Semarang  
### (Menggunakan UC Driver, Selenium, Requests, BS4 — Dengan 2 Versi: Sequential & Optimized Parallel)

Repository ini berisi **web scraper otomatis** untuk mengambil data seluruh **SD dan MI** di Kabupaten Semarang dari portal resmi Kemendikbud.  
Terdapat **dua versi** scraper yang dapat dipilih sesuai kebutuhan performa:

---

##  Ringkasan Dua Versi

### ** Versi 1 — Sequential (Tanpa ThreadPool)**
- Semua proses dilakukan **satu per satu**  
- Sangat stabil  
- Cocok untuk backend deployment yang ingin menghindari banyak instance Selenium berjalan bersamaan  
- Waktu scraping lebih lama, terutama kecamatan dengan banyak sekolah

### ** Versi 2 — Optimized Parallel (ThreadPool)**
- Optimasi dari versi 1  
- Detail sekolah di-scrape **secara paralel** menggunakan `ThreadPoolExecutor`  
- Hingga **5–12× lebih cepat**  
- Cocok untuk scraping massal atau batch besar  
- Beban CPU lebih tinggi

---

##  Sumber Data

Scraper mengambil data resmi dari dua portal Kemendikbud:

### **1. referensi.data.kemendikdasmen.go.id**  
Digunakan untuk **listing sekolah** (UC Driver)  
Mengambil:
- Nama Sekolah  
- NPSN  
- Status (Negeri/Swasta)  
- Kelurahan  
- Link referensi detail sekolah  

### **2. sekolah.data.kemendikdasmen.go.id (Profil Sekolah)**  
Digunakan untuk **detail per sekolah** (Selenium)  
Mengambil:
- Alamat  
- Kepala Sekolah  
- Email  
- Telepon  
- Website  
- Jumlah Siswa Laki-laki  
- Jumlah Siswa Perempuan  

### **3. BeautifulSoup + Requests**  
Digunakan untuk mendapatkan **UUID sekolah** dari halaman referensi lama.  
→ Lebih ringan daripada Selenium.

---

##  Teknologi & Library yang Digunakan

### **1. Undetected ChromeDriver (UC)**
Digunakan untuk:
- Listing sekolah (anti bot detection)
- Stabil untuk navigasi tabel referensi

### **2. Selenium ChromeDriver Standard**
Digunakan untuk:
- Mengambil data detail sekolah
- Render SPA/Angular di halaman profil sekolah
- Versi 2: dijalankan paralel

### **3. Requests**
- Mengambil HTML referensi sekolah (versi lama)
- Digunakan untuk ekstraksi UUID

### **4. BeautifulSoup4**
- Parsing HTML lama untuk mendapatkan link profil sekolah

### **5. ThreadPoolExecutor** *(Versi 2)*  
- Scraping detail sekolah secara parallel

---

##  Alur Kerja Scraper

### **1️ Load daftar kecamatan**
- Baca file JSON berisi kode kecamatan

### **2️ Listing sekolah (UC Driver)**
- Masuk ke halaman referensi sekolah per kecamatan  
- Set tabel menjadi 100 rows  
- Ambil semua data dasar + link referensi

### **3️ Ambil UUID via requests (BS4)**
- Parse HTML cepat  
- Ekstrak UUID sekolah

### **4️ Scrape detail sekolah**
- **Versi 1:** sequential (1 Selenium instance)  
- **Versi 2:** parallel (banyak Selenium instance)

### **5️ Merge semua hasil + sorting**
- Hasil digabung dengan data listing
- Sort berdasarkan kolom pertama yang dipilih

### **6️ Simpan CSV**
- Disimpan ke folder `/output/`

---

##  Instalasi Dependensi

Gunakan Python 3.9–3.12 (disarankan conda environment)

### **1. Install UC Driver & Selenium**
```bash
pip install undetected-chromedriver selenium
```
### **2. Install Requests + BS4**
```bash
pip install requests beautifulsoup4
```
### **3. Jika ingin menjalankan versi UI**
```bash
pip install gradio
```