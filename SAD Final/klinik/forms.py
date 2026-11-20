import os
from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import (
    Pasien, AlergiPasien, Kunjungan, TandaVital,
    Pemeriksaan, Obat, Tindakan, HasilLab
)


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': 'Masukkan username',
            'autocomplete': 'username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
            'placeholder': 'Masukkan password',
            'autocomplete': 'current-password',
            'required': True
        })
    )


class PasienForm(forms.ModelForm):
    class Meta:
        model = Pasien
        fields = ['nim_id', 'nama', 'tanggal_lahir', 'jenis_kelamin', 'fakultas', 'alamat']
        widgets = {
            'nim_id': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Contoh: 105012410033',
                'required': True
            }),
            'nama': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Nama lengkap pasien',
                'required': True
            }),
            'tanggal_lahir': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date',
                'required': True
            }),
            'jenis_kelamin': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'required': True
            }),
            'fakultas': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Contoh: Fakultas Ilmu Komputer / FEB / Staf'
            }),
            'alamat': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 3,
                'placeholder': 'Alamat asrama atau tempat tinggal di sekitar Airmadidi'
            }),
        }

    def clean_nim_id(self):
        nim_id = self.cleaned_data.get('nim_id', '').strip()
        if not nim_id:
            raise forms.ValidationError("NIM / ID Pasien wajib diisi.")
        # Cek keunikan NIM
        qs = Pasien.objects.filter(nim_id__iexact=nim_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"NIM / ID '{nim_id}' sudah terdaftar dalam sistem.")
        return nim_id

    def clean_nama(self):
        nama = self.cleaned_data.get('nama', '').strip()
        if not nama:
            raise forms.ValidationError("Nama pasien wajib diisi.")
        return nama

    def clean_tanggal_lahir(self):
        tgl = self.cleaned_data.get('tanggal_lahir')
        if not tgl:
            raise forms.ValidationError("Tanggal lahir wajib diisi.")
        if tgl > timezone.localdate():
            raise forms.ValidationError("Tanggal lahir tidak boleh di masa depan.")
        return tgl

    def clean_jenis_kelamin(self):
        jk = self.cleaned_data.get('jenis_kelamin')
        if not jk:
            raise forms.ValidationError("Jenis kelamin wajib dipilih.")
        return jk


class KunjunganForm(forms.ModelForm):
    class Meta:
        model = Kunjungan
        fields = ['keluhan_utama']
        widgets = {
            'keluhan_utama': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 3,
                'placeholder': 'Tuliskan keluhan utama pasien saat kedatangan...',
                'required': True
            }),
        }

    def clean_keluhan_utama(self):
        keluhan = self.cleaned_data.get('keluhan_utama', '').strip()
        if not keluhan:
            raise forms.ValidationError("Keluhan utama wajib diisi.")
        return keluhan


class TandaVitalForm(forms.ModelForm):
    class Meta:
        model = TandaVital
        fields = [
            'tekanan_sistolik', 'tekanan_diastolik', 'nadi', 'suhu_tubuh',
            'respirasi', 'saturasi_oksigen', 'skor_nyeri', 'berat_badan', 'catatan_eskalasi'
        ]
        widgets = {
            'tekanan_sistolik': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '120', 'min': 40, 'max': 300, 'required': True
            }),
            'tekanan_diastolik': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '80', 'min': 20, 'max': 200, 'required': True
            }),
            'nadi': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '80', 'min': 20, 'max': 250, 'required': True
            }),
            'suhu_tubuh': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '36.5', 'step': '0.1', 'min': 30.0, 'max': 45.0, 'required': True
            }),
            'respirasi': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '18', 'min': 4, 'max': 80, 'required': True
            }),
            'saturasi_oksigen': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '98', 'min': 50, 'max': 100, 'required': True
            }),
            'skor_nyeri': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '0 - 10', 'min': 0, 'max': 10
            }),
            'berat_badan': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': '60.5', 'step': '0.1', 'min': 2, 'max': 350
            }),
            'catatan_eskalasi': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 3,
                'placeholder': 'Catatan khusus eskalasi jika ditemukan parameter TTV abnormal...'
            }),
        }

    def clean_suhu_tubuh(self):
        val = self.cleaned_data.get('suhu_tubuh')
        if val is None or val < Decimal('30.0') or val > Decimal('45.0'):
            raise forms.ValidationError("Suhu tubuh harus berada di rentang realistis (30.0 - 45.0 °C).")
        return val

    def clean_nadi(self):
        val = self.cleaned_data.get('nadi')
        if val is None or val < 20 or val > 250:
            raise forms.ValidationError("Frekuensi nadi harus berada di rentang realistis (20 - 250 x/menit).")
        return val

    def clean_tekanan_sistolik(self):
        val = self.cleaned_data.get('tekanan_sistolik')
        if val is None or val < 40 or val > 300:
            raise forms.ValidationError("Tekanan sistolik harus berada di rentang realistis (40 - 300 mmHg).")
        return val

    def clean_tekanan_diastolik(self):
        val = self.cleaned_data.get('tekanan_diastolik')
        if val is None or val < 20 or val > 200:
            raise forms.ValidationError("Tekanan diastolik harus berada di rentang realistis (20 - 200 mmHg).")
        return val

    def clean_respirasi(self):
        val = self.cleaned_data.get('respirasi')
        if val is None or val < 4 or val > 80:
            raise forms.ValidationError("Frekuensi respirasi harus berada di rentang realistis (4 - 80 x/menit).")
        return val

    def clean_saturasi_oksigen(self):
        val = self.cleaned_data.get('saturasi_oksigen')
        if val is None or val < 50 or val > 100:
            raise forms.ValidationError("Saturasi oksigen (SpO2) harus berada di rentang 50 - 100%.")
        return val


class PemeriksaanForm(forms.ModelForm):
    class Meta:
        model = Pemeriksaan
        fields = ['anamnesis_lanjutan', 'riwayat_konsumsi_obat', 'pemeriksaan_fisik']
        widgets = {
            'anamnesis_lanjutan': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 4,
                'placeholder': 'Detail anamnesis tambahan, riwayat penyakit sekarang, kronologi keluhan...',
                'required': True
            }),
            'riwayat_konsumsi_obat': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 2,
                'placeholder': 'Obat yang sedang atau baru dikonsumsi pasien dalam 1-2 minggu terakhir...'
            }),
            'pemeriksaan_fisik': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 4,
                'placeholder': 'Pemeriksaan kepala, leher, thoraks, abdomen, ekstremitas, status lokalis...',
                'required': True
            }),
        }

    def clean_anamnesis_lanjutan(self):
        val = self.cleaned_data.get('anamnesis_lanjutan', '').strip()
        if not val:
            raise forms.ValidationError("Anamnesis lanjutan wajib diisi oleh dokter.")
        return val

    def clean_pemeriksaan_fisik(self):
        val = self.cleaned_data.get('pemeriksaan_fisik', '').strip()
        if not val:
            raise forms.ValidationError("Pemeriksaan fisik wajib diisi oleh dokter.")
        return val


class AlergiPasienForm(forms.ModelForm):
    class Meta:
        model = AlergiPasien
        fields = ['nama_alergen', 'jenis_alergi', 'reaksi']
        widgets = {
            'nama_alergen': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Contoh: Amoxicillin / Paracetamol / Udang',
                'required': True
            }),
            'jenis_alergi': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'required': True
            }),
            'reaksi': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Reaksi yang timbul (mis. gatal, ruam merah, bengkak, sesak)',
                'required': True
            }),
        }


class ObatForm(forms.ModelForm):
    class Meta:
        model = Obat
        fields = ['kode_obat', 'nama_obat', 'satuan', 'stok_tersedia', 'stok_minimum', 'zat_aktif', 'kelompok_obat']
        widgets = {
            'kode_obat': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'OBT-XXX',
                'required': True
            }),
            'nama_obat': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Nama obat & sediaan',
                'required': True
            }),
            'satuan': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'tablet, botol, kapsul, strip, sachet',
                'required': True
            }),
            'stok_tersedia': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'min': 0, 'required': True
            }),
            'stok_minimum': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'min': 0, 'required': True
            }),
            'zat_aktif': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Zat aktif farmakologi'
            }),
            'kelompok_obat': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Kelompok / golongan (mis. penisilin, NSAID, antihistamin)'
            }),
        }

    def clean_stok_tersedia(self):
        stok = self.cleaned_data.get('stok_tersedia')
        if stok is not None and stok < 0:
            raise forms.ValidationError("Stok obat tidak boleh bernilai negatif.")
        return stok


class MutasiStokForm(forms.Form):
    JENIS_MUTASI_CHOICES = (
        ('masuk', 'Stok Masuk (Penambahan)'),
        ('keluar', 'Stok Keluar (Pengurangan/Kadaluarsa)'),
        ('koreksi', 'Koreksi Stok (Penyesuaian Fisik)'),
    )

    jenis = forms.ChoiceField(
        choices=JENIS_MUTASI_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500'
        })
    )
    jumlah = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
            'placeholder': 'Jumlah satuan',
            'required': True
        })
    )
    keterangan = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
            'placeholder': 'Catatan mutasi (mis. Pengadaan baru dari apotek UNKLAB / expired)'
        })
    )


class HasilLabForm(forms.ModelForm):
    class Meta:
        model = HasilLab
        fields = ['jenis_pemeriksaan', 'sumber_fasilitas', 'tanggal_pemeriksaan', 'hasil_lab', 'file_lampiran']
        widgets = {
            'jenis_pemeriksaan': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Contoh: Darah Lengkap, Tes Widal, Urinalisis',
                'required': True
            }),
            'sumber_fasilitas': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Contoh: Laboratorium RS Advent Manado / Lab Pramita',
                'required': True
            }),
            'tanggal_pemeriksaan': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date',
                'required': True
            }),
            'hasil_lab': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 4,
                'placeholder': 'Ringkasan hasil uji laboratorium, nilai parameter, dan interpretasi klinis...',
                'required': True
            }),
            'file_lampiran': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-teal-500',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }

    def clean_file_lampiran(self):
        f = self.cleaned_data.get('file_lampiran')
        if f:
            # Validasi ekstensi
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                raise forms.ValidationError("Hanya berkas berformat PDF, JPG, atau PNG yang diizinkan.")
            # Validasi ukuran (maks 5MB)
            if f.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Ukuran berkas melebihi batas maksimal 5 MB.")
        return f
