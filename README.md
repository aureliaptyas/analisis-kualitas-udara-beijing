# Proyek Analisis Data: Kualitas Udara Beijing (PRSA, 12 Stasiun)

Analisis PM2.5 dari **PRSA Beijing Multi-Site Air Quality Dataset** (data per jam, 12 stasiun, 1 Maret 2013 – 28 Februari 2017) beserta dashboard interaktif Streamlit.

## Pertanyaan Bisnis
1. Berapa rata-rata PM2.5 per periode 12 bulan (Maret–Februari) dan per musim, serta pada musim apa tertinggi dan terendah?
2. Stasiun mana yang paling sering melewati baku mutu PM2.5 harian 75 µg/m³, dan berapa selisih antara stasiun perkotaan dan pinggiran?
3. Pada kombinasi arah dan kecepatan angin apa PM2.5 paling tinggi, dan berapa penurunannya saat angin > 3 m/s dibanding ≤ 1 m/s?

## Struktur Direktori
```
submission
├───dashboard
│   ├───main_data.csv      # data bersih untuk dashboard (dihasilkan notebook)
│   └───dashboard.py       # aplikasi Streamlit
├───data
│   └───PRSA_Data_*.csv    # 12 berkas dataset asli (satu per stasiun)
├───notebook.ipynb         # proses analisis lengkap (sudah dijalankan)
├───README.md
├───requirements.txt
└───url.txt                # tautan dashboard (isi setelah deploy)
```

## Menjalankan Dashboard di Lokal
Pastikan Python 3.9+ sudah terpasang.

```bash
# 1. (opsional) buat virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. pasang library
pip install -r requirements.txt

# 3. jalankan dashboard dari folder submission
streamlit run dashboard/dashboard.py
```
Dashboard akan terbuka di browser pada `http://localhost:8501`. Filter tersedia di sidebar (rentang tanggal, stasiun, ambang PM2.5 harian).

## Menjalankan Ulang Notebook
Tambahkan `jupyter` (`pip install jupyter`), lalu jalankan `jupyter notebook notebook.ipynb` **dari folder submission** (path data dibaca relatif: `data/`). Menjalankan seluruh sel akan membuat ulang `dashboard/main_data.csv`.

## Deploy ke Streamlit Community Cloud
1. Unggah folder proyek ke repositori GitHub (pastikan `requirements.txt` berada di root repositori).
2. Buka https://share.streamlit.io, pilih repositori, dan isi *Main file path* dengan `dashboard/dashboard.py`.
3. Setelah berhasil, tulis tautan aplikasi ke `url.txt`.

## Catatan Metodologi
- **Cleaning:** nilai PM2.5 identik ≥ 24 jam (sensor macet, 41 jam di Dongsi) dijadikan missing; gap missing ≤ 6 jam diisi interpolasi linear (arah angin: forward-fill), gap lebih panjang dibiarkan kosong. Outlier tidak dihapus karena merupakan episode polusi nyata.
- **Hari valid:** rata-rata harian hanya dihitung jika ≥ 20 dari 24 jam tersedia.
- **Periode 12 bulan** dimulai Maret agar tiap periode memuat empat musim lengkap.
- **Zona** (Pinggiran: Changping, Dingling, Huairou, Shunyi; sisanya Perkotaan) adalah pengelompokan manual berdasarkan lokasi administratif, bukan kolom bawaan dataset.
- **Kategori kualitas udara** (binning `pd.cut`) mengacu pada titik batas PM2.5 24 jam HJ 633-2012 (hanya PM2.5, bukan AQI gabungan). Baku mutu 75 µg/m³ = Kelas II GB 3095-2012.
- Analisis bersifat observasional: musim, angin, dan lokasi belum dipisahkan, sehingga hasil menunjukkan pola, bukan sebab-akibat.
