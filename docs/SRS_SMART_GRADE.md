# Software Requirements Specification (SRS)
## Proyek RampGradeAI (SMART GRADE Enterprise)
### Sistem Deteksi Kematangan TBS, Mutu Fisik, Tracking Loading Ramp & Ketertelusuran EUDR Berbasis Deep Learning

**Institusi**: Politeknik Citra Widya Edukasi (PCWE), Bekasi  
**Program Riset**: Hibah Riset Sawit / Lomba Riset Mahasiswa BPDP 2026-2027  
**Fokus Riset**: Pasca Panen & Pengolahan Kelapa Sawit (Smart Indicator TBS, Edge Vision & Traceability ISPO/RSPO/EUDR)  
**Status Dokumen**: Comprehensive Engineering Baseline (Waves 1 & 2 Completed)  
**Versi Dokumen**: 2.0.0 (Enterprise Release)

---

## 1. Pendahuluan

### 1.1 Latar Belakang & Masalah Industri
1. **Bias & Subjektivitas Grader Manual**: Berdasarkan investigasi lapangan dan studi empiris (Sutopo et al., 2021; Oyelade et al., 2025), tingkat diskrepansi dan bias grader manusia pada proses sortasi manual di *loading ramp* Pabrik Kelapa Sawit (PKS) mencapai **18.4% – 24.1%**. Hal ini memicu sengketa transparansi harga antara manajemen pabrik dan pekebun swadaya.
2. **Stagnasi Rendemen (OER) & Akumulasi ALB (FFA)**:
   - Masuknya fraksi mentah (*unripe/underripe*) ke sterilizer menyebabkan rendemen CPO (*Oil Extraction Rate*) stagnan di kisaran 19%–21% dan pemborosan uap pemrosesan.
   - Pencampuran buah terlalu matang (*overripe*) dan tandan busuk mengakibatkan hidrolisis enzimatik pascapanen yang mendongkrak Asam Lemak Bebas (*Free Fatty Acid* / FFA) melampaui ambang batas ekspor internasional 5% (Khoo et al., 2021).
3. **Cacat Fisik & Disiplin Panen**: Tandan dengan tangkai panjang (*long stalk* > 5 cm) menyerap minyak pada proses peremasan, sementara tandan kosong (*empty bunch*) dan abnormalitas buah menurunkan kapasitas olah pabrik.
4. **Regulasi Ketat EUDR & Sertifikasi Keberlanjutan**: Pemberlakuan *European Union Deforestation Regulation* (EUDR 2023/1115) dan mandat ISPO/RSPO mewajibkan penyertaan poligon geolokasi WGS84 asal kebun yang bebas deforestasi (cut-off 31 Desember 2020) per pengiriman tandan sawit (Pacheco et al., 2024).

### 1.2 Tujuan Sistem RampGradeAI
1. Mengotomatisasi inspeksi mutu dan klasifikasi kematangan TBS secara *real-time* (< 30 ms per frame streaming, < 400 ms per foto statis) menggunakan model komputer visi teroptimasi.
2. Mendeteksi **6 kelas standar kematangan dan kelainan fisik PPKS/IOPRI**:
   - `ripe` (Matang)
   - `underripe` (Kurang Matang)
   - `unripe` (Mentah)
   - `overripe` (Terlalu Matang / Lewat Masak)
   - `empty_bunch` (Tandan Kosong)
   - `abnormal` (Tandan Abnormal / Busuk / Partenokarpi)
   serta kalkulasi penalti tangkai panjang (*long stalk*).
3. Melacak dan menghitung TBS saat dijatuhkan dari bak truk ke hopper menggunakan algoritma **ByteTrack Spatial Multi-Object Tracking** dan **Virtual Tripwire**.
4. Melakukan normalisasi citra adaptif terhadap pencahayaan ekstrem lapangan menggunakan **CLAHE (Contrast Limited Adaptive Histogram Equalization)** pada kanal Luminansi LAB.
5. Menyediakan kalkulator **Dynamic Fair-Pricing** transparan sesuai pedoman Permentan No. 01/2018 untuk mencegah sengketa harga dengan petani swadaya.
6. Menyediakan portal transparansi pekebun (**Farmer Transparency Portal PWA**), sertifikat digital terverifikasi QR code (**ReportLab PDF Certificate**), dan **Lembar Hasil Penimbangan (LHP) Excel Exporter**.
7. Menghubungkan seluruh data grading dengan koordinat poligon WGS84 kebun (**EUDR & ISPO Compliance**).
8. Mengimplementasikan siklus **Active Learning & Edge MLOps** untuk peningkatan akurasi model mandiri di edge server PKS.

---

## 2. Kebutuhan Fungsional (Functional Requirements - FR)

### Modul 1: Vision Engine & Image Preprocessing
* **FR-01 (Adaptive Lighting CLAHE)**: Sistem harus menerapkan normalisasi CLAHE pada ruang warna CIE LAB sebelum inferensi untuk mereduksi pengaruh bayangan tajam dan sinar matahari langsung pada ramp terbuka.
* **FR-02 (Multi-Class Defect & Ripeness Detection)**: Sistem mampu mendeteksi bounding box, label kelas, dan skor kepercayaan untuk 6 kelas standar (ripe, underripe, unripe, overripe, empty bunch, abnormal).
* **FR-03 (Dual-Engine Inference Deployment)**: Sistem mendukung inferensi berbasis PyTorch Ultralytics dan runtime ONNX berakselerasi DirectML/OpenVINO/CPU untuk efisiensi edge hardware.
* **FR-04 (Heuristic Long Stalk Detection)**: Sistem mendeteksi rasio aspek bounding box untuk mengidentifikasi keberadaan tangkai panjang (> 5 cm) yang melanggar SOP panen.

### Modul 2: Dynamic Tracking & Virtual Tripwire
* **FR-05 (ByteTrack Spatial Multi-Object Tracking)**: Sistem melacak pergerakan tandan buah saat meluncur di hopper dengan ID unik konstan antar frame.
* **FR-06 (Bidirectional Virtual Tripwire)**: Sistem menyediakan garis pembatas virtual yang dapat dikonfigurasi posisinya pada kanvas video. Setiap tandan yang melintasi tripwire dihitung satu kali (*no double counting*).

### Modul 3: Dynamic Fair-Pricing & Quality Formulation
* **FR-07 (OER Estimation)**: Sistem menghitung estimasi rendemen minyak (OER) terbobot berdasarkan distribusi persentase kematangan per truk.
* **FR-08 (Penalti Mutu Progresif)**: Sistem menerapkan potongan penalti harga berdasarkan persentase buah mentah ($100\%$ penalti), kurang matang (di atas ambang 5%), tangkai panjang, dan tandan kosong sesuai Permentan No. 01/2018.
* **FR-09 (Simulasi Payout)**: Sistem menghitung harga bersih per kilogram dan total pembayaran rupiah berdasarkan berat bersih timbangan jembatan timbang.

### Modul 4: Traceability & EUDR GeoJSON Compliance
* **FR-10 (Registrasi Petani & Sertifikasi)**: Sistem mengelola data pekebun (NIK, nama, nomor telepon, koperasi, status ISPO/RSPO).
* **FR-11 (WGS84 Polygon Mapping)**: Sistem menyimpan dan memvisualisasikan poligon batas kebun (GeoJSON Polygon) serta menghitung kepatuhan EUDR (titik koordinat lengkap, area hektar, tahun tanam).
* **FR-12 (Penerimaan SPB & Immutable Audit)**: Setiap sesi grading terkunci ke nomor Surat Pengantar Buah (SPB) dan ID pengiriman.

### Modul 5: Dokumentasi Digital, Pelaporan, & Farmer Transparency
* **FR-13 (Digital PDF Certificate with Dynamic QR Code)**: Sistem mengenerate sertifikat digital resmi hasil grading berformat PDF dengan QR Code yang dapat dipindai oleh auditor atau petani untuk verifikasi integritas data.
* **FR-14 (Excel LHP Exporter)**: Sistem mengekspor laporan grading harian dalam format spreadsheet Lembar Hasil Penimbangan (LHP) berstandar pabrik sawit.
* **FR-15 (Farmer Transparency Portal PWA)**: Petani dapat mengakses portal swadaya berbasis web/PWA untuk mengecek hasil sortasi truk mereka secara real-time.

### Modul 6: Streaming Real-Time & Edge Resilience
* **FR-16 (WebSocket Binary Streaming)**: Endpoint `/ws-stream` menyediakan transmisi frame terdeteksi dan metadata telemetri FPS/latency secara biner melalui WebSocket dua arah.
* **FR-17 (Industrial RTSP Camera Worker)**: Sistem memiliki background worker multithreaded dengan reconnection otomatis untuk menangkap streaming CCTV IP camera H.264/RTSP.
* **FR-18 (Offline-First Sync Manager)**: Sistem menyimpan data grading ke local storage/SQLite saat jaringan internet terputus dan melakukan sinkronisasi otomatis ke cloud server saat konektivitas pulih.

### Modul 7: Edge MLOps & Active Learning
* **FR-19 (Uncertainty Ingestion)**: Sistem secara otomatis menandai citra dengan tingkat kepercayaan marjinal ($0.30 \le \text{confidence} \le 0.60$) ke dalam antrean review Active Learning.
* **FR-20 (Manual Relabel & Fine-Tuning Trigger)**: Operator ahli dapat melakukan re-labeling bounding box dan memicu proses fine-tuning model latar belakang (*background retrain task*).

---

## 3. Kebutuhan Non-Fungsional (Non-Functional Requirements - NFR)

* **NFR-01 (Inference Latency)**: Latensi inferensi video streaming $\le 30\text{ ms}$ per frame pada akselerator GPU/NPU dan $\le 400\text{ ms}$ pada CPU standar.
* **NFR-02 (Akurasi Deteksi)**: Nilai $mAP@0.5 \ge 0.92$ pada 6 kelas uji validasi.
* **NFR-03 (Edge Reliability)**: Sistem mampu beroperasi penuh 24/7 di remote area tanpa ketergantungan koneksi internet (*full offline autonomous operation*).
* **NFR-04 (Keamanan & Integritas Data)**: Sertifikat PDF menyertakan cryptographic verification hash; rekaman grading berstatus read-only pasca-komitmen.
* **NFR-05 (UI Accessibility & Taste-Skill)**: Tampilan visual mematuhi WCAG AA contrast, optical density layout, mobile-first responsive PWA, dan bebas elemen generik AI slop.

---

## 4. Formulasi Matematis & Domain Engineering

### 4.1 Estimasi Oil Extraction Rate (OER)
Formula rendemen minyak empiris terbobot ($\widehat{\text{OER}}$) dengan penyesuaian fraksi cacat:
$$\widehat{\text{OER}} (\%) = (0.12 \cdot P_{\text{unripe}}) + (0.17 \cdot P_{\text{underripe}}) + (0.235 \cdot P_{\text{ripe}}) + (0.21 \cdot P_{\text{overripe}}) + (0.00 \cdot P_{\text{empty}}) + (0.05 \cdot P_{\text{abnormal}})$$

### 4.2 Indeks Mutu TBS ($Q_{\text{score}}$)
$$Q_{\text{score}} = \max\left(0.0, \frac{1.0 \cdot n_{\text{ripe}} + 0.7 \cdot n_{\text{underripe}} + 0.4 \cdot n_{\text{overripe}} - 0.5 \cdot n_{\text{empty}} - 0.3 \cdot n_{\text{abnormal}}}{N}\right)$$

### 4.3 Potongan Penalti Harga Sesuai Permentan No. 01/2018
$$\text{Penalty}_{\text{total}} (\%) = \alpha_{\text{unripe}} \cdot P_{\text{unripe}} + \beta_{\text{underripe}} \cdot \max(0, P_{\text{underripe}} - 5\%) + \gamma_{\text{stalk}} \cdot P_{\text{stalk}} + \delta_{\text{empty}} \cdot P_{\text{empty}}$$

### 4.4 Estimasi Payout Petani
$$\text{Harga Bersih (Rp/Kg)} = \text{Harga Patokan Disbun} \times \left(1 - \frac{\text{Penalty}_{\text{total}}}{100}\right)$$
$$\text{Total Payout (Rp)} = \text{Berat Netto Timbangan (Kg)} \times \text{Harga Bersih (Rp/Kg)}$$

---

## 5. Matriks Ketertelusuran Regulasi (EUDR, ISPO, RSPO)

| Komponen Audit | Standar RSPO / ISPO | Regulasi EUDR (2023/1115) | Implementasi RampGradeAI |
| :--- | :--- | :--- | :--- |
| **Identitas Pekebun** | KTP, Kelompok Tani, Sertifikat | Operator & Trader ID | `Farmer.farmer_code`, `Farmer.nik`, `Farmer.cooperative_name` |
| **Batas Geospasial** | Titik pusat & batas blok | Poligon WGS84 GeoJSON presisi | `PlantationBlock.boundary_geojson`, `PlantationBlock.latitude/longitude` |
| **Deforestasi Cut-off** | 2005 / 2014 cut-off | 31 Desember 2020 cut-off | `PlantationBlock.planting_year`, `PlantationBlock.eudr_compliant` |
| **Bukti Pengiriman** | SPB fisik tercatat | Due Diligence Reference | `DeliveryOrder.spb_number`, `DeliveryOrder.truck_plate_number` |
| **Verifikasi Lapangan** | Berita Acara Grading | Digital Verification Audit | Digital Certificate PDF + Dynamic QR Code Verification Hash |
