# Ekspor hasil simulasi fermentasi ke file CSV, JSON, dan TXT

import csv
import json
import os
from contextlib import contextmanager
from datetime import datetime

from exceptions import EksporGagalError
from models.mesin_inkubator import MesinInkubator

KOLOM = ["bahan", "jam", "status", "ph", "tekstur", "suhu_lingkungan", "kedap_udara"]


# Seperti open(path, "w"), plus buat folder dan ubah OSError jadi EksporGagalError
@contextmanager
def _buka_untuk_tulis(path: str, newline: str | None = None):
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", newline=newline, encoding="utf-8") as f:
            yield f
    except OSError as e:
        raise EksporGagalError(f"Gagal menulis '{path}': {e.strerror or e}") from e


def _ringkasan(mesin: MesinInkubator) -> dict:
    bahan = mesin.bahan
    return {
        "bahan": type(bahan).__name__,
        "berat_awal": bahan._berat_awal,
        "total_jam": bahan.waktu_jam,
        "status_akhir": mesin.status_akhir(),
        "ph_akhir": round(bahan.get_ph(), 2),
        "tekstur_akhir": round(bahan.get_tekstur(), 1),
        "suhu_lingkungan": mesin.suhu_lingkungan,
        "kedap_udara": mesin.kedap_udara,
    }


def simpan_csv(mesin: MesinInkubator, path: str) -> str:
    with _buka_untuk_tulis(path, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=KOLOM)
        writer.writeheader()
        writer.writerows(mesin.riwayat)
    return path


def simpan_json(mesin: MesinInkubator, path: str) -> str:
    data = {
        "dibuat": datetime.now().isoformat(timespec="seconds"),
        "ringkasan": _ringkasan(mesin),
        "riwayat": mesin.riwayat,
    }
    with _buka_untuk_tulis(path) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def simpan_txt(mesin: MesinInkubator, path: str) -> str:
    r = _ringkasan(mesin)
    with _buka_untuk_tulis(path) as f:
        f.write("=" * 50 + "\n")
        f.write("HASIL SIMULASI FERMENTASI\n")
        f.write(f"Dibuat    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Bahan          : {r['bahan']}\n")
        f.write(f"Berat awal     : {r['berat_awal']}\n")
        f.write(f"Suhu lingkungan: {r['suhu_lingkungan']}\n")
        f.write(f"Kedap udara    : {'Ya' if r['kedap_udara'] else 'Tidak'}\n")
        f.write(f"Total jam      : {r['total_jam']}\n")
        f.write(f"Status akhir   : {r['status_akhir']}\n")
        f.write(f"pH akhir       : {r['ph_akhir']}\n")
        f.write(f"Tekstur akhir  : {r['tekstur_akhir']}\n")
        f.write("-" * 50 + "\n")
        f.write("Riwayat:\n")
        for line in mesin.log:
            f.write(line + "\n")
    return path


# Simpan CSV, JSON, TXT; satu gagal tidak menghentikan yang lain, error dilempar di akhir
def simpan_semua(mesin: MesinInkubator, folder: str = "hasil", nama_dasar: str = "simulasi") -> dict:
    penyimpan = {"csv": simpan_csv, "json": simpan_json, "txt": simpan_txt}
    file_tersimpan = {}
    gagal = []

    for fmt, simpan in penyimpan.items():
        try:
            file_tersimpan[fmt] = simpan(mesin, os.path.join(folder, f"{nama_dasar}.{fmt}"))
        except EksporGagalError as e:
            gagal.append(str(e))

    if gagal:
        raise EksporGagalError("; ".join(gagal), file_tersimpan=file_tersimpan)
    return file_tersimpan
