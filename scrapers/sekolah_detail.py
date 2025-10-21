import json
import csv
import os
from pandas import options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


# ==========================
# 🔧 Setup Driver
# ==========================
def setup_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def get_table_rows(driver, url):
    """Helper untuk ambil semua baris dari tabel referensi"""
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table#table1 tbody tr"))
    )
    try:
        select = Select(driver.find_element(By.NAME, "table1_length"))
        select.select_by_value("100")
    except:
        pass
    return driver.find_elements(By.CSS_SELECTOR, "table#table1 tbody tr")

# ==========================
#  Ambil Kode Kecamatan dari JSON
# ==========================
def get_kode_kecamatan_from_json(nama_kecamatan, json_path="../list_kecamatan/kecamatan_kab_semarang.json"):
    try:
        # Buka file JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            print("File JSON kosong.")
            return None

        nama_wilayah = next(iter(data))
        kabupaten_data = data[nama_wilayah].get("kecamatan", {})

        # Cari kecamatan
        for nama, kode in kabupaten_data.items():
            if nama.lower() == nama_kecamatan.lower():
                return kode

        print(f"Kecamatan '{nama_kecamatan}' tidak ditemukan di {nama_wilayah}.")
        return None

    except FileNotFoundError:
        print(f"File JSON '{json_path}' tidak ditemukan.")
        return None

    except Exception as e:
        print(f"Error saat membaca JSON: {e}")
        return None



# ==========================
# 🔍 Ambil data Siswa Laki-laki, Kepsek, Alamat dari website sekolah kita kemendikbud
# ==========================
def get_detail(driver):
    alamat, kepsek, siswa_laki, siswa_perempuan = "-", "-", "-", "-"

    try:
        # Tunggu tab identitas muncul
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='tab-1']"))
        )
        rows_identitas = driver.find_elements(By.CSS_SELECTOR, "div.tabby-content table tr")

        for rp in rows_identitas:
            tds = rp.find_elements(By.CSS_SELECTOR, "td")
            if len(tds) < 4:
                continue

            link_elem = tds[3].find_elements(By.TAG_NAME, "a")
            if not link_elem:
                continue

            link_kemdikbud = link_elem[0].get_attribute("href")

            #  Buka halaman sekolah.data.kemdikbud.go.id
            driver.execute_script("window.open(arguments[0]);", link_kemdikbud)
            driver.switch_to.window(driver.window_handles[-1])

            try:
                # Tunggu halaman profil terbuka
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h4.page-header"))
                )

                #  Ambil alamat
                try:
                    alamat_elem = driver.find_element(By.CSS_SELECTOR, "font.small")
                    # Bersihkan teks tambahan seperti "(master referensi)"
                    alamat_elem = alamat_elem.replace("(master referensi)", "").text.strip()
                    alamat = alamat_elem if alamat_elem else "-"
                except:
                    alamat = "-"

                #  Ambil Kepala Sekolah
                try:
                    kepsek_elem = driver.find_element(
                        By.XPATH, "//li[contains(., 'Kepala Sekolah')]"
                    )
                    kepsek = kepsek_elem.text.split(":", 1)[-1].strip()
                except:
                    kepsek = "-"

                #  Ambil jumlah siswa laki-laki
                try:
                    siswa_laki_elem = driver.find_element(
                        By.XPATH,
                        "//text()[contains(., 'Siswa Laki-laki')]/following::font[1]"
                    )
                    siswa_laki = siswa_laki_elem.text.strip()
                except:
                    siswa_laki = "-"
                    
                # Ambil jumlah siswa perempuan 
                try:
                    siswa_perempuan_elem = driver.find_element(
                        By.XPATH,
                        "//text()[contains(., 'Siswa Perempuan')]/following::font[1]"
                    )
                    siswa_perempuan = siswa_perempuan_elem.text.strip()
                except:
                    siswa_perempuan = "-"

            except Exception as e:
                print(f"Gagal ambil data di sekolah.data.kemdikbud.go.id: {e}")

            # Tutup tab & kembali ke tab utama
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])
            break

    except Exception as e:
        print(f"Gagal proses tab identitas: {e}")

    return alamat, kepsek, siswa_laki, siswa_perempuan


# ==========================
#  Ambil data kontak Referensi Data Kemendikbud
# ==========================
def get_kontak(driver):
    telepon, email, website = "-", "-", "-"
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='tab-4']"))
        )
        driver.find_element(By.CSS_SELECTOR, "label[for='tab-4']").click()
        rows_kontak = driver.find_elements(By.CSS_SELECTOR, "div.tabby-content table tr")

        for row in rows_kontak:
            tds = row.find_elements(By.CSS_SELECTOR, "td")
            if len(tds) < 4:
                continue
            label = tds[1].text.strip().lower()
            value = tds[3].text.strip() or "-"
            if "telepon" in label:
                telepon = value if len(value) >= 5 else "-"
            elif "email" in label:
                email = value
            elif "website" in label:
                val = value.lower()
                website = "-" if val in ["http://-", "https://-"] else val
    except:
        pass
    return telepon, email, website


# ==========================
#  Ambil Daftar Sekolah (SD & MI) dari Referensi Data Kemendikbud
# ==========================
def get_sd_mi_schools(kode_kecamatan, nama_kecamatan):
    driver = setup_driver(headless=True)
    sekolah_list = []

    for jenjang, value in [("SD", "5"), ("MI", "9")]:
        url = f"https://referensi.data.kemendikdasmen.go.id/pendidikan/dikdas/{kode_kecamatan}/3/all/{value}/all"
        print(f"Mengambil data {jenjang} dari: {url}")
        try:
            driver.get(url)
            WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table#table1"))
            )

            # Ubah tampilan jadi 100 baris
            get_table_rows(driver, url)

            rows = driver.find_elements(By.CSS_SELECTOR, "table#table1 tbody tr")
            if not rows:
                print(f"Tidak ada data {jenjang} di {nama_kecamatan}")
                continue

            for r in rows:
                try:
                    nama = r.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text.strip()
                    npsn = r.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                    status = r.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text.strip()
                    kelurahan = r.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
                    href = r.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                    # Buka halaman detail
                    driver.execute_script("window.open(arguments[0]);", href)
                    driver.switch_to.window(driver.window_handles[-1])

                    alamat, kepsek, siswa_laki, siswa_perempuan = get_detail(driver)
                    telepon, email, website = get_kontak(driver)

                    sekolah_list.append({
                        "Kelurahan": kelurahan,
                        "Nama Sekolah": nama,
                        "NPSN": npsn,
                        "Status": status,
                        "Kepala Sekolah": kepsek,
                        "Alamat": alamat,
                        "Telepon": telepon,
                        "Email": email,
                        "Website": website,
                        "Jumlah Siswa Laki-laki": siswa_laki,
                        "Jumlah Siswa Perempuan": siswa_perempuan,
                    })

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    print(f"Gagal proses {nama}: {e}")
                    continue

            print(f"{len(rows)} sekolah {jenjang} di {nama_kecamatan}")

        except Exception as e:
            print(f"Gagal ambil data {jenjang} di {nama_kecamatan}: {e}")
            continue

    driver.quit()
    # 🧩 SORTING berdasarkan nama kelurahan
    sekolah_list = sorted(sekolah_list, key=lambda x: x["Kelurahan"].lower())
    return sekolah_list


# ==========================
#  Simpan ke CSV
# ==========================
def save_school_list_by_kecamatan(nama_kecamatan):
    nama_kecamatan = nama_kecamatan.strip()
    kode_kecamatan = get_kode_kecamatan_from_json(nama_kecamatan)
    if not kode_kecamatan:
        return

    print(f"Mengambil daftar SD & MI di Kecamatan {nama_kecamatan} (kode {kode_kecamatan})...")
    sekolah_list = get_sd_mi_schools(kode_kecamatan, nama_kecamatan)

    if not sekolah_list:
        print(f"Tidak ditemukan SD atau MI di {nama_kecamatan}.")
        return

    folder = "output"
    os.makedirs(folder, exist_ok=True)
    filename = f"list_sd_mi_{nama_kecamatan.lower().replace(' ', '_')}.csv"
    fullpath = os.path.join(folder, filename)

    with open(fullpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Kelurahan", "Nama Sekolah", "NPSN", "Status", "Kepala Sekolah", "Alamat", "Telepon", "Email", "Website", "Jumlah Siswa Laki-laki", "Jumlah Siswa Perempuan"
        ])
        writer.writeheader()
        writer.writerows(sekolah_list)

    print(f"✅ {len(sekolah_list)} sekolah disimpan ke '{fullpath}'")


if __name__ == "__main__":
    nama_kecamatan = "Ambarawa"
    save_school_list_by_kecamatan(nama_kecamatan)