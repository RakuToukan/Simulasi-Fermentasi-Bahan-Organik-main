from config import Config
from models.bahan_organik import BahanOrganik


class Singkong(BahanOrganik):
    def __init__(self, berat_awal: float):
        super().__init__(berat_awal)
        self.__kadar_etanol: float = 0.0
        self.__glukosa: float = berat_awal * 100  # cadangan glukosa awal

    def reaksi_biologis(self, suhu: float, kedap_udara: bool) -> None:
        if self._status == "BUSUK":
            return

        # Tanpa kedap udara, singkong membusuk (bukan jadi tape)
        if not kedap_udara:
            self._status = "BUSUK"
            return

        # Glukosa diubah menjadi etanol
        glukosa_terpakai = min(Config.LAJU_GLUKOSA, self.__glukosa)
        self.__glukosa -= glukosa_terpakai
        self.__kadar_etanol += glukosa_terpakai

        # pH turun dan tekstur melunak
        self._ph -= Config.LAJU_PH
        self._tekstur = max(Config.TEKSTUR_MINIMUM, self._tekstur - 1.0)

        # Tentukan status
        if self._ph < Config.PH_MINIMUM_AMAN:
            self._status = "BUSUK"
        elif self.__glukosa == 0:
            self._status = "MATANG"
        else:
            self._status = "FERMENTASI"

    def get_kadar_etanol(self) -> float:
        return self.__kadar_etanol