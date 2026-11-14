# Proyek Analisis Data: Kualitas Udara Beijing (PRSA, 12 Stasiun)

Analisis PM2.5 dari **PRSA Beijing Multi-Site Air Quality Dataset** (data per jam, 12 stasiun, 1 Maret 2013 – 28 Februari 2017) beserta dashboard interaktif Streamlit.

## Pertanyaan Bisnis
1. Berapa rata-rata PM2.5 per periode 12 bulan (Maret–Februari) dan per musim, serta pada musim apa tertinggi dan terendah?
2. Stasiun mana yang paling sering melewati baku mutu PM2.5 harian 75 µg/m³, dan berapa selisih antara stasiun perkotaan dan pinggiran?
3. Pada kombinasi arah dan kecepatan angin apa PM2.5 paling tinggi, dan berapa penurunannya saat angin > 3 m/s dibanding ≤ 1 m/s?

## Catatan Metodologi
- **Cleaning:** nilai PM2.5 identik ≥ 24 jam (sensor macet, 41 jam di Dongsi) dijadikan missing; gap missing ≤ 6 jam diisi interpolasi linear (arah angin: forward-fill), gap lebih panjang dibiarkan kosong. Outlier tidak dihapus karena merupakan episode polusi nyata.
- **Hari valid:** rata-rata harian hanya dihitung jika ≥ 20 dari 24 jam tersedia.
- **Periode 12 bulan** dimulai Maret agar tiap periode memuat empat musim lengkap.
- **Zona** (Pinggiran: Changping, Dingling, Huairou, Shunyi; sisanya Perkotaan) adalah pengelompokan manual berdasarkan lokasi administratif, bukan kolom bawaan dataset.
- **Kategori kualitas udara** (binning `pd.cut`) mengacu pada titik batas PM2.5 24 jam HJ 633-2012 (hanya PM2.5, bukan AQI gabungan). Baku mutu 75 µg/m³ = Kelas II GB 3095-2012.
- Analisis bersifat observasional: musim, angin, dan lokasi belum dipisahkan, sehingga hasil menunjukkan pola, bukan sebab-akibat.
