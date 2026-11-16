from models.mesin_inkubator import MesinInkubator
from models.singkong import Singkong
from models.kedelai import Kedelai
from exporter import simpan_semua

if __name__ == "__main__":
    # Singkong -> Tape
    tape = Singkong(berat_awal=2.5)
    inkubator_tape = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=True, bahan=tape)
    inkubator_tape.jalankan_simulasi(jam=50, interval_cetak=5)
    print(inkubator_tape.status_akhir())
    file_tape = simpan_semua(inkubator_tape, folder="hasil", nama_dasar="tape")

    print()
    print("=" * 50)
    print()

    # Kedelai -> Tempe
    tempe = Kedelai(berat_awal=1.0)
    inkubator_tempe = MesinInkubator(suhu_lingkungan=30.0, kedap_udara=False, bahan=tempe)
    inkubator_tempe.jalankan_simulasi(jam=100, interval_cetak=10)
    print(inkubator_tempe.status_akhir())
    file_tempe = simpan_semua(inkubator_tempe, folder="hasil", nama_dasar="tempe")

    print()
    print("File tersimpan:")
    print("  Tape (singkong):")
    for path in file_tape.values():
        print(f"    {path}")
    print("  Tempe (kedelai):")
    for path in file_tempe.values():
        print(f"    {path}")