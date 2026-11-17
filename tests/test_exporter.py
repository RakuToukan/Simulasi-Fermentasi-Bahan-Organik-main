import json
import os
import tempfile
import unittest

from exceptions import EksporGagalError
from exporter import simpan_csv, simpan_semua
from models.mesin_inkubator import MesinInkubator
from models.singkong import Singkong


class TestExporter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mesin = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=True, bahan=Singkong(1.0))
        self.mesin.jalankan_simulasi(jam=4, interval_cetak=2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_simpan_semua_berhasil(self):
        file = simpan_semua(self.mesin, folder=self.tmp.name, nama_dasar="uji")
        self.assertEqual(set(file), {"csv", "json", "txt"})
        for path in file.values():
            self.assertTrue(os.path.isfile(path))
        with open(file["json"], encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)["riwayat"]), 2)

    def test_simpan_ke_folder_jadi_error_ekspor(self):
        # Path yang sudah berupa folder tidak bisa dibuka sebagai file
        with self.assertRaises(EksporGagalError):
            simpan_csv(self.mesin, self.tmp.name)

    def test_satu_format_gagal_lainnya_tetap_tersimpan(self):
        # Buat folder bernama uji.csv sehingga hanya CSV yang gagal
        os.mkdir(os.path.join(self.tmp.name, "uji.csv"))
        with self.assertRaises(EksporGagalError) as ctx:
            simpan_semua(self.mesin, folder=self.tmp.name, nama_dasar="uji")
        self.assertIn("uji.csv", str(ctx.exception))
        self.assertEqual(set(ctx.exception.file_tersimpan), {"json", "txt"})
        for path in ctx.exception.file_tersimpan.values():
            self.assertTrue(os.path.isfile(path))


if __name__ == "__main__":
    unittest.main()
