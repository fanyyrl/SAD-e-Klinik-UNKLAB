import base64
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def get_fernet_cipher():
    key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
    if not key:
        # Fallback key jika tidak diset di settings/env
        key = b'LxA6ugY3su85JcdbEdr77RHxjBXtQI0yxrEpk0VAEg0='
    elif isinstance(key, str):
        key = key.encode('utf-8')
    return Fernet(key)


class EncryptedTextField(models.TextField):
    """
    Field teks dengan enkripsi tingkat field menggunakan Fernet (AES-128-CBC + HMAC-SHA256).
    Data tersimpan terenkripsi di database, dan didekripsi otomatis saat diakses di Python.
    """
    description = "Encrypted text field using Fernet"

    def get_cipher(self):
        return get_fernet_cipher()

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        return self._decrypt(value)

    def to_python(self, value):
        if value is None or value == '':
            return value
        if isinstance(value, str) and value.startswith('gAAAAA'):
            return self._decrypt(value)
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        # Jika nilai sudah berbentuk token terenkripsi, jangan enkripsi ganda
        if isinstance(value, str) and value.startswith('gAAAAA'):
            try:
                cipher = self.get_cipher()
                cipher.decrypt(value.encode('utf-8'))
                return value
            except (InvalidToken, Exception):
                pass
        return self._encrypt(value)

    def _encrypt(self, text):
        if not text:
            return text
        cipher = self.get_cipher()
        encrypted_bytes = cipher.encrypt(str(text).encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def _decrypt(self, text):
        if not text:
            return text
        try:
            cipher = self.get_cipher()
            decrypted_bytes = cipher.decrypt(str(text).encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except (InvalidToken, Exception):
            # Jika bukan ciphertext valid (misal data legacy), kembalikan apa adanya
            return text
