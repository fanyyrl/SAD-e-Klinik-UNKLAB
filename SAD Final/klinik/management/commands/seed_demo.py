import random
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from klinik.models import (
    Pengguna, Pasien, AlergiPasien, Kunjungan, TandaVital,
    BatasTTV, Pemeriksaan, ICD10, Diagnosis, Tindakan,
    Obat, MutasiStok, Resep, DetailResep, HasilLab
)


class Command(BaseCommand):
    help = 'Mengisi database dengan data demo e-Klinik UNKLAB (idempoten)'

    def handle(self, *args, **options):
        self.stdout.write("Memulai penyemaian data demo e-Klinik UNKLAB...")

        with transaction.atomic():
            self.seed_pengguna()
            self.seed_batas_ttv()
            self.seed_icd10()
            self.seed_obat()
            pasien_list = self.seed_pasien()
            self.seed_kunjungan_dan_rekam_medis(pasien_list)

        self.stdout.write(self.style.SUCCESS("Penyemaian data demo berhasil selesai!"))

    def seed_pengguna(self):
        # 1. Staf Klinik
        staf, created = Pengguna.objects.update_or_create(
            username='staf_klinik',
            defaults={
                'nama_lengkap': 'Meisya Sumual, A.Md.Kep',
                'role_akses': 'staf_klinik',
                'status_aktif': True,
                'is_staff': False,
                'is_superuser': False,
            }
        )
        staf.set_password('Staf12345!')
        staf.save()

        # 2. Dokter
        dokter, created = Pengguna.objects.update_or_create(
            username='dokter1',
            defaults={
                'nama_lengkap': 'dr. Christian Manoppo, Sp.PD',
                'role_akses': 'dokter',
                'status_aktif': True,
                'is_staff': False,
                'is_superuser': False,
            }
        )
        dokter.set_password('Dokter12345!')
        dokter.save()

        # 3. Superuser Admin
        admin, created = Pengguna.objects.update_or_create(
            username='admin',
            defaults={
                'nama_lengkap': 'Administrator Sistem UNKLAB',
                'role_akses': 'staf_klinik',
                'status_aktif': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin.set_password('Admin12345!')
        admin.save()

        self.stdout.write(self.style.SUCCESS("✓ Pengguna demo (staf_klinik, dokter1, admin) berhasil disiapkan."))

    def seed_batas_ttv(self):
        defaults = [
            ('sistolik', 90.0, 139.0),
            ('diastolik', 60.0, 89.0),
            ('nadi', 60.0, 100.0),
            ('suhu', 36.0, 37.5),
            ('respirasi', 12.0, 20.0),
            ('spo2', 95.0, 100.0),
        ]
        for param, n_min, n_max in defaults:
            BatasTTV.objects.update_or_create(
                parameter=param,
                defaults={'nilai_min': n_min, 'nilai_maks': n_max}
            )
        self.stdout.write(self.style.SUCCESS("✓ Batas TTV default berhasil disiapkan."))

    def seed_icd10(self):
        icd_codes = [
            ("A09", "Infectious gastroenteritis and colitis, unspecified"),
            ("A01.0", "Typhoid fever"),
            ("A06.0", "Acute amoebic dysentery"),
            ("A15.0", "Tuberculosis of lung"),
            ("B01.9", "Varicella without complication"),
            ("B02.9", "Zoster without complication"),
            ("B05.9", "Measles without complication"),
            ("B26.9", "Mumps without complication"),
            ("B34.9", "Viral infection, unspecified"),
            ("B35.9", "Dermatophytosis, unspecified"),
            ("B35.4", "Tinea corporis"),
            ("B35.1", "Tinea unguium"),
            ("B36.0", "Pityriasis versicolor"),
            ("B37.0", "Candidal stomatitis"),
            ("B86", "Scabies"),
            ("D50.9", "Iron deficiency anaemia, unspecified"),
            ("D64.9", "Anaemia, unspecified"),
            ("E03.9", "Hypothyroidism, unspecified"),
            ("E05.9", "Thyrotoxicosis, unspecified"),
            ("E10.9", "Type 1 diabetes mellitus without complications"),
            ("E11.9", "Type 2 diabetes mellitus without complications"),
            ("E66.9", "Obesity, unspecified"),
            ("E78.0", "Pure hypercholesterolaemia"),
            ("E78.5", "Hyperlipidaemia, unspecified"),
            ("E79.0", "Hyperuricaemia without signs of inflammatory arthritis"),
            ("F32.9", "Depressive episode, unspecified"),
            ("F41.1", "Generalized anxiety disorder"),
            ("F41.2", "Mixed anxiety and depressive disorder"),
            ("F51.0", "Nonorganic insomnia"),
            ("G43.9", "Migraine, unspecified"),
            ("G44.2", "Tension-type headache"),
            ("G44.3", "Chronic post-traumatic headache"),
            ("H00.0", "Hordeolum and other deep inflammation of eyelid"),
            ("H01.0", "Blepharitis"),
            ("H10.9", "Conjunctivitis, unspecified"),
            ("H10.1", "Acute atopic conjunctivitis"),
            ("H16.0", "Corneal ulcer"),
            ("H60.9", "Otitis externa, unspecified"),
            ("H65.9", "Nonsuppurative otitis media, unspecified"),
            ("H66.9", "Otitis media, unspecified"),
            ("H81.0", "Meniere disease"),
            ("H81.1", "Benign paroxysmal vertigo"),
            ("I10", "Essential (primary) hypertension"),
            ("I11.9", "Hypertensive heart disease without heart failure"),
            ("I20.9", "Angina pectoris, unspecified"),
            ("I50.9", "Heart failure, unspecified"),
            ("I84.9", "Haemorrhoids without complication, unspecified"),
            ("J00", "Acute nasopharyngitis [common cold]"),
            ("J01.9", "Acute sinusitis, unspecified"),
            ("J02.9", "Acute pharyngitis, unspecified"),
            ("J03.9", "Acute tonsillitis, unspecified"),
            ("J04.0", "Acute laryngitis"),
            ("J06.9", "Acute upper respiratory infection, unspecified"),
            ("J11.1", "Influenza with other respiratory manifestations"),
            ("J18.9", "Pneumonia, unspecified"),
            ("J20.9", "Acute bronchitis, unspecified"),
            ("J30.4", "Allergic rhinitis, unspecified"),
            ("J31.0", "Chronic rhinitis"),
            ("J44.9", "Chronic obstructive pulmonary disease, unspecified"),
            ("J45.9", "Asthma, unspecified"),
            ("K02.9", "Dental caries, unspecified"),
            ("K04.0", "Pulpitis"),
            ("K05.0", "Acute gingivitis"),
            ("K12.0", "Recurrent aphthous stomatitis"),
            ("K21.9", "Gastro-oesophageal reflux disease without oesophagitis"),
            ("K25.9", "Gastric ulcer, unspecified as acute or chronic"),
            ("K29.7", "Gastritis, unspecified"),
            ("K29.1", "Other acute gastritis"),
            ("K30", "Dyspepsia"),
            ("K52.9", "Non-infective gastroenteritis and colitis, unspecified"),
            ("K58.9", "Irritable bowel syndrome without diarrhoea"),
            ("K59.0", "Constipation"),
            ("L01.0", "Impetigo"),
            ("L02.9", "Cutaneous abscess, furuncle and carbuncle, unspecified"),
            ("L03.9", "Cellulitis, unspecified"),
            ("L08.0", "Pyoderma"),
            ("L20.9", "Atopic dermatitis, unspecified"),
            ("L23.9", "Allergic contact dermatitis, unspecified cause"),
            ("L24.9", "Irritant contact dermatitis, unspecified cause"),
            ("L29.9", "Pruritus, unspecified"),
            ("L30.9", "Dermatitis, unspecified"),
            ("L50.9", "Urticaria, unspecified"),
            ("L60.0", "Ingrowing nail"),
            ("L70.0", "Acne vulgaris"),
            ("M06.9", "Rheumatoid arthritis, unspecified"),
            ("M10.9", "Gout, unspecified"),
            ("M19.9", "Osteoarthritis, unspecified"),
            ("M25.5", "Pain in joint"),
            ("M54.2", "Cervicalgia"),
            ("M54.5", "Low back pain"),
            ("M54.9", "Dorsalgia, unspecified"),
            ("M79.1", "Myalgia"),
            ("M79.2", "Neuralgia and neuritis, unspecified"),
            ("N30.9", "Cystitis, unspecified"),
            ("N39.0", "Urinary tract infection, site not specified"),
            ("N94.6", "Dysmenorrhoea, unspecified"),
            ("R05", "Cough"),
            ("R06.0", "Dyspnoea"),
            ("R07.0", "Pain in throat"),
            ("R07.4", "Chest pain, unspecified"),
            ("R10.4", "Other and unspecified abdominal pain"),
            ("R11", "Nausea and vomiting"),
            ("R42", "Dizziness and giddiness"),
            ("R50.9", "Fever, unspecified"),
            ("R51", "Headache"),
            ("R53", "Malaise and fatigue"),
            ("S00.9", "Superficial injury of head, part unspecified"),
            ("S01.9", "Open wound of head, part unspecified"),
            ("S13.4", "Sprain and strain of cervical spine"),
            ("S60.9", "Superficial injury of wrist and hand, part unspecified"),
            ("S61.9", "Open wound of wrist and hand, part unspecified"),
            ("S80.9", "Superficial injury of lower leg, part unspecified"),
            ("S83.6", "Sprain and strain of other and unspecified parts of knee"),
            ("S90.9", "Superficial injury of ankle and foot, part unspecified"),
            ("S93.4", "Sprain and strain of ankle"),
            ("T14.0", "Superficial injury of unspecified body region"),
            ("T14.1", "Open wound of unspecified body region"),
            ("T78.4", "Allergy, unspecified"),
            ("Z00.0", "General medical examination"),
            ("Z01.0", "Examination of eyes and vision"),
            ("Z01.2", "Dental examination"),
            ("Z02.1", "Pre-employment examination"),
            ("Z23", "Need for immunization against single bacterial diseases"),
            ("Z71.3", "Dietary surveillance and counselling"),
            ("A08.4", "Viral intestinal infection, unspecified"),
            ("B00.9", "Herpesviral infection, unspecified"),
            ("B35.0", "Tinea barbae and tinea capitis"),
            ("B35.3", "Tinea pedis"),
            ("D53.9", "Nutritional anaemia, unspecified"),
            ("E86", "Volume depletion [dehydration]"),
            ("F43.0", "Acute stress reaction"),
            ("F45.0", "Somatization disorder"),
            ("G47.0", "Disorders of initiating and maintaining sleep"),
            ("H52.1", "Myopia"),
            ("H52.2", "Astigmatism"),
            ("H92.0", "Otalgia"),
            ("H93.1", "Tinnitus"),
            ("I95.9", "Hypotension, unspecified"),
            ("J32.9", "Chronic sinusitis, unspecified"),
            ("J35.0", "Chronic tonsillitis"),
            ("J39.0", "Retropharyngeal and parapharyngeal abscess"),
            ("K12.1", "Other forms of stomatitis"),
            ("K27.9", "Peptic ulcer, site unspecified"),
            ("K59.1", "Functional diarrhoea"),
            ("L21.9", "Seborrhoeic dermatitis, unspecified"),
            ("L72.0", "Epidermal cyst"),
            ("M62.8", "Other specified disorders of muscle"),
            ("M77.9", "Enthesopathy, unspecified"),
            ("N91.2", "Amenorrhoea, unspecified"),
            ("R04.0", "Epistaxis"),
            ("R10.1", "Pain localized to upper abdomen"),
            ("R10.2", "Pelvic and perineal pain"),
            ("R55", "Syncope and collapse"),
            ("T67.0", "Heatstroke and sunstroke"),
            ("T78.1", "Other adverse food reactions, not elsewhere classified"),
        ]

        for kode, deskripsi in icd_codes:
            ICD10.objects.update_or_create(
                kode_icd10=kode,
                defaults={'deskripsi': deskripsi}
            )
        self.stdout.write(self.style.SUCCESS(f"✓ Master ICD-10 disiapkan ({len(icd_codes)} kode)."))

    def seed_obat(self):
        admin_user = Pengguna.objects.get(username='admin')
        daftar_obat = [
            ("OBT-001", "Paracetamol 500 mg", "tablet", 200, 50, "Paracetamol", "Analgesik-Antipiretik"),
            ("OBT-AMX", "Amoxicillin 500 mg", "kapsul", 150, 30, "Amoxicillin", "penisilin"),
            ("OBT-003", "Ibuprofen 400 mg", "tablet", 120, 25, "Ibuprofen", "NSAID"),
            ("OBT-004", "Asam Mefenamat 500 mg", "kapsul", 100, 20, "Asam Mefenamat", "NSAID"),
            ("OBT-005", "Cetirizine 10 mg", "tablet", 80, 20, "Cetirizine HCl", "Antihistamin"),
            ("OBT-006", "CTM (Chlorpheniramine) 4 mg", "tablet", 150, 30, "Chlorpheniramine maleate", "Antihistamin"),
            ("OBT-007", "Antasida Doen", "tablet", 250, 50, "Aluminium Hidroksida & Magnesium", "Antasida"),
            ("OBT-008", "Omeprazole 20 mg", "kapsul", 90, 25, "Omeprazole", "PPI"),
            ("OBT-009", "Ranitidine 150 mg", "tablet", 80, 20, "Ranitidine HCl", "H2 Blocker"),
            ("OBT-010", "Dexamethasone 0.5 mg", "tablet", 100, 20, "Dexamethasone", "Kortikosteroid"),
            ("OBT-011", "Metilprednisolon 4 mg", "tablet", 70, 20, "Metilprednisolon", "Kortikosteroid"),
            ("OBT-012", "Ciprofloxacin 500 mg", "tablet", 60, 20, "Ciprofloxacin", "Kuinolon"),
            ("OBT-013", "Kotrimoksazol 480 mg", "tablet", 50, 20, "Sulfametoksazol & Trimetoprim", "Sulfonamida"),
            ("OBT-014", "Doxycycline 100 mg", "kapsul", 40, 15, "Doksisiklin", "Tetrasiklin"),
            ("OBT-015", "Oralit Sachet", "sachet", 120, 30, "Elektrolit Glukosa", "Rehidrasi"),
            ("OBT-016", "Attapulgite 600 mg", "tablet", 80, 20, "Attapulgite", "Antidiare"),
            ("OBT-017", "Ambroxol 30 mg", "tablet", 110, 25, "Ambroxol HCl", "Mukolitik"),
            ("OBT-018", "OBH Sirup 100 ml", "botol", 30, 10, "Succus Liquiritiae", "Ekspektoran"),
            ("OBT-019", "Vitamin C 500 mg", "tablet", 300, 50, "Asam Askorbat", "Vitamin"),
            ("OBT-020", "Vitamin B Kompleks", "tablet", 180, 40, "Vitamin B1, B2, B6, B12", "Vitamin"),
            ("OBT-021", "Chloramphenicol Tetes Mata 0.5%", "botol", 25, 10, "Kloramfenikol", "Antibiotik Topikal"),
            ("OBT-022", "Betamethasone Salep Kulit 5g", "tube", 35, 10, "Betametason", "Kortikosteroid Topikal"),
            ("OBT-023", "Salep Oxytetracycline 1%", "tube", 20, 10, "Oksitetrasiklin", "Antibiotik Topikal"),
            ("OBT-024", "Antiseptik Povidone Iodine 60ml", "botol", 45, 10, "Povidone Iodine", "Antiseptik"),
            ("OBT-025", "Loratadine 10 mg", "tablet", 5, 20, "Loratadine", "Antihistamin"),  # Stok rendah (5 <= 20)
            ("OBT-026", "Amlodipine 5 mg", "tablet", 6, 20, "Amlodipine Besylate", "Antihipertensi"),  # Stok rendah (6 <= 20)
        ]

        for kode, nama, satuan, stok, min_stok, zat, kelompok in daftar_obat:
            obat, created = Obat.objects.update_or_create(
                kode_obat=kode,
                defaults={
                    'nama_obat': nama,
                    'satuan': satuan,
                    'stok_tersedia': stok,
                    'stok_minimum': min_stok,
                    'zat_aktif': zat,
                    'kelompok_obat': kelompok,
                    'status_aktif': True,
                }
            )
            if created or not MutasiStok.objects.filter(kode_obat=obat).exists():
                MutasiStok.objects.create(
                    kode_obat=obat,
                    jenis='masuk',
                    jumlah=stok,
                    id_pengguna=admin_user,
                    keterangan='Stok awal inisialisasi klinik'
                )

        self.stdout.write(self.style.SUCCESS(f"✓ Master Obat disiapkan ({len(daftar_obat)} obat)."))

    def seed_pasien(self):
        pasien_raw = [
            ("105012410033", "Fany Moningkey", date(2004, 5, 14), "P", "Fakultas Ilmu Komputer", "Asrama Crystal UNKLAB, Airmadidi"),
            ("105012410001", "Geraldo Pongoh", date(2003, 3, 10), "L", "Fakultas Ilmu Komputer", "Asrama Edelweiss UNKLAB"),
            ("105022310012", "Prisilia Mandagi", date(2003, 8, 22), "P", "Fakultas Ekonomi dan Bisnis", "Genset Street, Airmadidi Atas"),
            ("105032210005", "Kevin Runtuwene", date(2002, 11, 4), "L", "Fakultas Filsafat", "Asrama Pioneer UNKLAB"),
            ("105042410045", "Clarissa Wenas", date(2004, 2, 18), "P", "Fakultas Keperawatan", "Asrama Jasmine UNKLAB"),
            ("105012310088", "Michael Supit", date(2003, 7, 30), "L", "Fakultas Ilmu Komputer", "Airmadidi Bawah"),
            ("105052210019", "Natasha Sondakh", date(2002, 9, 15), "P", "Fakultas Keguruan dan Ilmu Pendidikan", "Sukur, Minahasa Utara"),
            ("105062410008", "David Palilingan", date(2005, 1, 25), "L", "Fakultas Pertanian", "Asrama Annex UNKLAB"),
            ("105022410077", "Angelique Lontoh", date(2004, 10, 5), "P", "Fakultas Ekonomi dan Bisnis", "Asrama Crystal UNKLAB"),
            ("105012210052", "Jonathan Walangitan", date(2002, 12, 12), "L", "Fakultas Ilmu Komputer", "Kos Boulevard UNKLAB"),
            ("105042310061", "Stephanie Tumbel", date(2003, 4, 19), "P", "Fakultas Keperawatan", "Asrama Jasmine UNKLAB"),
            ("105032310003", "Samuel Tendean", date(2003, 6, 8), "L", "Fakultas Filsafat", "Asrama Pioneer UNKLAB"),
            ("105052410029", "Valerie Kawengian", date(2004, 8, 14), "P", "Fakultas Keguruan dan Ilmu Pendidikan", "Kauditan, Minahasa Utara"),
            ("105022110090", "Christian Polii", date(2001, 11, 28), "L", "Fakultas Ekonomi dan Bisnis", "Matungkas, Dimembe"),
            ("105012410099", "Gabriella Roring", date(2004, 3, 3), "P", "Fakultas Ilmu Komputer", "Asrama Crystal UNKLAB"),
            ("105062310015", "Raymond Lumintang", date(2003, 5, 17), "L", "Fakultas Pertanian", "Airmadidi Atas"),
            ("105042210080", "Kezia Rumagit", date(2002, 10, 20), "P", "Fakultas Keperawatan", "Asrama Jasmine UNKLAB"),
            ("105012110040", "Bryan Sumampouw", date(2001, 9, 2), "L", "Fakultas Ilmu Komputer", "Kolongan, Tetempangan"),
            ("105022210034", "Jessica Pangemanan", date(2002, 12, 7), "P", "Fakultas Ekonomi dan Bisnis", "Asrama Crystal UNKLAB"),
            ("105052310041", "Daniel Dengah", date(2003, 1, 11), "L", "Fakultas Keguruan dan Ilmu Pendidikan", "Asrama Edelweiss UNKLAB"),
            ("105032410011", "Michelle Karundeng", date(2004, 7, 23), "P", "Fakultas Filsafat", "Sarongsong 2, Airmadidi"),
            ("105042410092", "Timothy Wowor", date(2004, 4, 6), "L", "Fakultas Keperawatan", "Asrama Pioneer UNKLAB"),
            ("105012310115", "Rebeca Manueke", date(2003, 11, 16), "P", "Fakultas Ilmu Komputer", "Asrama Crystal UNKLAB"),
            ("105022410048", "Andrew Senduk", date(2004, 9, 9), "L", "Fakultas Ekonomi dan Bisnis", "Kos Pinilih UNKLAB"),
            ("105062210030", "Fiona Tangkudung", date(2002, 6, 21), "P", "Fakultas Pertanian", "Lembean, Minahasa Utara"),
            ("105052110055", "Joshua Maramis", date(2001, 8, 1), "L", "Fakultas Keguruan dan Ilmu Pendidikan", "Asrama Edelweiss UNKLAB"),
            ("105042110072", "Vanessa Wantania", date(2001, 3, 29), "P", "Fakultas Keperawatan", "Kawangkoan Baru, Kalawat"),
            ("105032110008", "Edwin Rondonuwu", date(2001, 5, 13), "L", "Fakultas Filsafat", "Asrama Pioneer UNKLAB"),
            ("105012010022", "Grace Mamahit", date(2000, 10, 31), "P", "Fakultas Ilmu Komputer", "Airmadidi Atas"),
            ("105022010065", "Mario Paat", date(2000, 2, 14), "L", "Fakultas Ekonomi dan Bisnis", "Manado"),
            ("105072410002", "Ruth Kalalo", date(2004, 12, 19), "P", "Akademi Bahasa Asing", "Asrama Crystal UNKLAB"),
        ]

        pasien_objs = []
        for nim, nama, tgl, jk, fak, alm in pasien_raw:
            p, _ = Pasien.objects.update_or_create(
                nim_id=nim,
                defaults={
                    'nama': nama,
                    'tanggal_lahir': tgl,
                    'jenis_kelamin': jk,
                    'fakultas': fak,
                    'alamat': alm,
                }
            )
            pasien_objs.append(p)

        # Catatan Alergi:
        # Fany Moningkey alergi Amoxicillin / penisilin
        AlergiPasien.objects.update_or_create(
            id_pasien=pasien_objs[0],
            nama_alergen="Amoxicillin",
            defaults={'jenis_alergi': 'obat', 'reaksi': 'Gatal-gatal hebat, bintik merah seluruh tubuh, dan pembengkakan bibir'}
        )
        AlergiPasien.objects.update_or_create(
            id_pasien=pasien_objs[0],
            nama_alergen="penisilin",
            defaults={'jenis_alergi': 'obat', 'reaksi': 'Hipersensitivitas golongan penisilin, sesak napas ringan'}
        )

        # Geraldo Pongoh alergi Paracetamol & Udang
        AlergiPasien.objects.update_or_create(
            id_pasien=pasien_objs[1],
            nama_alergen="Paracetamol",
            defaults={'jenis_alergi': 'obat', 'reaksi': 'Bintik kemerahan dan mual setelah minum paracetamol'}
        )
        AlergiPasien.objects.update_or_create(
            id_pasien=pasien_objs[1],
            nama_alergen="Udang",
            defaults={'jenis_alergi': 'makanan', 'reaksi': 'Urtikaria dan gatal pada kulit'}
        )

        # Prisilia alergi Sulfa
        AlergiPasien.objects.update_or_create(
            id_pasien=pasien_objs[2],
            nama_alergen="Sulfonamida",
            defaults={'jenis_alergi': 'obat', 'reaksi': 'Erupsi kulit obat (fixed drug eruption)'}
        )

        self.stdout.write(self.style.SUCCESS(f"✓ Master Pasien disiapkan ({len(pasien_objs)} pasien) beserta data alergi."))
        return pasien_objs

    def seed_kunjungan_dan_rekam_medis(self, pasien_list):
        staf = Pengguna.objects.get(username='staf_klinik')
        dokter = Pengguna.objects.get(username='dokter1')

        icd_j00 = ICD10.objects.filter(kode_icd10="J00").first() or ICD10.objects.first()
        icd_k29 = ICD10.objects.filter(kode_icd10="K29.7").first() or icd_j00
        icd_r51 = ICD10.objects.filter(kode_icd10="R51").first() or icd_j00
        icd_a09 = ICD10.objects.filter(kode_icd10="A09").first() or icd_j00
        icd_m54 = ICD10.objects.filter(kode_icd10="M54.5").first() or icd_j00
        icd_list = [icd_j00, icd_k29, icd_r51, icd_a09, icd_m54]

        obat_pct = Obat.objects.filter(kode_obat="OBT-001").first()
        obat_ctz = Obat.objects.filter(kode_obat="OBT-005").first()
        obat_ant = Obat.objects.filter(kode_obat="OBT-007").first()

        now = timezone.now()

        # Buat kunjungan historis 60 hari ke belakang (rata-rata 1-3 kunjungan per hari)
        # agar grafik 7 hari, 1 bulan, 3 bulan terisi
        for hari_lalu in range(60, 0, -1):
            tgl_kunjungan = now - timedelta(days=hari_lalu)
            jumlah_hari_ini = random.randint(1, 3)

            for no_antrian in range(1, jumlah_hari_ini + 1):
                p = random.choice(pasien_list)
                waktu_tiba = tgl_kunjungan.replace(hour=8 + no_antrian, minute=random.randint(0, 50))

                k = Kunjungan.objects.create(
                    id_pasien=p,
                    id_dokter=dokter,
                    tanggal_waktu=waktu_tiba,
                    nomor_antrian=no_antrian,
                    status_antrian='selesai',
                    status_verifikasi=True,
                    keluhan_utama=f"Pasien mengeluhkan gejala lemas, sakit kepala, dan flu sejak kemarin.",
                    status_pemeriksaan_awal='siap_diperiksa',
                    prioritas_abnormal=False
                )

                # TTV
                TandaVital.objects.create(
                    id_kunjungan=k,
                    id_pencatat=staf,
                    tekanan_sistolik=random.randint(110, 130),
                    tekanan_diastolik=random.randint(70, 85),
                    nadi=random.randint(70, 88),
                    suhu_tubuh=round(random.uniform(36.4, 37.2), 1),
                    respirasi=random.randint(16, 20),
                    saturasi_oksigen=random.randint(97, 99),
                    skor_nyeri=random.randint(1, 3),
                    berat_badan=random.randint(48, 75),
                    status_abnormal=False,
                    catatan_eskalasi=""
                )

                # Pemeriksaan
                pmr = Pemeriksaan.objects.create(
                    id_kunjungan=k,
                    id_dokter=dokter,
                    anamnesis_lanjutan="Keluhan memberat di malam hari. Istirahat kurang karena tugas perkuliahan.",
                    riwayat_konsumsi_obat="Belum minum obat apapun sebelum ke klinik.",
                    pemeriksaan_fisik="KU: sedang, kesadaran compos mentis. Faring hiperemis (-), tonsil T1/T1.",
                )

                # Diagnosis
                pilih_icd = random.choice(icd_list)
                Diagnosis.objects.create(
                    id_pemeriksaan=pmr,
                    kode_icd10=pilih_icd,
                    jenis_diagnosis='primer'
                )

                # Tindakan
                Tindakan.objects.create(
                    id_pemeriksaan=pmr,
                    nama_tindakan="Edukasi istirahat cukup & hidrasi adekuat",
                    catatan_tindakan="Pasien disarankan istirahat di asrama dan minum air putih hangat minimal 2 liter."
                )

                # Resep
                rsp = Resep.objects.create(
                    id_pemeriksaan=pmr,
                    catatan="Minum teratur setelah makan."
                )
                if obat_pct:
                    DetailResep.objects.create(
                        id_resep=rsp,
                        kode_obat=obat_pct,
                        jumlah=10,
                        dosis="500 mg",
                        aturan_pakai="3x1 tab bila demam/nyeri"
                    )

        # Buat Kunjungan HARI INI (untuk menguji antrean aktif, FIFO, dan prioritas TTV)
        today = timezone.localdate()
        today_start = timezone.make_aware(timezone.datetime(today.year, today.month, today.day, 8, 0, 0))

        # Pasien 1: Fany Moningkey (Antrean #1 - selesai)
        k1 = Kunjungan.objects.create(
            id_pasien=pasien_list[0],
            id_dokter=dokter,
            tanggal_waktu=today_start + timedelta(minutes=15),
            nomor_antrian=1,
            status_antrian='selesai',
            status_verifikasi=True,
            keluhan_utama="Nyeri ulu hati terasa perih dan mual sejak tadi subuh.",
            status_pemeriksaan_awal='siap_diperiksa',
            prioritas_abnormal=False
        )
        TandaVital.objects.create(
            id_kunjungan=k1,
            id_pencatat=staf,
            tekanan_sistolik=115,
            tekanan_diastolik=75,
            nadi=78,
            suhu_tubuh=36.6,
            respirasi=18,
            saturasi_oksigen=99,
            skor_nyeri=4,
            berat_badan=52.0,
            status_abnormal=False,
            catatan_eskalasi=""
        )
        pmr1 = Pemeriksaan.objects.create(
            id_kunjungan=k1,
            id_dokter=dokter,
            anamnesis_lanjutan="Perih di epigastrium, riwayat makan terlambat karena jadwal praktikum pagi.",
            riwayat_konsumsi_obat="Tidak ada",
            pemeriksaan_fisik="Nyeri tekan epigastrium (+), bising usus normal, hepar/lien tidak teraba.",
        )
        Diagnosis.objects.create(
            id_pemeriksaan=pmr1,
            kode_icd10=icd_k29,
            jenis_diagnosis='primer'
        )
        Tindakan.objects.create(
            id_pemeriksaan=pmr1,
            nama_tindakan="Konseling Pola Makan",
            catatan_tindakan="Hindari makanan pedas, asam, dan kopi selama masa pengobatan."
        )
        rsp1 = Resep.objects.create(
            id_pemeriksaan=pmr1,
            catatan="Minum antasida 1 jam sebelum makan atau saat perut kosong."
        )
        if obat_ant:
            DetailResep.objects.create(
                id_resep=rsp1,
                kode_obat=obat_ant,
                jumlah=10,
                dosis="1 tablet kunyah",
                aturan_pakai="3x1 kunyah sebelum makan"
            )

        # Pasien 2: Geraldo Pongoh (Antrean #2 - ABNORMAL TTV, status 'dilayani')
        k2 = Kunjungan.objects.create(
            id_pasien=pasien_list[1],
            id_dokter=dokter,
            tanggal_waktu=today_start + timedelta(minutes=30),
            nomor_antrian=2,
            status_antrian='dilayani',
            status_verifikasi=True,
            keluhan_utama="Demam tinggi menggigil, sakit kepala berdenyut, dan badan ngilu.",
            status_pemeriksaan_awal='siap_diperiksa',
            prioritas_abnormal=True
        )
        TandaVital.objects.create(
            id_kunjungan=k2,
            id_pencatat=staf,
            tekanan_sistolik=130,
            tekanan_diastolik=85,
            nadi=112,  # ABNORMAL > 100
            suhu_tubuh=39.5,  # ABNORMAL > 37.5
            respirasi=22,  # ABNORMAL > 20
            saturasi_oksigen=97,
            skor_nyeri=5,
            berat_badan=64.0,
            status_abnormal=True,
            catatan_eskalasi="Demam tinggi 39.5°C dengan takikardia 112x/m. Eskalasi cepat ke dokter klinik."
        )

        # Pasien 3: Prisilia Mandagi (Antrean #3 - status 'dipanggil')
        k3 = Kunjungan.objects.create(
            id_pasien=pasien_list[2],
            id_dokter=None,
            tanggal_waktu=today_start + timedelta(minutes=45),
            nomor_antrian=3,
            status_antrian='dipanggil',
            status_verifikasi=True,
            keluhan_utama="Batuk berdahak dan hidung tersumbat 3 hari.",
            status_pemeriksaan_awal='siap_diperiksa',
            prioritas_abnormal=False
        )
        TandaVital.objects.create(
            id_kunjungan=k3,
            id_pencatat=staf,
            tekanan_sistolik=110,
            tekanan_diastolik=70,
            nadi=80,
            suhu_tubuh=37.0,
            respirasi=18,
            saturasi_oksigen=98,
            skor_nyeri=2,
            berat_badan=50.0,
            status_abnormal=False,
            catatan_eskalasi=""
        )

        # Pasien 4: Kevin Runtuwene (Antrean #4 - status 'menunggu')
        k4 = Kunjungan.objects.create(
            id_pasien=pasien_list[3],
            id_dokter=None,
            tanggal_waktu=today_start + timedelta(minutes=55),
            nomor_antrian=4,
            status_antrian='menunggu',
            status_verifikasi=True,
            keluhan_utama="Keseleo pergelangan kaki kanan saat bermain basket di gymnasium.",
            status_pemeriksaan_awal='siap_diperiksa',
            prioritas_abnormal=False
        )
        TandaVital.objects.create(
            id_kunjungan=k4,
            id_pencatat=staf,
            tekanan_sistolik=125,
            tekanan_diastolik=80,
            nadi=84,
            suhu_tubuh=36.7,
            respirasi=18,
            saturasi_oksigen=99,
            skor_nyeri=6,
            berat_badan=70.0,
            status_abnormal=False,
            catatan_eskalasi=""
        )

        # Pasien 5: Clarissa Wenas (Antrean #5 - status 'menunggu', 'belum_ttv')
        k5 = Kunjungan.objects.create(
            id_pasien=pasien_list[4],
            id_dokter=None,
            tanggal_waktu=today_start + timedelta(minutes=65),
            nomor_antrian=5,
            status_antrian='menunggu',
            status_verifikasi=True,
            keluhan_utama="Pusing dan mata berkunang-kunang setelah upacara bendera.",
            status_pemeriksaan_awal='belum_ttv',
            prioritas_abnormal=False
        )

        # Pasien 6: Michael Supit (Antrean #6 - status 'ditunda')
        k6 = Kunjungan.objects.create(
            id_pasien=pasien_list[5],
            id_dokter=None,
            tanggal_waktu=today_start + timedelta(minutes=70),
            nomor_antrian=6,
            status_antrian='ditunda',
            status_verifikasi=True,
            keluhan_utama="Konsultasi kesehatan rutin.",
            status_pemeriksaan_awal='belum_ttv',
            prioritas_abnormal=False
        )

        # Buat contoh Hasil Lab untuk kunjungan Fany Moningkey (k1)
        HasilLab.objects.create(
            id_kunjungan=k1,
            id_pencatat=dokter,
            jenis_pemeriksaan="Darah Lengkap & H. Pylori Serologi",
            sumber_fasilitas="Laboratorium RS Advent Manado",
            tanggal_pemeriksaan=today,
            hasil_lab="Hemoglobin: 13.2 g/dL, Leukosit: 7.200 /uL, Trombosit: 280.000 /uL. H. Pylori Serologi: Negatif. Kesan: Dalam batas normal.",
        )

        self.stdout.write(self.style.SUCCESS("✓ Kunjungan 60 hari terakhir dan antrean hari ini berhasil disiapkan."))
