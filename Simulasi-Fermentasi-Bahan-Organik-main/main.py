from models.mesin_inkubator import MesinInkubator
from models.singkong import Singkong
from models.kedelai import Kedelai

if __name__ == "__main__":
    tape = Singkong(berat_awal=2.5)
    
    inkubator_tape = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=True, bahan=tape)
    
    inkubator_tape.jalankan_simulasi(jam=48, interval_cetak=12)
    print(inkubator_tape.status_akhir())

    print()
    print("="*50)
    print()

    tempe = Kedelai(berat_awal=1.0)
    
    inkubator_tempe = MesinInkubator(suhu_lingkungan=30.0, kedap_udara=False, bahan=tempe)
    
    inkubator_tempe.jalankan_simulasi(jam=48, interval_cetak=12)
    print(inkubator_tempe.status_akhir())