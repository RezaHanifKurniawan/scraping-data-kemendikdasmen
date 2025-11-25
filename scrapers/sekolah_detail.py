import os
import csv
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Selenium imports (standard + fallback)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    STANDARD_SELENIUM_AVAILABLE = True
except Exception:
    STANDARD_SELENIUM_AVAILABLE = False

import undetected_chromedriver as uc
uc.logger.setLevel(logging.ERROR)

# =================== CONFIG ===================
MAX_WORKERS = 12
HEADLESS = True
TIMEOUT_PAGE = 20
# ===============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# =====================================================
#  DRIVER LISTING → UC
# =====================================================
def setup_uc_driver(headless=True):
    opts = uc.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1600,900")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-gpu")

    try:
        driver = uc.Chrome(options=opts)
    except Exception:
        driver = setup_standard_driver(headless)

    driver.set_page_load_timeout(TIMEOUT_PAGE)
    return driver


# =====================================================
#  DRIVER DETAIL → STANDARD SELENIUM
# =====================================================
def setup_standard_driver(headless=True):
    try:
        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1600,900")
        opts.add_argument("--blink-settings=imagesEnabled=false")
        opts.add_argument("--disable-gpu")

        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(TIMEOUT_PAGE)
        return driver
    except Exception as e:
        log.warning(f"Standard Chrome gagal, fallback ke UC: {e}")
        return setup_uc_driver(headless)


# =====================================================
#  BACA JSON KECAMATAN
# =====================================================
def get_kode_kecamatan_from_json(nama_kecamatan, json_path="./list_kecamatan/kecamatan_kab_semarang.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    wilayah = next(iter(data))
    return data[wilayah]["kecamatan"].get(nama_kecamatan)


# =====================================================
#  AUTO DETECT TABEL
# =====================================================
def wait_for_table_rows(driver, timeout=20):
    TABLE_CHOICES = [
        "table#dataTables tbody tr",
        "table#example tbody tr",
        "table#myTable tbody tr",
        "table.table tbody tr",
        "tbody tr"
    ]

    end = time.time() + timeout
    while time.time() < end:
        for sel in TABLE_CHOICES:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, sel)
                if rows:
                    return sel
            except:
                pass
        time.sleep(0.25)

    return None


# =====================================================
#  AUTO RETRY LISTING
# =====================================================
def load_listing_with_retry(driver, url, max_retry=4):
    for attempt in range(1, max_retry + 1):
        log.info(f"[LISTING] Attempt {attempt}/{max_retry}: {url}")

        try:
            driver.get(url)
        except:
            pass

        selector = wait_for_table_rows(driver, timeout=12)
        if selector:
            log.info(f"[LISTING] Tabel ditemukan: {selector}")
            return selector

        log.warning("[LISTING] Tidak muncul, refresh...")
        try:
            driver.refresh()
        except:
            pass

        time.sleep(2)

    return None


# =====================================================
#  SCRAPER DETAIL sekolah.data
# =====================================================
def fetch_detail_worker(npsn_and_base):
    npsn, base = npsn_and_base
    driver = None

    detail = {
        "Alamat": "-",
        "Kepala Sekolah": "-",
        "Telepon": "-",
        "Email": "-",
        "Website": "-",
        "Akreditasi": "-",
        "Yayasan": "-",
        "Jumlah Siswa Laki-laki": "-",
        "Jumlah Siswa Perempuan": "-",
    }

    try:
        driver = setup_standard_driver(headless=HEADLESS)

        search_url = f"https://sekolah.data.kemendikdasmen.go.id/sekolah?keyword={npsn}&page=0&size=12"
        driver.get(search_url)

        try:
            WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.XPATH, "//article")))
        except:
            return base

        articles = driver.find_elements(By.XPATH, "//article")
        target = next((a for a in articles if str(npsn) in a.text), articles[0])

        # klik lihat
        try:
            lihat_btn = target.find_element(By.XPATH, ".//button[contains(.,'Lihat')]")
            driver.execute_script("arguments[0].click();", lihat_btn)
        except:
            return base

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//h1")))
        time.sleep(1.3)  # tunggu Angular

        # Alamat
        try:
            h1 = driver.find_element(By.XPATH, "//h1")
            detail["Alamat"] = h1.find_element(By.XPATH, "following-sibling::p[1]").text.strip()
        except:
            pass

        # INFO GRID
        info_blocks = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'grid') and contains(@class,'gap-x-6')]//div[contains(@class,'flex')]"
        )

        for blk in info_blocks:
            try:
                label = blk.find_element(By.XPATH, ".//div[contains(@class,'text-slate-500')]").text.lower().strip()

                try:
                    value_div = blk.find_element(By.XPATH, ".//div[contains(@class,'font-semibold')]").text.strip()
                except:
                    value_div = ""

                if "akreditasi" in label:
                    detail["Akreditasi"] = value_div

                elif "kepala sekolah" in label:
                    detail["Kepala Sekolah"] = value_div

                elif "yayasan" in label:
                    detail["Yayasan"] = value_div

                elif "telepon" in label:
                    try:
                        detail["Telepon"] = blk.find_element(
                            By.XPATH, ".//a[starts-with(@href,'tel')]"
                        ).text.strip()
                    except:
                        detail["Telepon"] = value_div or "-"

                elif "email" in label:
                    try:
                        detail["Email"] = blk.find_element(
                            By.XPATH, ".//a[starts-with(@href,'mailto')]"
                        ).text.strip()
                    except:
                        detail["Email"] = value_div or "-"

                elif "website" in label:
                    try:
                        href = blk.find_element(By.XPATH, ".//a").get_attribute("href")
                        detail["Website"] = href if href.startswith("http") else "-"
                    except:
                        detail["Website"] = "-"

            except:
                continue

        # Statistik siswa
        stat_blocks = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'rounded-xl')]//div[contains(@class,'px-3')]"
        )

        for s in stat_blocks:
            try:
                lbl = s.find_element(By.XPATH, ".//div[contains(@class,'line-clamp-1')]").text.lower()
                val = s.find_element(By.XPATH, ".//div[contains(@class,'text-2xl')]").text.strip()

                if "laki" in lbl:
                    detail["Jumlah Siswa Laki-laki"] = val
                elif "perempuan" in lbl:
                    detail["Jumlah Siswa Perempuan"] = val

            except:
                continue

        return {**base, **detail}

    except Exception as e:
        log.exception(f"DETAIL ERROR {npsn}: {e}")
        return base

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


# =====================================================
#  SCRAPER LISTING + DETAIL
# =====================================================
def get_sd_mi_schools(kecamatan, selected_fields, json_path="./list_kecamatan/kecamatan_kab_semarang.json"):

    kode = get_kode_kecamatan_from_json(kecamatan, json_path)
    if not kode:
        return []

    list_driver = setup_uc_driver(headless=HEADLESS)
    url = f"https://dapo.kemendikdasmen.go.id/sp/3/{kode}"

    selector = load_listing_with_retry(list_driver, url)
    if not selector:
        return []

    rows = list_driver.find_elements(By.CSS_SELECTOR, selector)
    urls = []
    sekolah_list = []

    need_detail = any(f in selected_fields for f in [
        "Alamat", "Kepala Sekolah", "Telepon", "Email",
        "Website", "Jumlah Siswa Laki-laki",
        "Jumlah Siswa Perempuan", "Akreditasi", "Yayasan"
    ])

    for r in rows:
        cols = r.find_elements(By.TAG_NAME, "td")
        if len(cols) < 5:
            continue

        base = {
            "Nama Sekolah": cols[1].text.strip(),
            "NPSN": cols[2].text.strip(),
            "Status": cols[4].text.strip(),
        }

        if need_detail:
            urls.append((base["NPSN"], base))
        else:
            sekolah_list.append(base)

    list_driver.quit()

    if need_detail:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [ex.submit(fetch_detail_worker, u) for u in urls]
            for fut in as_completed(futures):
                sekolah_list.append(fut.result())

    return sekolah_list


# =====================================================
#  SAVE CSV
# =====================================================
def save_to_csv(kecamatan, selected_fields, outdir="output"):
    os.makedirs(outdir, exist_ok=True)

    data = get_sd_mi_schools(kecamatan, selected_fields)
    if not data:
        return None

    path = f"{outdir}/list_sd_mi_{kecamatan.lower().replace(' ','_')}.csv"

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=selected_fields)
        writer.writeheader()
        writer.writerows(data)

    return path


# =====================================================
#  CONTOH PENGGUNAAN
# =====================================================
if __name__ == "__main__":
    kec = "Bawen"
    fields = [
        "Nama Sekolah","NPSN","Status",
        "Kepala Sekolah","Alamat","Telepon","Email","Website",
        "Jumlah Siswa Laki-laki","Jumlah Siswa Perempuan","Akreditasi","Yayasan"
    ]

    output = save_to_csv(kec, fields)
    print("Saved to:", output)
