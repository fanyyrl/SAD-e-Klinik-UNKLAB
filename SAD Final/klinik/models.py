from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from .fields import EncryptedTextField


class Pengguna(AbstractUser):
    """
    Model Akun Pengguna e-Klinik UNKLAB (AbstractUser)
    Peran: 'staf_klinik' atau 'dokter'
    """
    ROLE_CHOICES = (
        ('staf_klinik', 'Staf Klinik'),
        ('dokter', 'Dokter'),
    )

    id_pengguna = models.BigAutoField(primary_key=True)
    nama_lengkap = models.CharField(max_length=150, verbose_name="Nama Lengkap")
    role_akses = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staf_klinik', verbose_name="Peran Akses")
    status_aktif = models.BooleanField(default=True, verbose_name="Status Aktif")

    class Meta:
        db_table = 'pengguna'
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Pengguna'

    def __str__(self):
        return f"{self.nama_lengkap} ({self.get_role_akses_display()})"

    @property
    def is_staf_klinik(self):
        return self.role_akses == 'staf_klinik'

    @property
    def is_dokter(self):
        return self.role_akses == 'dokter'

    def save(self, *args, **kwargs):
        # Sinkronkan is_active bawaan Django dengan status_aktif
        self.is_active = self.status_aktif
        if not self.nama_lengkap:
            self.nama_lengkap = f"{self.first_name} {self.last_name}".strip() or self.username
        super().save(*args, **kwargs)


class Pasien(models.Model):
    """
    Data Pasien e-Klinik UNKLAB
    """
    JENIS_KELAMIN_CHOICES = (
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    )

    id_pasien = models.BigAutoField(primary_key=True)
    nim_id = models.CharField(max_length=30, unique=True, db_index=True, verbose_name="NIM / ID Pasien")
    nama = models.CharField(max_length=150, db_index=True, verbose_name="Nama Lengkap")
    tanggal_lahir = models.DateField(verbose_name="Tanggal Lahir")
    jenis_kelamin = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES, verbose_name="Jenis Kelamin")
    fakultas = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fakultas / Unit")
    alamat = models.TextField(blank=True, null=True, verbose_name="Alamat Tinggal")
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pasien'
        verbose_name = 'Pasien'
        verbose_name_plural = 'Pasien'
        indexes = [
            models.Index(fields=['nim_id'], name='idx_pasien_nim'),
            models.Index(fields=['nama'], name='idx_pasien_nama'),
        ]

    def __str__(self):
        return f"{self.nim_id} - {self.nama}"

    @property
    def umur(self):
        """Menghitung umur otomatis dari tanggal_lahir"""
        if not self.tanggal_lahir:
            return 0
        today = timezone.localdate()
        return today.year - self.tanggal_lahir.year - (
            (today.month, today.day) < (self.tanggal_lahir.month, self.tanggal_lahir.day)
        )


class AlergiPasien(models.Model):
    """
    Catatan Alergi Pasien
    """
    JENIS_ALERGI_CHOICES = (
        ('obat', 'Obat'),
        ('makanan', 'Makanan'),
        ('lainnya', 'Lainnya'),
    )

    id_alergi = models.BigAutoField(primary_key=True)
    id_pasien = models.ForeignKey(Pasien, on_delete=models.CASCADE, related_name='alergi', db_column='id_pasien')
    nama_alergen = models.CharField(max_length=100, verbose_name="Nama Alergen")
    jenis_alergi = models.CharField(max_length=20, choices=JENIS_ALERGI_CHOICES, verbose_name="Jenis Alergi")
    reaksi = EncryptedTextField(verbose_name="Reaksi Alergi")

    class Meta:
        db_table = 'alergi_pasien'
        verbose_name = 'Alergi Pasien'
        verbose_name_plural = 'Alergi Pasien'

    def __str__(self):
        return f"{self.id_pasien.nama} - Alergi {self.nama_alergen} ({self.jenis_alergi})"


class Kunjungan(models.Model):
    """
    Kunjungan Pasien & Antrean Digital FIFO
    """
    STATUS_ANTRIAN_CHOICES = (
        ('menunggu', 'Menunggu'),
        ('dipanggil', 'Dipanggil'),
        ('dilayani', 'Dilayani'),
        ('ditunda', 'Ditunda'),
        ('selesai', 'Selesai'),
    )

    STATUS_PEMERIKSAAN_AWAL_CHOICES = (
        ('belum_ttv', 'Belum TTV'),
        ('siap_diperiksa', 'Siap Diperiksa'),
    )

    id_kunjungan = models.BigAutoField(primary_key=True)
    id_pasien = models.ForeignKey(Pasien, on_delete=models.CASCADE, related_name='kunjungan', db_column='id_pasien')
    id_dokter = models.ForeignKey(
        Pengguna, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='kunjungan_dokter', db_column='id_dokter'
    )
    tanggal_waktu = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Waktu Kedatangan")
    nomor_antrian = models.PositiveIntegerField(verbose_name="Nomor Antrean Harian")
    status_antrian = models.CharField(max_length=20, choices=STATUS_ANTRIAN_CHOICES, default='menunggu')
    status_verifikasi = models.BooleanField(default=True, verbose_name="Status Verifikasi")
    keluhan_utama = EncryptedTextField(verbose_name="Keluhan Utama")
    status_pemeriksaan_awal = models.CharField(
        max_length=20, choices=STATUS_PEMERIKSAAN_AWAL_CHOICES, default='belum_ttv',
        verbose_name="Status Pemeriksaan Awal"
    )
    prioritas_abnormal = models.BooleanField(default=False, verbose_name="Prioritas TTV Abnormal")

    class Meta:
        db_table = 'kunjungan'
        verbose_name = 'Kunjungan'
        verbose_name_plural = 'Kunjungan'
        ordering = ['tanggal_waktu']
        indexes = [
            models.Index(fields=['id_pasien', 'tanggal_waktu'], name='idx_kunjungan_pasien_waktu'),
            models.Index(fields=['tanggal_waktu'], name='idx_kunjungan_waktu'),
            models.Index(fields=['status_antrian'], name='idx_kunjungan_status'),
        ]

    def __str__(self):
        return f"Antrean #{self.nomor_antrian} - {self.id_pasien.nama} ({self.status_antrian})"


class TandaVital(models.Model):
    """
    Pemeriksaan Tanda Vital (TTV)
    """
    id_ttv = models.BigAutoField(primary_key=True)
    id_kunjungan = models.OneToOneField(
        Kunjungan, on_delete=models.CASCADE, related_name='tanda_vital', db_column='id_kunjungan'
    )
    id_pencatat = models.ForeignKey(
        Pengguna, on_delete=models.PROTECT, related_name='ttv_dicatat', db_column='id_pencatat'
    )
    tekanan_sistolik = models.IntegerField(verbose_name="Tekanan Sistolik (mmHg)")
    tekanan_diastolik = models.IntegerField(verbose_name="Tekanan Diastolik (mmHg)")
    nadi = models.IntegerField(verbose_name="Nadi (x/menit)")
    suhu_tubuh = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Suhu Tubuh (°C)")
    respirasi = models.IntegerField(verbose_name="Respirasi (x/menit)")
    saturasi_oksigen = models.IntegerField(verbose_name="Saturasi Oksigen / SpO2 (%)")
    skor_nyeri = models.IntegerField(null=True, blank=True, verbose_name="Skor Nyeri (0-10)")
    berat_badan = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name="Berat Badan (kg)")
    status_abnormal = models.BooleanField(default=False, verbose_name="Status Abnormal")
    catatan_eskalasi = EncryptedTextField(blank=True, default='', verbose_name="Catatan Eskalasi")
    waktu_catat = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tanda_vital'
        verbose_name = 'Tanda Vital'
        verbose_name_plural = 'Tanda Vital'

    def __str__(self):
        return f"TTV Kunjungan #{self.id_kunjungan.nomor_antrian} - {self.id_kunjungan.id_pasien.nama}"


class BatasTTV(models.Model):
    """
    Batas Rentang Normal Parameter TTV
    """
    id = models.BigAutoField(primary_key=True)
    parameter = models.CharField(max_length=50, unique=True, verbose_name="Nama Parameter")
    nilai_min = models.DecimalField(max_digits=6, decimal_places=1, verbose_name="Nilai Minimum")
    nilai_maks = models.DecimalField(max_digits=6, decimal_places=1, verbose_name="Nilai Maksimum")

    class Meta:
        db_table = 'batas_ttv'
        verbose_name = 'Batas TTV'
        verbose_name_plural = 'Batas TTV'

    def __str__(self):
        return f"{self.parameter}: {self.nilai_min} - {self.nilai_maks}"


class Pemeriksaan(models.Model):
    """
    Pemeriksaan Medis oleh Dokter
    """
    id_pemeriksaan = models.BigAutoField(primary_key=True)
    id_kunjungan = models.OneToOneField(
        Kunjungan, on_delete=models.CASCADE, related_name='pemeriksaan', db_column='id_kunjungan'
    )
    id_dokter = models.ForeignKey(
        Pengguna, on_delete=models.PROTECT, related_name='pemeriksaan_dokter', db_column='id_dokter'
    )
    anamnesis_lanjutan = EncryptedTextField(verbose_name="Anamnesis Lanjutan")
    riwayat_konsumsi_obat = EncryptedTextField(blank=True, default='', verbose_name="Riwayat Konsumsi Obat")
    pemeriksaan_fisik = EncryptedTextField(verbose_name="Pemeriksaan Fisik")
    waktu_periksa = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Pemeriksaan")

    class Meta:
        db_table = 'pemeriksaan'
        verbose_name = 'Pemeriksaan'
        verbose_name_plural = 'Pemeriksaan'

    def __str__(self):
        return f"Pemeriksaan #{self.id_pemeriksaan} - {self.id_kunjungan.id_pasien.nama}"


class ICD10(models.Model):
    """
    Master Data ICD-10
    """
    kode_icd10 = models.CharField(max_length=10, primary_key=True, verbose_name="Kode ICD-10")
    deskripsi = models.CharField(max_length=255, db_index=True, verbose_name="Deskripsi Penyakit")

    class Meta:
        db_table = 'icd10'
        verbose_name = 'ICD-10'
        verbose_name_plural = 'ICD-10'

    def __str__(self):
        return f"{self.kode_icd10} - {self.deskripsi}"


class Diagnosis(models.Model):
    """
    Diagnosis Pasien per Pemeriksaan
    """
    JENIS_DIAGNOSIS_CHOICES = (
        ('primer', 'Primer'),
        ('sekunder', 'Sekunder'),
    )

    id_diagnosis = models.BigAutoField(primary_key=True)
    id_pemeriksaan = models.ForeignKey(
        Pemeriksaan, on_delete=models.CASCADE, related_name='diagnosa', db_column='id_pemeriksaan'
    )
    kode_icd10 = models.ForeignKey(
        ICD10, on_delete=models.PROTECT, related_name='diagnosa', db_column='kode_icd10'
    )
    jenis_diagnosis = models.CharField(max_length=10, choices=JENIS_DIAGNOSIS_CHOICES, verbose_name="Jenis Diagnosis")

    class Meta:
        db_table = 'diagnosis'
        verbose_name = 'Diagnosis'
        verbose_name_plural = 'Diagnosis'

    def __str__(self):
        return f"{self.jenis_diagnosis.capitalize()}: {self.kode_icd10.kode_icd10}"

    def clean(self):
        super().clean()
        if self.jenis_diagnosis == 'primer':
            qs = Diagnosis.objects.filter(id_pemeriksaan=self.id_pemeriksaan, jenis_diagnosis='primer')
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Hanya diperbolehkan maksimal 1 diagnosis primer per pemeriksaan.")


class Tindakan(models.Model):
    """
    Tindakan Medis oleh Dokter
    """
    id_tindakan = models.BigAutoField(primary_key=True)
    id_pemeriksaan = models.ForeignKey(
        Pemeriksaan, on_delete=models.CASCADE, related_name='tindakan', db_column='id_pemeriksaan'
    )
    nama_tindakan = models.CharField(max_length=150, verbose_name="Nama Tindakan")
    catatan_tindakan = EncryptedTextField(blank=True, default='', verbose_name="Catatan Tindakan")

    class Meta:
        db_table = 'tindakan'
        verbose_name = 'Tindakan'
        verbose_name_plural = 'Tindakan'

    def __str__(self):
        return f"{self.nama_tindakan} ({self.id_pemeriksaan.id_kunjungan.id_pasien.nama})"


class Obat(models.Model):
    """
    Master Data Obat & Inventaris Klinik
    """
    kode_obat = models.CharField(max_length=30, primary_key=True, verbose_name="Kode Obat")
    nama_obat = models.CharField(max_length=150, db_index=True, verbose_name="Nama Obat")
    satuan = models.CharField(max_length=50, verbose_name="Satuan (tablet, botol, strip, dll)")
    stok_tersedia = models.IntegerField(default=0, verbose_name="Stok Tersedia")
    stok_minimum = models.IntegerField(default=10, verbose_name="Stok Minimum")
    zat_aktif = models.CharField(max_length=150, blank=True, default='', verbose_name="Zat Aktif")
    kelompok_obat = models.CharField(max_length=150, blank=True, default='', verbose_name="Kelompok Obat (mis. penisilin)")
    status_aktif = models.BooleanField(default=True, verbose_name="Status Aktif")

    class Meta:
        db_table = 'obat'
        verbose_name = 'Obat'
        verbose_name_plural = 'Obat'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stok_tersedia__gte=0),
                name='check_stok_tersedia_non_negatif'
            )
        ]

    def __str__(self):
        return f"{self.kode_obat} - {self.nama_obat} (Stok: {self.stok_tersedia} {self.satuan})"

    @property
    def is_stok_rendah(self):
        return self.stok_tersedia <= self.stok_minimum


class MutasiStok(models.Model):
    """
    Riwayat Mutasi Perubahan Stok Obat
    """
    JENIS_MUTASI_CHOICES = (
        ('masuk', 'Masuk'),
        ('keluar', 'Keluar'),
        ('koreksi', 'Koreksi'),
        ('resep', 'Resep'),
    )

    id = models.BigAutoField(primary_key=True)
    kode_obat = models.ForeignKey(Obat, on_delete=models.PROTECT, related_name='mutasi', db_column='kode_obat')
    jenis = models.CharField(max_length=10, choices=JENIS_MUTASI_CHOICES, verbose_name="Jenis Mutasi")
    jumlah = models.IntegerField(verbose_name="Jumlah")
    waktu = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Mutasi")
    id_pengguna = models.ForeignKey(
        Pengguna, on_delete=models.PROTECT, related_name='mutasi_stok', db_column='id_pengguna'
    )
    keterangan = models.CharField(max_length=255, blank=True, default='', verbose_name="Keterangan")

    class Meta:
        db_table = 'mutasi_stok'
        verbose_name = 'Mutasi Stok'
        verbose_name_plural = 'Mutasi Stok'
        ordering = ['-waktu']

    def __str__(self):
        return f"{self.kode_obat.nama_obat} - {self.jenis} {self.jumlah} ({self.waktu.strftime('%Y-%m-%d %H:%M')})"


class Resep(models.Model):
    """
    Resep Digital Dokter
    """
    id_resep = models.BigAutoField(primary_key=True)
    id_pemeriksaan = models.ForeignKey(
        Pemeriksaan, on_delete=models.CASCADE, related_name='resep', db_column='id_pemeriksaan'
    )
    tanggal_resep = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Resep")
    catatan = models.TextField(blank=True, default='', verbose_name="Catatan Resep")

    class Meta:
        db_table = 'resep'
        verbose_name = 'Resep'
        verbose_name_plural = 'Resep'

    def __str__(self):
        return f"Resep #{self.id_resep} - {self.id_pemeriksaan.id_kunjungan.id_pasien.nama}"


class DetailResep(models.Model):
    """
    Rincian Obat pada Resep Digital
    """
    id_detail = models.BigAutoField(primary_key=True)
    id_resep = models.ForeignKey(Resep, on_delete=models.CASCADE, related_name='details', db_column='id_resep')
    kode_obat = models.ForeignKey(Obat, on_delete=models.PROTECT, related_name='detail_resep', db_column='kode_obat')
    jumlah = models.IntegerField(verbose_name="Jumlah Obat")
    dosis = models.CharField(max_length=100, verbose_name="Dosis (mis. 500 mg)")
    aturan_pakai = models.CharField(max_length=150, verbose_name="Aturan Pakai (mis. 3x1 setelah makan)")

    class Meta:
        db_table = 'detail_resep'
        verbose_name = 'Detail Resep'
        verbose_name_plural = 'Detail Resep'

    def __str__(self):
        return f"{self.kode_obat.nama_obat} ({self.jumlah} {self.kode_obat.satuan}) - {self.aturan_pakai}"


class HasilLab(models.Model):
    """
    Lampiran Hasil Laboratorium Eksternal Penunjang
    """
    id_hasil_lab = models.BigAutoField(primary_key=True)
    id_kunjungan = models.ForeignKey(
        Kunjungan, on_delete=models.CASCADE, related_name='hasil_lab', db_column='id_kunjungan'
    )
    id_pencatat = models.ForeignKey(
        Pengguna, on_delete=models.PROTECT, related_name='lab_dicatat', db_column='id_pencatat'
    )
    jenis_pemeriksaan = models.CharField(max_length=150, verbose_name="Jenis Pemeriksaan")
    sumber_fasilitas = models.CharField(max_length=150, verbose_name="Sumber Fasilitas / Laboratorium")
    tanggal_pemeriksaan = models.DateField(verbose_name="Tanggal Pemeriksaan")
    hasil_lab = EncryptedTextField(verbose_name="Hasil / Ringkasan Lab")
    file_lampiran = models.FileField(upload_to='lab/%Y/%m/', null=True, blank=True, verbose_name="File Lampiran (PDF/JPG/PNG, Max 5MB)")
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hasil_lab'
        verbose_name = 'Hasil Laboratorium'
        verbose_name_plural = 'Hasil Laboratorium'
        ordering = ['-tanggal_pemeriksaan']

    def __str__(self):
        return f"Lab {self.jenis_pemeriksaan} - {self.id_kunjungan.id_pasien.nama}"
