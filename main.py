import argparse
import sys

from exceptions import EksporGagalError, InputTidakValidError
from models.mesin_inkubator import MesinInkubator
from models.singkong import Singkong
from models.kedelai import Kedelai
from exporter import simpan_semua


# Jalankan satu simulasi lalu ekspor; True jika semua berhasil
def jalankan_skenario(nama, kelas_bahan, berat, suhu, kedap_udara, jam, interval_cetak) -> bool:
    try:
        bahan = kelas_bahan(berat_awal=berat)
        mesin = MesinInkubator(suhu_lingkungan=suhu, kedap_udara=kedap_udara, bahan=bahan)
        mesin.jalankan_simulasi(jam=jam, interval_cetak=interval_cetak)
    except InputTidakValidError as e:
        print(f"[ERROR] {nama}: input tidak valid - {e}")
        return False
    print(mesin.status_akhir())

    try:
        file = simpan_semua(mesin, folder="hasil", nama_dasar=nama)
        sukses = True
    except EksporGagalError as e:
        print(f"[ERROR] {nama}: ekspor gagal - {e}")
        file = e.file_tersimpan
        sukses = False

    print(f"File tersimpan ({nama}):")
    for path in file.values():
        print(f"  {path}")
    return sukses


SKENARIO = [
    # nama,   bahan,    berat, suhu, kedap, jam, interval
    ("tape",  Singkong, 2.5,   31.0, True,  50,  5),
    ("tempe", Kedelai,  1.0,   30.0, False, 100, 10),
]

def jalankan_demo() -> int:
    hasil = {}
    for skenario in SKENARIO:
        hasil[skenario[0]] = jalankan_skenario(*skenario)
        print("\n" + "=" * 50 + "\n")

    print("Ringkasan:")
    for nama, sukses in hasil.items():
        print(f"  {nama:6}: {'BERHASIL' if sukses else 'GAGAL'}")

    return 0 if all(hasil.values()) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulasi fermentasi bahan organik")
    parser.add_argument("--visual", action="store_true",
                        help="buka visualisasi web (mesin inkubator, singkong, kedelai)")
    parser.add_argument("--gui", action="store_true",
                        help="buka aplikasi desktop (CustomTkinter)")
    args = parser.parse_args()
    if args.gui:
        from gui import jalankan_gui
        jalankan_gui()
    elif args.visual:
        from server import jalankan_server
        jalankan_server()
    else:
        sys.exit(jalankan_demo())
