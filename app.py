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
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. MANAGEMENT STATE HALAMAN ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Beranda Utama"

# --- 3. PREMIUM DARK THEME STYLE ---
bg_img_url = "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?q=80&w=2000&auto=format&fit=crop"

st.markdown(f"""
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
        text-align: center;
        height: 250px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA LOADING ---
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
    df['Kecocokan'] = 'Cocok'
    return df.dropna(subset=['Lat', 'Lon', 'Desa'])

df_kriging = load_kriging_base_data()

# --- 5. INTERACTIVE ROUTING ---
if st.session_state.current_page == "Beranda Utama":
    st.markdown("<h1 style='text-align: center;'>SISTEM INFORMASI GEOSPASIAL KENTANG</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Peta Sebaran"): st.session_state.current_page = "Peta Sebaran Titik Data"; st.rerun()
    with col2:
        if st.button("Analisis Kriging"): st.session_state.current_page = "Analisis Kriging (Mikro)"; st.rerun()
    with col3:
        if st.button("Peta Gradasi"): st.session_state.current_page = "Peta Gradasi Kesesuaian Lahan"; st.rerun()

elif st.session_state.current_page == "Analisis Kriging (Mikro)":
    # Sidebar
    if st.sidebar.button("‹ Kembali"): st.session_state.current_page = "Beranda Utama"; st.rerun()
    parameter_terpilih = st.sidebar.selectbox("Variabel Nutrisi:", ["N", "P", "K", "PH"])
    
    df_unique = df_kriging.groupby(['Desa', 'Lat', 'Lon', 'Kecocokan']).mean(numeric_only=True).reset_index()
    opsi_desa = [f"{row['Desa']} ({row['Lat']:.5f}, {row['Lon']:.5f})" for _, row in df_unique.iterrows()]
    pilihan_target = st.sidebar.selectbox("LOOCV Target Node:", opsi_desa)
    hitung_btn = st.sidebar.button("Hitung Estimasi Spasial")
    
    # Logic
    idx = opsi_desa.index(pilihan_target)
    target = df_unique.iloc[idx]
    
    # 4 Tetangga terdekat
    base_data = df_unique.drop(idx).copy()
    base_data['jarak'] = np.sqrt((base_data['Lon'] - target['Lon'])**2 + (base_data['Lat'] - target['Lat'])**2)
    titik_acuan_4 = base_data.nsmallest(4, 'jarak')
    
    prediksi = 0.0
    if hitung_btn:
        OK = OrdinaryKriging(base_data['Lon'].values, base_data['Lat'].values, base_data[parameter_terpilih].values, variogram_model='linear')
        prediksi, _ = OK.execute('points', [target['Lon']], [target['Lat']])
        prediksi = prediksi[0]

    # Layout
    col1, col2 = st.columns([1.6, 1.4])
    with col1:
        st.markdown(f"#### Analisis {parameter_terpilih}")
        # Tabel HTML Custom
        html_table = f"""
        <table style="width: 100%; border-collapse: collapse; text-align: center; color: #e4eed7; background-color: rgba(19, 27, 21, 0.8);">
            <tr style="background-color: #2a3d2e;">
                <th>Desa</th><th>Peran</th><th>{parameter_terpilih} (Aktual)</th><th>Prediksi {parameter_terpilih}</th>
            </tr>
            <tr style="background-color: #8b0000;">
                <td>{target['Desa']}</td><td>Titik Uji</td><td>{target[parameter_terpilih]:.2f}</td><td>{prediksi:.2f}</td>
            </tr>
        """
        for _, row in titik_acuan_4.iterrows():
            html_table += f"<tr><td>{row['Desa']}</td><td>Acuan</td><td>{row[parameter_terpilih]:.2f}</td><td>-</td></tr>"
        html_table += "</table>"
        st.markdown(html_table, unsafe_allow_html=True)

    with col2:
        st.markdown("#### Hasil Inferensi")
        if hitung_btn:
            st.success(f"Keputusan: COCOK") # Placeholder logika
            st.write(f"Keterangan: {parameter_terpilih} pada titik uji adalah {target[parameter_terpilih]:.2f}")
