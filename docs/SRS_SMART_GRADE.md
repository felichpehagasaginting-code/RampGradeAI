# Software Requirements Specification (SRS)
## Proyek SMART GRADE: Sistem Deteksi Kematangan TBS (Smart Indicator) & Ketertelusuran Rantai Pasok Berbasis Deep Learning

**Institusi**: Politeknik Citra Widya Edukasi (PCWE), Bekasi  
**Program Riset**: Usulan Lomba Riset Mahasiswa BPDP 2026–2027  
**Fokus Riset**: Pasca Panen & Pengolahan Kelapa Sawit (Smart Indicator & Traceability IoT/AI)  
**Status Dokumen**: Spesifikasi Kebutuhan Purwarupa Awal (Preliminary Prototype - TRL 3)  
**Versi Dokumen**: 1.5.0 (Selaras Proposal Riset BPDP)

---

## 1. Pendahuluan

### 1.1 Latar Belakang & Masalah
1. **Keterbatasan Grading Manual**: Proses penentuan fraksi kematangan Tandan Buah Segar (TBS) di *loading ramp* jembatan timbang Pabrik Kelapa Sawit (PKS) saat ini mengandalkan inspeksi visual manual oleh petugas grader. Metode ini rentan terhadap variasi subjektif antar individu dan kelelahan fisik saat antrean truk tinggi.
2. **Korelasi Fraksi terhadap Rendemen (OER) & Asam Lemak Bebas (FFA)**:
   - Buah mentah (*unripe*) dan kurang matang (*underripe*) memiliki kandungan minyak mesokarp yang belum sempurna sehingga menekan perolehan OER pabrik (nasional stagnan di kisaran 19%–21%).
   - Buah terlalu matang (*overripe*) memicu lonjakan asam lemak bebas (*Free Fatty Acid* / FFA) akibat hidrolisis enzimatik yang merugikan mutu CPO.
3. **Tuntutan Ketertelusuran (Traceability)**: Penerapan sertifikasi ISPO/RSPO dan regulasi global EUDR (2023/1115) menuntut integrasi pencatatan mutu buah dengan identitas pekebun dan geolokasi blok kebun asal.

### 1.2 Tujuan Sistem Purwarupa
1. Mengembangkan purwarupa awal alat deteksi kematangan TBS secara *real-time* berbasis visi komputer deep learning (keluarga arsitektur YOLO).
2. Mengklasifikasikan TBS ke dalam **4 kelas fraksi kematangan standar IOPRI (1997)**:
   - **Mentah (Unripe)**
   - **Kurang Matang (Underripe)**
   - **Matang (Ripe)**
   - **Terlalu Matang (Overripe)**
3. Menghitung estimasi *Oil Extraction Rate* (OER) terbobot berdasarkan formula baseline heuristik agronomi.
4. Menghubungkan sesi penilaian grading dengan nomor Surat Pengantar Buah (SPB), data petani, dan titik/poligon kebun asal.

---

## 2. Kebutuhan Fungsional (Functional Requirements - FR)

### Modul 1: Image Acquisition & Inference Engine
* **FR-01**: Sistem mampu menerima input citra berupa unggahan foto digital (`.jpg`, `.jpeg`, `.png`) dari kamera *loading ramp*.
* **FR-02**: Sistem menjalankan inferensi model YOLOv8 (format PyTorch `.pt` dan ONNX) dengan output *bounding box*, label fraksi kematangan, dan *confidence score*.
* **FR-03**: Sistem menerapkan filter batas kepercayaan (*confidence thresholding* $\ge 0.40$) dan *Non-Maximum Suppression* (NMS IoU $\ge 0.45$).
* **FR-04**: Jika citra tidak memuat objek TBS, sistem secara jujur mengembalikan hasil deteksi kosong (`[]`) tanpa mengarang objek acak.

### Modul 2: Decision Support & Estimasi OER
* **FR-05**: Sistem menghitung distribusi persentase fraksi kematangan ($P_{\text{unripe}}, P_{\text{underripe}}, P_{\text{ripe}}, P_{\text{overripe}}$).
* **FR-06**: Sistem menghitung estimasi OER batch menggunakan formula baseline heuristik terbobot.
* **FR-07**: Sistem menyediakan kalkulasi simulasi penalti mutu sesuai pedoman Permentan No. 01/2018 sebagai bahan evaluasi transparansi penetapan harga.

### Modul 3: Manajemen Ketertelusuran (Traceability)
* **FR-08**: Sistem mencatat master data Petani (ID Petani, Nama, NIK, Koperasi/Kelompok Tani, Status Sertifikasi ISPO/RSPO).
* **FR-09**: Sistem mencatat master data Blok Kebun (ID Blok, Luas Hektar, Titik Koordinat Lat/Long, Poligon WGS84 GeoJSON).
* **FR-10**: Sistem mencatat transaksi Penerimaan TBS / Surat Pengantar Buah (SPB) terhubung ke nomor polisi truk dan bobot netto timbangan.
* **FR-11**: Setiap sesi grading tertaut secara unik (*foreign key*) ke nomor tiket SPB, menghasilkan log audit yang tidak dapat dimanipulasi.

### Modul 4: Antarmuka Dashboard & Pelaporan
* **FR-12**: Menampilkan dashboard operator yang memvisualisasikan citra hasil deteksi, rincian hitungan TBS per fraksi, dan estimasi OER.
* **FR-13**: Menyediakan riwayat sesi grading yang dapat dicari berdasarkan nomor SPB atau nama petani.
* **FR-14**: Menyediakan fitur ekspor sertifikat hasil grading berformat PDF dilengkapi kode QR untuk verifikasi data.

---

## 3. Kebutuhan Non-Fungsional (Non-Functional Requirements - NFR)

* **NFR-01 (Inference Latency Target)**: Waktu inferensi $\le 1.0\text{ detik}$ per citra resolusi $640\times 640$ pada perangkat CPU/GPU standar.
* **NFR-02 (Akurasi Target Riset)**: Target capaian model final pada data primer lapangan adalah $mAP@0.5 \ge 0.90$.
* **NFR-03 (Offline / Edge Capable)**: Backend dan inference engine dapat beroperasi secara mandiri di jaringan lokal (*local intranet*) PKS tanpa ketergantungan internet kontinu.
* **NFR-04 (Integritas Data)**: Sistem menyimpan metadata waktu presisi dan versi model pada setiap rekaman sesi grading.

---

## 4. Formulasi Matematis Baseline (IOPRI 1997 & Wood et al.)

### 4.1 Distribusi Fraksi Kematangan
Untuk total deteksi tandan $N = \sum_{k} n_k$, di mana $k \in \{\text{unripe}, \text{underripe}, \text{ripe}, \text{overripe}\}$:
$$P_k = \frac{n_k}{N} \times 100\%$$

### 4.2 Formula Estimasi OER Baseline
$$\widehat{\text{OER}} (\%) = (0.12 \cdot P_{\text{unripe}}) + (0.17 \cdot P_{\text{underripe}}) + (0.235 \cdot P_{\text{ripe}}) + (0.21 \cdot P_{\text{overripe}})$$
> *Catatan: Koefisien rendemen ini merupakan parameter baseline heuristik yang akan dikalibrasi ulang secara empiris menggunakan data uji laboratorium Soxhlet di PKS mitra selama periode riset BPDP.*

---

## 5. Matriks Ketertelusuran Regulasi

| Parameter Kebutuhan | Standar ISPO / RSPO | Regulasi EUDR (2023/1115) | Field Data SMART GRADE |
| :--- | :--- | :--- | :--- |
| **Identitas Pekebun** | Nama & Kelompok Tani | Operator Legal Entity | `Farmer.name`, `Farmer.nik` |
| **Geolokasi Lahan** | Titik pusat & luas blok | Poligon WGS84 perimeter | `PlantationBlock.boundary_geojson` |
| **Tahun Tanam** | Legalitas budidaya | Cut-off deforestasi 2020 | `PlantationBlock.planting_year` |
| **Bukti Pengiriman** | Surat Pengantar Buah | Reference Tracking Number | `DeliveryOrder.spb_number` |
| **Kualitas TBS** | Fraksi mutu pabrik | Spesifikasi mutu komoditas | `GradingSession.counts`, `OERAssessment` |
