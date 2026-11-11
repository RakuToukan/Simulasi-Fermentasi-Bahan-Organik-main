class MesinInkubator:
    def __init__(self, suhu, kedap_udara):
        self.__suhu = suhu
        self.__kedap_udara = kedap_udara
        self.__bahan = None

    def muat_bahan(self, bahan):
        self.__bahan = bahan

    def jalankan_simulasi(self, jam, interval_cetak):
        print(f"--- Memulai Inkubasi {self.__bahan.nama} selama {jam} Jam ---")
        for _ in range(jam):
            self.__bahan.tambah_jam()
            self.__bahan.reaksi_biologis(self.__suhu, self.__kedap_udara)

            if self.__bahan.waktu_berjalan % interval_cetak == 0:
                self.cetak_laporan()

    def cetak_laporan(self):
        b = self.__bahan
        print(f"Jam {b.waktu_berjalan:02d} | Status: {b.status.name:10} | {b.metrik}")

    def status_akhir(self):
        return self.__bahan.status.name


if __name__ == "__main__":
    inkubator_anaerob = MesinInkubator(suhu=31.0, kedap_udara=True)
    inkubator_anaerob.muat_bahan(Singkong())
    inkubator_anaerob.jalankan_simulasi(jam=48, interval_cetak=12)
    print("Status akhir:", inkubator_anaerob.status_akhir())