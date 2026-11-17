from exceptions import InputTidakValidError
from models.bahan_organik import BahanOrganik
from validasi import pastikan_angka, pastikan_bulat_positif

SUHU_MIN = 0.0
SUHU_MAKS = 60.0


class MesinInkubator:
    def __init__(self, suhu_lingkungan: float, kedap_udara: bool, bahan: BahanOrganik):
        if not isinstance(bahan, BahanOrganik):
            raise InputTidakValidError(f"bahan harus BahanOrganik, bukan {type(bahan).__name__}")
        if not isinstance(kedap_udara, bool):
            raise InputTidakValidError(f"kedap_udara harus True/False, bukan {kedap_udara!r}")
        pastikan_angka("suhu_lingkungan", suhu_lingkungan)
        if not SUHU_MIN <= suhu_lingkungan <= SUHU_MAKS:
            raise InputTidakValidError(
                f"suhu_lingkungan harus {SUHU_MIN}-{SUHU_MAKS}, didapat {suhu_lingkungan}"
            )
        self.suhu_lingkungan: float = suhu_lingkungan
        self.kedap_udara: bool = kedap_udara
        self.__bahan: BahanOrganik = bahan
        self.__log: list = []
        self.__riwayat: list = []

    def jalankan_simulasi(self, jam: int, interval_cetak: int) -> None:
        pastikan_bulat_positif("jam", jam)
        pastikan_bulat_positif("interval_cetak", interval_cetak)
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

    # Salinan log laporan (teks)
    @property
    def log(self) -> list:
        return list(self.__log)

    # Salinan riwayat laporan (dict), siap diekspor
    @property
    def riwayat(self) -> list:
        return [dict(r) for r in self.__riwayat]

    @property
    def bahan(self) -> BahanOrganik:
        return self.__bahan