import unittest
from models.mesin_inkubator import MesinInkubator
from models.singkong import Singkong
from models.kedelai import Kedelai


class TestMesinInkubator(unittest.TestCase):
    def test_status_awal_mentah(self):
        mesin = MesinInkubator(suhu_lingkungan=30.0, kedap_udara=False, bahan=Singkong(1.0))
        self.assertEqual(mesin.status_akhir(), "MENTAH")

    def test_singkong_kedap_udara_fermentasi(self):
        mesin = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=True, bahan=Singkong(1.0))
        mesin.jalankan_simulasi(jam=1, interval_cetak=12)
        self.assertEqual(mesin.status_akhir(), "FERMENTASI")

    def test_singkong_tanpa_kedap_udara_busuk(self):
        mesin = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=False, bahan=Singkong(1.0))
        mesin.jalankan_simulasi(jam=1, interval_cetak=12)
        self.assertEqual(mesin.status_akhir(), "BUSUK")

    def test_kedelai_tanpa_kedap_udara_fermentasi(self):
        mesin = MesinInkubator(suhu_lingkungan=30.0, kedap_udara=False, bahan=Kedelai(1.0))
        mesin.jalankan_simulasi(jam=1, interval_cetak=12)
        self.assertEqual(mesin.status_akhir(), "FERMENTASI")

    def test_kedelai_kedap_udara_busuk(self):
        mesin = MesinInkubator(suhu_lingkungan=30.0, kedap_udara=True, bahan=Kedelai(1.0))
        mesin.jalankan_simulasi(jam=1, interval_cetak=12)
        self.assertEqual(mesin.status_akhir(), "BUSUK")

    def test_matang_setelah_48_jam(self):
        tape = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=True, bahan=Singkong(2.5))
        tempe = MesinInkubator(suhu_lingkungan=30.0, kedap_udara=False, bahan=Kedelai(1.0))
        tape.jalankan_simulasi(jam=48, interval_cetak=12)
        tempe.jalankan_simulasi(jam=48, interval_cetak=12)
        self.assertEqual(tape.status_akhir(), "MATANG")
        self.assertEqual(tempe.status_akhir(), "MATANG")


if __name__ == "__main__":
    unittest.main()