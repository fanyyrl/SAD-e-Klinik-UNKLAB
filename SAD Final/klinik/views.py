import os
import mimetypes
from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Count, Q, Max
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, FileResponse, Http404
from django.core.paginator import Paginator

from .models import (
    Pengguna, Pasien, AlergiPasien, Kunjungan, TandaVital,
    BatasTTV, Pemeriksaan, ICD10, Diagnosis, Tindakan,
    Obat, MutasiStok, Resep, DetailResep, HasilLab
)
from .forms import (
    LoginForm, PasienForm, KunjunganForm, TandaVitalForm,
    PemeriksaanForm, AlergiPasienForm, ObatForm, MutasiStokForm, HasilLabForm
)
from .decorators import role_required


# ==========================================
# UC-01: AUTENTIKASI (L-01 Login & Logout)
# ==========================================

def login_view(request):
    """L-01: Login Pengguna (Staf Klinik / Dokter)"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.status_aktif and user.is_active:
                    login(request, user)
                    messages.success(request, f"Selamat datang, {user.nama_lengkap} ({user.get_role_akses_display()}).")
                    next_url = request.GET.get('next') or 'dashboard'
                    return redirect(next_url)
                else:
                    messages.error(request, "Akun Anda dinonaktifkan. Silakan hubungi administrator.")
            else:
                messages.error(request, "Username/Password salah")
        else:
            messages.error(request, "Mohon lengkapi username dan password dengan benar.")

    return render(request, 'klinik/login.html', {'form': form, 'judul': 'L-01 Login - e-Klinik UNKLAB'})


@login_required
def logout_view(request):
    """Logout pengguna dan akhiri sesi"""
    logout(request)
    messages.info(request, "Anda telah berhasil keluar dari sistem.")
    return redirect('login')


# ==========================================
# UC-02: DASHBOARD ANALITIK (L-02)
# ==========================================

@login_required
def dashboard_view(request):
    """L-02: Dashboard Analitik Kesehatan"""
    today = timezone.localdate()
    today_start = timezone.make_aware(timezone.datetime(today.year, today.month, today.day, 0, 0, 0))
    today_end = timezone.make_aware(timezone.datetime(today.year, today.month, today.day, 23, 59, 59))

    # Kartu Ringkasan Hari Ini
    kunjungan_hari_ini = Kunjungan.objects.filter(tanggal_waktu__range=(today_start, today_end)).count()
    antrean_menunggu = Kunjungan.objects.filter(
        tanggal_waktu__range=(today_start, today_end),
        status_antrian__in=['menunggu', 'dipanggil']
    ).count()
    pasien_dilayani = Kunjungan.objects.filter(
        tanggal_waktu__range=(today_start, today_end),
        status_antrian__in=['dilayani', 'selesai']
    ).count()
    ttv_abnormal_hari_ini = Kunjungan.objects.filter(
        tanggal_waktu__range=(today_start, today_end),
        prioritas_abnormal=True
    ).count()

    # Filter rentang waktu untuk grafik kunjungan
    rentang = request.GET.get('rentang', '1_bulan')
    end_date = today
    if rentang == '7_hari':
        start_date = today - timedelta(days=6)
    elif rentang == '3_bulan':
        start_date = today - timedelta(days=90)
    elif rentang == 'kustom':
        s_str = request.GET.get('start_date')
        e_str = request.GET.get('end_date')
        try:
            start_date = timezone.datetime.strptime(s_str, '%Y-%m-%d').date() if s_str else today - timedelta(days=30)
            end_date = timezone.datetime.strptime(e_str, '%Y-%m-%d').date() if e_str else today
        except ValueError:
            start_date = today - timedelta(days=30)
    else:  # default 1_bulan
        rentang = '1_bulan'
        start_date = today - timedelta(days=29)

    chart_start_dt = timezone.make_aware(timezone.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0))
    chart_end_dt = timezone.make_aware(timezone.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))

    # Agregasi Kunjungan Harian untuk Chart.js
    kunjungan_qs = Kunjungan.objects.filter(tanggal_waktu__range=(chart_start_dt, chart_end_dt))
    
    # Hitung jumlah per tanggal
    date_counts = {}
    cur = start_date
    while cur <= end_date:
        date_counts[cur.strftime('%Y-%m-%d')] = 0
        cur += timedelta(days=1)

    for k in kunjungan_qs:
        k_local_date = timezone.localtime(k.tanggal_waktu).date().strftime('%Y-%m-%d')
        if k_local_date in date_counts:
            date_counts[k_local_date] += 1

    chart_labels = list(date_counts.keys())
    chart_values = list(date_counts.values())

    # Distribusi Diagnosis ICD-10 (Top 10) - Statistik Agregat Tanpa Identitas Pasien
    top_diagnosa = Diagnosis.objects.filter(
        id_pemeriksaan__id_kunjungan__tanggal_waktu__range=(chart_start_dt, chart_end_dt)
    ).values('kode_icd10__kode_icd10', 'kode_icd10__deskripsi').annotate(
        total=Count('id_diagnosis')
    ).order_by('-total')[:10]

    icd_labels = [f"{d['kode_icd10__kode_icd10']} - {d['kode_icd10__deskripsi'][:25]}" for d in top_diagnosa]
    icd_values = [d['total'] for d in top_diagnosa]

    # Stok Obat di Bawah Minimum
    obat_stok_kritis = Obat.objects.filter(
        status_aktif=True,
        stok_tersedia__lte=models.F('stok_minimum')
    ).order_by('stok_tersedia')[:10]

    context = {
        'judul': 'L-02 Dashboard Analitik Kesehatan',
        'kunjungan_hari_ini': kunjungan_hari_ini,
        'antrean_menunggu': antrean_menunggu,
        'pasien_dilayani': pasien_dilayani,
        'ttv_abnormal_hari_ini': ttv_abnormal_hari_ini,
        'rentang': rentang,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'icd_labels': icd_labels,
        'icd_values': icd_values,
        'top_diagnosa': top_diagnosa,
        'obat_stok_kritis': obat_stok_kritis,
    }
    return render(request, 'klinik/dashboard.html', context)


# ==========================================
# UC-03, UC-04, UC-05: DATA & VERIFIKASI PASIEN (L-03, L-04)
# ==========================================

@login_required
def pasien_list_view(request):
    """L-03: Data Pasien (Daftar & Pencarian)"""
    q = request.GET.get('q', '').strip()
    pasien_qs = Pasien.objects.all().order_by('-id_pasien')
    if q:
        pasien_qs = pasien_qs.filter(
            Q(nim_id__icontains=q) | Q(nama__icontains=q) | Q(fakultas__icontains=q)
        )

    paginator = Paginator(pasien_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'judul': 'L-03 Data Pasien',
        'page_obj': page_obj,
        'q': q,
        'total_pasien': pasien_qs.count(),
    }
    return render(request, 'klinik/pasien_list.html', context)


@login_required
@role_required(['staf_klinik'])
def pasien_create_view(request):
    """Tambah Pasien Baru (UC-03, UC-05)"""
    if request.method == 'POST':
        form = PasienForm(request.POST)
        if form.is_valid():
            pasien = form.save()
            messages.success(request, f"Data pasien {pasien.nama} (NIM: {pasien.nim_id}) berhasil disimpan!")
            return redirect('pasien_verifikasi_detail', id_pasien=pasien.id_pasien)
        else:
            messages.error(request, "Gagal menyimpan data pasien. Periksa kolom yang bertanda bintang (*).")
    else:
        initial_nim = request.GET.get('nim', '')
        form = PasienForm(initial={'nim_id': initial_nim})

    return render(request, 'klinik/pasien_form.html', {
        'form': form,
        'judul': 'Tambah Pasien Baru',
        'is_edit': False
    })


@login_required
@role_required(['staf_klinik'])
def pasien_update_view(request, id_pasien):
    """Ubah Data Pasien (UC-03, UC-05)"""
    pasien = get_object_or_404(Pasien, pk=id_pasien)
    if request.method == 'POST':
        form = PasienForm(request.POST, instance=pasien)
        if form.is_valid():
            form.save()
            messages.success(request, f"Data pasien {pasien.nama} berhasil diperbarui!")
            return redirect('pasien_list')
        else:
            messages.error(request, "Gagal memperbarui data. Mohon periksa kembali isian form.")
    else:
        form = PasienForm(instance=pasien)

    return render(request, 'klinik/pasien_form.html', {
        'form': form,
        'pasien': pasien,
        'judul': f'Ubah Data Pasien: {pasien.nama}',
        'is_edit': True
    })


@login_required
@role_required(['staf_klinik'])
def pasien_delete_view(request, id_pasien):
    """Hapus Data Pasien dengan konfirmasi; tolak jika memiliki riwayat kunjungan (UC-03)"""
    pasien = get_object_or_404(Pasien, pk=id_pasien)

    # Validasi: Cek apakah pasien memiliki kunjungan
    if pasien.kunjungan.exists():
        messages.error(request, f"Pasien {pasien.nama} tidak dapat dihapus karena sudah memiliki riwayat kunjungan. Data harus diarsipkan.")
        return redirect('pasien_list')

    if request.method == 'POST':
        nama = pasien.nama
        pasien.delete()
        messages.success(request, f"Data pasien {nama} berhasil dihapus.")
        return redirect('pasien_list')

    return render(request, 'klinik/pasien_confirm_delete.html', {
        'pasien': pasien,
        'judul': f'Konfirmasi Hapus Pasien: {pasien.nama}'
    })


@login_required
@role_required(['staf_klinik'])
def pasien_verifikasi_view(request):
    """L-04: Pencarian dan Verifikasi Identitas Pasien (UC-04)"""
    q = request.GET.get('q', '').strip()
    hasil_pencarian = []
    sudah_mencari = False

    if q:
        sudah_mencari = True
        hasil_pencarian = Pasien.objects.filter(
            Q(nim_id__icontains=q) | Q(nama__icontains=q)
        ).prefetch_related('alergi')[:20]

    context = {
        'judul': 'L-04 Pencarian dan Verifikasi Identitas',
        'q': q,
        'hasil_pencarian': hasil_pencarian,
        'sudah_mencari': sudah_mencari,
    }
    return render(request, 'klinik/pasien_verifikasi.html', context)


@login_required
@role_required(['staf_klinik'])
def pasien_verifikasi_detail_view(request, id_pasien):
    """Detail Verifikasi Identitas dan Konfirmasi untuk Buat Kunjungan (UC-04, UC-06)"""
    pasien = get_object_or_404(Pasien.objects.prefetch_related('alergi'), pk=id_pasien)
    
    today = timezone.localdate()
    kunjungan_aktif = Kunjungan.objects.filter(
        id_pasien=pasien,
        tanggal_waktu__date=today,
        status_antrian__in=['menunggu', 'dipanggil', 'dilayani']
    ).first()

    context = {
        'judul': 'L-04 Verifikasi Pasien: ' + pasien.nama,
        'pasien': pasien,
        'kunjungan_aktif': kunjungan_aktif,
    }
    return render(request, 'klinik/pasien_verifikasi_detail.html', context)


# ==========================================
# UC-06: BUAT KUNJUNGAN & FIFO (L-05)
# ==========================================

@login_required
@role_required(['staf_klinik'])
def kunjungan_create_view(request, id_pasien):
    """L-05: Buat Kunjungan Pasien Terverifikasi (UC-06)"""
    pasien = get_object_or_404(Pasien, pk=id_pasien)

    if request.method == 'POST':
        form = KunjunganForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                today = timezone.localdate()
                max_nomor = Kunjungan.objects.filter(tanggal_waktu__date=today).aggregate(
                    Max('nomor_antrian')
                )['nomor_antrian__max'] or 0
                nomor_antrian_baru = max_nomor + 1

                kunjungan = form.save(commit=False)
                kunjungan.id_pasien = pasien
                kunjungan.tanggal_waktu = timezone.now()
                kunjungan.nomor_antrian = nomor_antrian_baru
                kunjungan.status_antrian = 'menunggu'
                kunjungan.status_verifikasi = True
                kunjungan.status_pemeriksaan_awal = 'belum_ttv'
                kunjungan.prioritas_abnormal = False
                kunjungan.save()

            messages.success(
                request,
                f"Kunjungan berhasil dibuat! Pasien {pasien.nama} mendapatkan Nomor Antrean #{nomor_antrian_baru}."
            )
            return redirect('ttv_create_or_update', id_kunjungan=kunjungan.id_kunjungan)
        else:
            messages.error(request, "Gagal membuat kunjungan. Mohon lengkapi keluhan utama.")
    else:
        form = KunjunganForm()

    return render(request, 'klinik/kunjungan_form.html', {
        'form': form,
        'pasien': pasien,
        'judul': 'L-05 Buat Kunjungan: ' + pasien.nama
    })


# ==========================================
# UC-07: ANTREAN DIGITAL (L-06)
# ==========================================

@login_required
def antrean_view(request):
    """L-06: Antrean Digital Berbasis FIFO (Staf & Dokter)"""
    today = timezone.localdate()
    antrean_qs = Kunjungan.objects.filter(
        tanggal_waktu__date=today
    ).select_related('id_pasien', 'tanda_vital').order_by('tanggal_waktu')

    menunggu_count = antrean_qs.filter(status_antrian='menunggu').count()
    dipanggil_count = antrean_qs.filter(status_antrian='dipanggil').count()
    dilayani_count = antrean_qs.filter(status_antrian='dilayani').count()
    ditunda_count = antrean_qs.filter(status_antrian='ditunda').count()
    selesai_count = antrean_qs.filter(status_antrian='selesai').count()

    context = {
        'judul': 'L-06 Antrean Digital',
        'antrean_list': antrean_qs,
        'today': today,
        'menunggu_count': menunggu_count,
        'dipanggil_count': dipanggil_count,
        'dilayani_count': dilayani_count,
        'ditunda_count': ditunda_count,
        'selesai_count': selesai_count,
    }
    return render(request, 'klinik/antrean.html', context)


@login_required
def antrean_api_today(request):
    """API JSON ringan untuk auto-refresh polling antrean (UC-07)"""
    today = timezone.localdate()
    antrean_qs = Kunjungan.objects.filter(
        tanggal_waktu__date=today
    ).select_related('id_pasien').order_by('tanggal_waktu')

    data = []
    for k in antrean_qs:
        data.append({
            'id_kunjungan': k.id_kunjungan,
            'nomor_antrian': k.nomor_antrian,
            'nim_id': k.id_pasien.nim_id,
            'nama_pasien': k.id_pasien.nama,
            'waktu_kedatangan': timezone.localtime(k.tanggal_waktu).strftime('%H:%M'),
            'status_antrian': k.status_antrian,
            'status_antrian_display': k.get_status_antrian_display(),
            'status_pemeriksaan_awal': k.status_pemeriksaan_awal,
            'prioritas_abnormal': k.prioritas_abnormal,
        })
    return JsonResponse({'status': 'ok', 'antrean': data})


@login_required
@role_required(['staf_klinik'])
def antrean_update_status_view(request, id_kunjungan, status_baru):
    """Perbarui status antrean: dipanggil, dilayani, ditunda, selesai (UC-07)"""
    kunjungan = get_object_or_404(Kunjungan, pk=id_kunjungan)
    valid_statuses = ['menunggu', 'dipanggil', 'dilayani', 'ditunda', 'selesai']

    if status_baru not in valid_statuses:
        messages.error(request, f"Status antrean '{status_baru}' tidak valid.")
        return redirect('antrean')

    kunjungan.status_antrian = status_baru
    kunjungan.save()
    messages.success(request, f"Antrean #{kunjungan.nomor_antrian} ({kunjungan.id_pasien.nama}) dialihkan ke status: {kunjungan.get_status_antrian_display()}.")
    return redirect('antrean')


# ==========================================
# UC-08 & UC-09: KELUHAN & TANDA VITAL (L-07)
# ==========================================

def evaluasi_ttv_abnormal(ttv_dict):
    """
    Mengevaluasi apakah parameter TTV berada di luar batas normal BatasTTV.
    Mengembalikan: (is_abnormal: bool, list_abnormal_params: list)
    """
    batas_map = {b.parameter: (b.nilai_min, b.nilai_maks) for b in BatasTTV.objects.all()}
    abnormal_params = []

    # Sistolik
    if 'sistolik' in batas_map and ttv_dict.get('tekanan_sistolik') is not None:
        min_v, max_v = batas_map['sistolik']
        val = ttv_dict['tekanan_sistolik']
        if val < min_v or val > max_v:
            abnormal_params.append(f"Tekanan Sistolik: {val} mmHg (Normal: {min_v}-{max_v})")

    # Diastolik
    if 'diastolik' in batas_map and ttv_dict.get('tekanan_diastolik') is not None:
        min_v, max_v = batas_map['diastolik']
        val = ttv_dict['tekanan_diastolik']
        if val < min_v or val > max_v:
            abnormal_params.append(f"Tekanan Diastolik: {val} mmHg (Normal: {min_v}-{max_v})")

    # Nadi
    if 'nadi' in batas_map and ttv_dict.get('nadi') is not None:
        min_v, max_v = batas_map['nadi']
        val = ttv_dict['nadi']
        if val < min_v or val > max_v:
            abnormal_params.append(f"Nadi: {val} x/m (Normal: {min_v}-{max_v})")

    # Suhu
    if 'suhu' in batas_map and ttv_dict.get('suhu_tubuh') is not None:
        min_v, max_v = batas_map['suhu']
        val = Decimal(str(ttv_dict['suhu_tubuh']))
        if val < min_v or val > max_v:
            abnormal_params.append(f"Suhu Tubuh: {val} °C (Normal: {min_v}-{max_v})")

    # Respirasi
    if 'respirasi' in batas_map and ttv_dict.get('respirasi') is not None:
        min_v, max_v = batas_map['respirasi']
        val = ttv_dict['respirasi']
        if val < min_v or val > max_v:
            abnormal_params.append(f"Respirasi: {val} x/m (Normal: {min_v}-{max_v})")

    # SpO2
    if 'spo2' in batas_map and ttv_dict.get('saturasi_oksigen') is not None:
        min_v, max_v = batas_map['spo2']
        val = ttv_dict['saturasi_oksigen']
        if val < min_v or val > max_v:
            abnormal_params.append(f"Saturasi Oksigen (SpO2): {val}% (Normal: {min_v}-{max_v})")

    return (len(abnormal_params) > 0, abnormal_params)


@login_required
@role_required(['staf_klinik'])
def ttv_create_or_update_view(request, id_kunjungan):
    """L-07: Keluhan dan Tanda Vital (UC-08, UC-09)"""
    kunjungan = get_object_or_404(
        Kunjungan.objects.select_related('id_pasien'),
        pk=id_kunjungan
    )
    ttv_instance = getattr(kunjungan, 'tanda_vital', None)
    batas_list = BatasTTV.objects.all()

    if request.method == 'POST':
        form = TandaVitalForm(request.POST, instance=ttv_instance)
        keluhan_input = request.POST.get('keluhan_utama', '').strip()

        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Update keluhan utama jika diubah
                    if keluhan_input:
                        kunjungan.keluhan_utama = keluhan_input

                    # 2. Evaluasi apakah parameter TTV abnormal
                    cd = form.cleaned_data
                    is_abnormal, abnormal_list = evaluasi_ttv_abnormal(cd)

                    ttv = form.save(commit=False)
                    ttv.id_kunjungan = kunjungan
                    ttv.id_pencatat = request.user
                    ttv.status_abnormal = is_abnormal
                    ttv.save()

                    # 3. Update status pemeriksaan awal kunjungan
                    kunjungan.status_pemeriksaan_awal = 'siap_diperiksa'
                    kunjungan.prioritas_abnormal = is_abnormal
                    kunjungan.save()

                if is_abnormal:
                    messages.warning(
                        request,
                        f"PERINGATAN TTV ABNORMAL! Data berhasil disimpan. Parameter abnormal: {'; '.join(abnormal_list)}. Status prioritas dokter diaktifkan."
                    )
                else:
                    messages.success(request, f"Data TTV untuk pasien {kunjungan.id_pasien.nama} berhasil disimpan dengan status normal.")

                return redirect('antrean')

            except Exception as e:
                messages.error(request, f"Terjadi kesalahan saat menyimpan data TTV: {str(e)}")
        else:
            messages.error(request, "Gagal menyimpan TTV. Mohon periksa nilai parameter pada form.")
    else:
        form = TandaVitalForm(instance=ttv_instance)

    context = {
        'judul': 'L-07 Keluhan dan Tanda Vital',
        'kunjungan': kunjungan,
        'form': form,
        'ttv_instance': ttv_instance,
        'batas_list': batas_list,
    }
    return render(request, 'klinik/ttv_form.html', context)


# ==========================================
# UC-10: INVENTARIS OBAT (L-08)
# ==========================================

@login_required
@role_required(['staf_klinik'])
def obat_list_view(request):
    """L-08: Inventaris Obat Klinik"""
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'semua')

    obat_qs = Obat.objects.all().order_by('nama_obat')
    if q:
        obat_qs = obat_qs.filter(
            Q(kode_obat__icontains=q) | Q(nama_obat__icontains=q) |
            Q(zat_aktif__icontains=q) | Q(kelompok_obat__icontains=q)
        )

    if status_filter == 'kritis':
        obat_qs = obat_qs.filter(stok_tersedia__lte=models.F('stok_minimum'))
    elif status_filter == 'aktif':
        obat_qs = obat_qs.filter(status_aktif=True)
    elif status_filter == 'nonaktif':
        obat_qs = obat_qs.filter(status_aktif=False)

    paginator = Paginator(obat_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'judul': 'L-08 Inventaris Obat',
        'page_obj': page_obj,
        'q': q,
        'status_filter': status_filter,
    }
    return render(request, 'klinik/obat_list.html', context)


@login_required
@role_required(['staf_klinik'])
def obat_create_view(request):
    """Tambah Obat Baru (UC-10)"""
    if request.method == 'POST':
        form = ObatForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                obat = form.save()
                if obat.stok_tersedia > 0:
                    MutasiStok.objects.create(
                        kode_obat=obat,
                        jenis='masuk',
                        jumlah=obat.stok_tersedia,
                        id_pengguna=request.user,
                        keterangan='Stok awal pendaftaran obat baru'
                    )
            messages.success(request, f"Obat {obat.nama_obat} ({obat.kode_obat}) berhasil ditambahkan!")
            return redirect('obat_list')
        else:
            messages.error(request, "Gagal menambahkan obat. Periksa kembali isian form.")
    else:
        form = ObatForm()

    return render(request, 'klinik/obat_form.html', {
        'form': form,
        'judul': 'Tambah Obat Baru',
        'is_edit': False
    })


@login_required
@role_required(['staf_klinik'])
def obat_update_view(request, kode_obat):
    """Ubah Data Master Obat (UC-10)"""
    obat = get_object_or_404(Obat, pk=kode_obat)
    if request.method == 'POST':
        form = ObatForm(request.POST, instance=obat)
        if form.is_valid():
            form.save()
            messages.success(request, f"Data obat {obat.nama_obat} berhasil diperbarui.")
            return redirect('obat_list')
        else:
            messages.error(request, "Gagal memperbarui data obat.")
    else:
        form = ObatForm(instance=obat)

    return render(request, 'klinik/obat_form.html', {
        'form': form,
        'obat': obat,
        'judul': f'Ubah Obat: {obat.nama_obat}',
        'is_edit': True
    })


@login_required
@role_required(['staf_klinik'])
def obat_mutasi_view(request, kode_obat):
    """Kelola Mutasi Stok Obat: Masuk, Keluar, Koreksi (UC-10)"""
    obat = get_object_or_404(Obat, pk=kode_obat)
    riwayat_mutasi = MutasiStok.objects.filter(kode_obat=obat).select_related('id_pengguna')[:20]

    if request.method == 'POST':
        form = MutasiStokForm(request.POST)
        if form.is_valid():
            jenis = form.cleaned_data['jenis']
            jumlah = form.cleaned_data['jumlah']
            keterangan = form.cleaned_data['keterangan']

            with transaction.atomic():
                obat_locked = Obat.objects.select_for_update().get(pk=obat.pk)

                if jenis == 'masuk':
                    obat_locked.stok_tersedia += jumlah
                elif jenis == 'keluar':
                    if obat_locked.stok_tersedia < jumlah:
                        messages.error(request, f"Gagal mutasi: Stok tersedia ({obat_locked.stok_tersedia}) tidak mencukupi untuk pengurangan {jumlah} {obat.satuan}.")
                        return redirect('obat_mutasi', kode_obat=obat.pk)
                    obat_locked.stok_tersedia -= jumlah
                elif jenis == 'koreksi':
                    obat_locked.stok_tersedia = jumlah
                    keterangan = f"Koreksi fisik dari {obat.stok_tersedia} menjadi {jumlah}. " + keterangan

                obat_locked.save()
                MutasiStok.objects.create(
                    kode_obat=obat_locked,
                    jenis=jenis,
                    jumlah=jumlah,
                    id_pengguna=request.user,
                    keterangan=keterangan
                )

            messages.success(request, f"Mutasi stok {obat.nama_obat} ({jenis.capitalize()}: {jumlah}) berhasil disimpan! Sisa stok: {obat_locked.stok_tersedia} {obat.satuan}.")
            return redirect('obat_mutasi', kode_obat=obat.pk)
        else:
            messages.error(request, "Isian formulir mutasi tidak valid.")
    else:
        form = MutasiStokForm()

    return render(request, 'klinik/obat_mutasi.html', {
        'form': form,
        'obat': obat,
        'riwayat_mutasi': riwayat_mutasi,
        'judul': f'Mutasi Stok: {obat.nama_obat}'
    })


@login_required
@role_required(['staf_klinik'])
def obat_delete_view(request, kode_obat):
    """Hapus Obat: Tolak jika sudah terpakai di resep -> nonaktifkan (UC-10)"""
    obat = get_object_or_404(Obat, pk=kode_obat)

    if obat.detail_resep.exists():
        if request.method == 'POST':
            obat.status_aktif = False
            obat.save()
            messages.info(request, f"Obat {obat.nama_obat} sudah pernah diresepkan, sehingga dinonaktifkan (arsip) dan tidak dapat dihapus permanen.")
            return redirect('obat_list')
        return render(request, 'klinik/obat_confirm_deactivate.html', {
            'obat': obat,
            'judul': f'Nonaktifkan Obat: {obat.nama_obat}'
        })

    if request.method == 'POST':
        nama = obat.nama_obat
        obat.delete()
        messages.success(request, f"Obat {nama} berhasil dihapus permanen.")
        return redirect('obat_list')

    return render(request, 'klinik/obat_confirm_delete.html', {
        'obat': obat,
        'judul': f'Konfirmasi Hapus Obat: {obat.nama_obat}'
    })


# ==========================================
# UC-11: RIWAYAT MEDIS PASIEN (L-09) — DOKTER ONLY
# ==========================================

@login_required
@role_required(['dokter'])
def riwayat_medis_view(request, id_pasien):
    """L-09: Riwayat Medis Pasien (UC-11) — Sangat rahasia, dioptimalkan < 3 detik"""
    pasien = get_object_or_404(
        Pasien.objects.prefetch_related('alergi'),
        pk=id_pasien
    )

    if request.method == 'POST' and 'tambah_alergi' in request.POST:
        alergi_form = AlergiPasienForm(request.POST)
        if alergi_form.is_valid():
            al = alergi_form.save(commit=False)
            al.id_pasien = pasien
            al.save()
            messages.success(request, f"Alergi {al.nama_alergen} berhasil ditambahkan pada pasien {pasien.nama}.")
            return redirect('riwayat_medis', id_pasien=pasien.id_pasien)
        else:
            messages.error(request, "Gagal menambahkan catatan alergi.")
    else:
        alergi_form = AlergiPasienForm()

    kunjungan_qs = Kunjungan.objects.filter(
        id_pasien=pasien
    ).select_related(
        'tanda_vital', 'pemeriksaan', 'id_dokter'
    ).prefetch_related(
        'pemeriksaan__diagnosa__kode_icd10',
        'pemeriksaan__tindakan',
        'pemeriksaan__resep__details__kode_obat',
        'hasil_lab'
    ).order_by('-tanggal_waktu')

    paginator = Paginator(kunjungan_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'judul': 'L-09 Riwayat Medis Pasien',
        'pasien': pasien,
        'page_obj': page_obj,
        'alergi_list': pasien.alergi.all(),
        'alergi_form': alergi_form,
    }
    return render(request, 'klinik/riwayat_medis.html', context)


# ==========================================
# UC-12: PEMERIKSAAN MEDIS (L-10) — DOKTER ONLY
# ==========================================

@login_required
@role_required(['dokter'])
def pemeriksaan_view(request, id_kunjungan):
    """L-10: Pemeriksaan Medis oleh Dokter (UC-12)"""
    kunjungan = get_object_or_404(
        Kunjungan.objects.select_related('id_pasien', 'tanda_vital'),
        pk=id_kunjungan
    )
    pemeriksaan_instance = getattr(kunjungan, 'pemeriksaan', None)
    alergi_pasien = kunjungan.id_pasien.alergi.all()
    ttv = getattr(kunjungan, 'tanda_vital', None)

    if request.method == 'POST':
        form = PemeriksaanForm(request.POST, instance=pemeriksaan_instance)
        if form.is_valid():
            with transaction.atomic():
                pmr = form.save(commit=False)
                pmr.id_kunjungan = kunjungan
                pmr.id_dokter = request.user
                pmr.save()

                kunjungan.id_dokter = request.user
                if kunjungan.status_antrian in ['menunggu', 'dipanggil']:
                    kunjungan.status_antrian = 'dilayani'
                kunjungan.save()

            messages.success(request, f"Data pemeriksaan klinis untuk {kunjungan.id_pasien.nama} berhasil disimpan!")
            return redirect('diagnosis_view', id_pemeriksaan=pmr.id_pemeriksaan)
        else:
            messages.error(request, "Gagal menyimpan pemeriksaan. Anamnesis lanjutan dan pemeriksaan fisik wajib diisi.")
    else:
        form = PemeriksaanForm(instance=pemeriksaan_instance)

    context = {
        'judul': 'L-10 Pemeriksaan Medis',
        'kunjungan': kunjungan,
        'form': form,
        'ttv': ttv,
        'alergi_pasien': alergi_pasien,
        'pemeriksaan_instance': pemeriksaan_instance,
    }
    return render(request, 'klinik/pemeriksaan_form.html', context)


# ==========================================
# UC-13: DIAGNOSIS ICD-10 (L-11) — DOKTER ONLY
# ==========================================

@login_required
@role_required(['dokter'])
def diagnosis_view(request, id_pemeriksaan):
    """L-11: Diagnosis ICD-10 (UC-13)"""
    pemeriksaan = get_object_or_404(
        Pemeriksaan.objects.select_related('id_kunjungan__id_pasien'),
        pk=id_pemeriksaan
    )
    diagnosa_list = Diagnosis.objects.filter(id_pemeriksaan=pemeriksaan).select_related('kode_icd10')

    if request.method == 'POST' and 'tambah_diagnosis' in request.POST:
        kode_icd = request.POST.get('kode_icd10', '').strip().upper()
        jenis = request.POST.get('jenis_diagnosis', 'primer')

        icd_obj = ICD10.objects.filter(kode_icd10=kode_icd).first()
        if not icd_obj:
            messages.error(request, f"Kode ICD-10 '{kode_icd}' tidak ditemukan dalam master data.")
        else:
            if jenis == 'primer' and diagnosa_list.filter(jenis_diagnosis='primer').exists():
                messages.error(request, "Pemeriksaan ini sudah memiliki diagnosis primer. Ubah diagnosis primer sebelumnya atau pilih jenis Sekunder.")
            else:
                Diagnosis.objects.create(
                    id_pemeriksaan=pemeriksaan,
                    kode_icd10=icd_obj,
                    jenis_diagnosis=jenis
                )
                messages.success(request, f"Diagnosis {jenis.capitalize()} ({icd_obj.kode_icd10} - {icd_obj.deskripsi}) berhasil ditambahkan.")
                return redirect('diagnosis_view', id_pemeriksaan=pemeriksaan.pk)

    context = {
        'judul': 'L-11 Diagnosis ICD-10',
        'pemeriksaan': pemeriksaan,
        'diagnosa_list': diagnosa_list,
    }
    return render(request, 'klinik/diagnosis.html', context)


@login_required
@role_required(['dokter'])
def diagnosis_delete_view(request, id_diagnosis):
    """Hapus diagnosis dari pemeriksaan"""
    diag = get_object_or_404(Diagnosis, pk=id_diagnosis)
    id_pmr = diag.id_pemeriksaan.pk
    diag.delete()
    messages.success(request, "Diagnosis berhasil dihapus.")
    return redirect('diagnosis_view', id_pemeriksaan=id_pmr)


@login_required
def icd10_search_api(request):
    """API Autocomplete ICD-10 untuk pencarian cepat di UI dokter (UC-13)"""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})

    results = ICD10.objects.filter(
        Q(kode_icd10__icontains=q) | Q(deskripsi__icontains=q)
    )[:15]

    data = [{'kode': item.kode_icd10, 'deskripsi': item.deskripsi} for item in results]
    return JsonResponse({'results': data})


# ==========================================
# UC-14: TINDAKAN MEDIS (L-12) — DOKTER ONLY
# ==========================================

@login_required
@role_required(['dokter'])
def tindakan_view(request, id_pemeriksaan):
    """L-12: Tindakan Medis oleh Dokter (UC-14)"""
    pemeriksaan = get_object_or_404(
        Pemeriksaan.objects.select_related('id_kunjungan__id_pasien'),
        pk=id_pemeriksaan
    )
    tindakan_list = Tindakan.objects.filter(id_pemeriksaan=pemeriksaan)

    if request.method == 'POST' and 'tambah_tindakan' in request.POST:
        nama = request.POST.get('nama_tindakan', '').strip()
        catatan = request.POST.get('catatan_tindakan', '').strip()

        if not nama:
            messages.error(request, "Nama tindakan wajib diisi.")
        else:
            Tindakan.objects.create(
                id_pemeriksaan=pemeriksaan,
                nama_tindakan=nama,
                catatan_tindakan=catatan
            )
            messages.success(request, f"Tindakan '{nama}' berhasil dicatat.")
            return redirect('tindakan_view', id_pemeriksaan=pemeriksaan.pk)

    context = {
        'judul': 'L-12 Tindakan Medis',
        'pemeriksaan': pemeriksaan,
        'tindakan_list': tindakan_list,
    }
    return render(request, 'klinik/tindakan.html', context)


@login_required
@role_required(['dokter'])
def tindakan_delete_view(request, id_tindakan):
    """Hapus tindakan dari pemeriksaan"""
    tdk = get_object_or_404(Tindakan, pk=id_tindakan)
    id_pmr = tdk.id_pemeriksaan.pk
    tdk.delete()
    messages.success(request, "Tindakan berhasil dihapus.")
    return redirect('tindakan_view', id_pemeriksaan=id_pmr)


# ==========================================
# UC-15 & UC-16: RESEP DIGITAL & ALERGI (L-13) — DOKTER ONLY
# ==========================================

def cek_alergi_obat(pasien, obat):
    """
    Pencocokan Alergi Obat (UC-16, DIR-02):
    Mencocokkan obat terhadap alergi_pasien jenis 'obat'
    (nama_obat, zat_aktif, kelompok_obat; case-insensitive substring).
    Mengembalikan (is_allergic: bool, reason: str)
    """
    alergi_obat_list = pasien.alergi.filter(jenis_alergi='obat')
    for al in alergi_obat_list:
        alergen = al.nama_alergen.strip().lower()
        if not alergen:
            continue

        nama_low = obat.nama_obat.lower()
        zat_low = obat.zat_aktif.lower()
        kel_low = obat.kelompok_obat.lower()

        if (alergen in nama_low) or (alergen in zat_low) or (alergen in kel_low) or \
           (zat_low and zat_low in alergen) or (kel_low and kel_low in alergen):
            return True, f"Pasien alergi terhadap '{al.nama_alergen}' (Reaksi: {al.reaksi or 'Tidak dicatat'}). Obat ini mengandung zat/kelompok '{obat.zat_aktif or obat.kelompok_obat or obat.nama_obat}'."

    return False, ""


@login_required
@role_required(['dokter'])
def resep_view(request, id_pemeriksaan):
    """L-13: Resep Digital Dokter (UC-15, UC-16)"""
    pemeriksaan = get_object_or_404(
        Pemeriksaan.objects.select_related('id_kunjungan__id_pasien'),
        pk=id_pemeriksaan
    )
    pasien = pemeriksaan.id_kunjungan.id_pasien
    resep_instance = pemeriksaan.resep.first()
    daftar_obat = Obat.objects.filter(status_aktif=True).order_by('nama_obat')

    if request.method == 'POST':
        catatan_resep = request.POST.get('catatan_resep', '').strip()
        tandai_selesai = request.POST.get('tandai_selesai') == '1'

        obat_ids = request.POST.getlist('obat_id[]')
        jumlah_list = request.POST.getlist('jumlah[]')
        dosis_list = request.POST.getlist('dosis[]')
        aturan_list = request.POST.getlist('aturan[]')

        if not obat_ids:
            messages.error(request, "Resep harus memuat minimal 1 item obat.")
            return redirect('resep_view', id_pemeriksaan=pemeriksaan.pk)

        # 1. VALIDASI SERVER-SIDE: Peringatan Alergi Obat (UC-16, DIR-02)
        for kode_obat in obat_ids:
            if not kode_obat:
                continue
            obat_obj = Obat.objects.filter(pk=kode_obat).first()
            if obat_obj:
                is_allergic, reason = cek_alergi_obat(pasien, obat_obj)
                if is_allergic:
                    messages.error(
                        request,
                        f"🚨 BAHAYA ALERGI OBAT! Resep diblokir oleh sistem: {obat_obj.nama_obat} tidak dapat diresepkan karena {reason}"
                    )
                    return redirect('resep_view', id_pemeriksaan=pemeriksaan.pk)

        # 2. VALIDASI SERVER-SIDE: Cek Ketersediaan Stok
        for kode_obat, jml_str in zip(obat_ids, jumlah_list):
            if not kode_obat:
                continue
            try:
                jml = int(jml_str)
                if jml <= 0:
                    messages.error(request, "Jumlah obat harus lebih besar dari 0.")
                    return redirect('resep_view', id_pemeriksaan=pemeriksaan.pk)
            except ValueError:
                messages.error(request, "Jumlah obat harus berupa angka bulat.")
                return redirect('resep_view', id_pemeriksaan=pemeriksaan.pk)

            obat_obj = Obat.objects.filter(pk=kode_obat).first()
            if not obat_obj or obat_obj.stok_tersedia < jml:
                stok_ada = obat_obj.stok_tersedia if obat_obj else 0
                messages.error(
                    request,
                    f"Stok obat '{obat_obj.nama_obat if obat_obj else kode_obat}' tidak mencukupi! Dibutuhkan: {jml}, Tersedia: {stok_ada}."
                )
                return redirect('resep_view', id_pemeriksaan=pemeriksaan.pk)

        # 3. TRANSAKSI ATOMIK: Simpan Resep, Kurangi Stok, dan Catat Mutasi
        try:
            with transaction.atomic():
                if not resep_instance:
                    resep_instance = Resep.objects.create(
                        id_pemeriksaan=pemeriksaan,
                        catatan=catatan_resep
                    )
                else:
                    resep_instance.catatan = catatan_resep
                    resep_instance.save()

                for kode_obat, jml_str, dos, aturan in zip(obat_ids, jumlah_list, dosis_list, aturan_list):
                    if not kode_obat:
                        continue
                    jml = int(jml_str)
                    obat_locked = Obat.objects.select_for_update().get(pk=kode_obat)
                    if obat_locked.stok_tersedia < jml:
                        raise ValueError(f"Stok {obat_locked.nama_obat} berubah saat proses transaksi. Tersedia: {obat_locked.stok_tersedia}.")

                    obat_locked.stok_tersedia -= jml
                    obat_locked.save()

                    MutasiStok.objects.create(
                        kode_obat=obat_locked,
                        jenis='resep',
                        jumlah=jml,
                        id_pengguna=request.user,
                        keterangan=f"Pengeluaran resep #{resep_instance.id_resep} untuk pasien {pasien.nama}"
                    )

                    DetailResep.objects.create(
                        id_resep=resep_instance,
                        kode_obat=obat_locked,
                        jumlah=jml,
                        dosis=dos or 'Sesuai indikasi',
                        aturan_pakai=aturan or '3x1 sesudah makan'
                    )

                if tandai_selesai:
                    kunjungan = pemeriksaan.id_kunjungan
                    kunjungan.status_antrian = 'selesai'
                    kunjungan.save()

            messages.success(request, f"Resep digital untuk {pasien.nama} berhasil disimpan dan stok obat telah disesuaikan.")
            if tandai_selesai:
                messages.info(request, f"Kunjungan pasien {pasien.nama} telah ditandai Selesai.")
                return redirect('antrean')
            return redirect('resep_view', id_pemeriksaan=pemeriksaan.pk)

        except Exception as e:
            messages.error(request, f"Gagal memproses resep: {str(e)}")
            return redirect('resep_view', id_pemeriksaan=pemeriksaan.pk)

    context = {
        'judul': 'L-13 Resep Digital',
        'pemeriksaan': pemeriksaan,
        'pasien': pasien,
        'resep_instance': resep_instance,
        'daftar_obat': daftar_obat,
        'alergi_obat': pasien.alergi.filter(jenis_alergi='obat'),
    }
    return render(request, 'klinik/resep.html', context)


@login_required
@role_required(['dokter'])
def resep_check_medicine_api(request):
    """API Cek Alergi dan Ketersediaan Stok Obat Real-time di Form Resep (UC-15, UC-16)"""
    id_pasien = request.GET.get('pasien_id')
    kode_obat = request.GET.get('kode_obat')

    pasien = get_object_or_404(Pasien, pk=id_pasien)
    obat = get_object_or_404(Obat, pk=kode_obat)

    is_allergic, reason = cek_alergi_obat(pasien, obat)

    return JsonResponse({
        'kode_obat': obat.kode_obat,
        'nama_obat': obat.nama_obat,
        'satuan': obat.satuan,
        'stok_tersedia': obat.stok_tersedia,
        'is_allergic': is_allergic,
        'allergy_reason': reason,
    })


# ==========================================
# UC-17: HASIL LABORATORIUM (L-14) — DOKTER ONLY
# ==========================================

@login_required
@role_required(['dokter'])
def hasil_lab_view(request, id_kunjungan):
    """L-14: Hasil Laboratorium Penunjang (UC-17)"""
    kunjungan = get_object_or_404(
        Kunjungan.objects.select_related('id_pasien'),
        pk=id_kunjungan
    )
    daftar_lab = HasilLab.objects.filter(id_kunjungan=kunjungan).select_related('id_pencatat')

    if request.method == 'POST':
        form = HasilLabForm(request.POST, request.FILES)
        if form.is_valid():
            lab = form.save(commit=False)
            lab.id_kunjungan = kunjungan
            lab.id_pencatat = request.user
            lab.save()
            messages.success(request, f"Hasil laboratorium '{lab.jenis_pemeriksaan}' berhasil disimpan!")
            return redirect('hasil_lab_view', id_kunjungan=kunjungan.pk)
        else:
            messages.error(request, "Gagal mengunggah hasil lab. Pastikan format berkas PDF/JPG/PNG dan ukuran maks 5 MB.")
    else:
        form = HasilLabForm(initial={'tanggal_pemeriksaan': timezone.localdate()})

    context = {
        'judul': 'L-14 Hasil Laboratorium',
        'kunjungan': kunjungan,
        'daftar_lab': daftar_lab,
        'form': form,
    }
    return render(request, 'klinik/hasil_lab.html', context)


@login_required
@role_required(['dokter'])
def unduh_lab_view(request, id_hasil_lab):
    """
    Unduh Berkas Lampiran Lab secara aman (Hanya Dokter yang Berhak).
    Menolak akses dari peran Staf Klinik dengan HTTP 403 Forbidden.
    """
    lab = get_object_or_404(HasilLab, pk=id_hasil_lab)
    if not lab.file_lampiran:
        raise Http404("Berkas lampiran tidak ditemukan.")

    file_path = lab.file_lampiran.path
    if not os.path.exists(file_path):
        raise Http404("Berkas fisik tidak ditemukan di server.")

    mime_type, _ = mimetypes.guess_type(file_path)
    response = FileResponse(open(file_path, 'rb'), content_type=mime_type or 'application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
    return response


# ==========================================
# SELESAIKAN KUNJUNGAN
# ==========================================

@login_required
def selesaikan_kunjungan_view(request, id_kunjungan):
    """Tandai Kunjungan Selesai (oleh Staf atau Dokter)"""
    kunjungan = get_object_or_404(Kunjungan, pk=id_kunjungan)
    kunjungan.status_antrian = 'selesai'
    kunjungan.save()
    messages.success(request, f"Kunjungan pasien {kunjungan.id_pasien.nama} telah ditandai Selesai.")
    return redirect('antrean')
