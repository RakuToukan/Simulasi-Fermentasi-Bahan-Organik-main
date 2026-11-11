import unittest
from models.mesin_inkubator import MesinInkubator
from models.singkong import Singkong
from models.kedelai import Kedelai

class TestMesinInkubator(unittest.TestCase):
    def test_status_awal_mentah(self):
        mesin = MesinInkubator(suhu=30.0, kedap_udara=False)
        mesin.muat_bahan(Singkong())
        self.assertEqual(mesin.status_akhir(), "MENTAH")

    def test_singkong_kedap_udara_busuk(self):
        mesin = MesinInkubator(suhu=31.0, kedap_udara=True)
        mesin.muat_bahan(Singkong())
        mesin.jalankan_simulasi(jam=1, interval_cetak=12)
        self.assertEqual(mesin.status_akhir(), "BUSUK")

    def test_kedelai_tanpa_kedap_udara_proses(self):
        mesin = MesinInkubator(suhu=30.0, kedap_udara=False)
        mesin.muat_bahan(Kedelai())
        mesin.jalankan_simulasi(jam=1, interval_cetak=12)
        self.assertEqual(mesin.status_akhir(), "PROSES")

if __name__ == "__main__":
    unittest.main()