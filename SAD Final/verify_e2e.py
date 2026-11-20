import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "docs", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def run_e2e_verification():
    print(f"Memulai verifikasi End-to-End dengan browser Chrome...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True
        )
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Step 1: Login Staf
        print("1. Mengakses halaman Login (L-01)...")
        page.goto(f"{BASE_URL}/login/")
        page.fill('input[name="username"]', "staf_klinik")
        page.fill('input[name="password"]', "Staf12345!")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_login_staf.png"))
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Step 2: Cari Pasien & Verifikasi (L-04)
        print("2. Mencari & Memverifikasi Pasien (L-04)...")
        page.goto(f"{BASE_URL}/pasien/verifikasi/?q=105012410033")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "02_cari_pasien_verifikasi.png"))

        # Step 3: Klik Detail Verifikasi Pasien
        print("3. Membuka Detail Verifikasi Pasien...")
        page.click('text=Verifikasi & Buat Kunjungan')
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "03_verifikasi_detail.png"))

        # Step 4: Buat Kunjungan Baru (L-05)
        print("4. Mengisi Formulir Kunjungan Baru (L-05)...")
        page.click('text=Verifikasi Identitas & Buat Kunjungan (L-05)')
        page.wait_for_load_state("networkidle")
        page.fill('textarea[name="keluhan_utama"]', "Demam tinggi sejak kemarin sore, pusing kepala berat dan badan terasa menggigil.")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "04_buat_kunjungan.png"))
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Step 5: Input Keluhan dan TTV Abnormal (L-07)
        print("5. Input Tanda Vital Abnormal (L-07)...")
        page.fill('#id_tekanan_sistolik', "135")
        page.fill('#id_tekanan_diastolik', "85")
        page.fill('#id_nadi', "115")       # ABNORMAL > 100
        page.fill('#id_suhu_tubuh', "39.5") # ABNORMAL > 37.5
        page.fill('#id_respirasi', "24")   # ABNORMAL > 20
        page.fill('#id_saturasi_oksigen', "96")
        page.fill('#id_skor_nyeri', "5")
        page.fill('#id_berat_badan', "53.5")
        page.fill('#id_catatan_eskalasi', "Demam tinggi 39.5°C dengan takikardia 115x/m dan takipnea 24x/m. Segera prioritaskan konsultasi dokter!")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "05_ttv_abnormal.png"))
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Step 6: Antrean Digital (L-06)
        print("6. Memeriksa Antrean Digital (L-06)...")
        page.goto(f"{BASE_URL}/antrean/")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "06_antrean_digital.png"))

        # Step 7: Logout Staf & Login Dokter (L-01)
        print("7. Logout Staf & Login Dokter...")
        page.goto(f"{BASE_URL}/logout/")
        page.wait_for_load_state("networkidle")
        page.fill('input[name="username"]', "dokter1")
        page.fill('input[name="password"]', "Dokter12345!")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "07_login_dokter.png"))
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Step 8: Riwayat Medis Pasien (L-09)
        print("8. Buka Riwayat Medis Pasien (L-09)...")
        page.goto(f"{BASE_URL}/rekam-medis/pasien/1/")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "08_riwayat_medis.png"))

        # Step 9: Buka Antrean & Pemeriksaan Dokter (L-10)
        print("9. Buka Pemeriksaan Klinis Dokter (L-10)...")
        page.goto(f"{BASE_URL}/antrean/")
        page.wait_for_load_state("networkidle")
        first_periksa = page.locator('text=Periksa Pasien').first
        if first_periksa.is_visible():
            first_periksa.click()
            page.wait_for_load_state("networkidle")
        else:
            page.goto(f"{BASE_URL}/pemeriksaan/1/")

        page.fill('textarea[name="anamnesis_lanjutan"]', "Pasien mengeluhkan demam tinggi akut hari ke-2 disertai nyeri retro-orbital, artralgia, dan malaise. Nafsu makan menurun.")
        page.fill('textarea[name="riwayat_konsumsi_obat"]', "Belum minum obat penurun panas.")
        page.fill('textarea[name="pemeriksaan_fisik"]', "KU: Sakit sedang, compos mentis. Suhu febris, sklera ikterik (-), konjungtiva anemis (-). Faring hiperemis (-), uji tourniquet (+).")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "09_pemeriksaan_dokter.png"))
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Step 10: Diagnosis ICD-10 (L-11)
        print("10. Diagnosis ICD-10 (L-11)...")
        page.fill('#icd-search-input', "A09")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "10_diagnosis_icd10.png"))
        page.click('button:has-text("Tambahkan Diagnosis")')
        page.wait_for_load_state("networkidle")

        # Step 11: Tindakan Medis (L-12)
        print("11. Tindakan Medis (L-12)...")
        page.click('text=Lanjut ke Tindakan (L-12)')
        page.wait_for_load_state("networkidle")
        page.fill('input[name="nama_tindakan"]', "Edukasi Rehidrasi Oral & Pengawasan Tanda Bahaya DBD")
        page.fill('textarea[name="catatan_tindakan"]', "Instruksi minum cairan minimal 2.5 liter per hari (air mineral, jus buah, oralit). Segera ke IGD jika timbul perdarahan spontan atau muntah terus menerus.")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "11_tindakan_medis.png"))
        page.click('button:has-text("Catat Tindakan Ini")')
        page.wait_for_load_state("networkidle")

        # Step 12: Resep Digital dengan Alergi Terblokir (L-13)
        print("12. Uji Resep Digital - Deteksi Alergi Amoxicillin (DIR-02)...")
        page.click('text=Lanjut ke Resep Digital (L-13)')
        page.wait_for_load_state("networkidle")
        # Pilih obat Amoxicillin yang pasien punya alergi
        page.select_option('select.select-obat', 'OBT-AMX')
        page.dispatch_event('select.select-obat', 'change')
        time.sleep(1.5) # Biarkan AJAX cek alergi berjalan
        page.screenshot(path=os.path.join(OUTPUT_DIR, "12_resep_alergi_terblokir.png"))

        # Step 13: Ganti dengan Obat Aman (Paracetamol) & Selesaikan Resep
        print("13. Ganti dengan Paracetamol & Selesaikan Resep...")
        page.select_option('select.select-obat', 'OBT-001')
        page.dispatch_event('select.select-obat', 'change')
        time.sleep(1.5)
        page.fill('input.input-jumlah', "15")
        page.fill('input[name="dosis[]"]', "500 mg")
        page.fill('input[name="aturan[]"]', "3x1 tablet bila demam")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "13_resep_valid_dan_selesai.png"))
        page.click('#btn-simpan-resep')
        page.wait_for_load_state("networkidle")

        # Step 14: Dashboard Analitik (L-02)
        print("14. Dashboard Analitik Kesehatan (L-02)...")
        page.goto(f"{BASE_URL}/dashboard/?rentang=1_bulan")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "14_dashboard_analitik.png"))

        browser.close()
        print("Semua verifikasi End-to-End berhasil dijalankan dan tangkapan layar tersimpan di docs/screenshots/!")

if __name__ == "__main__":
    run_e2e_verification()
