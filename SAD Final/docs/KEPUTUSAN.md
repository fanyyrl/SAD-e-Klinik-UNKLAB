# Dokumentasi Keputusan Desain & Asumsi (docs/KEPUTUSAN.md)
Sistem Informasi e-Klinik UNKLAB (Universitas Klabat)

Dokumen ini mencatat keputusan teknis, arsitektur, dan asumsi yang diambil selama pengembangan e-Klinik UNKLAB sesuai prinsip Prototyping dan aturan bisnis yang ditetapkan.

---

### 1. Zona Waktu dan Lokasi
- **Keputusan**: Menggunakan `TIME_ZONE = 'Asia/Makassar'` (WITA, UTC+8).
- **Alasan**: Universitas Klabat berlokasi di Airmadidi, Minahasa Utara, Sulawesi Utara yang berada di zona Waktu Indonesia Tengah (WITA). Reset nomor antrean harian dan pencatatan waktu kunjungan menggunakan waktu lokal WITA agar akurat.

### 2. Autentikasi dan Model Akun (`Pengguna`)
- **Keputusan**: Mewarisi `AbstractUser` Django dengan nama tabel `pengguna` dan primary key `id_pengguna`. Kolom `status_aktif` disinkronkan dengan `is_active` bawaan Django.
- **Peran Akses**:
  - `staf_klinik`: Akses operasional pendaftaran pasien, verifikasi, antrean FIFO, TTV, dan stok obat.
  - `dokter`: Akses pemeriksaan klinis, rekam medis rahasia, ICD-10, tindakan, resep digital, dan lampiran laboratorium.
- **Enforcement Keamanan**: Dilakukan di tingkat server menggunakan decorator `@role_required(['staf_klinik'])` dan `@role_required(['dokter'])`. Jika ada upaya akses lintas peran, server langsung mengembalikan HTTP 403 Forbidden.

### 3. Enkripsi Field Medis (SR-02 / NFR-02)
- **Keputusan**: Menggunakan `EncryptedTextField` berbasis modul `cryptography.fernet.Fernet`.
- **Kolom yang Dienkripsi**:
  1. `anamnesis_lanjutan` (Pemeriksaan)
  2. `riwayat_konsumsi_obat` (Pemeriksaan)
  3. `pemeriksaan_fisik` (Pemeriksaan)
  4. `keluhan_utama` (Kunjungan)
  5. `catatan_tindakan` (Tindakan)
  6. `catatan_eskalasi` (TandaVital)
  7. `hasil_lab` (HasilLab)
  8. `reaksi` (AlergiPasien)
- **Mekanisme**: Ciphertext diawali token standar Fernet (`gAAAAA`). Data disimpan terenkripsi di SQLite/MySQL, dan otomatis didekripsi saat diakses di model layer Python. Kunci enkripsi dibaca dari variabel lingkungan `FIELD_ENCRYPTION_KEY`.

### 4. Nomor Antrean Digital FIFO (BR-01, UC-06, UC-07)
- **Keputusan**: Nomor antrean berupa urutan bilangan bulat harian (1, 2, 3, ...) yang dihitung berdasarkan jumlah kunjungan pada tanggal kalender yang sama (`tanggal_waktu__date = today`).
- **Urutan Pemanggilan**: Berdasarkan FIFO waktu kedatangan (`tanggal_waktu`).
- **Penanganan Pasien Ditunda**: Pasien dengan status `ditunda` tetap mempertahankan posisi waktu kedatangan aslinya (`tanggal_waktu`) saat dipanggil kembali atau diurutkan.
- **Prioritas Abnormal TTV**: Pasien dengan tanda vital abnormal diberi penanda visual (badge merah `PRIORITAS TTV ABNORMAL`) pada antrean, namun urutan antrean FIFO tidak diubah secara artifisial, melainkan menjadi perhatian segera bagi dokter dan staf.

### 5. Pencocokan Alergi Obat (UC-16, DIR-02)
- **Keputusan**: Pencocokan dilakukan dua lapis (client-side warning saat memilih obat + server-side validation saat submit resep).
- **Kriteria Pencocokan**:
  - Mencocokkan nama alergen pasien bertipe `obat` terhadap `nama_obat`, `zat_aktif`, dan `kelompok_obat` pada model `Obat`.
  - Pemeriksaan bersifat case-insensitive substring (misal: alergi "Amoxicillin" atau "penisilin" akan mendeteksi obat dengan zat aktif atau kelompok "penisilin").
  - Jika terdeteksi alergi, server memblokir penyimpanan resep, transaksi dibatalkan (rollback), dan pesan error penolakan ditampilkan dengan jelas.

### 6. Transaksi Atomik dan Mutasi Stok (UC-10, UC-15, NFR-04)
- **Keputusan**: Setiap pengurangan stok pada resep digital dieksekusi dalam blok `transaction.atomic()` bersama pencatatan riwayat di `MutasiStok` (jenis: `'resep'`).
- **Pencegahan Stok Minus**: Pengecekan ketersediaan stok dilakukan di server sebelum pengurangan, didukung `CheckConstraint(stok_tersedia >= 0)` di database level. Jika stok tidak mencukupi, seluruh transaksi resep dibatalkan.

### 7. Pengamanan Berkas Hasil Laboratorium (UC-17, BR-03, BR-04)
- **Keputusan**: Berkas lampiran lab (PDF/JPG/PNG maks 5MB) tidak disajikan secara publik melalui media url statis biasa, melainkan melalui endpoint terproteksi (`unduh_lab`) yang memverifikasi bahwa pengguna yang meminta sedang login dan memiliki peran `dokter`. Staf klinik atau pengguna anonim ditolak dengan status HTTP 403 / 401.

### 8. Peringatan TTV Abnormal (UC-09)
- **Keputusan**: Parameter batas TTV disimpan di tabel `BatasTTV` (sistolik, diastolik, nadi, suhu, respirasi, spo2). Nilai default di-seed dari data medis dewasa:
  - Sistolik: 90 - 139 mmHg
  - Diastolik: 60 - 89 mmHg
  - Nadi: 60 - 100 x/menit
  - Suhu tubuh: 36.0 - 37.5 °C
  - Respirasi: 12 - 20 x/menit
  - SpO2: 95 - 100 %
- Jika satu atau lebih parameter berada di luar batas, sistem otomatis menandai `status_abnormal = True` dan `kunjungan.prioritas_abnormal = True`, serta mewajibkan staf mengisi `catatan_eskalasi`.

### 9. Kompatibilitas Python 3.15 & Performa Query (NFR-01)
- **Keputusan**:
  - Di Python 3.15, penanganan `copy(super())` pada `BaseContext.__copy__` Django 5.1 disesuaikan di `core/__init__.py` agar `client.get()` dan `client.post()` saat instrumented template render berjalan mulus tanpa AttributeError.
  - Untuk memenuhi NFR-01 (query riwayat medis pasien < 3 detik bahkan dengan >= 1.000 pasien), dibuat indeks majemuk `idx_kunjungan_pasien_waktu` pada `(id_pasien, tanggal_waktu)` serta penggunaan `select_related` dan `prefetch_related` pada relasi resep, diagnosa, dan tindakan, sehingga tidak terjadi masalah N+1 queries.
