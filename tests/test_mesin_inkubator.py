import unittest
from exceptions import InputTidakValidError
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

    def test_bahan_bukan_bahan_organik(self):
        with self.assertRaises(InputTidakValidError):
            MesinInkubator(suhu_lingkungan=30.0, kedap_udara=True, bahan="singkong")

    def test_kedap_udara_bukan_bool(self):
        with self.assertRaises(InputTidakValidError):
            MesinInkubator(suhu_lingkungan=30.0, kedap_udara="ya", bahan=Singkong(1.0))

    def test_suhu_tidak_valid(self):
        for suhu in (-5.0, 100.0, "30", None):
            with self.subTest(suhu=suhu):
                with self.assertRaises(InputTidakValidError):
                    MesinInkubator(suhu_lingkungan=suhu, kedap_udara=True, bahan=Singkong(1.0))

    def test_jam_dan_interval_tidak_valid(self):
        mesin = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=True, bahan=Singkong(1.0))
        for jam, interval in ((10, 0), (-1, 5), (0, 5), (2.5, 1), (10, "5")):
            with self.subTest(jam=jam, interval_cetak=interval):
                with self.assertRaises(InputTidakValidError):
                    mesin.jalankan_simulasi(jam=jam, interval_cetak=interval)
        self.assertEqual(mesin.bahan.waktu_jam, 0)


if __name__ == "__main__":
    unittest.main()