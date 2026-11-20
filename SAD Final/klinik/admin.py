from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Pengguna, Pasien, AlergiPasien, Kunjungan, TandaVital,
    BatasTTV, Pemeriksaan, ICD10, Diagnosis, Tindakan,
    Obat, MutasiStok, Resep, DetailResep, HasilLab
)


@admin.register(Pengguna)
class PenggunaAdmin(UserAdmin):
    list_display = ('username', 'nama_lengkap', 'role_akses', 'status_aktif', 'is_staff')
    list_filter = ('role_akses', 'status_aktif', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Informasi Tambahan UNKLAB', {'fields': ('nama_lengkap', 'role_akses', 'status_aktif')}),
    )


@admin.register(Pasien)
class PasienAdmin(admin.ModelAdmin):
    list_display = ('nim_id', 'nama', 'tanggal_lahir', 'umur', 'jenis_kelamin', 'fakultas')
    search_fields = ('nim_id', 'nama')
    list_filter = ('jenis_kelamin', 'fakultas')


@admin.register(AlergiPasien)
class AlergiPasienAdmin(admin.ModelAdmin):
    list_display = ('id_pasien', 'nama_alergen', 'jenis_alergi')
    search_fields = ('id_pasien__nama', 'id_pasien__nim_id', 'nama_alergen')


@admin.register(Kunjungan)
class KunjunganAdmin(admin.ModelAdmin):
    list_display = ('nomor_antrian', 'id_pasien', 'tanggal_waktu', 'status_antrian', 'status_pemeriksaan_awal', 'prioritas_abnormal')
    list_filter = ('status_antrian', 'status_pemeriksaan_awal', 'prioritas_abnormal', 'tanggal_waktu')
    search_fields = ('id_pasien__nama', 'id_pasien__nim_id')


@admin.register(TandaVital)
class TandaVitalAdmin(admin.ModelAdmin):
    list_display = ('id_kunjungan', 'tekanan_sistolik', 'tekanan_diastolik', 'nadi', 'suhu_tubuh', 'status_abnormal')
    list_filter = ('status_abnormal',)


@admin.register(BatasTTV)
class BatasTTVAdmin(admin.ModelAdmin):
    list_display = ('parameter', 'nilai_min', 'nilai_maks')


@admin.register(Pemeriksaan)
class PemeriksaanAdmin(admin.ModelAdmin):
    list_display = ('id_pemeriksaan', 'id_kunjungan', 'id_dokter', 'waktu_periksa')


@admin.register(ICD10)
class ICD10Admin(admin.ModelAdmin):
    list_display = ('kode_icd10', 'deskripsi')
    search_fields = ('kode_icd10', 'deskripsi')


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('id_pemeriksaan', 'kode_icd10', 'jenis_diagnosis')
    list_filter = ('jenis_diagnosis',)


@admin.register(Tindakan)
class TindakanAdmin(admin.ModelAdmin):
    list_display = ('id_pemeriksaan', 'nama_tindakan')


@admin.register(Obat)
class ObatAdmin(admin.ModelAdmin):
    list_display = ('kode_obat', 'nama_obat', 'satuan', 'stok_tersedia', 'stok_minimum', 'kelompok_obat', 'status_aktif')
    search_fields = ('kode_obat', 'nama_obat', 'zat_aktif', 'kelompok_obat')
    list_filter = ('status_aktif', 'kelompok_obat')


@admin.register(MutasiStok)
class MutasiStokAdmin(admin.ModelAdmin):
    list_display = ('kode_obat', 'jenis', 'jumlah', 'waktu', 'id_pengguna')
    list_filter = ('jenis', 'waktu')


@admin.register(Resep)
class ResepAdmin(admin.ModelAdmin):
    list_display = ('id_resep', 'id_pemeriksaan', 'tanggal_resep')


@admin.register(DetailResep)
class DetailResepAdmin(admin.ModelAdmin):
    list_display = ('id_resep', 'kode_obat', 'jumlah', 'dosis', 'aturan_pakai')


@admin.register(HasilLab)
class HasilLabAdmin(admin.ModelAdmin):
    list_display = ('id_kunjungan', 'jenis_pemeriksaan', 'sumber_fasilitas', 'tanggal_pemeriksaan')
