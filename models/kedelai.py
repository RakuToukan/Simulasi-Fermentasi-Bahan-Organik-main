from config import Config
from models.bahan_organik import BahanOrganik


class Kedelai(BahanOrganik):
    def __init__(self, berat_awal: float):
        super().__init__(berat_awal)
        self.__kadar_miselium: float = 0.0
        self.__suhu_internal: float = 0.0

    def reaksi_biologis(self, suhu: float, kedap_udara: bool) -> None:
        if self._status == "BUSUK":
            return

        # Jamur tempe butuh oksigen; kalau kedap udara, gagal jadi tempe
        if kedap_udara:
            self._status = "BUSUK"
            return

        # Miselium tumbuh, panas metabolisme menaikkan suhu internal
        self.__kadar_miselium += Config.LAJU_GLUKOSA
        self.__suhu_internal = suhu + self.__kadar_miselium * 0.1

        # pH naik sedikit dan tekstur memadat/menurun
        self._ph += Config.LAJU_PH
        self._tekstur = max(Config.TEKSTUR_MINIMUM, self._tekstur - 1.0)

        # Tentukan status
        if self.__kadar_miselium >= self._berat_awal * 20:
            self._status = "MATANG"
        else:
            self._status = "FERMENTASI"

    def get_kadar_miselium(self) -> float:
        return self.__kadar_miselium

    def get_suhu_internal(self) -> float:
        return self.__suhu_internal