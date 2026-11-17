# Exception kustom untuk simulasi fermentasi

# Induk semua error simulasi
class FermentasiError(Exception):
    pass

# Input (berat, suhu, jam, dll.) tidak valid
class InputTidakValidError(FermentasiError, ValueError):
    pass

# Gagal menulis file; `file_tersimpan` berisi file yang tetap tersimpan meski ada yang gagal
class EksporGagalError(FermentasiError):
    def __init__(self, pesan: str, file_tersimpan: dict | None = None):
        super().__init__(pesan)
        self.file_tersimpan: dict = file_tersimpan or {}
