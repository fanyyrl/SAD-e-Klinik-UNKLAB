import os
import time
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.db import connection, IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from klinik.models import (
    Pengguna, Pasien, AlergiPasien, Kunjungan, TandaVital,
    BatasTTV, Pemeriksaan, ICD10, Diagnosis, Tindakan,
    Obat, MutasiStok, Resep, DetailResep, HasilLab
)


class EKlinikTestCase(TestCase):
    def setUp(self):
        # 1. Batas TTV
        BatasTTV.objects.update_or_create(parameter='sistolik', defaults={'nilai_min': 90, 'nilai_maks': 139})
        BatasTTV.objects.update_or_create(parameter='diastolik', defaults={'nilai_min': 60, 'nilai_maks': 89})
        BatasTTV.objects.update_or_create(parameter='nadi', defaults={'nilai_min': 60, 'nilai_maks': 100})
        BatasTTV.objects.update_or_create(parameter='suhu', defaults={'nilai_min': Decimal('36.0'), 'nilai_maks': Decimal('37.5')})
        BatasTTV.objects.update_or_create(parameter='respirasi', defaults={'nilai_min': 12, 'nilai_maks': 20})
        BatasTTV.objects.update_or_create(parameter='spo2', defaults={'nilai_min': 95, 'nilai_maks': 100})

        # 2. Pengguna
        self.staf = Pengguna.objects.create_user(
            username='staf_klinik',
            password='Staf12345!',
            nama_lengkap='Staf Klinik UNKLAB',
            role_akses='staf_klinik',
            status_aktif=True
        )
        self.dokter = Pengguna.objects.create_user(
            username='dokter1',
            password='Dokter12345!',
            nama_lengkap='dr. Christian Manoppo, Sp.PD',
            role_akses='dokter',
            status_aktif=True
        )

        # 3. ICD-10
        self.icd_j00 = ICD10.objects.create(
            kode_icd10="J00",
            deskripsi="Acute nasopharyngitis [common cold]"
        )
        self.icd_k29 = ICD10.objects.create(
            kode_icd10="K29.7",
            deskripsi="Gastritis, unspecified"
        )

        # 4. Master Obat
        self.obat_pct = Obat.objects.create(
            kode_obat="OBT-001",
            nama_obat="Paracetamol 500 mg",
            satuan="tablet",
            stok_tersedia=200,
            stok_minimum=50,
            zat_aktif="Paracetamol",
            kelompok_obat="Analgesik-Antipiretik",
            status_aktif=True
        )
        self.obat_amx = Obat.objects.create(
            kode_obat="OBT-AMX",
            nama_obat="Amoxicillin 500 mg",
            satuan="kapsul",
            stok_tersedia=150,
            stok_minimum=30,
            zat_aktif="Amoxicillin",
            kelompok_obat="penisilin",
            status_aktif=True
        )

        # 5. Pasien Sample (Fany Moningkey dengan Alergi Amoxicillin / penisilin)
        self.pasien = Pasien.objects.create(
            nim_id="105012410033",
            nama="Fany Moningkey",
            tanggal_lahir=date(2004, 5, 14),
            jenis_kelamin="P",
            fakultas="Fakultas Ilmu Komputer",
            alamat="Asrama Crystal UNKLAB"
        )
        AlergiPasien.objects.create(
            id_pasien=self.pasien,
            nama_alergen="Amoxicillin",
            jenis_alergi="obat",
            reaksi="Syok anafilaksis dan ruam gatal parah"
        )
        AlergiPasien.objects.create(
            id_pasien=self.pasien,
            nama_alergen="penisilin",
            jenis_alergi="obat",
            reaksi="Urtikaria hebat dan sesak napas"
        )

    # TC-01: Login valid
    def test_tc01_login_valid(self):
        client = Client()
        response = client.post(reverse('login'), {
            'username': 'staf_klinik',
            'password': 'Staf12345!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(client.session['_auth_user_id']), self.staf.pk)

    # TC-02: Login salah -> pesan "Username/Password salah"
    def test_tc02_login_salah(self):
        client = Client()
        response = client.post(reverse('login'), {
            'username': 'staf_klinik',
            'password': 'PasswordSalahTotal!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username/Password salah")

    # TC-03: Cari pasien by NIM
    def test_tc03_cari_pasien_by_nim(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')
        response = client.get(reverse('pasien_verifikasi') + '?q=105012410033')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fany Moningkey")
        self.assertContains(response, "105012410033")

    # TC-04: Kunjungan masuk antrean FIFO + nomor harian benar
    def test_tc04_kunjungan_fifo_dan_nomor_harian(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        # Pasien ke-2
        p2 = Pasien.objects.create(
            nim_id="105012410001",
            nama="Geraldo Pongoh",
            tanggal_lahir=date(2003, 3, 10),
            jenis_kelamin="L"
        )

        # Buat Kunjungan 1
        resp1 = client.post(reverse('kunjungan_create', args=[self.pasien.pk]), {
            'keluhan_utama': 'Demam dan meriang sejak semalam'
        })
        self.assertEqual(resp1.status_code, 302)
        k1 = Kunjungan.objects.get(id_pasien=self.pasien)
        self.assertEqual(k1.nomor_antrian, 1)

        # Buat Kunjungan 2
        resp2 = client.post(reverse('kunjungan_create', args=[p2.pk]), {
            'keluhan_utama': 'Sakit gigi berdenyut'
        })
        self.assertEqual(resp2.status_code, 302)
        k2 = Kunjungan.objects.get(id_pasien=p2)
        self.assertEqual(k2.nomor_antrian, 2)

        # Cek daftar antrean terurut tanggal_waktu (FIFO)
        antrean_resp = client.get(reverse('antrean'))
        self.assertEqual(antrean_resp.status_code, 200)
        antrean_list = list(antrean_resp.context['antrean_list'])
        self.assertEqual(antrean_list[0].pk, k1.pk)
        self.assertEqual(antrean_list[1].pk, k2.pk)

    # TC-05: TTV normal tersimpan
    def test_tc05_ttv_normal_tersimpan(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Pemeriksaan rutin"
        )

        response = client.post(reverse('ttv_create_or_update', args=[k.pk]), {
            'keluhan_utama': 'Pemeriksaan rutin kampus',
            'tekanan_sistolik': 120,
            'tekanan_diastolik': 80,
            'nadi': 75,
            'suhu_tubuh': '36.6',
            'respirasi': 18,
            'saturasi_oksigen': 98,
            'skor_nyeri': 0,
            'berat_badan': 55.0,
            'catatan_eskalasi': ''
        })
        self.assertEqual(response.status_code, 302)

        ttv = TandaVital.objects.get(id_kunjungan=k)
        k.refresh_from_db()
        self.assertFalse(ttv.status_abnormal)
        self.assertFalse(k.prioritas_abnormal)
        self.assertEqual(k.status_pemeriksaan_awal, 'siap_diperiksa')

    # TC-06: Suhu 39.5 memicu status_abnormal & prioritas abnormal
    def test_tc06_suhu_39_5_memicu_status_abnormal(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Demam tinggi menggigil"
        )

        response = client.post(reverse('ttv_create_or_update', args=[k.pk]), {
            'keluhan_utama': 'Demam tinggi menggigil',
            'tekanan_sistolik': 120,
            'tekanan_diastolik': 80,
            'nadi': 110,  # Abnormal (>100)
            'suhu_tubuh': '39.5',  # Abnormal (>37.5)
            'respirasi': 22,  # Abnormal (>20)
            'saturasi_oksigen': 96,
            'catatan_eskalasi': 'Demam tinggi dan takikardia, eskalasi prioritas dokter'
        })
        self.assertEqual(response.status_code, 302)

        ttv = TandaVital.objects.get(id_kunjungan=k)
        k.refresh_from_db()
        self.assertTrue(ttv.status_abnormal)
        self.assertTrue(k.prioritas_abnormal)
        self.assertEqual(k.status_pemeriksaan_awal, 'siap_diperiksa')

    # TC-07: Riwayat medis < 3 detik (diuji dengan >= 1.000 pasien dummy)
    def test_tc07_riwayat_medis_kurang_dari_3_detik_dengan_1000_pasien(self):
        # Buat 1.000 pasien dummy secara bulk
        bulk_pasien = []
        for i in range(1, 1001):
            bulk_pasien.append(Pasien(
                nim_id=f"TEST_NIM_{i:04d}",
                nama=f"Mahasiswa Uji {i}",
                tanggal_lahir=date(2002, 1, 1),
                jenis_kelamin="L" if i % 2 == 0 else "P",
                fakultas="Fakultas Ilmu Komputer"
            ))
        Pasien.objects.bulk_create(bulk_pasien)

        client = Client()
        client.login(username='dokter1', password='Dokter12345!')

        # Ukur waktu eksekusi query & render riwayat medis
        start_time = time.time()
        response = client.get(reverse('riwayat_medis', args=[self.pasien.pk]))
        elapsed_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed_time, 3.0, f"Query riwayat medis memakan waktu {elapsed_time:.3f} detik (melebihi 3 detik)!")
        self.assertContains(response, "Fany Moningkey")

    # TC-08: Simpan pemeriksaan medis dokter
    def test_tc08_simpan_pemeriksaan(self):
        client = Client()
        client.login(username='dokter1', password='Dokter12345!')

        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Nyeri kepala",
            status_antrian="dipanggil"
        )

        response = client.post(reverse('pemeriksaan_view', args=[k.pk]), {
            'anamnesis_lanjutan': 'Sakit kepala sejak 2 hari, terasa berdenyut di pelipis kanan.',
            'riwayat_konsumsi_obat': 'Tidak ada',
            'pemeriksaan_fisik': 'Keadaan umum baik, tanda vital stabil. Tidak ada defisit neurologis fokal.'
        })
        self.assertEqual(response.status_code, 302)

        pmr = Pemeriksaan.objects.get(id_kunjungan=k)
        self.assertEqual(pmr.id_dokter, self.dokter)
        k.refresh_from_db()
        self.assertEqual(k.status_antrian, 'dilayani')

    # TC-09: Pencarian ICD-10 "Acute nasopharyngitis" -> J00 bisa dijadikan diagnosis
    def test_tc09_pencarian_icd10_dan_diagnosis(self):
        client = Client()
        client.login(username='dokter1', password='Dokter12345!')

        # API search
        api_resp = client.get(reverse('icd10_search_api') + '?q=Acute+nasopharyngitis')
        self.assertEqual(api_resp.status_code, 200)
        data = api_resp.json()
        self.assertTrue(any(item['kode'] == 'J00' for item in data['results']))

        # Simpan diagnosis
        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Flu"
        )
        pmr = Pemeriksaan.objects.create(
            id_kunjungan=k,
            id_dokter=self.dokter,
            anamnesis_lanjutan="Hidung tersumbat dan bersin-bersin",
            pemeriksaan_fisik="Faring tenang, rhinitis serosa"
        )

        diag_resp = client.post(reverse('diagnosis_view', args=[pmr.pk]), {
            'tambah_diagnosis': '1',
            'kode_icd10': 'J00',
            'jenis_diagnosis': 'primer'
        })
        self.assertEqual(diag_resp.status_code, 302)

        diag = Diagnosis.objects.filter(id_pemeriksaan=pmr, kode_icd10=self.icd_j00).first()
        self.assertIsNotNone(diag)
        self.assertEqual(diag.jenis_diagnosis, 'primer')

    # TC-10: Resep Amoxicillin untuk pasien alergi diblokir di server (DIR-02)
    def test_tc10_resep_amoxicillin_alergi_diblokir(self):
        client = Client()
        client.login(username='dokter1', password='Dokter12345!')

        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Infeksi radang tenggorokan"
        )
        pmr = Pemeriksaan.objects.create(
            id_kunjungan=k,
            id_dokter=self.dokter,
            anamnesis_lanjutan="Sakit menelan",
            pemeriksaan_fisik="Tonsil T2/T2 hiperemis"
        )

        stok_amx_awal = self.obat_amx.stok_tersedia

        # Coba resepkan Amoxicillin (pasien punya alergi Amoxicillin dan penisilin)
        response = client.post(reverse('resep_view', args=[pmr.pk]), {
            'catatan_resep': 'Harus diminum habis',
            'obat_id[]': [self.obat_amx.pk],
            'jumlah[]': ['10'],
            'dosis[]': ['500 mg'],
            'aturan[]': ['3x1 sesudah makan']
        }, follow=True)

        # Resep harus diblokir!
        self.assertContains(response, "BAHAYA ALERGI OBAT")
        self.assertEqual(DetailResep.objects.count(), 0)
        self.obat_amx.refresh_from_db()
        self.assertEqual(self.obat_amx.stok_tersedia, stok_amx_awal)

    # TC-11: Stok OBT-001 +50 bertambah + mutasi tercatat
    def test_tc11_mutasi_stok_tambah(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        stok_awal = self.obat_pct.stok_tersedia
        response = client.post(reverse('obat_mutasi', args=[self.obat_pct.pk]), {
            'jenis': 'masuk',
            'jumlah': 50,
            'keterangan': 'Pengadaan obat bulanan UNKLAB'
        })
        self.assertEqual(response.status_code, 302)

        self.obat_pct.refresh_from_db()
        self.assertEqual(self.obat_pct.stok_tersedia, stok_awal + 50)

        mutasi = MutasiStok.objects.filter(kode_obat=self.obat_pct, jenis='masuk').latest('waktu')
        self.assertEqual(mutasi.jumlah, 50)
        self.assertEqual(mutasi.id_pengguna, self.staf)

    # TC-12: Unduh lampiran lab: Dokter bisa, Staf Klinik ditolak 403
    def test_tc12_unduh_lampiran_lab(self):
        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Cek darah"
        )
        dummy_file = SimpleUploadedFile("hasil_lab.pdf", b"%PDF-1.4 dummy pdf content", content_type="application/pdf")
        lab = HasilLab.objects.create(
            id_kunjungan=k,
            id_pencatat=self.dokter,
            jenis_pemeriksaan="Darah Rutin",
            sumber_fasilitas="Lab UNKLAB",
            tanggal_pemeriksaan=timezone.localdate(),
            hasil_lab="Hb 13.5 g/dL normal",
            file_lampiran=dummy_file
        )

        # 1. Login sebagai Dokter -> boleh unduh
        client_dokter = Client()
        client_dokter.login(username='dokter1', password='Dokter12345!')
        resp_dok = client_dokter.get(reverse('unduh_lab', args=[lab.pk]))
        self.assertEqual(resp_dok.status_code, 200)

        # 2. Login sebagai Staf Klinik -> ditolak 403 Forbidden!
        client_staf = Client()
        client_staf.login(username='staf_klinik', password='Staf12345!')
        resp_staf = client_staf.get(reverse('unduh_lab', args=[lab.pk]))
        self.assertEqual(resp_staf.status_code, 403)

    # TC-13: Dashboard terender dengan filter 1 bulan
    def test_tc13_dashboard_terender_filter_1_bulan(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')
        response = client.get(reverse('dashboard') + '?rentang=1_bulan')
        self.assertEqual(response.status_code, 200)
        self.assertIn('chart_labels', response.context)
        self.assertIn('chart_values', response.context)
        self.assertIn('kunjungan_hari_ini', response.context)
        self.assertContains(response, "L-02 Dashboard Analitik Kesehatan")

    # TEST ROLE-BASED ACCESS CONTROL (SR-01)
    def test_staf_mendapat_403_pada_halaman_medis_dokter(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Keluhan"
        )
        pmr = Pemeriksaan.objects.create(
            id_kunjungan=k,
            id_dokter=self.dokter,
            anamnesis_lanjutan="Anamnesis rahasia",
            pemeriksaan_fisik="Fisik rahasia"
        )

        # Halaman medis dokter:
        self.assertEqual(client.get(reverse('riwayat_medis', args=[self.pasien.pk])).status_code, 403)
        self.assertEqual(client.get(reverse('pemeriksaan_view', args=[k.pk])).status_code, 403)
        self.assertEqual(client.get(reverse('diagnosis_view', args=[pmr.pk])).status_code, 403)
        self.assertEqual(client.get(reverse('tindakan_view', args=[pmr.pk])).status_code, 403)
        self.assertEqual(client.get(reverse('resep_view', args=[pmr.pk])).status_code, 403)
        self.assertEqual(client.get(reverse('hasil_lab_view', args=[k.pk])).status_code, 403)

    def test_dokter_mendapat_403_pada_inventaris_dan_buat_kunjungan(self):
        client = Client()
        client.login(username='dokter1', password='Dokter12345!')

        self.assertEqual(client.get(reverse('obat_list')).status_code, 403)
        self.assertEqual(client.get(reverse('obat_create')).status_code, 403)
        self.assertEqual(client.get(reverse('kunjungan_create', args=[self.pasien.pk])).status_code, 403)
        self.assertEqual(client.get(reverse('pasien_verifikasi')).status_code, 403)

    # TEST VALIDASI DATA WAJIB (DIR-03, UC-05)
    def test_validasi_data_wajib_pasien_dir_03(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        # Kosongkan nama & tanggal lahir
        response = client.post(reverse('pasien_create'), {
            'nim_id': '105099999999',
            'nama': '',
            'tanggal_lahir': '',
            'jenis_kelamin': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Pasien.objects.filter(nim_id='105099999999').exists())

    # TEST DUPLIKASI NIM
    def test_duplikasi_nim_ditolak(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        response = client.post(reverse('pasien_create'), {
            'nim_id': '105012410033',  # NIM sudah ada (Fany Moningkey)
            'nama': 'Fany Kembaran',
            'tanggal_lahir': '2004-05-14',
            'jenis_kelamin': 'P'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sudah terdaftar")

    # TEST RESEP DENGAN STOK KURANG DITOLAK
    def test_resep_stok_kurang_ditolak(self):
        client = Client()
        client.login(username='dokter1', password='Dokter12345!')

        # Pasien tanpa alergi
        p_sehat = Pasien.objects.create(
            nim_id="105088888888",
            nama="Budi Sehat",
            tanggal_lahir=date(2003, 1, 1),
            jenis_kelamin="L"
        )
        k = Kunjungan.objects.create(
            id_pasien=p_sehat,
            nomor_antrian=1,
            keluhan_utama="Sakit kepala"
        )
        pmr = Pemeriksaan.objects.create(
            id_kunjungan=k,
            id_dokter=self.dokter,
            anamnesis_lanjutan="Sakit kepala ringan",
            pemeriksaan_fisik="Normal"
        )

        stok_awal = self.obat_pct.stok_tersedia  # 200

        # Minta 500 tablet (lebih dari stok 200)
        response = client.post(reverse('resep_view', args=[pmr.pk]), {
            'catatan_resep': 'Dosis tinggi',
            'obat_id[]': [self.obat_pct.pk],
            'jumlah[]': ['500'],
            'dosis[]': ['500 mg'],
            'aturan[]': ['3x1']
        }, follow=True)

        self.assertContains(response, "tidak mencukupi")
        self.obat_pct.refresh_from_db()
        self.assertEqual(self.obat_pct.stok_tersedia, stok_awal)
        self.assertEqual(DetailResep.objects.count(), 0)

    # TEST STOK TIDAK BISA NEGATIF
    def test_stok_tidak_bisa_negatif(self):
        client = Client()
        client.login(username='staf_klinik', password='Staf12345!')

        # Coba keluarkan stok melebihi stok yang ada
        stok_awal = self.obat_pct.stok_tersedia  # 200
        response = client.post(reverse('obat_mutasi', args=[self.obat_pct.pk]), {
            'jenis': 'keluar',
            'jumlah': 300,
            'keterangan': 'Penyusutan'
        }, follow=True)

        self.assertContains(response, "tidak mencukupi")
        self.obat_pct.refresh_from_db()
        self.assertEqual(self.obat_pct.stok_tersedia, stok_awal)

        # Cek database check constraint level
        with self.assertRaises(Exception):
            self.obat_pct.stok_tersedia = -10
            self.obat_pct.save()

    # TEST ENKRIPSI FIELD MEDIS (SR-02 / NFR-02)
    def test_field_terenkripsi_tidak_terbaca_plaintext_di_db(self):
        teks_rahasia = "Pasien menderita keluhan sangat sensitif dan rahasia medis kampus UNKLAB."

        k = Kunjungan.objects.create(
            id_pasien=self.pasien,
            nomor_antrian=1,
            keluhan_utama="Keluhan awal"
        )
        pmr = Pemeriksaan.objects.create(
            id_kunjungan=k,
            id_dokter=self.dokter,
            anamnesis_lanjutan=teks_rahasia,
            pemeriksaan_fisik="Status lokalis normal"
        )

        # 1. Baca langsung secara raw SQL dari database
        with connection.cursor() as cursor:
            cursor.execute("SELECT anamnesis_lanjutan FROM pemeriksaan WHERE id_pemeriksaan = %s", [pmr.pk])
            raw_db_value = cursor.fetchone()[0]

        # Pastikan data di database terenkripsi:
        # - Diawali token Fernet standar "gAAAAA"
        # - Plaintext teks_rahasia TIDAK ditemukan di raw_db_value
        self.assertTrue(raw_db_value.startswith("gAAAAA"), f"Nilai di DB bukan Fernet token: {raw_db_value[:20]}")
        self.assertNotIn(teks_rahasia, raw_db_value)

        # 2. Baca lewat Django ORM: otomatis terdekripsi
        pmr_reloaded = Pemeriksaan.objects.get(pk=pmr.pk)
        self.assertEqual(pmr_reloaded.anamnesis_lanjutan, teks_rahasia)
