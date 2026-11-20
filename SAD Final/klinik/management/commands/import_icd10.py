import csv
import os
from django.core.management.base import BaseCommand, CommandError
from klinik.models import ICD10


class Command(BaseCommand):
    help = 'Mengimpor kode ICD-10 dari file CSV (kolom: kode_icd10, deskripsi)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path ke file CSV ICD-10')

    def handle(self, *args, **options):
        file_path = options['file_path']
        if not os.path.exists(file_path):
            raise CommandError(f"File tidak ditemukan: {file_path}")

        created_count = 0
        updated_count = 0

        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Deteksi header
            first_row = next(reader, None)
            if not first_row:
                self.stdout.write(self.style.WARNING("File CSV kosong."))
                return

            rows_to_process = []
            # Cek jika baris pertama adalah header
            if any(h.lower() in ('kode', 'kode_icd10', 'code', 'icd') for h in first_row):
                pass
            else:
                rows_to_process.append(first_row)

            for row in reader:
                if row:
                    rows_to_process.append(row)

            for row in rows_to_process:
                if len(row) >= 2:
                    kode = row[0].strip().upper()
                    deskripsi = row[1].strip()
                    if kode and deskripsi:
                        obj, created = ICD10.objects.update_or_create(
                            kode_icd10=kode,
                            defaults={'deskripsi': deskripsi}
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Impor ICD-10 selesai: {created_count} kode baru dibuat, {updated_count} diperbarui."
        ))
