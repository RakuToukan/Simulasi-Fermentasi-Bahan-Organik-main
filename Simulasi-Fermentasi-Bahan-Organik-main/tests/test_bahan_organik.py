import unittest
from models.bahan_organik import BahanOrganik

class BahanUji(BahanOrganik):
    def __init__(self, berat_awal):
        super().__init__(berat_awal)
        self.dipanggil = False

    def reaksi_biologis(self, suhu, kedap_udara):
        self.dipanggil = True

class TestBahanOrganik(unittest.TestCase):
    def setUp(self):
        self.bahan = BahanUji(2.0)

    def test_inisialisasi(self):
        self.assertEqual(self.bahan._berat_awal, 2.0)
        self.assertEqual(self.bahan.waktu_jam, 0)
        self.assertEqual(self.bahan.status, "MENTAH")
        self.assertEqual(self.bahan.get_ph(), 7.0)
        self.assertEqual(self.bahan.get_tekstur(), 100.0)

    def test_tambah_jam(self):
        self.bahan.tambah_jam_simulasi(30.0, True)

        self.assertEqual(self.bahan.waktu_jam, 1)
        self.assertTrue(self.bahan.dipanggil)

    def test_status(self):
        self.bahan.status = "PROSES"
        self.assertEqual(self.bahan.status, "PROSES")

if __name__ == "__main__":
    unittest.main()