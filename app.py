import streamlit as st
import pandas as pd
import numpy as np
import folium
import streamlit.components.v1 as components
import os
from pykrige.ok import OrdinaryKriging

# --- 1. KONFIGURASI HALAMAN (WAJIB DI PALING ATAS) ---
st.set_page_config(
    page_title="Geospasial Sentra Kentang",
    page_icon="🥔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNGSI LOAD DATA (Di-cache agar cepat) ---
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

# --- 3. MENU NAVIGASI (SIDEBAR) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/thumb/0/03/Logo_Telkom_University_potrait.png/250px-Logo_Telkom_University_potrait.png", width=100)
st.sidebar.title("📌 Navigasi Sistem")
menu = st.sidebar.radio(
    "Pilih Modul:",
    ("🏠 Beranda Utama", "🗺️ Peta GIS Regional", "📈 Analisis Kriging (Mikro)")
)
st.sidebar.markdown("---")

# --- 4. LOGIKA ROUTING HALAMAN ---

if menu == "🏠 Beranda Utama":
    # --- HALAMAN BERANDA ---
    bg_img_url = "https://images.unsplash.com/photo-1595841696677-6489ff3f8cd1?q=80&w=2000&auto=format&fit=crop"
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{bg_img_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .css-10trblm, .css-16idsys p, h1, h2, h3, h4, p {{
            color: white !important;
            font-family: 'Arial', sans-serif;
        }}
        [data-testid="stSidebar"] {{
            background-color: #f4f6f9;
        }}
        [data-testid="stSidebar"] * {{
            color: #2c3e50 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br><h1 style='text-align: center; color: white;'>SISTEM INFORMASI GEOSPASIAL<br>SENTRA PRODUKSI KENTANG PULAU JAWA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #d1e8e2; font-weight: normal;'>Pendekatan <i>Dual Geospatial</i> untuk Mendukung <i>Site-Specific Management</i></h4>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white;'>Tugas Akhir S1 Teknik Fisika - Telkom University</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='background-color: rgba(255,255,255,0.15); padding: 25px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.3); height: 200px;'>
            <h3 style='margin-top:0;'>🗺️ Peta GIS Regional (Makro)</h3>
            <p>Visualisasi pemetaan observasi in-situ pada 12 sentra kentang di Pulau Jawa. Mengintegrasikan model prediktif (ANN) untuk menghasilkan zonasi kesesuaian lahan secara makroskopis.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='background-color: rgba(255,255,255,0.15); padding: 25px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.3); height: 200px;'>
            <h3 style='margin-top:0;'>📈 Interpolasi Geostatistik (Mikro)</h3>
            <p>Engine komputasi spasial berbasis <i>Ordinary Kriging</i>. Mengestimasi distribusi hara (N, P, K, pH) pada area tidak terukur dengan validasi silang (LOOCV).</p>
        </div>
        """, unsafe_allow_html=True)

elif menu == "🗺️ Peta GIS Regional":
    # --- HALAMAN PETA GIS ---
    st.markdown("""<style>.stApp { background-image: none !important; background-color: white; } p, h1, h2, h3, h4, h5, h6 {color: #2c3e50 !important;} </style>""", unsafe_allow_html=True)
    
    st.title("🗺️ Peta Kesesuaian Lahan Digital")
    st.write("Visualisasi spasial makro hasil integrasi data hara dan lingkungan untuk 12 sentra produksi kentang di Pulau Jawa.")
    
    link_gis_anda = "https://arcg.is/1LDCjO4"
    components.html(f"""
        <iframe src="{link_gis_anda}" width="100%" height="650" style="border:0; border-radius: 8px; box-shadow: 0px 4px 12px rgba(0,0,0,0.15);" allowfullscreen="" loading="lazy"></iframe>
    """, height=700)

elif menu == "📈 Analisis Kriging (Mikro)":
    # --- HALAMAN INTERPOLASI KRIGING ---
    st.markdown("""<style>.stApp { background-image: none !important; background-color: #f8f9fa; } p, h1, h2, h3, h4, h5, h6, label {color: #2c3e50 !important;} </style>""", unsafe_allow_html=True)
    
    st.title("📈 Komputasi Ordinary Kriging (LOOCV)")
    st.markdown("Implementasi Metode *Ordinary Kriging* untuk Analisis Distribusi Hara Makro")
    st.markdown("---")

    if df_clean is None or df_clean.empty:
        st.error("Sistem tidak dapat menemukan berkas dataset 'Data_Kriging.xlsx'.")
    else:
        # Pindahkan kontrol Kriging ke Sidebar KHUSUS SAAT MENU INI AKTIF
        st.sidebar.markdown("### Konfigurasi Geostatistik")
        parameter_terpilih = st.sidebar.selectbox("Parameter Observasi:", ["N", "P", "K", "PH"])
        opsi_desa = [f"{row['Desa']} ({row['Lat']:.5f}, {row['Lon']:.5f})" for _, row in df_clean.iterrows()]
        pilihan_target = st.sidebar.selectbox("Validasi Silang (LOOCV Target):", opsi_desa)
        
        st.sidebar.markdown("### Model Autokorelasi")
        model_variogram = st.sidebar.selectbox("Fungsi Variogram:", ["linear", "spherical", "exponential", "gaussian"])
        hitung_btn = st.sidebar.button("Eksekusi Pemodelan Spasial", type="primary", use_container_width=True)
        
        # PERSIAPAN DATA TARGET & BASE
        idx_target = opsi_desa.index(pilihan_target)
        target_node = df_clean.iloc[idx_target]
        t_lat, t_lon = float(target_node['Lat']), float(target_node['Lon'])
        nilai_aktual = float(target_node[parameter_terpilih])
        
        base_data = df_clean.drop(df_clean.index[idx_target]).copy()
        
        # ALGORITMA ORDINARY KRIGING
        X_base, Y_base, Z_base = base_data['Lon'].values, base_data['Lat'].values, base_data[parameter_terpilih].values
        
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
                status_hitung = f"Galat Komputasi: {e}"

        # TATA LETAK UTAMA DASHBOARD KRIGING
        kolom_kiri, kolom_kanan = st.columns([1.5, 1.5])
        
        with kolom_kiri:
            st.markdown("#### Pemetaan Visual Citra Satelit")
            peta_lahan = folium.Map(location=[float(df_clean['Lat'].mean()), float(df_clean['Lon'].mean())], zoom_start=14, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri')
            
            for _, row in df_clean.iterrows():
                r_lat, r_lon = float(row['Lat']), float(row['Lon'])
                if r_lat == t_lat and r_lon == t_lon:
                    folium.Marker([r_lat, r_lon], popup=f"<b>LOKASI UJI: {row['Desa']}</b>", icon=folium.Icon(color='red', icon='info-sign')).add_to(peta_lahan)
                else:
                    html_popup = f"""
                    <div style="font-family: Arial; font-size: 13px; color: #333; width: 160px;">
                        <div style="background-color: #2c3e50; color: white; padding: 5px; text-align: center; font-weight: bold; border-radius: 3px;">Referensi: {row['Desa']}</div>
                        <table style="width: 100%; margin-top: 8px; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #ddd;"><td>Nitrogen (N)</td><td style="text-align: right;"><b>{row['N']:.2f}</b></td></tr>
                            <tr style="border-bottom: 1px solid #ddd;"><td>Fosfor (P)</td><td style="text-align: right;"><b>{row['P']:.2f}</b></td></tr>
                            <tr style="border-bottom: 1px solid #ddd;"><td>Kalium (K)</td><td style="text-align: right;"><b>{row['K']:.2f}</b></td></tr>
                            <tr><td>Kadar pH</td><td style="text-align: right;"><b>{row['PH']:.2f}</b></td></tr>
                        </table>
                    </div>
                    """
                    folium.CircleMarker([r_lat, r_lon], radius=7, color='#ffffff', weight=1, fill_color='#2980b9', fill_opacity=0.9, popup=folium.Popup(html_popup, max_width=250)).add_to(peta_lahan)
            components.html(peta_lahan._repr_html_(), height=550)
            
        with kolom_kanan:
            st.markdown("#### Analisis dan Validasi Spasial")
            if hitung_btn:
                if status_hitung == "Sukses":
                    st.success(f"Pemodelan Kriging dengan Semivariogram '{model_variogram.title()}' berhasil dieksekusi.")
                    
                    m1, m2 = st.columns(2)
                    with m1: st.metric("Estimasi Spasial", f"{prediksi_kriging:.2f}")
                    with m2: st.metric("Data Aktual Lapangan", f"{nilai_aktual:.2f}")
                        
                    c1, c2 = st.columns(2)
                    with c1: st.metric("Mean Absolute Error (MAE)", f"{error_mae:.2f} Unit")
                    with c2: 
                        nmae = (error_mae / df_clean[parameter_terpilih].mean()) * 100
                        st.metric("Normalized Error (NMAE)", f"{nmae:.2f} %", delta_color="inverse")
                    
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2980b9; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <b>Interpretasi Geostatistik:</b><br>Varians Kriging (Ketidakpastian): <b>{kriging_variance:.4f}</b><br><br>
                    <i style="font-size: 0.9em; color: #555;">Catatan: NMAE disertakan sebagai metrik pendamping guna menormalisasi efek pembagi bernilai kecil pada data lapangan.</i>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Matriks Data Referensi Geospasial:**")
                    st.dataframe(base_data[['Desa', 'Lat', 'Lon', parameter_terpilih]].copy(), use_container_width=True)
                else:
                    st.error(status_hitung)
                    st.warning("Kurva Semivariogram gagal konvergen. Disarankan untuk menggunakan model 'Linear'.")
            else:
                st.info("Sistem siaga. Tetapkan parameter di sidebar, kemudian klik 'Eksekusi Pemodelan Spasial'.")
