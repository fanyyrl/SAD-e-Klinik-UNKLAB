from django.urls import path
from . import views

urlpatterns = [
    # Autentikasi (L-01)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard Analitik (L-02)
    path('', views.dashboard_view, name='dashboard'),

    # Data Pasien (L-03)
    path('pasien/', views.pasien_list_view, name='pasien_list'),
    path('pasien/tambah/', views.pasien_create_view, name='pasien_create'),
    path('pasien/<int:id_pasien>/ubah/', views.pasien_update_view, name='pasien_update'),
    path('pasien/<int:id_pasien>/hapus/', views.pasien_delete_view, name='pasien_delete'),

    # Pencarian & Verifikasi Identitas (L-04)
    path('pasien/verifikasi/', views.pasien_verifikasi_view, name='pasien_verifikasi'),
    path('pasien/<int:id_pasien>/verifikasi/', views.pasien_verifikasi_detail_view, name='pasien_verifikasi_detail'),

    # Buat Kunjungan (L-05)
    path('kunjungan/buat/<int:id_pasien>/', views.kunjungan_create_view, name='kunjungan_create'),

    # Antrean Digital (L-06)
    path('antrean/', views.antrean_view, name='antrean'),
    path('antrean/<int:id_kunjungan>/status/<str:status_baru>/', views.antrean_update_status_view, name='antrean_update_status'),

    # Keluhan dan Tanda Vital (L-07)
    path('kunjungan/<int:id_kunjungan>/ttv/', views.ttv_create_or_update_view, name='ttv_create_or_update'),

    # Inventaris Obat (L-08)
    path('obat/', views.obat_list_view, name='obat_list'),
    path('obat/tambah/', views.obat_create_view, name='obat_create'),
    path('obat/<str:kode_obat>/ubah/', views.obat_update_view, name='obat_update'),
    path('obat/<str:kode_obat>/mutasi/', views.obat_mutasi_view, name='obat_mutasi'),
    path('obat/<str:kode_obat>/hapus/', views.obat_delete_view, name='obat_delete'),

    # Alur Medis Dokter (L-09 s/d L-14)
    path('rekam-medis/pasien/<int:id_pasien>/', views.riwayat_medis_view, name='riwayat_medis'),
    path('pemeriksaan/<int:id_kunjungan>/', views.pemeriksaan_view, name='pemeriksaan_view'),
    path('pemeriksaan/<int:id_pemeriksaan>/diagnosis/', views.diagnosis_view, name='diagnosis_view'),
    path('diagnosis/<int:id_diagnosis>/hapus/', views.diagnosis_delete_view, name='diagnosis_delete'),
    path('pemeriksaan/<int:id_pemeriksaan>/tindakan/', views.tindakan_view, name='tindakan_view'),
    path('tindakan/<int:id_tindakan>/hapus/', views.tindakan_delete_view, name='tindakan_delete'),
    path('pemeriksaan/<int:id_pemeriksaan>/resep/', views.resep_view, name='resep_view'),
    path('kunjungan/<int:id_kunjungan>/lab/', views.hasil_lab_view, name='hasil_lab_view'),
    path('lab/unduh/<int:id_hasil_lab>/', views.unduh_lab_view, name='unduh_lab'),
    path('kunjungan/<int:id_kunjungan>/selesai/', views.selesaikan_kunjungan_view, name='selesaikan_kunjungan'),

    # AJAX & JSON APIs
    path('api/antrean/today/', views.antrean_api_today, name='antrean_api_today'),
    path('api/icd10/search/', views.icd10_search_api, name='icd10_search_api'),
    path('api/resep/check-medicine/', views.resep_check_medicine_api, name='resep_check_medicine_api'),
]
