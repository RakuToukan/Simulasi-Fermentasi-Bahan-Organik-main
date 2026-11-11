from models.bahan_organik import BahanOrganik


class MesinInkubator:
    def __init__(self, suhu_lingkungan: float, kedap_udara: bool, bahan: BahanOrganik):
        self.suhu_lingkungan: float = suhu_lingkungan
        self.kedap_udara: bool = kedap_udara
        self.__bahan: BahanOrganik = bahan
        self.__log: list = []

    def jalankan_simulasi(self, jam: int, interval_cetak: int) -> None:
        nama_bahan = type(self.__bahan).__name__
        print(f"--- Memulai Inkubasi {nama_bahan} selama {jam} Jam ---")

        for _ in range(jam):
            self.__bahan.tambah_jam_simulasi(self.suhu_lingkungan, self.kedap_udara)

            if self.__bahan.waktu_jam % interval_cetak == 0:
                self.cetak_laporan()

    def cetak_laporan(self) -> None:
        b = self.__bahan
        laporan = (
            f"Jam {b.waktu_jam:02d} | Status: {b.status:10} | "
            f"pH: {b.get_ph():.2f} | Tekstur: {b.get_tekstur():.1f}"
        )
        self.__log.append(laporan)
        print(laporan)

    def status_akhir(self) -> str:
        return self.__bahan.status