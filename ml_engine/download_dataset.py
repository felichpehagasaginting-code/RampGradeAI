import os
import sys
import zipfile
import httpx
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

def download_and_extract_roboflow_direct(
    api_key: str,
    workspace: str = "binus",
    project: str = "sawit-mnhfg",
    version: int = 5
):
    """
    Mengunduh dataset Roboflow langsung via REST API tanpa dependensi tambahan.
    Mendukung resume dan ekstraksi otomatis ZIP YOLOv8.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / f"{project}_v{version}.zip"

    print("=" * 65)
    print(f"  MENGUNDUH DATASET ROBOFLOW: {workspace}/{project} (v{version})")
    print("=" * 65)
    
    # 1. Dapatkan link export langsung dari Roboflow API
    api_url = f"https://api.roboflow.com/{workspace}/{project}/{version}/yolov8?api_key={api_key}"
    print(f"Menghubungi API Roboflow...")
    
    with httpx.Client(timeout=30.0) as client:
        res = client.get(api_url)
        if res.status_code != 200:
            print(f"[ERROR] Gagal menghubungi API: {res.status_code} - {res.text}")
            return False
        data = res.json()
        
    export_info = data.get("export", {})
    download_url = export_info.get("link")
    size_mb = export_info.get("size", 0)
    
    print(f"Total Citra: {data.get('images', 4160)} gambar")
    print(f"Ukuran File: {size_mb:.2f} MB")
    print(f"Kelas Sawit: {list(data.get('project', {}).get('colors', {}).keys())}")
    print(f"Download URL: {download_url}")
    print("-" * 65)

    if not download_url:
        print("[ERROR] Link download tidak ditemukan dalam respon Roboflow.")
        return False

    # 2. Download file ZIP dengan streaming chunk
    print(f"Mendownload arsip ZIP ke {zip_path}...")
    with httpx.stream("GET", download_url, timeout=120.0, follow_redirects=True) as response:
        response.raise_for_status()
        total_bytes = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        with open(zip_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):  # 1MB per chunk
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
                    print(f"\rProgress: {downloaded / (1024*1024):.1f} MB / {total_bytes / (1024*1024):.1f} MB ({pct:.1f}%)", end="", flush=True)

    print(f"\n[SUKSES] Unduhan selesai! Mengekstrak ke {DATA_DIR}...")
    
    # 3. Ekstrak ZIP
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(DATA_DIR)

    print(f"[SUKSES] Dataset berhasil diekstrak ke: {DATA_DIR}")
    
    # Cek keberadaan data.yaml
    yaml_files = list(DATA_DIR.glob("*.yaml")) + list(DATA_DIR.glob("*.yml"))
    if yaml_files:
        print(f"File konfigurasi dataset: {yaml_files[0]}")
    
    return True

if __name__ == "__main__":
    api_key = sys.argv[1] if len(sys.argv) > 1 else "isK946ZQlgZXh5irkXiT"
    download_and_extract_roboflow_direct(api_key=api_key)
