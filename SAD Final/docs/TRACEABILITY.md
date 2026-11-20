# Matriks Penelusuran Kebutuhan (docs/TRACEABILITY.md)
Sistem Informasi e-Klinik UNKLAB (Universitas Klabat)

Dokumen ini memetakan hubungan antara aturan bisnis (BR), kebutuhan fungsional (FR), kebutuhan non-fungsional (NFR), direktif keselamatan (DIR), spesifikasi keamanan (SR), Use Case (UC), View & URL, Model Data, Layar Antarmuka (L), dan Pengujian Otomatis (TC).

---

## 1. Tabel Matriks Penelusuran (Traceability Matrix)

| Kode Kebutuhan | Deskripsi Singkat | Use Case | View / URL | Model Terkait | Layar | Uji Otomatis (TestCase) |
|---|---|---|---|---|---|---|
| **SR-01** | Autentikasi Pengguna & Pembatasan Peran (RBAC) di Server | UC-01 | `login_view`, `logout_view`<br>`/login/`, `/logout/` | `Pengguna` | **L-01 Login** | `test_tc01_login_valid`<br>`test_tc02_login_salah`<br>`test_staf_mendapat_403...`<br>`test_dokter_mendapat_403...` |
| **FR-01** | Dashboard Analitik Kesehatan (Kunjungan, Antrean, TTV Abnormal, Tren ICD-10, Stok Obat Kritis) | UC-02 | `dashboard_view`<br>`/`, `/dashboard/` | `Kunjungan`, `TandaVital`, `Diagnosis`, `Obat` | **L-02 Dashboard Analitik Kesehatan** | `test_tc13_dashboard_terender_filter_1_bulan` |
| **FR-02** | Manajemen Data Pasien (CRUD, Pencarian Partial, Pencegahan Hapus jika ada Riwayat) | UC-03 | `pasien_list_view`<br>`pasien_create_view`<br>`pasien_update_view`<br>`pasien_delete_view`<br>`/pasien/` | `Pasien` | **L-03 Data Pasien** | `test_tc03_cari_pasien_by_nim`<br>`test_validasi_data_wajib_pasien_dir_03` |
| **BR-02 / FR-03** | Verifikasi Identitas Pasien via NIM/ID Card/Nama Sebelum Kunjungan | UC-04 | `pasien_verifikasi_view`<br>`pasien_verifikasi_detail_view`<br>`/pasien/verifikasi/` | `Pasien`, `AlergiPasien` | **L-04 Pencarian dan Verifikasi Identitas** | `test_tc03_cari_pasien_by_nim` |
| **DIR-03 / NFR-05** | Validasi Data Wajib (NIM, Nama, Tanggal Lahir, Jenis Kelamin) & Pencegahan Duplikasi NIM | UC-05 | `PasienForm`, `pasien_create_view`<br>`/pasien/tambah/` | `Pasien` | **L-03 Data Pasien** | `test_validasi_data_wajib_pasien_dir_03`<br>`test_duplikasi_nim_ditolak` |
| **BR-01 / FR-04** | Pendaftaran Kunjungan Pasien Terverifikasi & Penomoran Antrean Harian Otomatis | UC-06 | `kunjungan_create_view`<br>`/kunjungan/buat/<id>/` | `Kunjungan`, `Pasien` | **L-05 Buat Kunjungan** | `test_tc04_kunjungan_fifo_dan_nomor_harian` |
| **BR-01 / FR-05** | Antrean Digital Berbasis FIFO Waktu Kedatangan, Transisi Status, Retensi Pasien Tunda | UC-07 | `antrean_view`<br>`antrean_update_status_view`<br>`antrean_api_today`<br>`/antrean/` | `Kunjungan`, `Pasien`, `TandaVital` | **L-06 Antrean Digital** | `test_tc04_kunjungan_fifo_dan_nomor_harian` |
| **FR-06 / NFR-04** | Pencatatan Keluhan Utama & Tanda Vital (TTV) dengan Validasi Rentang Realistis & Transaksi Atomik | UC-08 | `ttv_create_or_update_view`<br>`/kunjungan/<id>/ttv/` | `TandaVital`, `Kunjungan`, `BatasTTV` | **L-07 Keluhan dan Tanda Vital** | `test_tc05_ttv_normal_tersimpan` |
| **FR-07** | Deteksi Otomatis & Peringatan TTV Abnormal, Highlighting Merah, Catatan Eskalasi | UC-09 | `evaluasi_ttv_abnormal`<br>`ttv_create_or_update_view`<br>`/kunjungan/<id>/ttv/` | `BatasTTV`, `TandaVital`, `Kunjungan` | **L-07 Keluhan dan Tanda Vital** | `test_tc06_suhu_39_5_memicu_status_abnormal` |
| **FR-08** | Manajemen Inventaris Obat, Pencatatan Mutasi Stok (Masuk/Keluar/Koreksi), Pencegahan Stok Negatif | UC-10 | `obat_list_view`<br>`obat_create_view`<br>`obat_update_view`<br>`obat_mutasi_view`<br>`obat_delete_view`<br>`/obat/` | `Obat`, `MutasiStok` | **L-08 Inventaris Obat** | `test_tc11_mutasi_stok_tambah`<br>`test_stok_tidak_bisa_negatif` |
| **BR-03 / NFR-01** | Rekam Medis Rahasia Pasien Kronologis < 3 Detik (Dokter Only), Catatan Alergi Pasien | UC-11 | `riwayat_medis_view`<br>`/rekam-medis/pasien/<id>/` | `Pasien`, `Kunjungan`, `Pemeriksaan`, `AlergiPasien` | **L-09 Riwayat Medis Pasien** | `test_tc07_riwayat_medis_kurang_dari_3_detik_dengan_1000_pasien`<br>`test_staf_mendapat_403...` |
| **FR-09** | Pemeriksaan Medis Klinis Dokter (Anamnesis Lanjutan & Pemeriksaan Fisik Terenkripsi) | UC-12 | `pemeriksaan_view`<br>`/pemeriksaan/<id>/` | `Pemeriksaan`, `Kunjungan`, `TandaVital` | **L-10 Pemeriksaan** | `test_tc08_simpan_pemeriksaan` |
| **FR-10** | Pencarian ICD-10 Autocomplete AJAX, Diagnosis Primer & Sekunder (Maks 1 Primer) | UC-13 | `diagnosis_view`<br>`icd10_search_api`<br>`/pemeriksaan/<id>/diagnosis/` | `Diagnosis`, `ICD10`, `Pemeriksaan` | **L-11 Diagnosis ICD-10** | `test_tc09_pencarian_icd10_dan_diagnosis` |
| **FR-11** | Pencatatan Tindakan Medis & Edukasi Kesehatan Multi-Tindakan per Pemeriksaan | UC-14 | `tindakan_view`<br>`/pemeriksaan/<id>/tindakan/` | `Tindakan`, `Pemeriksaan` | **L-12 Tindakan Medis** | `test_tc08_simpan_pemeriksaan` |
| **FR-12 / NFR-04** | Resep Digital Multi-Obat, Pengurangan Stok Otomatis, Pencatatan Mutasi Jenis Resep | UC-15 | `resep_view`<br>`/pemeriksaan/<id>/resep/` | `Resep`, `DetailResep`, `Obat`, `MutasiStok` | **L-13 Resep Digital** | `test_resep_stok_kurang_ditolak` |
| **DIR-02 / FR-13** | Peringatan Keras Alergi Obat & Pemblokiran Simpan Resep (Client & Server Side) | UC-16 | `cek_alergi_obat`<br>`resep_check_medicine_api`<br>`resep_view` | `AlergiPasien`, `Obat`, `Resep` | **L-13 Resep Digital** | `test_tc10_resep_amoxicillin_alergi_diblokir` |
| **BR-04 / FR-14** | Lampiran Berkas Laboratorium Eksternal Penunjang & Unduh Terproteksi Dokter | UC-17 | `hasil_lab_view`<br>`unduh_lab_view`<br>`/kunjungan/<id>/lab/` | `HasilLab`, `Kunjungan` | **L-14 Hasil Laboratorium** | `test_tc12_unduh_lampiran_lab` |
| **SR-02 / NFR-02** | Enkripsi Tingkat Field Medis Menggunakan Fernet (8 Kolom Sensitif) | - | `EncryptedTextField`<br>`klinik/fields.py` | Seluruh model medis sensitif | Semua Layar Medis | `test_field_terenkripsi_tidak_terbaca_plaintext_di_db` |

---

## 2. Rincian 14 Layar Antarmuka (Screens)

1. **L-01 Login**: Form masuk pengguna (Staf Klinik / Dokter), validasi kredensial, proteksi brute-force, dan pengarah peran otomatis.
2. **L-02 Dashboard Analitik Kesehatan**: 4 kartu ringkasan (Kunjungan Hari Ini, Antrean Menunggu, Pasien Dilayani, TTV Abnormal), grafik kunjungan harian (filter 7 hari, 1 bulan, 3 bulan, kustom), tren penyakit ICD-10 (Top 10), dan daftar obat kritis (stok <= minimum).
3. **L-03 Data Pasien**: Tabel seluruh pasien terdaftar, filter pencarian partial nama/NIM, tombol tambah, ubah, dan hapus dengan proteksi integritas kunjungan.
4. **L-04 Pencarian dan Verifikasi Identitas**: Pencarian instan identitas civitas akademika UNKLAB lewat NIM/ID Card/Nama dan verifikasi sebelum pembuatan kunjungan.
5. **L-05 Buat Kunjungan**: Registrasi kunjungan baru pasien terverifikasi, pencatatan keluhan utama kedatangan terenkripsi, dan penerbitan nomor antrean harian FIFO.
6. **L-06 Antrean Digital**: Tampilan urutan pemanggilan pasien hari ini murni berbasis FIFO waktu kedatangan, tombol transisi status (Panggil, Layani, Tunda, Selesai), tanda prioritas TTV abnormal, dan auto-refresh 10 detik.
7. **L-07 Keluhan dan Tanda Vital**: Formulir input TTV lengkap, evaluasi realtime terhadap `BatasTTV`, penandaan visual merah per-parameter, peringatan pop-up keselamatan, dan kewajiban catatan eskalasi jika abnormal.
8. **L-08 Inventaris Obat**: Tabel stok obat klinik, filter status stok kritis (≤ minimum), pengelolaan data master obat, mutasi stok, serta penonaktifan aman jika obat pernah diresepkan.
9. **L-09 Riwayat Medis Pasien**: Rangkuman kronologis rahasia kunjungan, TTV, diagnosis, terapi, dan riwayat alergi yang dapat diakses oleh dokter dalam waktu < 3 detik.
10. **L-10 Pemeriksaan**: Halaman pemeriksaan klinis dokter menampilkan TTV awal tersorot, isian anamnesis lanjutan terenkripsi, riwayat konsumsi obat, dan pemeriksaan fisik terenkripsi.
11. **L-11 Diagnosis ICD-10**: Autocomplete pencarian cepat kode ICD-10 berbasis AJAX, pemilihan jenis primer atau sekunder (maks 1 primer), dan daftar diagnosis pemeriksaan.
12. **L-12 Tindakan Medis**: Pencatatan intervensi medis, perawatan luka, atau konseling edukasi kesehatan pasien.
13. **L-13 Resep Digital**: Formulir resep dinamis multi-obat, validasi stok instan, pencocokan alergi obat (DIR-02) yang memblokir tombol simpan, transaksi atomik pengurangan stok dan mutasi.
14. **L-14 Hasil Laboratorium**: Unggah data penunjang lab eksternal (maks 5MB, format PDF/JPG/PNG) dan pengunduhan aman terisolasi khusus dokter.
