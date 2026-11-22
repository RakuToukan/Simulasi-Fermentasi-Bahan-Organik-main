import contextlib
import io
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk

from config import Config
from exceptions import FermentasiError, InputTidakValidError
from models.kedelai import Kedelai
from models.mesin_inkubator import SUHU_MAKS, SUHU_MIN, MesinInkubator
from models.singkong import Singkong

MESIN = ("A", "B")
BAHAN = {"A": Singkong, "B": Kedelai}
JUDUL = {"A": "Singkong → Tape", "B": "Kedelai → Tempe"}
CONFIG_KEYS = ["LAJU_GLUKOSA", "LAJU_PH", "PH_MINIMUM_AMAN", "TEKSTUR_MINIMUM", "TEKSTUR_MAKSIMUM"]

DURASI_PUTAR_MS = 14000   # satu putaran animasi dari jam 0 sampai jam terakhir
INTERVAL_FRAME_MS = 50
MAKS_JAM = 5000           # di atas ini animasi mulai berat
PH_GRAFIK_MIN, PH_GRAFIK_MAKS = 3.0, 13.0

# Warna UI: hijau hanya untuk aksi utama, warna lain berasal dari status
BG = "#141619"
SURFACE = "#1d2024"
SURFACE_2 = "#121417"
BORDER = "#2c3036"
TEKS = "#e6e7ea"
TEKS_REDUP = "#a3a9b2"
AKSEN = "#2fa572"
AKSEN_HOVER = "#268a5f"
NETRAL = "#343941"
NETRAL_HOVER = "#41474f"
ERROR = "#e5484d"
ERROR_LATAR = "#3a1d1f"
FONT = "Segoe UI"

LABEL_STATUS = {"MENTAH": "Mentah", "FERMENTASI": "Fermentasi", "MATANG": "Matang", "BUSUK": "Busuk"}
TEKS_VERDIK = {"MENTAH": "MENTAH", "FERMENTASI": "BELUM MATANG", "MATANG": "MATANG", "BUSUK": "BUSUK"}
# (latar badge, warna teks di atasnya)
WARNA_STATUS = {
    "MENTAH": ("#6b7280", "#ffffff"),
    "FERMENTASI": ("#f5a623", "#1b1300"),
    "MATANG": ("#2ecc71", "#052e16"),
    "BUSUK": ("#b3261e", "#ffffff"),
}

# Warna bahan dipakai ilustrasi dan legenda, jadi keduanya selalu sama
WARNA_SINGKONG = {"MENTAH": "#efe8d0", "FERMENTASI": "#e9d78f", "MATANG": "#d9a441", "BUSUK": "#3b3426"}
WARNA_TEMPE = {"MENTAH": "#e2cf96", "FERMENTASI": "#f1ede0", "MATANG": "#ffffff", "BUSUK": "#2e2e2e"}
# Butir kedelai makin tertutup miselium; saat matang tidak terlihat lagi
BUTIR_TEMPE = {"MENTAH": "#b8923f", "FERMENTASI": "#cdbb8a"}
WARNA_JAMUR = "#9be36b"
WARNA_GELEMBUNG = "#dfe9f5"
WARNA_BUNGKUS = ("#6b4d2c", "#8a6a3e")   # (isi, garis)
WARNA_KEDAP = "#bfdcff"


# Simulasi

def nilai_indikator(bahan) -> float:
    # Besaran penentu matang: sisa glukosa (singkong) atau miselium (kedelai)
    if isinstance(bahan, Singkong):
        return bahan.get_glukosa()
    return bahan.get_kadar_miselium()


def jalankan_simulasi(input_mesin: dict, config: dict) -> dict:
    # Config diubah sementara lalu dikembalikan, agar tidak bocor ke simulasi berikutnya
    asli = {k: getattr(Config, k) for k in CONFIG_KEYS}
    try:
        for k, v in config.items():
            setattr(Config, k, v)
        hasil = {}
        for kode, kelas in BAHAN.items():
            i = input_mesin[kode]
            bahan = kelas(berat_awal=i["berat"])
            mesin = MesinInkubator(suhu_lingkungan=i["suhu"], kedap_udara=i["kedap"], bahan=bahan)
            # Riwayat model punya kolom tetap (dipakai exporter), jadi indikator dicatat terpisah
            indikator = [nilai_indikator(bahan)]
            for _ in range(i["jam"]):
                mesin.jalankan_simulasi(jam=1, interval_cetak=1)
                indikator.append(nilai_indikator(bahan))
            hasil[kode] = {**i, "bahan": kelas.__name__, "riwayat": mesin.riwayat, "indikator": indikator}
        return hasil
    finally:
        for k, v in asli.items():
            setattr(Config, k, v)


# Olah hasil untuk tampilan

def riwayat_per_jam(data: dict, tekstur_awal: float) -> list:
    # Indeks ke-k adalah kondisi pada jam k; jam 0 = kondisi awal
    awal = {"jam": 0, "status": "MENTAH", "ph": 7.0, "tekstur": tekstur_awal}
    baris = [awal] + data["riwayat"]
    for r in baris:
        r["indikator"] = data["indikator"][r["jam"]]
    return baris


def status_pada(riwayat: list, jam: float) -> dict:
    return riwayat[min(int(jam), len(riwayat) - 1)]


def info_indikator(data: dict) -> dict:
    if data["bahan"] == "Singkong":
        return {"nama": "Glukosa tersisa", "kolom": "Glukosa", "syarat": "Matang saat habis",
                "maks": data["indikator"][0], "warna": "#e9d78f"}
    return {"nama": "Miselium", "kolom": "Miselium", "syarat": "Matang saat penuh",
            "maks": data["berat"] * 20, "warna": "#f4f3ec"}


def ringkas(data: dict, ph_aman: float) -> dict:
    # Kesimpulan diambil dari riwayat model, bukan dihitung ulang
    hourly = data["hourly"]
    akhir = hourly[-1]
    total, status = akhir["jam"], akhir["status"]
    jam_matang = next((r["jam"] for r in hourly if r["status"] == "MATANG"), None)
    jam_busuk = next((r["jam"] for r in hourly if r["status"] == "BUSUK"), None)

    if status == "BUSUK":
        if data["bahan"] == "Singkong" and not data["kedap"]:
            alasan = "Udara tidak kedap, jadi singkong membusuk dan tidak menjadi tape."
        elif data["bahan"] == "Kedelai" and data["kedap"]:
            alasan = "Bungkus tertutup, jadi jamur tempe tidak mendapat udara dan gagal tumbuh."
        else:
            alasan = f"pH turun di bawah batas aman {ph_aman:g}."
    elif status == "MATANG":
        alasan = f"Matang pada jam {jam_matang} dari {total} jam simulasi."
    else:
        alasan = f"Belum matang setelah {total} jam. Tambah total jam untuk melihat hasil akhirnya."

    return {"status": status, "alasan": alasan, "total": total, "jam_matang": jam_matang,
            "jam_busuk": jam_busuk, "ph": akhir["ph"], "tekstur": akhir["tekstur"]}


def keterangan(s: dict, r: dict) -> str:
    if s["status"] == "BUSUK":
        return f"Membusuk sejak jam {r['jam_busuk']}. Proses berhenti."
    if s["status"] == "MATANG":
        return f"Matang sejak jam {r['jam_matang']}."
    if s["jam"] == 0:
        return "Belum dimulai."
    if s["jam"] >= r["total"]:
        return f"Selesai di jam {r['total']}, belum matang."
    return "Sedang fermentasi."


def tabel_teks(data: dict) -> str:
    kolom = info_indikator(data)["kolom"]
    baris = [f"{'Jam':>4}  {'Status':<12} {'pH':>6}  {'Tekstur':>8}  {kolom:>9}", "-" * 49]
    for r in data["hourly"]:
        if r["jam"] % data["interval"] == 0:
            baris.append(f"{r['jam']:>4}  {r['status']:<12} {r['ph']:>6.2f}  "
                         f"{r['tekstur']:>8.1f}  {r['indikator']:>9.1f}")
    return "\n".join(baris)


# Gambar di kanvas

def gambar_butir_kedelai(c, x0, y0, x1, y1, warna, r=3):
    kolom = max(2, int((x1 - x0) // (r * 4)))
    baris = max(1, int((y1 - y0) // (r * 4)))
    for i in range(kolom):
        for j in range(baris):
            cx = x0 + (i + 0.5) * (x1 - x0) / kolom + (r * 0.6 if j % 2 else 0)
            cy = y0 + (j + 0.5) * (y1 - y0) / baris
            if cx + r <= x1:
                c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=warna, outline="")


def gambar_jamur(c, titik):
    for x, y in titik:
        c.create_oval(x - 7, y - 7, x + 7, y + 7, fill=WARNA_JAMUR, outline="")


def gambar_singkong(c, w, h, status, kedap):
    if kedap:
        x0, x1, y0, y1 = w * 0.22, w * 0.78, h * 0.22, h * 0.86
        c.create_rectangle(x0, y0, x1, y1, outline=WARNA_KEDAP, width=2)
        c.create_rectangle(x0 - 6, y0 - 12, x1 + 6, y0, fill="#5b6474", outline="")
        c.create_text(w / 2, h - 16, fill=WARNA_KEDAP, font=(FONT, 9), text="Wadah kedap udara")
        cx, cy, rx, ry = w / 2, h / 2 + 6, w * 0.13, h * 0.11
        posisi = [(cx + (i % 3 - 1) * rx, cy + (i // 3 - 0.5) * ry * 2) for i in range(6)]
    else:
        # Mangkuk terbuka: setengah lingkaran di bawah garis bibir
        x0, x1 = w * 0.2, w * 0.8
        bibir, dalam = h * 0.5, h * 0.34
        c.create_arc(x0, bibir - dalam, x1, bibir + dalam, start=180, extent=180,
                     fill="#9aa0ab", outline="#c4c9d2", width=2)
        c.create_line(x0, bibir, x1, bibir, fill="#c4c9d2", width=2)
        c.create_text(w / 2, h - 16, fill="#f0a35e", font=(FONT, 9), text="Wadah terbuka: udara masuk")
        posisi = [(w * (0.36 + i % 3 * 0.14), bibir + h * (0.08 + i // 3 * 0.13)) for i in range(6)]

    for x, y in posisi:
        c.create_oval(x - 18, y - 11, x + 18, y + 11, fill=WARNA_SINGKONG[status], outline="#8a7a4a")
    if status == "BUSUK":
        gambar_jamur(c, [(w * 0.3, h * 0.45), (w * 0.62, h * 0.5), (w * 0.45, h * 0.66)])
    elif kedap and status == "FERMENTASI":
        for x, y in ((w * 0.3, h * 0.33), (w * 0.7, h * 0.3), (w * 0.5, h * 0.4)):
            c.create_oval(x - 4, y - 4, x + 4, y + 4, outline=WARNA_GELEMBUNG)


def gambar_tempe(c, w, h, status, kedap):
    isi, garis = WARNA_BUNGKUS
    c.create_rectangle(w * 0.1, h * 0.3, w * 0.9, h * 0.72, fill=isi, outline=garis, width=2)
    for i in range(6):
        x, y = w * (0.2 + i % 3 * 0.3), h * (0.4 + i // 3 * 0.2)
        x0, y0, x1, y1 = x - w * 0.09, y - h * 0.06, x + w * 0.09, y + h * 0.06
        c.create_rectangle(x0, y0, x1, y1, fill=WARNA_TEMPE[status], outline="")
        if status in BUTIR_TEMPE:
            gambar_butir_kedelai(c, x0 + 3, y0 + 3, x1 - 3, y1 - 3, BUTIR_TEMPE[status])
    if status == "BUSUK":
        gambar_jamur(c, [(w * 0.25, h * 0.5), (w * 0.55, h * 0.6), (w * 0.8, h * 0.45)])

    if kedap:
        c.create_rectangle(w * 0.07, h * 0.26, w * 0.93, h * 0.76, outline=WARNA_KEDAP, width=2, dash=(4, 3))
        c.create_text(w / 2, h - 16, fill=WARNA_KEDAP, font=(FONT, 9),
                      text="Bungkus tertutup: jamur tidak dapat udara")
    else:
        c.create_text(w / 2, h - 16, fill="#a7f0b5", font=(FONT, 9),
                      text="Bungkus terbuka: jamur mendapat udara")


def gambar_tanda_busuk(c, w, h):
    c.create_rectangle(2, 2, w - 2, h - 2, outline=ERROR, width=4)
    c.create_rectangle(w / 2 - 52, 8, w / 2 + 52, 34, fill=ERROR, outline="")
    c.create_text(w / 2, 21, fill="#ffffff", font=(FONT, 12, "bold"), text="BUSUK")


def gambar_legenda(c, bahan, status_kini):
    c.delete("all")
    font = tkfont.Font(family=FONT, size=9)
    tebal = tkfont.Font(family=FONT, size=9, weight="bold")
    lebar = max(c.winfo_width(), 200)
    kiri, tinggi_baris = 88, 22

    def contoh_warna(status):
        def gambar(x, y):
            if bahan == "Singkong":
                c.create_oval(x, y - 5, x + 16, y + 5, fill=WARNA_SINGKONG[status], outline="#8a7a4a")
            else:
                c.create_rectangle(x, y - 5, x + 16, y + 5, fill=WARNA_TEMPE[status], outline=WARNA_BUNGKUS[1])
                for dx in (4, 8, 12) if status in BUTIR_TEMPE else ():
                    c.create_oval(x + dx - 1.5, y - 1.5, x + dx + 1.5, y + 1.5,
                                  fill=BUTIR_TEMPE[status], outline="")
            if status == status_kini:
                c.create_rectangle(x - 3, y - 8, x + 19, y + 8, outline=TEKS)
        return gambar

    warna = [(contoh_warna(st), LABEL_STATUS[st], st == status_kini) for st in LABEL_STATUS]
    if bahan == "Singkong":
        simbol = [(lambda x, y: c.create_oval(x + 4, y - 4, x + 12, y + 4, outline=WARNA_GELEMBUNG),
                   "Gelembung gas fermentasi", False)]
    else:
        simbol = [(lambda x, y: c.create_rectangle(x, y - 6, x + 16, y + 6, fill=WARNA_BUNGKUS[0],
                                                   outline=WARNA_BUNGKUS[1]), "Pembungkus", False),
                  (lambda x, y: c.create_rectangle(x, y - 6, x + 16, y + 6, outline=WARNA_KEDAP,
                                                   dash=(3, 2)), "Bungkus rapat", False)]
    simbol.append((lambda x, y: c.create_oval(x + 2, y - 6, x + 14, y + 6, fill=WARNA_JAMUR, outline=""),
                   "Jamur pembusuk", False))

    # Item mengalir ke kanan dan turun ke baris baru bila tidak muat
    y = 14
    for judul, items in (("Warna bahan", warna), ("Simbol", simbol)):
        c.create_text(10, y, anchor="w", fill=TEKS_REDUP, font=font, text=judul)
        x = kiri
        for gambar, teks, aktif in items:
            f = tebal if aktif else font
            lebar_item = 22 + f.measure(teks)
            if x > kiri and x + lebar_item > lebar - 8:
                x, y = kiri, y + tinggi_baris
            gambar(x, y)
            c.create_text(x + 22, y, anchor="w", fill=TEKS if aktif else TEKS_REDUP, font=f, text=teks)
            x += lebar_item + 14
        y += tinggi_baris

    tinggi = y - tinggi_baris + 14
    if int(c.cget("height")) != tinggi:
        c.configure(height=tinggi)


def gambar_grafik(c, riwayat, jam_maks, jam_kini, batas_ph=None):
    c.delete("all")
    w, h = c.winfo_width(), c.winfo_height()
    if w < 60 or h < 40:
        return
    gx, gy = 34, 22
    gw, gh = w - gx - 12, h - gy - 22
    font = (FONT, 9)

    def X(jam):
        return gx + jam / jam_maks * gw

    def Y(ph):
        ph = min(max(ph, PH_GRAFIK_MIN), PH_GRAFIK_MAKS)
        return gy + gh - (ph - PH_GRAFIK_MIN) / (PH_GRAFIK_MAKS - PH_GRAFIK_MIN) * gh

    c.create_text(gx, 4, anchor="nw", fill=TEKS_REDUP, font=(FONT, 9, "bold"), text="pH per jam")
    for ph in (4, 7, 10, 13):
        c.create_line(gx, Y(ph), gx + gw, Y(ph), fill="#23272e")
        c.create_text(gx - 6, Y(ph), anchor="e", fill=TEKS_REDUP, font=font, text=str(ph))
    if batas_ph is not None:
        c.create_line(gx, Y(batas_ph), gx + gw, Y(batas_ph), fill=ERROR, dash=(4, 3))
        c.create_text(gx + gw, 4, anchor="ne", fill="#f08a8d", font=font, text=f"- - batas aman pH {batas_ph:g}")

    titik = [v for r in riwayat for v in (X(r["jam"]), Y(r["ph"]))]
    if len(titik) >= 4:
        c.create_line(*titik, fill=TEKS, width=2)

    s = status_pada(riwayat, jam_kini)
    xk = X(min(jam_kini, riwayat[-1]["jam"]))
    c.create_line(xk, gy, xk, gy + gh, fill="#5c636d")
    c.create_oval(xk - 5, Y(s["ph"]) - 5, xk + 5, Y(s["ph"]) + 5,
                  fill=WARNA_STATUS[s["status"]][0], outline=SURFACE_2, width=2)
    c.create_text(gx, h - 4, anchor="sw", fill=TEKS_REDUP, font=font, text="jam 0")
    c.create_text(gx + gw, h - 4, anchor="se", fill=TEKS_REDUP, font=font, text=f"jam {jam_maks}")


# Jendela utama

class AplikasiSimulasi(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.title("Simulasi Fermentasi · Mesin Inkubator")
        self.geometry("1280x800")
        self.minsize(1100, 700)

        self.sim = None           # hasil simulasi terakhir yang valid, per mesin
        self.ph_aman = None
        self.jam_maks = 0         # sumbu waktu bersama kedua mesin
        self.berjalan = False
        self.progres_ms = 0.0
        self.input = {}
        self._vars = []           # StringVar harus disimpan, kalau tidak dibuang garbage collector
        self._jadwal = None
        self._cache = {}          # nilai terakhir tiap widget, agar configure() tidak diulang tiap frame
        self._legenda_kini = {}

        self._bangun_layout()
        self.terapkan()
        self.after(INTERVAL_FRAME_MS, self._frame)

    # Layout

    def _bangun_layout(self):
        self.configure(fg_color=BG)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._bangun_sidebar()

        self.tab = ctk.CTkTabview(self, fg_color=BG, segmented_button_fg_color=SURFACE,
                                  segmented_button_unselected_color=SURFACE,
                                  segmented_button_selected_color=NETRAL,
                                  segmented_button_selected_hover_color=NETRAL_HOVER)
        self.tab.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=(4, 12))
        self._bangun_tab_simulasi(self.tab.add("Simulasi"))
        self._bangun_tab_hasil(self.tab.add("Hasil"))

    def _bangun_sidebar(self):
        # Judul dan kotak status tetap terlihat; hanya isian yang digulir
        sisi = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=10)
        sisi.grid(row=0, column=0, sticky="ns", padx=(12, 6), pady=12)
        sisi.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(sisi, text="Pengaturan", text_color=TEKS, anchor="w",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="ew",
                                                                    padx=16, pady=(14, 2))

        panel = ctk.CTkScrollableFrame(sisi, width=290, fg_color="transparent")
        panel.grid(row=1, column=0, sticky="ns", padx=(4, 0))
        self._grup_bahan(panel, "A", "Ya: wadah tertutup rapat. Tape hanya jadi jika kedap udara.",
                         berat="2.5", suhu="31", kedap="Ya", jam="50", interval="5")
        self._pemisah(panel)
        self._grup_bahan(panel, "B", "Tidak: tempe butuh udara. Jika dibungkus rapat, tempe gagal.",
                         berat="1.0", suhu="30", kedap="Tidak", jam="100", interval="10")
        self._pemisah(panel)
        self._grup_config(panel)

        self.kotak_status = ctk.CTkFrame(sisi, fg_color=SURFACE_2, corner_radius=8)
        self.kotak_status.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
        self.lbl_status = ctk.CTkLabel(self.kotak_status, text="", wraplength=270, justify="left",
                                       anchor="w", font=ctk.CTkFont(size=12))
        self.lbl_status.pack(fill="x", padx=10, pady=8)

    def _pemisah(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(fill="x", padx=10, pady=10)

    def _judul_grup(self, parent, kecil, besar):
        ctk.CTkLabel(parent, text=kecil, text_color=TEKS_REDUP, anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", padx=10, pady=(4, 0))
        ctk.CTkLabel(parent, text=besar, text_color=TEKS, anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", padx=10, pady=(0, 6))

    def _baris(self, parent, label, pady=3):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=10, pady=pady)
        if label:
            ctk.CTkLabel(r, text=label, text_color=TEKS).pack(side="left")
        return r

    def _catatan(self, parent, teks, pady):
        ctk.CTkLabel(parent, text=teks, font=ctk.CTkFont(size=12), text_color=TEKS_REDUP,
                     wraplength=270, justify="left", anchor="w").pack(fill="x", padx=10, pady=pady)

    def _grup_bahan(self, parent, kode, catatan, **nilai):
        self._judul_grup(parent, f"Mesin {kode}", JUDUL[kode])
        isian = [("Berat awal (kg)", "berat"), (f"Suhu ({SUHU_MIN:g}–{SUHU_MAKS:g} °C)", "suhu"),
                 ("Total jam", "jam"), ("Tabel tiap (jam)", "interval")]
        for label, kunci in isian:
            self.input[f"{kode}_{kunci}"] = self._buat_entry(self._baris(parent, label), nilai[kunci])

        opsi = ctk.CTkSegmentedButton(self._baris(parent, "Kedap udara", pady=(3, 2)),
                                      values=["Ya", "Tidak"], width=110, text_color=TEKS,
                                      fg_color=SURFACE_2, unselected_color=SURFACE_2,
                                      unselected_hover_color=NETRAL, selected_color="#5a616b",
                                      selected_hover_color="#666d78",
                                      command=lambda _: self._input_berubah())
        opsi.set(nilai["kedap"])
        opsi.pack(side="right")
        self.input[f"{kode}_kedap"] = opsi
        self._catatan(parent, catatan, pady=(4, 0))

    def _grup_config(self, parent):
        self._judul_grup(parent, "Model (config.py)", "Konfigurasi")
        isian = [("Laju glukosa", "LAJU_GLUKOSA", "0.5"), ("Laju pH", "LAJU_PH", "0.05"),
                 ("pH minimum aman", "PH_MINIMUM_AMAN", "3.5"),
                 ("Tekstur minimum", "TEKSTUR_MINIMUM", "10"),
                 ("Tekstur maksimum", "TEKSTUR_MAKSIMUM", "100")]
        for label, nama, awal in isian:
            r = self._baris(parent, None)
            teks = ctk.CTkFrame(r, fg_color="transparent")
            teks.pack(side="left")
            ctk.CTkLabel(teks, text=label, text_color=TEKS, height=18, anchor="w").pack(anchor="w")
            ctk.CTkLabel(teks, text=nama, text_color=TEKS_REDUP, height=14, anchor="w",
                         font=ctk.CTkFont(family="Consolas", size=10)).pack(anchor="w")
            self.input[f"cfg_{nama}"] = self._buat_entry(r, awal)
        self._catatan(parent, "Perubahan diterapkan otomatis ke kedua mesin.", pady=(6, 8))

    def _buat_entry(self, parent, nilai):
        var = tk.StringVar(value=nilai)
        var.trace_add("write", lambda *_: self._input_berubah())
        self._vars.append(var)
        e = ctk.CTkEntry(parent, width=100, textvariable=var, justify="right",
                         fg_color=SURFACE_2, border_color=BORDER, text_color=TEKS)
        e.pack(side="right")
        return e

    def _bangun_tab_simulasi(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1, uniform="mesin")
        tab.grid_rowconfigure(0, weight=1)
        self.kartu = {}
        for col, k in enumerate(MESIN):
            self.kartu[k] = self._kartu_mesin(tab, k)
            self.kartu[k]["frame"].grid(row=0, column=col, sticky="nsew", padx=6, pady=(4, 6))

        dock = ctk.CTkFrame(tab, fg_color=SURFACE, corner_radius=10)
        dock.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
        self.btn_mulai = ctk.CTkButton(dock, text="▶  Mulai", width=110, height=34, command=self.mulai,
                                       fg_color=AKSEN, hover_color=AKSEN_HOVER, state="disabled",
                                       font=ctk.CTkFont(weight="bold"))
        self.btn_mulai.pack(side="left", padx=(12, 6), pady=10)
        self.btn_jeda = ctk.CTkButton(dock, text="Jeda", width=80, height=34, fg_color=NETRAL,
                                      hover_color=NETRAL_HOVER, command=self.jeda, state="disabled")
        self.btn_jeda.pack(side="left", padx=(0, 6))
        self.btn_ulang = ctk.CTkButton(dock, text="Ulang", width=80, height=34, fg_color=NETRAL,
                                       hover_color=NETRAL_HOVER, command=self.ulang, state="disabled")
        self.btn_ulang.pack(side="left", padx=(0, 16))
        self.lbl_jam = ctk.CTkLabel(dock, text="Jam 0 / 0", width=110, anchor="e", text_color=TEKS,
                                    font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_jam.pack(side="right", padx=(12, 14))
        self.slider = ctk.CTkSlider(dock, from_=0, to=1, command=self._geser, button_color=TEKS,
                                    button_hover_color="#ffffff", progress_color=AKSEN)
        self.slider.set(0)
        self.slider.pack(side="left", fill="x", expand=True)

    def _kartu_mesin(self, parent, k):
        kartu = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10)
        kartu.grid_columnconfigure(0, weight=1)
        kartu.grid_rowconfigure(4, weight=1)
        ui = {"frame": kartu}

        head = ctk.CTkFrame(kartu, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 0))
        ctk.CTkLabel(head, text=f"Mesin {k}", text_color=TEKS_REDUP,
                     font=ctk.CTkFont(size=12)).pack(side="top", anchor="w")
        ctk.CTkLabel(head, text=JUDUL[k], text_color=TEKS,
                     font=ctk.CTkFont(size=17, weight="bold")).pack(side="left")
        ui["badge"] = ctk.CTkLabel(head, text="", width=96, height=28, corner_radius=6,
                                   font=ctk.CTkFont(size=13, weight="bold"))
        ui["badge"].pack(side="right")

        ui["ket"] = ctk.CTkLabel(kartu, text="", text_color=TEKS, wraplength=380, justify="left",
                                 font=ctk.CTkFont(size=13))
        ui["ket"].grid(row=1, column=0, sticky="w", padx=14, pady=(6, 0))
        ui["info"] = ctk.CTkLabel(kartu, text="", text_color=TEKS_REDUP, wraplength=380, justify="left",
                                  font=ctk.CTkFont(size=12))
        ui["info"].grid(row=2, column=0, sticky="w", padx=14, pady=(0, 8))

        ind = ctk.CTkFrame(kartu, fg_color=SURFACE_2, corner_radius=8)
        ind.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 8))
        ind.grid_columnconfigure(0, weight=1)
        tebal = ctk.CTkFont(size=12, weight="bold")
        ui["ind_nama"] = ctk.CTkLabel(ind, text="", text_color=TEKS, anchor="w", height=18, font=tebal)
        ui["ind_nama"].grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
        ui["ind_nilai"] = ctk.CTkLabel(ind, text="", text_color=TEKS, anchor="e", height=18, font=tebal)
        ui["ind_nilai"].grid(row=0, column=1, sticky="e", padx=10, pady=(8, 0))
        ui["ind_bar"] = ctk.CTkProgressBar(ind, height=10, corner_radius=4, fg_color="#2a2e34")
        ui["ind_bar"].grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(6, 2))
        ui["ind_syarat"] = ctk.CTkLabel(ind, text="", text_color=TEKS_REDUP, anchor="w", height=16,
                                        font=ctk.CTkFont(size=11))
        ui["ind_syarat"].grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6))

        ui["mesin"] = tk.Canvas(kartu, bg=SURFACE_2, highlightthickness=0)
        ui["mesin"].grid(row=4, column=0, sticky="nsew", padx=14)
        ui["legenda"] = tk.Canvas(kartu, height=50, bg=SURFACE_2, highlightthickness=0)
        ui["legenda"].grid(row=5, column=0, sticky="ew", padx=14, pady=(1, 8))
        ui["grafik"] = tk.Canvas(kartu, height=130, bg=SURFACE_2, highlightthickness=0)
        ui["grafik"].grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 14))
        return ui

    def _bangun_tab_hasil(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1, uniform="hasil")
        tab.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(tab, text="Kesimpulan akhir tiap mesin. Tabel berisi kondisi tiap jam "
                               "sesuai 'Tabel tiap (jam)' (jam 0 = kondisi awal).",
                     text_color=TEKS_REDUP, wraplength=900, justify="left").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 2))

        self.hasil_ui = {}
        for col, k in enumerate(MESIN):
            f = ctk.CTkFrame(tab, fg_color=SURFACE, corner_radius=10)
            f.grid(row=1, column=col, sticky="nsew", padx=6, pady=6)
            f.grid_columnconfigure(0, weight=1)
            f.grid_rowconfigure(4, weight=1)
            ctk.CTkLabel(f, text=f"Mesin {k} · {JUDUL[k]}", text_color=TEKS,
                         font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w",
                                                                        padx=14, pady=(12, 6))
            ui = {
                "verdik": ctk.CTkLabel(f, text="—", corner_radius=8, height=44,
                                       font=ctk.CTkFont(size=20, weight="bold")),
                "alasan": ctk.CTkLabel(f, text="", text_color=TEKS, wraplength=400, justify="left"),
                "ringkas": ctk.CTkLabel(f, text="", text_color=TEKS_REDUP, justify="left",
                                        font=ctk.CTkFont(size=12)),
                "tabel": ctk.CTkTextbox(f, font=("Consolas", 12), fg_color=SURFACE_2, text_color=TEKS),
            }
            ui["verdik"].grid(row=1, column=0, sticky="ew", padx=14, pady=4)
            ui["alasan"].grid(row=2, column=0, sticky="w", padx=14, pady=(6, 2))
            ui["ringkas"].grid(row=3, column=0, sticky="w", padx=14, pady=(0, 6))
            ui["tabel"].grid(row=4, column=0, sticky="nsew", padx=14, pady=(4, 14))
            self.hasil_ui[k] = ui

    # Membaca isian dan menjalankan simulasi

    def _baca_isian(self):
        # Semua isian dicek sekaligus; isian salah diberi garis merah
        salah = []

        def angka(kunci, nama, bulat=False, minimum=None, maksimum=None, lebih_dari=None):
            teks = self.input[kunci].get().strip().replace(",", ".")
            try:
                v = int(teks) if bulat else float(teks)
            except ValueError:
                salah.append((kunci, f"{nama} harus {'bilangan bulat' if bulat else 'angka'}."))
                return None
            if lebih_dari is not None and v <= lebih_dari:
                salah.append((kunci, f"{nama} harus lebih dari {lebih_dari:g}."))
            elif minimum is not None and not minimum <= v <= maksimum:
                salah.append((kunci, f"{nama} harus antara {minimum:g} dan {maksimum:g}."))
            return v

        input_mesin = {}
        for k in MESIN:
            m = f"Mesin {k}:"
            input_mesin[k] = {
                "berat": angka(f"{k}_berat", f"{m} berat awal", lebih_dari=0),
                "suhu": angka(f"{k}_suhu", f"{m} suhu", minimum=SUHU_MIN, maksimum=SUHU_MAKS),
                "kedap": self.input[f"{k}_kedap"].get() == "Ya",
                "jam": angka(f"{k}_jam", f"{m} total jam", bulat=True, minimum=1, maksimum=MAKS_JAM),
                "interval": angka(f"{k}_interval", f"{m} tabel tiap", bulat=True, lebih_dari=0),
            }
        config = {nama: angka(f"cfg_{nama}", nama) for nama in CONFIG_KEYS}

        kunci_salah = {k for k, _ in salah}
        for kunci, widget in self.input.items():
            if isinstance(widget, ctk.CTkEntry):
                widget.configure(border_color=ERROR if kunci in kunci_salah else BORDER)
        if salah:
            lain = f" (+{len(salah) - 1} isian lain)" if len(salah) > 1 else ""
            raise InputTidakValidError(salah[0][1] + lain)
        return input_mesin, config

    def terapkan(self):
        try:
            input_mesin, config = self._baca_isian()
            with contextlib.redirect_stdout(io.StringIO()):   # model mencetak log tiap jam
                hasil = jalankan_simulasi(input_mesin, config)
        except FermentasiError as e:
            self._status(str(e), error=True)
            return
        except Exception as e:
            self._status(f"Terjadi kesalahan: {e}", error=True)
            return

        self.ph_aman = config["PH_MINIMUM_AMAN"]
        for d in hasil.values():
            d["hourly"] = riwayat_per_jam(d, config["TEKSTUR_MAKSIMUM"])
            d["ringkas"] = ringkas(d, self.ph_aman)
        self.sim = hasil
        self.jam_maks = max(d["hourly"][-1]["jam"] for d in hasil.values())
        self.berjalan = False
        self.progres_ms = 0.0

        self._isi_tab_hasil()
        self._atur_tombol()
        tape, tempe = (TEKS_VERDIK[hasil[k]["ringkas"]["status"]].lower() for k in MESIN)
        self._status(f"Tape: {tape} · Tempe: {tempe}. Rincian ada di tab Hasil.")
        self._perbarui_tampilan()

    def _input_berubah(self):
        # Tunggu isian berhenti berubah sebentar sebelum menjalankan ulang simulasi
        if self._jadwal is not None:
            self.after_cancel(self._jadwal)
        self._jadwal = self.after(400, self._terapkan_otomatis)

    def _terapkan_otomatis(self):
        self._jadwal = None
        self.terapkan()

    def _status(self, teks, error=False):
        if error and self.sim is not None:
            teks += "\nTampilan masih memakai hasil terakhir yang valid."
        self.kotak_status.configure(fg_color=ERROR_LATAR if error else SURFACE_2)
        self.lbl_status.configure(text=teks, text_color="#ffb4b6" if error else TEKS_REDUP)

    def _atur(self, widget, **opsi):
        if self._cache.get(str(widget)) != opsi:
            widget.configure(**opsi)
            self._cache[str(widget)] = opsi

    # Kontrol animasi

    def _atur_tombol(self):
        ada = self.sim is not None
        lanjut = 0 < self.progres_ms < DURASI_PUTAR_MS
        self.btn_mulai.configure(state="normal" if ada and not self.berjalan else "disabled",
                                 text="▶  Lanjut" if lanjut else "▶  Mulai")
        self.btn_jeda.configure(state="normal" if self.berjalan else "disabled")
        self.btn_ulang.configure(state="normal" if ada else "disabled")

    def mulai(self):
        if not self.sim:
            return
        if self.progres_ms >= DURASI_PUTAR_MS:
            self.progres_ms = 0.0
        self.berjalan = True
        self._atur_tombol()

    def jeda(self):
        self.berjalan = False
        self._atur_tombol()

    def ulang(self):
        self.progres_ms = 0.0
        self.jeda()
        self._perbarui_tampilan()

    def _geser(self, nilai):
        if not self.sim:
            return
        self.progres_ms = float(nilai) * DURASI_PUTAR_MS
        self._atur_tombol()
        self._perbarui_tampilan()

    def _frame(self):
        if self.sim and self.berjalan:
            self.progres_ms += INTERVAL_FRAME_MS
            if self.progres_ms >= DURASI_PUTAR_MS:
                self.progres_ms = DURASI_PUTAR_MS
                self.jeda()
                self._status("Simulasi selesai. Lihat tab Hasil untuk kesimpulannya.")
        if self.sim:
            self._perbarui_tampilan()
        self.after(INTERVAL_FRAME_MS, self._frame)

    # Tampilan

    def _perbarui_tampilan(self):
        frac = self.progres_ms / DURASI_PUTAR_MS
        jam = frac * self.jam_maks
        self.slider.set(frac)
        self._atur(self.lbl_jam, text=f"Jam {int(jam)} / {self.jam_maks}")
        for k in MESIN:
            self._perbarui_kartu(k, jam)

    def _perbarui_kartu(self, k, jam):
        d, ui = self.sim[k], self.kartu[k]
        s = status_pada(d["hourly"], jam)
        fg, teks = WARNA_STATUS[s["status"]]
        udara = "kedap udara" if d["kedap"] else "udara terbuka"
        self._atur(ui["badge"], text=LABEL_STATUS[s["status"]], fg_color=fg, text_color=teks)
        self._atur(ui["ket"], text=keterangan(s, d["ringkas"]))
        self._atur(ui["info"], text=f"Jam {s['jam']} · pH {s['ph']:.2f} · Tekstur {s['tekstur']:.0f} · "
                                    f"{d['suhu']:g} °C · {udara}")

        ind = info_indikator(d)
        self._atur(ui["ind_nama"], text=ind["nama"])
        self._atur(ui["ind_syarat"], text=ind["syarat"])
        self._atur(ui["ind_nilai"], text=f"{s['indikator']:.1f} / {ind['maks']:g}")
        self._atur(ui["ind_bar"], progress_color=ind["warna"])
        ui["ind_bar"].set(min(s["indikator"] / ind["maks"], 1.0) if ind["maks"] else 0.0)

        self._gambar_mesin(k, s)
        batas_ph = self.ph_aman if d["bahan"] == "Singkong" else None   # tempe tidak punya batas pH
        gambar_grafik(ui["grafik"], d["hourly"], self.jam_maks, jam, batas_ph)

    def _gambar_mesin(self, k, s):
        d, ui = self.sim[k], self.kartu[k]
        c = ui["mesin"]
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 60 or h < 60:
            return
        gambar = gambar_singkong if d["bahan"] == "Singkong" else gambar_tempe
        gambar(c, w, h, s["status"], d["kedap"])
        if s["status"] == "BUSUK":
            gambar_tanda_busuk(c, w, h)

        # Legenda cukup digambar ulang saat status atau lebarnya berubah
        leg = ui["legenda"]
        kini = (s["status"], leg.winfo_width())
        if self._legenda_kini.get(k) != kini:
            gambar_legenda(leg, d["bahan"], s["status"])
            self._legenda_kini[k] = kini

    def _isi_tab_hasil(self):
        for k in MESIN:
            d, ui = self.sim[k], self.hasil_ui[k]
            r = d["ringkas"]
            fg, teks = WARNA_STATUS[r["status"]]
            ui["verdik"].configure(text=TEKS_VERDIK[r["status"]], fg_color=fg, text_color=teks)
            ui["alasan"].configure(text=r["alasan"])
            ui["ringkas"].configure(text=f"Total {r['total']} jam · pH akhir {r['ph']:.2f} · "
                                         f"Tekstur akhir {r['tekstur']:.1f}")
            tb = ui["tabel"]
            tb.configure(state="normal")
            tb.delete("1.0", "end")
            tb.insert("1.0", tabel_teks(d))
            tb.configure(state="disabled")


def jalankan_gui() -> None:
    AplikasiSimulasi().mainloop()
