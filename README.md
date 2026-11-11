# Simulasi Fermentasi Bahan Organik

Simulasi berbasis OOP (Python) untuk proses fermentasi dua bahan organik di dalam mesin inkubator:

- **Singkong → Tape** (fermentasi anaerob, butuh wadah kedap udara)
- **Kedelai → Tempe** (fermentasi aerob, butuh udara)

Setiap jam simulasi, bahan mengalami reaksi biologis yang mengubah pH, tekstur, dan statusnya.

---

## Struktur Proyek

```
.
├── config.py                  # Konstanta simulasi (laju, batas pH, batas tekstur)
├── main.py                    # Titik masuk program (demo tape & tempe)
├── models/
│   ├── __init__.py
│   ├── bahan_organik.py       # Class abstract BahanOrganik
│   ├── singkong.py            # Turunan: fermentasi tape
│   ├── kedelai.py             # Turunan: fermentasi tempe
│   └── mesin_inkubator.py     # Mesin yang menjalankan simulasi
└── tests/
    ├── test_bahan_organik.py
    └── test_mesin_inkubator.py
```

---

## Cara Menjalankan

Kebutuhan: **Python 3.10+**, tanpa library tambahan.

Semua perintah dijalankan dari **folder root proyek** (folder yang berisi `main.py`).

### Menjalankan simulasi

```bash
python main.py
```

Contoh output:

```
--- Memulai Inkubasi Singkong selama 48 Jam ---
Jam 12 | Status: FERMENTASI | pH: 6.40 | Tekstur: 88.0
Jam 24 | Status: FERMENTASI | pH: 5.80 | Tekstur: 76.0
Jam 36 | Status: MATANG     | pH: 5.20 | Tekstur: 64.0
Jam 48 | Status: MATANG     | pH: 4.60 | Tekstur: 52.0
MATANG

==================================================

--- Memulai Inkubasi Kedelai selama 48 Jam ---
Jam 12 | Status: FERMENTASI | pH: 7.60 | Tekstur: 88.0
Jam 24 | Status: FERMENTASI | pH: 8.20 | Tekstur: 76.0
Jam 36 | Status: FERMENTASI | pH: 8.80 | Tekstur: 64.0
Jam 48 | Status: MATANG     | pH: 9.40 | Tekstur: 52.0
MATANG
```

### Menjalankan unit test

```bash
python -m unittest discover -s tests -v
```

Hasil yang diharapkan: **9 tes, semua `ok`**.

---

## Desain Class (UML)

| Class                       | Peran                | Atribut penting                                                                     | Method penting                                                                         |
| --------------------------- | -------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `BahanOrganik` _(abstract)_ | Induk semua bahan    | `berat_awal`, `waktu_jam`, `status`, `ph`, `tekstur`                                | `tambah_jam_simulasi()`, `reaksi_biologis()` _(abstract)_, `get_ph()`, `get_tekstur()` |
| `Singkong`                  | Fermentasi tape      | `__kadar_etanol`, `__glukosa`                                                       | `reaksi_biologis()`, `get_kadar_etanol()`                                              |
| `Kedelai`                   | Fermentasi tempe     | `__kadar_miselium`, `__suhu_internal`                                               | `reaksi_biologis()`, `get_suhu_internal()`                                             |
| `MesinInkubator`            | Menjalankan simulasi | `suhu_lingkungan`, `kedap_udara`, `__bahan`, `__log`                                | `jalankan_simulasi()`, `cetak_laporan()`, `status_akhir()`                             |
| `Config` _(utility)_        | Konstanta            | `LAJU_GLUKOSA`, `LAJU_PH`, `PH_MINIMUM_AMAN`, `TEKSTUR_MINIMUM`, `TEKSTUR_MAKSIMUM` | –                                                                                      |

Relasi:

- `Singkong` dan `Kedelai` **mewarisi** `BahanOrganik`.
- `MesinInkubator` **menampung** satu `BahanOrganik` (komposisi).
- `BahanOrganik` dan turunannya **memakai konstanta** dari `Config`.

---

## Alur Program

```
main.py
 └─ MesinInkubator(suhu_lingkungan, kedap_udara, bahan)
     └─ jalankan_simulasi(jam=48, interval_cetak=12)
         └─ ulangi setiap jam:
             ├─ bahan.tambah_jam_simulasi(suhu, kedap_udara)
             │    ├─ waktu_jam += 1
             │    └─ reaksi_biologis()   ← isi berbeda untuk Singkong / Kedelai
             └─ jika waktu_jam % 12 == 0 → cetak_laporan()
     └─ status_akhir()
```

### Perubahan status

```
MENTAH ──► FERMENTASI ──► MATANG
   │            │            │
   └────────────┴────────────┴──► BUSUK  (reaksi berhenti)
```

| Aturan                   | Singkong (tape)                                  | Kedelai (tempe)                     |
| ------------------------ | ------------------------------------------------ | ----------------------------------- |
| Kondisi udara yang benar | Kedap udara (`True`)                             | Tidak kedap (`False`)               |
| Setiap jam               | Glukosa −0.5 → etanol +0.5, pH −0.05, tekstur −1 | Miselium +0.5, pH +0.05, tekstur −1 |
| Syarat MATANG            | Glukosa habis (glukosa awal = berat × 5)         | Miselium ≥ berat × 20               |
| Syarat BUSUK             | Udara salah, atau pH < 3.5                       | Udara salah                         |

---

## Konsep OOP yang Diterapkan

| Konsep           | Penerapan                                                                             |
| ---------------- | ------------------------------------------------------------------------------------- |
| **Abstraksi**    | `BahanOrganik` adalah class abstract dengan method abstract `reaksi_biologis()`       |
| **Pewarisan**    | `Singkong` dan `Kedelai` mewarisi `BahanOrganik`                                      |
| **Polimorfisme** | Mesin memanggil `tambah_jam_simulasi()` yang sama; reaksinya berbeda per bahan        |
| **Enkapsulasi**  | Atribut private (`__glukosa`, `__kadar_etanol`, `__bahan`, dll.) diakses lewat getter |
| **Komposisi**    | `MesinInkubator` menyimpan objek `BahanOrganik`                                       |

---

## Skenario Demonstrasi

Ubah parameter di `main.py` untuk menunjukkan perilaku yang berbeda.

### 1. Kondisi normal (default)

Jalankan `python main.py` → tape dan tempe sama-sama **MATANG**.

### 2. Kondisi udara salah → BUSUK

```python
inkubator_tape = MesinInkubator(suhu_lingkungan=31.0, kedap_udara=False, bahan=tape)
inkubator_tempe = MesinInkubator(suhu_lingkungan=30.0, kedap_udara=True, bahan=tempe)
```

Hasil: keduanya langsung **BUSUK** sejak jam pertama.

### 3. Fermentasi terlalu lama → tape BUSUK

```python
inkubator_tape.jalankan_simulasi(jam=72, interval_cetak=12)
```

Hasil: tape **MATANG** di jam 25–70, lalu **BUSUK** di jam 71 karena pH < 3.5.

### 4. Waktu terlalu singkat → belum matang

```python
inkubator_tempe.jalankan_simulasi(jam=24, interval_cetak=6)
```

Hasil: tempe masih **FERMENTASI** (baru matang di jam ke-40 untuk berat 1 kg).

### 5. Berat bahan memengaruhi lama fermentasi

```python
tape = Singkong(berat_awal=5.0)   # glukosa 25 → matang di jam ke-50
tempe = Kedelai(berat_awal=2.0)   # target miselium 40 → matang di jam ke-80
```

---

## Konfigurasi

Nilai di `config.py` dapat diubah untuk eksperimen:

| Konstanta          | Nilai | Fungsi                                     |
| ------------------ | ----- | ------------------------------------------ |
| `LAJU_GLUKOSA`     | 0.5   | Glukosa terpakai / miselium tumbuh per jam |
| `LAJU_PH`          | 0.05  | Perubahan pH per jam                       |
| `PH_MINIMUM_AMAN`  | 3.5   | Di bawah nilai ini, tape menjadi BUSUK     |
| `TEKSTUR_MINIMUM`  | 10.0  | Batas bawah tekstur                        |
| `TEKSTUR_MAKSIMUM` | 100.0 | Tekstur awal bahan                         |
