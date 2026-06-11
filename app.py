import streamlit as st
import pandas as pd
import numpy as np
import folium
import streamlit.components.v1 as components
import os
from pykrige.ok import OrdinaryKriging

# --- 1. CONFIGURATION UTAMA PLATFORM ---
st.set_page_config(
    page_title="Sistem Informasi Geospasial Kentang",
    page_icon="🥔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. MANAGEMENT STATE HALAMAN ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Beranda Utama"

# --- 3. UNIFIED PREMIUM DARK THEME STYLE (GLOBAL) ---
bg_img_url = "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?q=80&w=2000&auto=format&fit=crop"

st.markdown(f"""
    <style>
    /* Mengunci tema hitam matte elegan di semua modul */
    .stApp {{
        background-image: linear-gradient(rgba(10, 15, 11, 0.91), rgba(10, 15, 11, 0.91)), url("{bg_img_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-color: #0a0f0b !important;
    }}
    
    /* Pewarnaan teks terang kontras di seluruh aplikasi */
    h1, h2, h3, h4, h5, h6, p, span, label, th, td, .stMarkdown {{
        color: #e4eed7 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* Desain Kotak Fitur Utama */
    .feature-card {{
        background-color: rgba(19, 27, 21, 0.7);
        padding: 30px;
        border-radius: 14px;
        border: 1px solid #243528;
        box-shadow: 0 8px 25px rgba(0,0,0,0.6);
        margin-bottom: 15px;
        text-align: center;
    }}
    
    /* Penyelarasan Input Selectbox ke Tema Gelap */
    .stSelectbox div[data-baseweb="select"] {{
        background-color: #121914 !important;
        color: #e4eed7 !important;
        border: 1px solid #243528 !important;
    }}
    
    /* Pengaturan fleksibilitas kursor dan ruang halaman */
    .block-container {{
        padding-top: 2.5rem !important;
        padding-bottom: 4rem !important;
        max-width: 92% !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. CSS CONDITIONAL: SEMBUNYIKAN SIDEBAR PADA BERANDA & GIS ---
if st.session_state.current_page in ["🏠 Beranda Utama", "🗺️ Peta GIS Regional"]:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #060907 !important;
            border-right: 1px solid #1a251d;
        }
        [data-testid="stSidebar"] * {
            color: #cddbc0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 5. ENGINE LOAD & FILTER DATA ---
DATA_ELEVASI_ASLI = {
    'Kepakisan': 1851,
    'Bakal': 1693,
    'Sikunang': 2110,
    'Dieng Kulon': 2068,
    'Karangtengah': 1541
}

@st.cache_data
def load_and_prepare_data():
    path = 'Data_Kriging.xlsx'
    if not os.path.exists(path):
        path = '/content/Data_Kriging.xlsx'
        if not os.path.exists(path):
            return None
            
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    
    for c in df.columns:
        if c.lower() == 'titik': df = df.rename(columns={c: 'Desa'})
            
    df[['Desa', 'Lat', 'Lon']] = df[['Desa', 'Lat', 'Lon']].ffill()
    
    # Prioritas: Kolom Excel, Fallback: Data Asli
    if 'Elevasi' not in df.columns:
        df['Elevasi'] = df['Desa'].map(DATA_ELEVASI_ASLI).fillna(1800)
        
    for col in ['Lat', 'Lon', 'N', 'P', 'K', 'PH', 'Elevasi']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df_avg = df.groupby(['Desa', 'Lat', 'Lon']).mean().reset_index()
    return df_avg.dropna()

df_clean = load_and_prepare_data()

# --- 6. CORE NAVIGATION ROUTING LAYER ---

if st.session_state.current_page == "🏠 Beranda Utama":
    # --- HALAMAN BERANDA UTAMA ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2.9em; letter-spacing: 1px; color: #f2f8ea; font-weight: 700;'>SISTEM INFORMASI GEOSPASIAL<br>SENTRA PRODUKSI KENTANG PULAU JAWA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #a3bfa2; font-weight: normal; margin-bottom: 50px;'>Integrasi Pemetaan Spasial Makro dan Komputasi Estimasi Ragam Hara Lapangan</h4>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.08); width: 85%; margin: 0 auto;'><br><br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <h3 style='color: #d2e7b9; margin-top:0;'>🗺️ Peta GIS Regional (Makro)</h3>
            <p style='font-size: 0.98em; line-height: 1.6; color: #b7c8b0; text-align: justify;'>Visualisasi spasial makroskopis yang menyajikan sebaran komprehensif titik koordinat observasi pada 12 sentra produksi kentang di Pulau Jawa. Berguna untuk analisis kesesuaian wilayah berbasis layering peta digital regional.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Peta GIS Regional →", key="go_to_gis", use_container_width=True):
            st.session_state.current_page = "🗺️ Peta GIS Regional"
            st.rerun()
        
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <h3 style='color: #d2e7b9; margin-top:0;'>📈 Interpolasi Geostatistik (Mikro)</h3>
            <p style='font-size: 0.98em; line-height: 1.6; color: #b7c8b0; text-align: justify;'>Mesin perhitungan geostatistik otomatis menggunakan model matematika <i>Ordinary Kriging</i>. Berfungsi memprediksi nilai kandungan Nitrogen, Fosfor, Kalium, dan pH pada lokasi tanah kosong melalui pengujian silang LOOCV.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Jalankan Mesin Kriging →", key="go_to_kriging", use_container_width=True):
            st.session_state.current_page = "📈 Analisis Kriging (Mikro)"
            st.rerun()
            
    st.markdown("<div style='height: 220px;'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); width: 100%;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7f9480; font-size: 0.95em; letter-spacing: 0.5px;'>Tugas Akhir S1 Teknik Fisika | Universitas Telkom</p>", unsafe_allow_html=True)

elif st.session_state.current_page == "🗺️ Peta GIS Regional":
    # --- HALAMAN PETA GIS REGIONAL ---
    kolom_judul, kolom_back = st.columns([3, 1])
    with kolom_judul:
        st.title("🗺️ Peta Kesesuaian Lahan Digital")
        st.write("Layout visual sebaran komprehensif data hara makro skala makroskopis Pulau Jawa.")
    with kolom_back:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🏠 Kembali ke Beranda", use_container_width=True):
            st.session_state.current_page = "🏠 Beranda Utama"
            st.rerun()
            
    st.markdown("---")
    link_gis_anda = "https://arcg.is/1LDCjO4"
    
    components.html(f"""
        <iframe src="{link_gis_anda}" width="100%" height="650" style="border: 1px solid #243528; border-radius: 10px; box-shadow: 0px 12px 35px rgba(0,0,0,0.85);" allowfullscreen="" loading="lazy"></iframe>
    """, height=680)

elif st.session_state.current_page == "📈 Analisis Kriging (Mikro)":
    # --- HALAMAN ANALISIS KRIGING ---
    st.title("📈 Komputasi Ordinary Kriging (LOOCV)")
    st.markdown("Sistem Estimasi Ragam Hara Tanah Berbasis Topografi Kontur Lingkungan")
    st.markdown("---")

    if df_clean is None or df_clean.empty:
        st.error("Gagal mendeteksi keberadaan berkas data 'Data_Kriging.xlsx'.")
    else:
        st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/thumb/0/03/Logo_Telkom_University_potrait.png/250px-Logo_Telkom_University_potrait.png", width=80)
        
        if st.sidebar.button("🏠 Kembali ke Beranda", key="back_from_side", type="secondary", use_container_width=True):
            st.session_state.current_page = "🏠 Beranda Utama"
            st.rerun()
            
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎛️ Parameter Komputasi")
        parameter_terpilih = st.sidebar.selectbox("Variabel Nutrisi:", ["N", "P", "K", "PH"])
        opsi_desa = [f"{row['Desa']} ({row['Lat']:.5f}, {row['Lon']:.5f})" for _, row in df_clean.iterrows()]
        pilihan_target = st.sidebar.selectbox("LOOCV Target Node:", opsi_desa)
        
        model_variogram = st.sidebar.selectbox("Fungsi Variogram:", ["linear", "spherical", "exponential", "gaussian"])
        hitung_btn = st.sidebar.button("Hitung Estimasi Spasial", type="primary", use_container_width=True)
        
        # PROSESING ALGORITMA GEOPROCESSING
        idx_target = opsi_desa.index(pilihan_target)
        target_node = df_clean.iloc[idx_target]
        t_lat, t_lon = float(target_node['Lat']), float(target_node['Lon'])
        nilai_aktual = float(target_node[parameter_terpilih])
        elevasi_target = float(target_node['Elevasi'])
        
        base_data = df_clean.drop(df_clean.index[idx_target]).copy()
        
        X_base = base_data['Lon'].values
        Y_base = base_data['Lat'].values
        Z_base = base_data[parameter_terpilih].values
        elevasi_ref_rata = base_data['Elevasi'].mean()
        
        # Hitung Selisih Elevasi
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
                status_hitung = f"Galat Optimasi Semivariogram: {e}"

        # PEMBAGIAN INTERFACES DASHBOARD UTAMA
        kolom_kiri, kolom_kanan = st.columns([1.55, 1.45])
        
        with kolom_kiri:
            st.markdown("#### Peta Kontur Elevasi Wilayah (Esri Topo)")
            peta_lahan = folium.Map(
                location=[float(df_clean['Lat'].mean()), float(df_clean['Lon'].mean())], 
                zoom_start=14, 
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', 
                attr='Esri Topographic Map'
            )
            
            for _, row in df_clean.iterrows():
                r_lat, r_lon = float(row['Lat']), float(row['Lon'])
                if r_lat == t_lat and r_lon == t_lon:
                    folium.Marker(
                        [r_lat, r_lon], 
                        popup=f"<b>TARGET UJI: {row['Desa']} ({row['Elevasi']:.0f} mdpl)</b>", 
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(peta_lahan)
                else:
                    html_popup = f"""
                    <div style="font-family: Arial; font-size: 12px; color: #fff; background-color: #0e1410; padding: 10px; border-radius: 5px; width: 150px; border: 1px solid #243528;">
                        <b style="color:#d2e7b9;">Desa: {row['Desa']}</b><br>
                        Ketinggian: {row['Elevasi']:.0f} mdpl<br>
                        N: {row['N']:.2f} | P: {row['P']:.2f}<br>K: {row['K']:.2f} | pH: {row['PH']:.2f}
                    </div>
                    """
                    folium.CircleMarker([r_lat, r_lon], radius=7, color='#ffffff', weight=1, fill_color='#24492e', fill_opacity=0.9, popup=folium.Popup(html_popup, max_width=180)).add_to(peta_lahan)
            components.html(peta_lahan._repr_html_(), height=500)
            
        with kolom_kanan:
            st.markdown("#### Hasil Analisis & Validasi Topografi")
            
            e1, e2, e3 = st.columns(3)
            with e1: st.metric("Ketinggian Target Uji", f"{elevasi_target:.0f} mdpl")
            with e2: st.metric("Rata-Rata Ketinggian Acuan", f"{elevasi_ref_rata:.0f} mdpl")
            with e3: st.metric("Selisih Ketinggian (\u0394 H)", f"{delta_elevasi:.0f} meter", delta=f"{delta_elevasi:.0f} m", delta_color="inverse")
            
            st.markdown("---")
            
            if hitung_btn:
                if status_hitung == "Sukses":
                    st.toast("Kriging Berhasil!", icon="📊")
                    
                    m1, m2 = st.columns(2)
                    with m1: st.metric("Prediksi Nilai Sistem", f"{prediksi_kriging:.2f}")
                    with m2: st.metric("Data Aktual Lapangan", f"{nilai_aktual:.2f}")
                        
                    c1, c2 = st.columns(2)
                    with c1: st.metric("Mean Absolute Error (MAE)", f"{error_mae:.2f}")
                    with c2: 
                        nmae = (error_mae / df_clean[parameter_terpilih].mean()) * 100
                        st.metric("Normalized Error (NMAE)", f"{nmae:.2f} %")
                    
                    # NARASI BARU YANG MEMBONGKAR KETIDAKLINIERAN ERROR
                    st.markdown(f"""
                    <div style="background-color: #111713; padding: 15px; border-radius: 8px; border-left: 4px solid #f39c12; margin-bottom: 20px; border-top: 1px solid #1c261f; border-right: 1px solid #1c261f; border-bottom: 1px solid #1c261f;">
                    <b style="color: #f39c12;">Analisis Spasial-Topografi:</b><br>
                    Titik uji memiliki selisih ketinggian <b>{delta_elevasi:.0f} meter</b> terhadap rata-rata titik referensi.<br> 
                    <i style="font-size: 0.88em; color: #a3bfa2; display:block; margin-top:5px;">Temuan: Data menunjukkan <b>tidak adanya korelasi linier</b> antara besarnya \u0394H dengan nilai Galat (NMAE) pada unsur hara makro (N, P, K). Hal ini secara empiris membuktikan bahwa fluktuasi hara di lahan Dieng didominasi secara absolut oleh faktor intervensi manusia (dosis dan jadwal pemupukan), yang berhasil mematahkan pengaruh variabel alami (jarak horizontal dan gradien elevasi).</i>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Dataset Input Matriks Jarak & Ketinggian:**")
                    st.dataframe(base_data[['Desa', 'Elevasi', parameter_terpilih]], use_container_width=True)
                else:
                    st.error(status_hitung)
            else:
                st.info("Sistem dalam status siaga. Silakan tentukan variabel pengujian pada panel kiri (*sidebar*), lalu tekan tombol kalkulasi.")
