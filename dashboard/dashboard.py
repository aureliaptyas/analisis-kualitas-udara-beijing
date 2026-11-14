"""Dashboard Kualitas Udara Beijing (PRSA, 12 stasiun, Mar 2013 - Feb 2017).

Menjawab tiga pertanyaan bisnis dari notebook.ipynb:
  1. PM2.5 per periode 12 bulan (Mar-Feb) dan per musim
  2. Persentase hari melewati baku mutu PM2.5 harian per stasiun & zona
  3. Pengaruh arah dan kecepatan angin terhadap PM2.5

Jalankan:  streamlit run dashboard/dashboard.py
"""
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

# ----------------------------------------------------------------------------
# Konfigurasi & konstanta (sama dengan notebook.ipynb)
# ----------------------------------------------------------------------------
st.set_page_config(page_title='Dashboard Kualitas Udara Beijing', page_icon='🌫️', layout='wide')

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main_data.csv')

C_BLUE, C_ORANGE = '#2a78d6', '#eb6834'
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
SEQ = LinearSegmentedColormap.from_list(
    'seq_blue', ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
AQI_RAMP = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#104281', '#0d366b']

SEASON_MAP = {12: 'Dingin', 1: 'Dingin', 2: 'Dingin', 3: 'Semi', 4: 'Semi', 5: 'Semi',
              6: 'Panas', 7: 'Panas', 8: 'Panas', 9: 'Gugur', 10: 'Gugur', 11: 'Gugur'}
SEASON_ORDER = ['Semi', 'Panas', 'Gugur', 'Dingin']
WD_ORDER = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
SPEED_LABELS = ['≤ 1 m/s', '1-2 m/s', '2-3 m/s', '> 3 m/s']
AQI_BINS = [-np.inf, 35, 75, 115, 150, 250, np.inf]
AQI_LABELS = ['Sangat baik (≤ 35)', 'Baik (35-75)', 'Tercemar ringan (75-115)',
              'Tercemar sedang (115-150)', 'Tercemar berat (150-250)', 'Sangat berat (> 250)']
MIN_JAM = 20     # hari valid = minimal 20 dari 24 jam tersedia
MIN_N = 30       # sel heatmap angin dengan pengamatan lebih sedikit disembunyikan
SUMBER = 'Sumber: PRSA Beijing Multi-Site Air Quality, Mar 2013 - Feb 2017'

plt.rcParams.update({
    'figure.dpi': 100, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'font.size': 10, 'text.color': INK,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': '#b9b8b2', 'axes.labelcolor': INK2,
    'axes.titlesize': 12, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
    'axes.grid': True, 'axes.axisbelow': True, 'grid.color': GRID, 'grid.linewidth': 0.8,
    'xtick.color': INK2, 'ytick.color': INK2, 'legend.frameon': False,
})


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=['datetime'])
    month, year = df['datetime'].dt.month, df['datetime'].dt.year
    df['date'] = df['datetime'].dt.normalize()
    start_year = pd.Series(np.where(month >= 3, year, year - 1), index=df.index)
    df['periode'] = start_year.map(lambda y: f'Mar {y} - Feb {y + 1}')
    df['musim'] = month.map(SEASON_MAP)
    df['kec_angin'] = pd.cut(df['WSPM'], bins=[-np.inf, 1, 2, 3, np.inf], labels=SPEED_LABELS)

    daily = (df.groupby(['station', 'zona', 'date'])['PM2.5']
               .agg(pm25_harian='mean', jam_valid='count').reset_index())
    daily = daily[daily['jam_valid'] >= MIN_JAM].copy()
    daily['kategori'] = pd.cut(daily['pm25_harian'], bins=AQI_BINS, labels=AQI_LABELS)
    return df, daily


def add_source(fig, text=SUMBER):
    fig.text(0.01, -0.02, text, fontsize=8, color=INK2)


# ----------------------------------------------------------------------------
# Grafik
# ----------------------------------------------------------------------------
def fig_monthly(bulanan):
    fig, ax = plt.subplots(figsize=(11, 4))
    x = bulanan.index.to_timestamp()
    ax.plot(x, bulanan.values, color=C_BLUE, lw=2, marker='o', ms=4)
    ax.axhline(35, color=C_ORANGE, ls='--', lw=1.5)
    ax.text(x[0], 37, 'Baku mutu tahunan Kelas II: 35 µg/m³', color=INK2, fontsize=9, va='bottom')
    i = int(np.argmax(bulanan.values))
    ax.annotate(f"Tertinggi: {bulanan.values[i]:.0f} µg/m³\n{bulanan.index[i].strftime('%b %Y')}",
                xy=(x[i], bulanan.values[i]), xytext=(0, 12), textcoords='offset points',
                ha='center', fontsize=9, color=INK)
    ax.set_ylim(0, max(bulanan.max() * 1.25, 45))
    ax.set_ylabel('Rata-rata PM2.5 bulanan (µg/m³)')
    ax.set_title('Rata-rata PM2.5 bulanan')
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=10))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(axis='x', visible=False)
    add_source(fig, SUMBER + '. Rata-rata stasiun terpilih.')
    fig.tight_layout()
    return fig


def fig_season_heatmap(tbl):
    fig, ax = plt.subplots(figsize=(6.5, 1.2 + 0.7 * len(tbl)))
    sns.heatmap(tbl, annot=True, fmt='.0f', cmap=SEQ, vmin=0, mask=tbl.isna(), linewidths=2,
                linecolor='white', cbar_kws={'label': 'PM2.5 (µg/m³)'}, annot_kws={'fontsize': 10}, ax=ax)
    ax.set_title('Rata-rata PM2.5 per periode dan musim')
    ax.set_xlabel('Musim')
    ax.set_ylabel('')
    ax.tick_params(axis='y', rotation=0)
    ax.grid(False)
    add_source(fig)
    fig.tight_layout()
    return fig


def fig_station_bar(tbl, thresh):
    plot_df = tbl.sort_values('persen')
    colors = plot_df['zona'].map({'Perkotaan': C_BLUE, 'Pinggiran': C_ORANGE})
    fig, ax = plt.subplots(figsize=(6.5, 0.9 + 0.38 * len(plot_df)))
    bars = ax.barh(plot_df['station'], plot_df['persen'], color=colors, height=0.68)
    for b, v in zip(bars, plot_df['persen']):
        ax.text(v + 0.5, b.get_y() + b.get_height() / 2, f'{v:.1f}%', va='center', fontsize=9, color=INK)
    ax.set_xlim(0, max(plot_df['persen'].max() * 1.15, 5))
    ax.set_xlabel(f'Hari dengan PM2.5 harian > {thresh} µg/m³ (% dari hari valid)')
    ax.set_title('Persentase hari melewati ambang per stasiun')
    ax.grid(axis='y', visible=False)
    ax.legend(handles=[Patch(color=C_BLUE, label='Perkotaan'), Patch(color=C_ORANGE, label='Pinggiran')],
              loc='lower right', title='Zona')
    add_source(fig, SUMBER + f'. Hari valid = minimal {MIN_JAM} jam data.')
    fig.tight_layout()
    return fig


def fig_aqi(kat_pct):
    fig, ax = plt.subplots(figsize=(6.5, 2.2 + 0.5 * len(kat_pct)))
    left = pd.Series(0.0, index=kat_pct.index)
    for lab, col in zip(AQI_LABELS, AQI_RAMP):
        ax.barh(kat_pct.index, kat_pct[lab], left=left, color=col, edgecolor='white', linewidth=2,
                height=0.6, label=lab)
        for zona, v, l in zip(kat_pct.index, kat_pct[lab], left):
            if v >= 3:
                ax.text(l + v / 2, zona, f'{v:.0f}%', ha='center', va='center', fontsize=9,
                        color=INK if col in AQI_RAMP[:2] else 'white')
        left = left + kat_pct[lab]
    ax.set_xlim(0, 100)
    ax.set_xlabel('Persentase hari valid (%)')
    ax.set_title('Sebaran kategori kualitas udara (PM2.5 harian)')
    ax.grid(axis='y', visible=False)
    ax.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, -0.32), fontsize=8)
    add_source(fig, SUMBER + '. Kategori: HJ 633-2012.')
    fig.tight_layout()
    return fig


def fig_wind_heatmap(matrix, counts):
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    sns.heatmap(matrix, mask=(counts < MIN_N) | counts.isna(), annot=True, fmt='.0f', cmap=SEQ, vmin=0,
                linewidths=2, linecolor='white', cbar_kws={'label': 'PM2.5 (µg/m³)'},
                annot_kws={'fontsize': 9}, ax=ax)
    ax.set_title('Rata-rata PM2.5 menurut arah dan kecepatan angin')
    ax.set_xlabel('Kecepatan angin')
    ax.set_ylabel('Arah asal angin')
    ax.tick_params(axis='y', rotation=0)
    ax.grid(False)
    add_source(fig, SUMBER + f'. Sel kosong: < {MIN_N} pengamatan.')
    fig.tight_layout()
    return fig


def fig_wind_bar(wind_speed):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    bars = ax.bar(wind_speed.index.astype(str), wind_speed['rata_rata'], color=C_BLUE, width=0.6)
    for b, v in zip(bars, wind_speed['rata_rata']):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, f'{v:.0f}', ha='center', fontsize=10, color=INK)
    ax.set_ylim(0, wind_speed['rata_rata'].max() * 1.18)
    ax.set_xlabel('Kecepatan angin')
    ax.set_ylabel('Rata-rata PM2.5 (µg/m³)')
    ax.set_title('Rata-rata PM2.5 menurut kecepatan angin')
    ax.grid(axis='x', visible=False)
    add_source(fig)
    fig.tight_layout()
    return fig


def show(fig):
    st.pyplot(fig)
    plt.close(fig)


# ----------------------------------------------------------------------------
# Halaman
# ----------------------------------------------------------------------------
df, daily_all = load_data()

st.title('🌫️ Dashboard Kualitas Udara Beijing')
st.caption('PM2.5 dari 12 stasiun pemantau (PRSA Beijing Multi-Site Air Quality), data per jam '
           '1 Maret 2013 - 28 Februari 2017. Gunakan filter di sidebar untuk menelusuri data.')

# ---- Sidebar (filter)
st.sidebar.header('Filter')
min_date, max_date = df['date'].min().date(), df['date'].max().date()
rentang = st.sidebar.date_input('Rentang tanggal', value=(min_date, max_date),
                                min_value=min_date, max_value=max_date)
all_stations = sorted(df['station'].unique())
stations = st.sidebar.multiselect('Stasiun', all_stations, default=all_stations)
thresh = st.sidebar.selectbox('Ambang PM2.5 harian (µg/m³)', [75, 35], index=0,
                              format_func=lambda v: f'{v} (Kelas II)' if v == 75 else f'{v} (Kelas I)')
st.sidebar.caption('75 µg/m³ = baku mutu 24 jam Kelas II (GB 3095-2012). '
                   'Zona: Pinggiran = Changping, Dingling, Huairou, Shunyi; sisanya Perkotaan '
                   '(pengelompokan manual berdasarkan lokasi administratif).')

if not isinstance(rentang, (tuple, list)) or len(rentang) != 2:
    st.info('Pilih tanggal awal dan tanggal akhir pada filter "Rentang tanggal".')
    st.stop()
if not stations:
    st.warning('Pilih minimal satu stasiun.')
    st.stop()

start, end = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1])
sub = df[(df['date'] >= start) & (df['date'] <= end) & df['station'].isin(stations)]
sub_daily = daily_all[(daily_all['date'] >= start) & (daily_all['date'] <= end)
                      & daily_all['station'].isin(stations)].copy()
if sub.empty or sub_daily.empty:
    st.warning('Tidak ada data pada filter yang dipilih.')
    st.stop()

sub_daily['lewat'] = sub_daily['pm25_harian'] > thresh
stasiun_tbl = (sub_daily.groupby(['station', 'zona'])['lewat']
               .agg(hari_lewat='sum', hari_valid='count', persen='mean').reset_index())
stasiun_tbl['persen'] *= 100

wind_speed = sub.groupby('kec_angin', observed=True)['PM2.5'].agg(rata_rata='mean', jam_valid='count')

# ---- KPI
k1, k2, k3, k4 = st.columns(4)
k1.metric('Rata-rata PM2.5', f"{sub['PM2.5'].mean():.1f} µg/m³")
k2.metric(f'Hari > {thresh} µg/m³', f"{sub_daily['lewat'].mean() * 100:.1f}%")
worst = stasiun_tbl.sort_values('persen', ascending=False).iloc[0]
k3.metric('Stasiun paling sering melewati ambang', worst['station'], f"{worst['persen']:.1f}% hari",
          delta_color='off')
if {'≤ 1 m/s', '> 3 m/s'} <= set(wind_speed.index):
    turun = (1 - wind_speed.loc['> 3 m/s', 'rata_rata'] / wind_speed.loc['≤ 1 m/s', 'rata_rata']) * 100
    k4.metric('PM2.5 turun saat angin > 3 m/s', f'{turun:.0f}%', 'dibanding angin ≤ 1 m/s', delta_color='off')
else:
    k4.metric('PM2.5 turun saat angin > 3 m/s', 'n/a')

if (end - start).days < 90:
    st.caption('Rentang tanggal kurang dari 90 hari: jumlah data sedikit sehingga angka bisa sangat berfluktuasi.')

tab1, tab2, tab3, tab4 = st.tabs(['1. Tren & musim', '2. Stasiun & zona', '3. Arah & kecepatan angin',
                                  'Kesimpulan & rekomendasi'])

# ---- Tab 1
with tab1:
    st.subheader('Berapa rata-rata PM2.5 per periode 12 bulan dan per musim, dan kapan tertinggi?')
    bulanan = sub.groupby(sub['datetime'].dt.to_period('M'))['PM2.5'].mean()
    show(fig_monthly(bulanan))

    musim_tbl = (sub.pivot_table(index='periode', columns='musim', values='PM2.5', aggfunc='mean')
                 .reindex(columns=SEASON_ORDER))
    periode_mean = sub.groupby('periode')['PM2.5'].mean()
    musim_mean = sub.groupby('musim')['PM2.5'].mean().reindex(SEASON_ORDER).dropna()

    c1, c2 = st.columns([3, 2])
    with c1:
        show(fig_season_heatmap(musim_tbl))
    with c2:
        st.markdown('**Ringkasan pada filter saat ini**')
        if len(musim_mean) > 1:
            st.write(f"- Musim tertinggi: **{musim_mean.idxmax()}** ({musim_mean.max():.1f} µg/m³); "
                     f"terendah: **{musim_mean.idxmin()}** ({musim_mean.min():.1f} µg/m³).")
        else:
            st.write(f"- Hanya musim **{musim_mean.index[0]}** yang tercakup ({musim_mean.iloc[0]:.1f} µg/m³).")
        if len(bulanan) > 1:
            st.write(f"- Bulan tertinggi: **{bulanan.idxmax().strftime('%b %Y')}** ({bulanan.max():.1f} µg/m³).")
            st.write(f"- Bulan terendah: **{bulanan.idxmin().strftime('%b %Y')}** ({bulanan.min():.1f} µg/m³).")
        else:
            st.write(f"- Hanya bulan **{bulanan.index[0].strftime('%b %Y')}** yang tercakup.")
        st.markdown('**Rata-rata per periode (µg/m³)**')
        st.dataframe(periode_mean.round(1).rename('PM2.5'))
        st.caption('Periode Mar-Feb mencakup empat musim lengkap. Jika rentang tanggal dipersempit, '
                   'periode/musim yang tidak tercakup penuh bersifat parsial.')

# ---- Tab 2
with tab2:
    st.subheader(f'Stasiun mana yang paling sering melewati {thresh} µg/m³, dan apa bedanya perkotaan vs pinggiran?')
    kat_pct = (pd.crosstab(sub_daily['zona'], sub_daily['kategori'], normalize='index') * 100)
    kat_pct = kat_pct.reindex(columns=AQI_LABELS, fill_value=0)

    c1, c2 = st.columns(2)
    with c1:
        show(fig_station_bar(stasiun_tbl, thresh))
    with c2:
        show(fig_aqi(kat_pct))

    zona_tbl = sub_daily.groupby('zona')['lewat'].mean() * 100
    best = stasiun_tbl.sort_values('persen').iloc[0]
    st.markdown('**Ringkasan pada filter saat ini**')
    st.write(f"- Tertinggi: **{worst['station']}** ({worst['persen']:.1f}%); "
             f"terendah: **{best['station']}** ({best['persen']:.1f}%).")
    if {'Perkotaan', 'Pinggiran'} <= set(zona_tbl.index):
        st.write(f"- Perkotaan **{zona_tbl['Perkotaan']:.1f}%** vs Pinggiran **{zona_tbl['Pinggiran']:.1f}%** "
                 f"(selisih {zona_tbl['Perkotaan'] - zona_tbl['Pinggiran']:.1f} poin persentase).")
    else:
        st.write('- Pilih stasiun dari kedua zona untuk membandingkan perkotaan dan pinggiran.')
    with st.expander('Lihat tabel data per stasiun'):
        st.dataframe(stasiun_tbl.sort_values('persen', ascending=False).round(1)
                     .rename(columns={'station': 'Stasiun', 'zona': 'Zona', 'hari_lewat': 'Hari melewati ambang',
                                      'hari_valid': 'Hari valid', 'persen': '% hari melewati ambang'}))

# ---- Tab 3
with tab3:
    st.subheader('Pada arah dan kecepatan angin seperti apa PM2.5 paling tinggi?')
    wind_matrix = sub.pivot_table(index='wd', columns='kec_angin', values='PM2.5',
                                  aggfunc='mean', observed=False).reindex(index=WD_ORDER, columns=SPEED_LABELS)
    wind_counts = sub.pivot_table(index='wd', columns='kec_angin', values='PM2.5',
                                  aggfunc='count', observed=False).reindex(index=WD_ORDER, columns=SPEED_LABELS)
    c1, c2 = st.columns(2)
    with c1:
        show(fig_wind_heatmap(wind_matrix, wind_counts))
    with c2:
        show(fig_wind_bar(wind_speed))
        valid = wind_matrix.where(wind_counts >= MIN_N).stack()
        if not valid.empty:
            top = valid.sort_values(ascending=False).head(3)
            st.markdown('**Kombinasi tertinggi pada filter saat ini**')
            for (wd, spd), v in top.items():
                st.write(f'- Angin dari **{wd}**, kecepatan **{spd}**: {v:.0f} µg/m³')
        st.caption('Musim dan angin belum dipisahkan, sehingga hasil menunjukkan pola, bukan efek independen.')

# ---- Tab 4
with tab4:
    st.subheader('Kesimpulan (seluruh periode, 12 stasiun, sesuai notebook)')
    st.markdown("""
- **Pertanyaan 1:** rata-rata PM2.5 per periode 12 bulan adalah 86,8; 81,4; 72,9; dan 78,0 µg/m³, selalu
  2,1-2,5 kali baku mutu tahunan 35 µg/m³. Musim dingin tertinggi (95,5 µg/m³) dan musim panas terendah (64,6 µg/m³).
  Secara bulanan, Oktober-Maret berkisar 88-104 µg/m³ dengan puncak Desember 2015 (149,8 µg/m³).
- **Pertanyaan 2:** persentase hari melewati 75 µg/m³ berkisar 31,6% (Dingling) hingga 43,4% (Dongsi).
  Perkotaan 42,5% vs pinggiran 35,7% (selisih 6,8 poin persentase); delapan stasiun perkotaan nyaris seragam,
  Shunyi (pinggiran) hampir setara kota. Pola ini mengarah pada pencemaran regional.
- **Pertanyaan 3:** PM2.5 tertinggi saat angin lemah (≤ 1 m/s) dari timur (E 114,7; ENE 113,3; ESE 112,4 µg/m³).
  PM2.5 turun 65,4% saat angin > 3 m/s, tetapi angin kuat dari ESE/SE/SSE tetap membawa 76-86 µg/m³,
  sedangkan dari utara-barat laut hanya 19-22 µg/m³.
""")
    st.subheader('Rekomendasi action item')
    st.markdown("""
1. **Peringatan dini berbasis cuaca:** keluarkan imbauan saat prakiraan angin ≤ 1 m/s atau angin ≤ 2 m/s dari
   sektor timur-tenggara (rata-rata PM2.5 96-115 µg/m³).
2. **Perkuat pengendalian pada Oktober-Maret** (rata-rata bulanan 88-104 µg/m³, vs 53-73 µg/m³ pada April-September).
3. **Kebijakan kota-luas dan koordinasi regional**, bukan per-stasiun; prioritaskan zona perkotaan
   (13,5% hari > 150 µg/m³).
4. **Perbaiki kualitas pemantauan:** kekosongan data yang panjang dan sensor macet perlu alarm otomatis.
5. **Analisis lanjutan:** pisahkan efek musim dan angin serta tambahkan data sumber emisi sebelum menetapkan
   kebijakan sumber tertentu.
""")
    st.caption('Angka pada tab ini adalah hasil analisis seluruh periode di notebook dan tidak berubah mengikuti filter.')
