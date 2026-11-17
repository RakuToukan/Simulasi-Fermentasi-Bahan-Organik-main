# Pengecekan input yang dipakai bersama oleh model

from exceptions import InputTidakValidError


def pastikan_angka(nama: str, nilai) -> None:
    # bool adalah turunan int di Python, jadi True/False harus ditolak secara eksplisit
    if isinstance(nilai, bool) or not isinstance(nilai, (int, float)):
        raise InputTidakValidError(f"{nama} harus angka, bukan {type(nilai).__name__}")


def pastikan_bulat_positif(nama: str, nilai) -> None:
    if isinstance(nilai, bool) or not isinstance(nilai, int):
        raise InputTidakValidError(f"{nama} harus bilangan bulat, bukan {type(nilai).__name__}")
    if nilai <= 0:
        raise InputTidakValidError(f"{nama} harus lebih dari 0, didapat {nilai}")
