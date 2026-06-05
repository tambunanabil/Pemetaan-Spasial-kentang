import streamlit as st
import pandas as pd
import numpy as np
import folium
import streamlit.components.v1 as components
import os
from pykrige.ok import OrdinaryKriging

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Sistem Informasi Geospasial Kentang",
    page_icon="🥔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STATE MANAGEMENT NAVIGASI ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Beranda Utama"

# Fungsi pembantu untuk pindah halaman dari tombol beranda
def pindah_halaman(nama_halaman):
    st.session_state.current_page = nama_halaman

# --- 3. GLOBAL PRESET STYLE (TEMA GELAP ELEGAN & PERTANIAN) ---
# Menggunakan gambar lanskap pertanian dataran tinggi/pegunungan yang sangat relevan dengan Dieng
bg_img_url = "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?q=80&w=2000&auto=format&fit=crop"

st.markdown(f"""
    <style>
    /* Mengunci tema gelap di seluruh halaman aplikasi */
    .stApp {{
        background-image: linear-gradient(rgba(13, 18, 14, 0.85), rgba(13, 18, 14, 0.85)), url("{bg_img_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-color: #0d120e !important;
    }}
    
    /* Memastikan font dan warna teks konsisten putih/terang di semua komponen */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {{
        color: #e3ebd5 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* Styling Sidebar Gelap Senada */
    [data-testid="stSidebar"] {{
        background-color: #090d0a !important;
        border-right: 1px solid #1c261e;
    }}
    [data-testid="stSidebar"] * {{
        color: #c5d1b4 !important;
    }}
    
    /* Pengaturan Kotak Fitur di Beranda */
    .fitur-box {{
        background-color: rgba(23, 33, 25, 0.6);
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #2d3f31;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 10px;
        transition: transform 0.2s;
    }}
    
    /* Styling Tabel Data agar masuk tema gelap */
    .stDataFrame, div[data-testid="stTable"] {{
        background-color: #121813 !important;
        border: 1px solid #2d3f31 !important;
    }}
    
    /* Mengatasi bug geser/POV kursor yang kaku */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA LOADER ENGINE ---
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
    for col in ['Lat', 'Lon', 'N', 'P', 'K', 'PH']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df_avg = df.groupby(['Desa', 'Lat', 'Lon']).mean().reset_index()
    return df_avg.dropna()

df_clean = load_and_prepare_data()

# --- 5. SIDEBAR NAVIGATION CONTROLLER ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/thumb/0/03/Logo_Telkom_University_potrait.png/250px-Logo_Telkom_University_potrait.png", width=90)
st.sidebar.markdown("<h3 style='margin-bottom:0;'>Navigation Panel</h3>", unsafe_allow_html=True)

# Menggunakan selectbox/radio yang mendengarkan perubahan session state halaman
opsi_menu = ["🏠 Beranda Utama", "🗺️ Peta GIS Regional", "📈 Analisis Kriging (Mikro)"]
index_halaman = opsi_menu.index(st.session_state.current_page)

pilihan_sidebar = st.sidebar.radio(
    "Pilih Modul Sistem:",
    opsi_menu,
    index=index_halaman,
    key="nav_radio"
)

# Jika pengguna mengubah via sidebar, update session state
if pilihan_sidebar != st.session_state.current_page:
    st.session_state.current_page = pilihan_sidebar
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Tugas Akhir S1 Teknik Fisika\nUniversitas Telkom")

# --- 6. CORE APP ROUTING ---

if st.session_state.current_page == "🏠 Beranda Utama":
    # --- HALAMAN BERANDA UTAMA ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2.8em; letter-spacing: 1px; color: #f1f7e8;'>SISTEM INFORMASI GEOSPASIAL<br>SENTRA PRODUKSI KENTANG PULAU JAWA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #a4bfa3; font-weight: normal; margin-bottom: 40px;'>Integrasi Analisis Spasial Makro dan Estimasi Ragam Hara untuk Komoditas Pertanian Presisi</h4>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); width: 80%; margin: 0 auto;'><br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='fitur-box'>
            <h3 style='color: #d1e6b8; margin-top:0;'>🗺️ Peta GIS Regional (Makro)</h3>
            <p style='font-size: 0.95em; line-height: 1.6; color: #b8c7b1;'>Visualisasi sebaran komprehensif lebih dari 100 titik observasi hara tanah pada 12 sentra produksi kentang utama di Pulau Jawa. Modul ini menyajikan layout visual layering kesesuaian lahan regional.</p>
        </div>
        """, unsafe_allow_html=True)
        # Tombol aksi langsung untuk memindahkan halaman ke GIS
        st.button("Buka Peta GIS Regional →", key="btn_gis", on_click=pindah_halaman, args=("🗺️ Peta GIS Regional",), use_container_width=True)
        
    with col2:
        st.markdown("""
        <div class='fitur-box'>
            <h3 style='color: #d1e6b8; margin-top:0;'>📈 Interpolasi Geostatistik (Mikro)</h3>
            <p style='font-size: 0.95em; line-height: 1.6; color: #b8c7b1;'>Mesin perhitungan geostatistik mandiri menggunakan metode <i>Ordinary Kriging</i>. Berfungsi mengestimasi nilai Nitrogen, Fosfor, Kalium, dan pH pada koordinat tanah kosong melalui skema validasi LOOCV.</p>
        </div>
        """, unsafe_allow_html=True)
        # Tombol aksi langsung untuk memindahkan halaman ke Kriging
        st.button("Jalankan Mesin Kriging →", key="btn_kriging", on_click=pindah_halaman, args=("📈 Analisis Kriging (Mikro)",), use_container_width=True)
        
    # MEMBERIKAN SPACER SPACE PADDING DI BAWAH REQ NO 3
    st.markdown("<div style='height: 180px;'></div>", unsafe_allow_html=True)

elif st.session_state.current_page == "🗺️ Peta GIS Regional":
    # --- HALAMAN PETA GIS REGIONAL ---
    st.title("🗺️ Peta Kesesuaian Lahan Digital")
    st.write("Visualisasi spasial makro hasil pemetaan data hara pada 12 sentra produksi kentang di Pulau Jawa.")
    st.markdown("---")
    
    link_gis_anda = "https://arcg.is/1LDCjO4"
    
    # Menampilkan Iframe dengan efek bayangan elegan transparan agar menyatu dengan latar gelap
    components.html(f"""
        <iframe src="{link_gis_anda}" width="100%" height="650" style="border: 1px solid #2d3f31; border-radius: 8px; box-shadow: 0px 10px 30px rgba(0,0,0,0.7);" allowfullscreen="" loading="lazy"></iframe>
    """, height=680)

elif st.session_state.current_page == "📈 Analisis Kriging (Mikro)":
    # --- HALAMAN ANALISIS KRIGING ---
    st.title("📈 Komputasi Ordinary Kriging (LOOCV)")
    st.markdown("Analisis Skala Mikro Estimasi Distribusi Kandungan Hara Tanah")
    st.markdown("---")

    if df_clean is None or df_clean.empty:
        st.error("Sistem tidak dapat mendeteksi file basis data 'Data_Kriging.xlsx'.")
    else:
        # Menampilkan pengontrol konfigurasi khusus di sidebar jika modul ini dibuka
        st.sidebar.markdown("### 🎛️ Parameter Komputasi")
        parameter_terpilih = st.sidebar.selectbox("Variabel Target:", ["N", "P", "K", "PH"])
        opsi_desa = [f"{row['Desa']} ({row['Lat']:.5f}, {row['Lon']:.5f})" for _, row in df_clean.iterrows()]
        pilihan_target = st.sidebar.selectbox("LOOCV Target Node:", opsi_desa)
        
        model_variogram = st.sidebar.selectbox("Fungsi Variogram:", ["linear", "spherical", "exponential", "gaussian"])
        hitung_btn = st.sidebar.button("Hitung Estimasi Spasial", type="primary", use_container_width=True)
        
        # PROSESING MATRIKS DATA
        idx_target = opsi_desa.index(pilihan_target)
        target_node = df_clean.iloc[idx_target]
        t_lat, t_lon = float(target_node['Lat']), float(target_node['Lon'])
        nilai_aktual = float(target_node[parameter_terpilih])
        
        base_data = df_clean.drop(df_clean.index[idx_target]).copy()
        X_base, Y_base, Z_base = base_data['Lon'].values, base_data['Lat'].values, base_data[parameter_terpilled] = base_data[parameter_terpilih].values
        
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

        # PEMBAGIAN LAYOUT INTERAKTIF GELAP ELEGAN
        kolom_kiri, kolom_kanan = st.columns([1.6, 1.4])
        
        with kolom_kiri:
            st.markdown("#### Visualisasi Spasial Titik Referensi")
            # Set peta satelit dasar gelap/berwarna agar pas dengan tema aplikasi
            peta_lahan = folium.Map(
                location=[float(df_clean['Lat'].mean()), float(df_clean['Lon'].mean())], 
                zoom_start=14, 
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                attr='Esri'
            )
            
            for _, row in df_clean.iterrows():
                r_lat, r_lon = float(row['Lat']), float(row['Lon'])
                if r_lat == t_lat and r_lon == t_lon:
                    folium.Marker([r_lat, r_lon], popup=f"<b>TARGET UJI LOOCV: {row['Desa']}</b>", icon=folium.Icon(color='red', icon='info-sign')).add_to(peta_lahan)
                else:
                    html_popup = f"""
                    <div style="font-family: Arial; font-size: 12px; color: #fff; background-color: #172119; padding: 10px; border-radius: 5px; width: 150px;">
                        <b style="color:#d1e6b8;">Desa: {row['Desa']}</b><br>
                        N: {row['N']:.2f}<br>P: {row['P']:.2f}<br>K: {row['K']:.2f}<br>pH: {row['PH']:.2f}
                    </div>
                    """
                    folium.CircleMarker([r_lat, r_lon], radius=7, color='#ffffff', weight=1, fill_color='#2d4f37', fill_opacity=0.9, popup=folium.Popup(html_popup, max_width=200)).add_to(peta_lahan)
            components.html(peta_lahan._repr_html_(), height=500)
            
        with kolom_kanan:
            st.markdown("#### Matriks Komputasi Validasi")
            if hitung_btn:
                if status_hitung == "Sukses":
                    st.toast("Kriging Berhasil Dieksekusi!", icon="📊")
                    
                    m1, m2 = st.columns(2)
                    with m1: st.metric("Prediksi Interpolasi Spasial", f"{prediksi_kriging:.2f}")
                    with m2: st.metric("Data Aktual Lapangan", f"{nilai_aktual:.2f}")
                        
                    c1, c2 = st.columns(2)
                    with c1: st.metric("Mean Absolute Error (MAE)", f"{error_mae:.2f}")
                    with c2: 
                        nmae = (error_mae / df_clean[parameter_terpilih].mean()) * 100
                        st.metric("Normalized Error (NMAE)", f"{nmae:.2f} %")
                    
                    st.markdown(f"""
                    <div style="background-color: #121813; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50; margin-bottom: 20px;">
                    <b style="color: #4caf50;">Kriging Variance (Ketidakpastian Kuantitatif):</b> {kriging_variance:.4f}<br>
                    <i style="font-size: 0.85em; color: #a4bfa3;">Model matematika berhasil melakukan konvergensi parameter semivariogram spasial.</i>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Dataset Input Semivariogram Spasial:**")
                    st.dataframe(base_data[['Desa', 'Lat', 'Lon', parameter_terpilih]], use_container_width=True)
                else:
                    st.error(status_hitung)
            else:
                st.info("Sistem siap. Atur konfigurasi parameter pada panel navigasi di sebelah kiri, lalu tekan tombol kalkulasi.")
