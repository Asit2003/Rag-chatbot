from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet


class KeyCipher:
    def __init__(self, key_file: Path) -> None:
        self.key_file = key_file
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.key_file.exists():
            self.key_file.write_bytes(Fernet.generate_key())
        self._fernet = Fernet(self.key_file.read_bytes())

    def encrypt(self, plain: str) -> str:
        return self._fernet.encrypt(plain.encode("utf-8")).decode("utf-8")

    def decrypt(self, cipher_text: str) -> str:
        return self._fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")

