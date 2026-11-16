from models.bahan_organik import BahanOrganik


class MesinInkubator:
    def __init__(self, suhu_lingkungan: float, kedap_udara: bool, bahan: BahanOrganik):
        self.suhu_lingkungan: float = suhu_lingkungan
        self.kedap_udara: bool = kedap_udara
        self.__bahan: BahanOrganik = bahan
        self.__log: list = []
        self.__riwayat: list = []

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
        self.__riwayat.append({
            "bahan": type(b).__name__,
            "jam": b.waktu_jam,
            "status": b.status,
            "ph": round(b.get_ph(), 2),
            "tekstur": round(b.get_tekstur(), 1),
            "suhu_lingkungan": self.suhu_lingkungan,
            "kedap_udara": self.kedap_udara,
        })
        print(laporan)

    def status_akhir(self) -> str:
        return self.__bahan.status

    @property
    def log(self) -> list:
        """Log laporan dalam bentuk teks (salinan)."""
        return list(self.__log)

    @property
    def riwayat(self) -> list:
        """Riwayat laporan dalam bentuk terstruktur (salinan), siap diekspor."""
        return [dict(r) for r in self.__riwayat]

    @property
    def bahan(self) -> BahanOrganik:
        return self.__bahan