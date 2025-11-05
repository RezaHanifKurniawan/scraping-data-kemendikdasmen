import os, csv, json, time, requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# =====================================================
#  SETUP DRIVER UNTUK LOKAL
# =====================================================
def setup_driver_local(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1600,900")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--log-level=3")
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(25)
    return driver


# =====================================================
#  KODE KECAMATAN
# =====================================================
def get_kode_kecamatan_from_json(nama_kecamatan, json_path="./list_kecamatan/kecamatan_kab_semarang.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        nama_wilayah = next(iter(data))
        return data[nama_wilayah]["kecamatan"].get(nama_kecamatan)
    except Exception as e:
        print("JSON error:", e)
        return None


# =====================================================
#  OPTIMIZED REQUEST SESSION (keep-alive pool)
# =====================================================
def create_fast_session():
    s = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=2)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121 Safari/537.36"
    })
    return s


# =====================================================
#  FETCH TAB-4 (KONTAK)
# =====================================================
def fetch_contact(url, selected_fields, session):
    result = {}
    try:
        resp = session.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        if any(f in selected_fields for f in ["Telepon", "Email", "Website"]):
            for row in soup.select("table tr"):
                tds = row.find_all("td")
                if len(tds) >= 4:
                    label = tds[1].get_text(strip=True).lower()
                    val = tds[3].get_text(strip=True)
                    if "telepon" in label:
                        result["Telepon"] = val if len(val) > 4 else "-"
                    elif "email" in label:
                        result["Email"] = val
                    elif "website" in label:
                        result["Website"] = "-" if val in ["http://-", "https://-"] else val
    except Exception:
        pass
    return result


# =====================================================
#  FETCH PROFIL SEKOLAH (Tab-1 redirect)
# =====================================================
def fetch_school_profile(url_tabs, session):
    result = {
        "Alamat": "-", "Kepala Sekolah": "-",
        "Jumlah Siswa Laki-laki": "-", "Jumlah Siswa Perempuan": "-"
    }
    try:
        resp_ref = session.get(url_tabs, timeout=10)
        soup_ref = BeautifulSoup(resp_ref.text, "html.parser")
        link_tag = soup_ref.find("a", href=lambda x: x and "sekolah.data" in x)
        if not link_tag:
            return result

        sekolah_url = link_tag["href"].strip()
        resp = session.get(sekolah_url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        alamat = soup.select_one("font.small")
        if alamat:
            result["Alamat"] = alamat.text.replace("(master referensi)", "").strip()

        for li in soup.select("li.list-group-item"):
            txt = li.get_text(strip=True)
            if "Kepala Sekolah" in txt:
                result["Kepala Sekolah"] = txt.split(":", 1)[-1].strip()
                break

        div_stat = soup.find("div", class_="col-xs-12 col-md-3 text-left")
        if div_stat:
            tag_m = div_stat.find(string=lambda t: "Siswa Laki-laki" in t)
            if tag_m:
                font_m = tag_m.find_next("font", class_="text-info")
                if font_m:
                    result["Jumlah Siswa Laki-laki"] = font_m.text.strip()
            tag_f = div_stat.find(string=lambda t: "Siswa Perempuan" in t)
            if tag_f:
                font_f = tag_f.find_next("font", class_="text-info")
                if font_f:
                    result["Jumlah Siswa Perempuan"] = font_f.text.strip()

    except Exception as e:
        print(f"Gagal ambil profil sekolah: {e}")
    return result


# =====================================================
#  MAIN SCRAPER (tanpa UI)
# =====================================================
def get_sd_mi_schools_fast_local(kode_kecamatan, nama_kecamatan, selected_fields):
    driver = setup_driver_local(True)
    session = create_fast_session()
    sekolah_list, urls = [], []

    need_detail = any(f in selected_fields for f in
                      ["Alamat", "Kepala Sekolah", "Jumlah Siswa Laki-laki",
                       "Jumlah Siswa Perempuan", "Telepon", "Email", "Website"])

    for jenjang, value in [("SD", "5"), ("MI", "9")]:
        url = f"https://referensi.data.kemendikdasmen.go.id/pendidikan/dikdas/{kode_kecamatan}/3/all/{value}/all"
        print(f"Mengambil data {jenjang} - {nama_kecamatan}")
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table#table1 tbody tr")))

        try:
            Select(driver.find_element(By.NAME, "table1_length")).select_by_value("100")
            time.sleep(0.5)
        except:
            pass

        for r in driver.find_elements(By.CSS_SELECTOR, "table#table1 tbody tr"):
            data = {}
            if "Nama Sekolah" in selected_fields:
                data["Nama Sekolah"] = r.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text.strip()
            if "NPSN" in selected_fields:
                data["NPSN"] = r.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
            if "Status" in selected_fields:
                data["Status"] = r.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text.strip()
            if "Kelurahan" in selected_fields:
                data["Kelurahan"] = r.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
            if need_detail:
                link = r.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                urls.append((link, data))
            else:
                sekolah_list.append(data)

    driver.quit()

    if need_detail:
        print(f"Fetch {len(urls)} sekolah secara paralel...")
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = {
                executor.submit(
                    lambda l, base: {
                        **base,
                        **fetch_contact(l, selected_fields, session),
                        **fetch_school_profile(l, session)
                    }, link, base
                ): (link, base) for link, base in urls
            }
            for i, f in enumerate(as_completed(futures), 1):
                sekolah_list.append(f.result())
                if i % 10 == 0:
                    print(f"  → {i}/{len(futures)} sekolah selesai...")

    if selected_fields:
        sort_key = selected_fields[0]
        sekolah_list.sort(key=lambda x: str(x.get(sort_key, "")).lower())

    print(f"Total {len(sekolah_list)} sekolah dari {nama_kecamatan}")
    return sekolah_list


# =====================================================
#  SAVE CSV (Backend callable)
# =====================================================
def scrape_sd_mi_by_kecamatan(nama_kecamatan, selected_fields):
    kode = get_kode_kecamatan_from_json(nama_kecamatan)
    if not kode:
        raise ValueError(f"Kecamatan '{nama_kecamatan}' tidak ditemukan di JSON.")

    start = time.time()
    data = get_sd_mi_schools_fast_local(kode, nama_kecamatan, selected_fields)
    if not data:
        return None, f"Tidak ada data untuk {nama_kecamatan}"

    os.makedirs("output", exist_ok=True)
    path = f"output/list_sd_mi_{nama_kecamatan.lower().replace(' ', '_')}.csv"
    cols = [c for c in [
        "Kelurahan", "Nama Sekolah", "NPSN", "Status", "Kepala Sekolah",
        "Alamat", "Telepon", "Email", "Website",
        "Jumlah Siswa Laki-laki", "Jumlah Siswa Perempuan"
    ] if c in selected_fields]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(data)

    dur = int(time.time() - start)
    print(f"{len(data)} sekolah disimpan ke '{path}' ({dur}s)")
    return path, f"{len(data)} data sekolah berhasil diambil."


# =====================================================
#  CONTOH PENGGUNAAN
# =====================================================
if __name__ == "__main__":
    kecamatan = input("Masukkan nama kecamatan: ").strip()
    selected = ["Nama Sekolah", "NPSN", "Status", "Kepala Sekolah",
                "Alamat", "Telepon", "Email", "Website",
                "Jumlah Siswa Laki-laki", "Jumlah Siswa Perempuan"]
    scrape_sd_mi_by_kecamatan(kecamatan, selected)
