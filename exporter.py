"""Ekspor hasil simulasi fermentasi ke file CSV, JSON, dan TXT."""

import csv
import json
import os
from datetime import datetime

from models.mesin_inkubator import MesinInkubator

KOLOM = ["bahan", "jam", "status", "ph", "tekstur", "suhu_lingkungan", "kedap_udara"]


def _pastikan_folder(path: str) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)


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
    _pastikan_folder(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=KOLOM)
        writer.writeheader()
        writer.writerows(mesin.riwayat)
    return path


def simpan_json(mesin: MesinInkubator, path: str) -> str:
    _pastikan_folder(path)
    data = {
        "dibuat": datetime.now().isoformat(timespec="seconds"),
        "ringkasan": _ringkasan(mesin),
        "riwayat": mesin.riwayat,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def simpan_txt(mesin: MesinInkubator, path: str) -> str:
    _pastikan_folder(path)
    r = _ringkasan(mesin)
    with open(path, "w", encoding="utf-8") as f:
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


def simpan_semua(mesin: MesinInkubator, folder: str = "hasil", nama_dasar: str = "simulasi") -> dict:
    """Simpan ke CSV, JSON, dan TXT sekaligus. Mengembalikan dict format -> path."""
    return {
        "csv": simpan_csv(mesin, os.path.join(folder, f"{nama_dasar}.csv")),
        "json": simpan_json(mesin, os.path.join(folder, f"{nama_dasar}.json")),
        "txt": simpan_txt(mesin, os.path.join(folder, f"{nama_dasar}.txt")),
    }