from abc import ABC, abstractmethod

class BahanOrganik(ABC):
    def __init__(self, berat_awal: float):
        self._berat_awal: float = berat_awal
        self._waktu_jam: int = 0
        self._status: str = "MENTAH"
        self._ph: float = 7.0 
        self._tekstur: float = 100.0

    def tambah_jam_simulasi(self, suhu: float, kedap_udara: bool) -> None:
        self._waktu_jam += 1
        self.reaksi_biologis(suhu, kedap_udara)

    @abstractmethod
    def reaksi_biologis(self, suhu: float, kedap_udara: bool) -> None:
        pass

    def get_ph(self) -> float:
        return self._ph

    def get_tekstur(self) -> float:
        return self._tekstur

    @property
    def waktu_jam(self) -> int:
        return self._waktu_jam

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, status_baru: str) -> None:
        self._status = status_baru