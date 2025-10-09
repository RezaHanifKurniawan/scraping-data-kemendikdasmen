import requests
import json

# ==========================
# 1️⃣ Ambil Tahun yang Tersedia
# ==========================
def get_tahun():
    url = "https://sipedas.pertanian.go.id/api/wilayah/list_thn"
    resp = requests.get(url)
    resp.raise_for_status()
    tahun = resp.json()
    print("📅 Tahun tersedia:")
    return tahun

# ==========================
# 2️⃣ Ambil Daftar Provinsi berdasarkan Tahun
# ==========================
def get_provinsi(tahun):
    url = f"https://sipedas.pertanian.go.id/api/wilayah/list_pro?thn={tahun}"
    resp = requests.get(url)
    resp.raise_for_status()
    provinsi = resp.json()

    print(f"✅ Total provinsi: {len(provinsi)}")
    return provinsi

# ==========================
# 3️⃣ Ambil Daftar Kabupaten berdasarkan Provinsi
# ==========================
def get_kabupaten(tahun, prov_id):  # 33 = Jawa Tengah
    url = f"https://sipedas.pertanian.go.id/api/wilayah/list_kab?thn={tahun}&pro={prov_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    kabupaten = resp.json()

    print(f"✅ Total kabupaten di provinsi {prov_id}: {len(kabupaten)}")
    return kabupaten

# ==========================
# 4️⃣ Ambil Daftar Kecamatan per Kabupaten
# ==========================
def get_kecamatan(tahun, prov_id, kab_id):  # 33=Jateng, 22=Kab Semarang
    url = f"https://sipedas.pertanian.go.id/api/wilayah/list_kec?thn={tahun}&pro={prov_id}&kab={kab_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    kecamatan = resp.json()
    
    print(f"✅ Total kecamatan di kabupaten {kab_id}: {len(kecamatan)}")
    return kecamatan

# ==========================
# Simpan daftar ke file JSON
# ==========================
def save_to_json(data, filename):
    hasil = {
        "Kabupaten Semarang": {
            "kecamatan": [v for v in data.values()]
        }
    }
    # Simpan ke JSON
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)

    print(f"💾 Data kecamatan disimpan ke '{filename}'")
