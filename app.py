import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import streamlit.components.v1 as components
import os
from pykrige.ok import OrdinaryKriging

# --- 1. CONFIGURATION UTAMA PLATFORM ---
st.set_page_config(
    page_title="Sistem Informasi Geospasial Kentang",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. MANAGEMENT STATE HALAMAN ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Beranda Utama"

# --- 3. UNIFIED PREMIUM DARK THEME STYLE (GLOBAL) ---
bg_img_url = "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?q=80&w=2000&auto=format&fit=crop"

st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,300,0,0" rel="stylesheet" />
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(10, 15, 11, 0.92), rgba(10, 15, 11, 0.92)), url("{bg_img_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-color: #0a0f0b !important;
    }}
    h1, h2, h3, h4, h5, h6, p, span, label, th, td, .stMarkdown {{
        color: #e4eed7 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    .feature-card {{
        background-color: rgba(19, 27, 21, 0.45);
        padding: 35px;
        border-radius: 8px;
        border: 1px solid rgba(163, 191, 162, 0.2);
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        margin-bottom: 15px;
        text-align: center;
        backdrop-filter: blur(4px);
        height: 250px;
    }}
    .premium-icon {{
        font-size: 34px;
        color: #a3bfa2;
        margin-bottom: 15px;
        display: block;
    }}
    .stSelectbox div[data-baseweb="select"] {{
        background-color: #121914 !important;
        color: #e4eed7 !important;
        border: 1px solid #243528 !important;
        border-radius: 4px !important;
    }}
    .block-container {{
        padding-top: 2.5rem !important;
        padding-bottom: 4rem !important;
        max-width: 90% !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. CSS CONDITIONAL: SEMBUNYIKAN SIDEBAR PADA MENU UTAMA BERANDA & SUB-HALAMAN ---
if st.session_state.current_page in ["Beranda Utama", "Peta Sebaran Titik Data", "Peta Gradasi Kesesuaian Lahan"]:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapseButton"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #060907 !important;
            border-right: 1px solid #1a251d;
        }
        [data-testid="stSidebar"] * { color: #cddbc0 !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 5. DATA LOADING LOGIC ENGINE ---
# Kamus Sentroid Geografis Pendukung Plotting Peta Gradasi di Lapangan Satelit
KOORDINAT_SENTRA = {
    'Karangtengah': [-7.21450, 109.81230], 'Bakal': [-7.22310, 109.82450], 'Sikunang': [-7.23410, 109.84120],
    'Kepakisan': [-7.20120, 109.79150], 'Dieng Kulon': [-7.21140, 109.80210], 'Sumberejo': [-7.22800, 109.83100],
    'Surengede': [-7.25100, 109.87200], 'Tieng': [-7.26300, 109.89100], 'Kledung': [-7.31200, 110.02100],
    'Wonokitri': [-7.82100, 112.91200], 'Podokoyo': [-7.83400, 112.89400], 'Ngadisari': [-7.91200, 112.95100],
    'Sapikerep': [-7.89500, 112.99200], 'Pandansari': [-7.92100, 112.88400], 'Wringinanom': [-7.90400, 112.72100],
    'Ngantru': [-7.93100, 112.69400], 'Pudjon Kidul': [-7.88100, 112.45100], 'Margamukti': [-7.18200, 107.61200],
    'Sukamanah': [-7.19400, 107.63100], 'Cikole': [-6.79100, 107.64100], 'Simpang': [-7.32100, 107.75100],
    'Margamulya': [-7.21100, 107.60400], 'Cibeet': [-7.28400, 107.69100], 'Karya Mekar': [-7.25100, 107.72100],
    'Linggarjati': [-7.19100, 108.12100]
}

DATA_ELEVASI_ASLI = {'Kepakisan': 1851, 'Bakal': 1693, 'Sikunang': 2110, 'Dieng Kulon': 2068, 'Karangtengah': 1541}

@st.cache_data
def load_kriging_base_data():
    path = 'Data_Kriging.xlsx'
    if not os.path.exists(path): return None
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    for c in df.columns:
        if 'titik' in c.lower() or 'desa' in c.lower(): df = df.rename(columns={c: 'Desa'})
    df[['Desa', 'Lat', 'Lon']] = df[['Desa', 'Lat', 'Lon']].ffill()
    if 'Elevasi' not in df.columns: df['Elevasi'] = df['Desa'].map(DATA_ELEVASI_ASLI).fillna(1800)
    for col in ['Lat', 'Lon', 'N', 'P', 'K', 'PH', 'Elevasi']: df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.groupby(['Desa', 'Lat', 'Lon']).mean(numeric_only=True).reset_index().dropna()

@st.cache_data
def load_suitability_all_data():
    nama_fail = 'Data_Kesesuaian.xlsx - sheet 1.csv'
    if not os.path.exists(nama_fail):
        nama_fail = 'Data_Kesesuaian.xlsx'
        if not os.path.exists(nama_fail): return None
            
    df = pd.read_csv(nama_fail) if nama_fail.endswith('.csv') else pd.read_excel(nama_fail)
    df.columns = [str(c).strip() for c in df.columns]
    
    for c in df.columns:
        if 'desa' in c.lower() or 'titik' in c.lower(): df = df.rename(columns={c: 'Desa'})
        if 'cocok' in c.lower() or 'kesesuaian' in c.lower(): df = df.rename(columns={c: 'Kecocokan'})
            
    df['Desa'] = df['Desa'].ffill()
    df['Lat'] = df['Desa'].map(lambda x: KOORDINAT_SENTRA.get(str(x).strip(), [-7.5, 110.0])[0])
    df['Lon'] = df['Desa'].map(lambda x: KOORDINAT_SENTRA.get(str(x).strip(), [-7.5, 110.0])[1])
    
    for col in ['EC_S1', 'N_S1', 'P_S1', 'K_S1', 'PH_S1', 'Moist_S1', 'Temp_D_S1', 'Elevasi', 'Produktivitas']:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
    # BINER/ORDINAL FILTER TEGAS: Mengonversi langsung string "Cocok", "Netral", "Tidak Sesuai" menjadi 2, 1, 0
    def konversi_biner_skor(label):
        lbl = str(label).lower().strip()
        if "tidak" in lbl or "kurang" in lbl: 
            return 0.0
        elif "netral" in lbl: 
            return 1.0
        return 2.0
        
    df['Skor_Kesesuaian'] = df['Kecocokan'].apply(konversi_biner_skor)
    return df.dropna(subset=['Desa', 'Kecocokan'])

df_kriging = load_kriging_base_data()
df_suit_all = load_suitability_all_data()

# --- 6. INTERACTIVE ROUTING CONTROLLER ---

if st.session_state.current_page == "Beranda Utama":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2.8em; letter-spacing: 2px; color: #f2f8ea; font-weight: 300;'>SISTEM INFORMASI GEOSPASIAL<br>SENTRA PRODUKSI KENTANG PULAU JAWA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #8da68c; font-weight: 400; letter-spacing: 0.5px; margin-bottom: 50px;'>Integrasi Pemetaan Spasial Makro dan Komputasi Estimasi Ragam Hara Lapangan</h4>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); width: 85%; margin: 0 auto;'><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        # MENU PERTAMA: PETA SEBARAN DARI LINK ARCGIS ONLINE ASLI
        st.markdown("""<div class='feature-card'><span class="material-symbols-outlined premium-icon">public</span><h3 style='color: #d2e7b9; margin-top:0; font-weight: 400; font-size:1.3em;'>Peta Sebaran Titik Data</h3><p style='font-size: 0.93em; color: #9ab098; text-align: justify; line-height:1.6;'>Visualisasi spasial regional sebaran titik data yang diambil di lapangan pada 12 sentra produksi kentang Pulau Jawat melalui visualisasi platform ArcGIS Online.</p></div>""", unsafe_allow_html=True)
        if st.button("Buka Peta Sebaran Titik  ›", key="go_to_gis", use_container_width=True):
            st.session_state.current_page = "Peta Sebaran Titik Data"; st.rerun()
    with col2:
        # MENU KEDUA: DASHBOARD INTERPOLASI KRIGING MIKRO DIENG
        st.markdown("""<div class='feature-card'><span class="material-symbols-outlined premium-icon">architecture</span><h3 style='color: #d2e7b9; margin-top:0; font-weight: 400; font-size:1.3em;'>Interpolasi Geostatistik</h3><p style='font-size: 0.93em; color: #9ab098; text-align: justify; line-height:1.6;'>Mesin komputasi menggunakan pemodelan matematika <i>Ordinary Kriging</i> univariat guna mengestimasi hara (N, P, K, pH) tak tersampel via LOOCV pada 5 desa inti Dieng.</p></div>""", unsafe_allow_html=True)
        if st.button("Jalankan Modul Kriging  ›", key="go_to_kriging", use_container_width=True):
            st.session_state.current_page = "Analisis Kriging (Mikro)"; st.rerun()
    with col3:
        # MENU KETIGA: PETA GRADASI KESESUAIAN SE-PULAU JAWA (DATA_KESESUAIAN)
        st.markdown("""<div class='feature-card'><span class="material-symbols-outlined premium-icon">layers</span><h3 style='color: #d2e7b9; margin-top:0; font-weight: 400; font-size:1.3em;'>Kesesuaian Lahan Bergradasi</h3><p style='font-size: 0.93em; color: #9ab098; text-align: justify; line-height:1.6;'>Pemetaan mikro spasial hasil interpolasi nilai biner tegas berskor kontinu dari berkas Data_Kesesuaian. Menghasilkan visualisasi heatmap bergradasi halus halus.</p></div>""", unsafe_allow_html=True)
        if st.button("Lihat Gradasi Kesesuaian Lahan ›", key="go_to_suitability", use_container_width=True):
            st.session_state.current_page = "Peta Gradasi Kesesuaian Lahan"; st.rerun()
            
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.03); width: 100%;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #5b6b5c; font-size: 0.85em; letter-spacing: 1px; text-transform: uppercase;'>Tugas Akhir S1 Teknik Fisika &nbsp;|&nbsp; Universitas Telkom</p>", unsafe_allow_html=True)

elif st.session_state.current_page == "Peta Sebaran Titik Data":
    # --- FIXED MODUL MENU 1: IFRAME LINK GIS REGIONAL ASLI ---
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown("<h1 style='font-weight: 300;'>Peta Sebaran Koordinat Titik Data Regional (Makro)</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("‹  Kembali ke Beranda", use_container_width=True): st.session_state.current_page = "Beranda Utama"; st.rerun()
    components.html(f'<iframe src="https://arcg.is/1LDCjO4" width="100%" height="650" style="border: 1px solid rgba(163, 191, 162, 0.2); border-radius: 6px; box-shadow: 0px 8px 30px rgba(0,0,0,0.85);"></iframe>', height=680)

elif st.session_state.current_page == "Peta Gradasi Kesesuaian Lahan":
    # --- FIXED MODUL MENU 3: HEATMAP GRADASI HALUS BINER DARI FILE DATA_KESESUAIAN ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 style='font-weight: 300;'>Peta Gradasi Kontinu Kesesuaian Lahan Mikro (12 Sentra)</h1>", unsafe_allow_html=True)
        st.write("Visualisasi Nilai Klasifikasi Biner Lahan Kontinu: Merah (Tidak Sesuai), Kuning (Netral), dan Hijau (Cocok).")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("‹  Kembali ke Beranda", key="back_from_suit", use_container_width=True): st.session_state.current_page = "Beranda Utama"; st.rerun()
        
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    
    if df_suit_all is None or df_suit_all.empty:
        st.error("Gagal mendeteksi berkas data kesesuaian di repositori.")
    else:
        # Kelompokkan data rata-rata koordinat spasial dan skor biner tegas (0,1,2) per desa
        df_suit_group = df_suit_all.groupby(['Desa', 'Lat', 'Lon']).mean(numeric_only=True).reset_index()
        
        # Penentuan batas grid spasial Pulau Jawa
        lat_min, lat_max = df_suit_group['Lat'].min() - 0.3, df_suit_group['Lat'].max() + 0.3
        lon_min, lon_max = df_suit_group['Lon'].min() - 0.3, df_suit_group['Lon'].max() + 0.3
        
        grid_lat = np.linspace(lat_min, lat_max, 80)
        grid_lon = np.linspace(lon_min, lon_max, 80)
        
        # Eksekusi komputasi Ordinary Kriging pemetaan gradasi kontinu biner
        OK_suit = OrdinaryKriging(
            df_suit_group['Lon'].values, df_suit_group['Lat'].values, df_suit_group['Skor_Kesesuaian'].values,
            variogram_model='linear', verbose=False, enable_plotting=False
        )
        z_grid, ss_grid = OK_suit.execute('grid', grid_lon, grid_lat)
        
        peta_heat = folium.Map(location=[df_suit_group['Lat'].mean(), df_suit_group['Lon'].mean()], zoom_start=7, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri Satellite')
        
        data_heatmap = []
        for i in range(len(grid_lat)):
            for j in range(len(grid_lon)):
                skor_val = max(0.0, min(z_grid[i, j], 2.0))
                data_heatmap.append([grid_lat[i], grid_lon[j], skor_val])
                
        # Integrasi plugins HeatMap kontinu linear permukaan biner (0,1,2)
        HeatMap(
            data=data_heatmap, radius=42, blur=28, min_opacity=0.38, max_val=2.0,
            gradient={0.0: '#ff3333', 0.5: '#ff9933', 1.0: '#ffff33', 1.5: '#88ff33', 2.0: '#1f991f'}
        ).add_to(peta_heat)
        
        # Tampilkan marker referensi transparan di atas heatmap
        for _, row in df_suit_group.iterrows():
            folium.CircleMarker(location=[row['Lat'], row['Lon']], radius=5, color='#ffffff', weight=1.0, fill_color='#222', fill_opacity=0.5, popup=f"<b>Sentra: {row['Desa']}</b><br>Skor Kontinu: {row['Skor_Kesesuaian']:.2f}").add_to(peta_heat)
            
        components.html(peta_heat._repr_html_(), height=620)

elif st.session_state.current_page == "Analisis Kriging (Mikro)":
    # --- MODUL MENU 2: DASHBOARD INTERPOLASI HARA MIKRO DIENG ---
    st.markdown("<h1 style='font-weight: 300;'>Komputasi Ordinary Kriging (LOOCV)</h1>", unsafe_allow_html=True)
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/thumb/0/03/Logo_Telkom_University_potrait.png/250px-Logo_Telkom_University_potrait.png", width=80)
    if st.sidebar.button("‹ Kembali ke Beranda", key="back_from_side", type="secondary", use_container_width=True):
        st.session_state.current_page = "Beranda Utama"; st.rerun()
        
    st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    st.sidebar.markdown("### Parameter Komputasi")
    parameter_terpilih = st.sidebar.selectbox("Variabel Nutrisi:", ["N", "P", "K", "PH"])
    opsi_desa = [f"{row['Desa']} ({row['Lat']:.5f}, {row['Lon']:.5f})" for _, row in df_kriging.iterrows()]
    pilihan_target = st.sidebar.selectbox("LOOCV Target Node:", opsi_desa)
    model_variogram = st.sidebar.selectbox("Fungsi Variogram:", ["linear", "spherical", "exponential", "gaussian"])
    hitung_btn = st.sidebar.button("Hitung Estimasi Spasial", type="primary", use_container_width=True)
    
    idx_target = opsi_desa.index(pilihan_target)
    target_node = df_kriging.iloc[idx_target]
    t_lat, t_lon = float(target_node['Lat']), float(target_node['Lon'])
    nilai_aktual = float(target_node[parameter_terpilih])
    elevasi_target = float(target_node['Elevasi'])
    
    base_data = df_kriging.drop(df_kriging.index[idx_target]).copy()
    X_base, Y_base, Z_base = base_data['Lon'].values, base_data['Lat'].values, base_data[parameter_terpilih].values
    elevasi_ref_rata = base_data['Elevasi'].mean()
    delta_elevasi = abs(elevasi_target - elevasi_ref_rata)
    
    prediksi_kriging, kriging_variance, error_mae = 0.0, 0.0, 0.0
    status_hitung = ""
    
    if hitung_btn:
        try:
            OK = OrdinaryKriging(X_base, Y_base, Z_base, variogram_model=model_variogram, verbose=False, enable_plotting=False)
            z_pred, sigmasq = OK.execute('points', [t_lon], [t_lat])
            prediksi_kriging, kriging_variance = z_pred[0], sigmasq[0]
            error_mae = abs(prediksi_kriging - nilai_aktual)
            status_hitung = "Sukses"
        except Exception as e:
            status_hitung = f"Galat: {e}"

    kolom_kiri, kolom_kanan = st.columns([1.55, 1.45])
    with kolom_kiri:
        st.markdown("<h4 style='font-weight: 400; color: #d2e7b9;'>Peta Kontur Elevasi Wilayah (Esri Topo)</h4>", unsafe_allow_html=True)
        peta_lahan = folium.Map(location=[float(df_kriging['Lat'].mean()), float(df_kriging['Lon'].mean())], zoom_start=14, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri Topographic Map')
        for _, row in df_kriging.iterrows():
            r_lat, r_lon = float(row['Lat']), float(row['Lon'])
            if r_lat == t_lat and r_lon == t_lon:
                folium.Marker([r_lat, r_lon], popup=f"<b>TARGET UJI: {row['Desa']}</b>", icon=folium.Icon(color='red', icon='info-sign')).add_to(peta_lahan)
            else:
                folium.CircleMarker([r_lat, r_lon], radius=7, color='#ffffff', weight=1, fill_color='#24492e', fill_opacity=0.9, popup=f"<b>{row['Desa']}</b>").add_to(peta_lahan)
        components.html(peta_lahan._repr_html_(), height=500)
        
    with kolom_kanan:
        st.markdown("<h4 style='font-weight: 400; color: #d2e7b9;'>Hasil Analisis & Validasi Topografi</h4>", unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        with e1: st.metric("Elevasi Target", f"{elevasi_target:.0f} mdpl")
        with e2: st.metric("Rerata Referensi", f"{elevasi_ref_rata:.0f} mdpl")
        with e3: st.metric("Selisih (\u0394 H)", f"{delta_elevasi:.0f} m", delta=f"{delta_elevasi:.0f} m", delta_color="inverse")
        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 15px 0;'>", unsafe_allow_html=True)
        
        if hitung_btn:
            if status_hitung == "Sukses":
                m1, m2 = st.columns(2)
                with m1: st.metric("Prediksi Nilai Sistem", f"{prediksi_kriging:.2f}")
                with m2: st.metric("Data Aktual Lapangan", f"{nilai_aktual:.2f}")
                c1, c2 = st.columns(2)
                with c1: st.metric("Mean Absolute Error (MAE)", f"{error_mae:.2f}")
                with c2: st.metric("Normalized Error (NMAE)", f"{(error_mae / df_kriging[parameter_terpilih].mean()) * 100:.2f} %")
                st.markdown(f"""<div style="background-color: rgba(19, 27, 21, 0.6); padding: 20px; border-radius: 6px; border-left: 3px solid #d4a373; margin-bottom: 20px; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(19, 27, 21, 0.6);"><b style="color: #e2c099; font-weight: 500; font-size: 1.05em;">Analisis Spasial-Topografi</b><br><i style="font-size: 0.88em; color: #8da68c; display:block; margin-top:10px; line-height: 1.6;">Temuan: Data menunjukkan tidak adanya korelasi linier antara besarnya \u0394H dengan nilai Galat (NMAE) pada unsur hara makro (N, P, K). Hal ini secara empiris membuktikan bahwa fluktuasi hara didominasi secara absolut oleh faktor intervensi manusia (manajemen pemupukan).</i></div>""", unsafe_allow_html=True)
            else: st.error(status_hitung)
        else: st.info("Sistem siaga. Tetapkan variabel lalu klik kalkulasi.")
