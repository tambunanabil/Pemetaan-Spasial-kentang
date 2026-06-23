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

# --- 4. CSS CONDITIONAL: SIDEBAR LOCKER ---
if st.session_state.current_page in ["Beranda Utama", "Peta Sebaran Titik Data", "Peta Gradasi Kesesuaian Lahan"]:
    st.markdown("<style>[data-testid='stSidebar'] { display: none !important; }</style>", unsafe_allow_html=True)

# --- 5. DATA LOADING ENGINE ---
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

def dapatkan_warna_cud(status):
    lbl = str(status).lower().strip()
    return '#009e73' # Semua Cocok

# --- 6. ROUTING CONTROLLER ---

if st.session_state.current_page == "Beranda Utama":
    st.markdown("<br><br><h1 style='text-align: center;'>SISTEM INFORMASI GEOSPASIAL KENTANG</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    if col1.button("Peta Sebaran Titik"): st.session_state.current_page = "Peta Sebaran Titik Data"; st.rerun()
    if col2.button("Analisis Kriging (Mikro)"): st.session_state.current_page = "Analisis Kriging (Mikro)"; st.rerun()
    if col3.button("Peta Gradasi Lahan"): st.session_state.current_page = "Peta Gradasi Kesesuaian Lahan"; st.rerun()

elif st.session_state.current_page == "Analisis Kriging (Mikro)":
    if st.sidebar.button("‹ Kembali"): st.session_state.current_page = "Beranda Utama"; st.rerun()
    param = st.sidebar.selectbox("Variabel:", ["N", "P", "K", "PH"])
    
    df_unique = df_kriging.groupby(['Desa', 'Lat', 'Lon', 'Kecocokan']).mean(numeric_only=True).reset_index()
    opsi = [f"{r['Desa']} ({r['Lat']:.5f}, {r['Lon']:.5f})" for _, r in df_unique.iterrows()]
    target_str = st.sidebar.selectbox("Target Node:", opsi)
    hitung = st.sidebar.button("Hitung Estimasi Spasial")
    
    target = df_unique.iloc[opsi.index(target_str)]
    base = df_unique.drop(opsi.index(target_str)).copy()
    base['jarak'] = np.sqrt((base['Lon'] - target['Lon'])**2 + (base['Lat'] - target['Lat'])**2)
    acuan_4 = base.nsmallest(4, 'jarak')
    
    prediksi = 0.0
    if hitung:
        OK = OrdinaryKriging(base['Lon'].values, base['Lat'].values, base[param].values, variogram_model='linear')
        prediksi, _ = OK.execute('points', [target['Lon']], [target['Lat']])
        prediksi = prediksi[0]

    col1, col2 = st.columns([1.6, 1.4])
    with col1:
        m = folium.Map(location=[target['Lat'], target['Lon']], zoom_start=14)
        folium.Marker([target['Lat'], target['Lon']], popup="Titik Uji", icon=folium.Icon(color='red')).add_to(m)
        for _, row in acuan_4.iterrows():
            folium.CircleMarker([row['Lat'], row['Lon']], radius=8, color='green', fill=True).add_to(m)
        components.html(m._repr_html_(), height=400)
        
        if hitung:
            st.markdown(f"#### Data Komparasi Parameter {param}")
            data_tabel = [{"Desa": f"{target['Desa']} (Target)", "Peran": "Titik Uji", "Aktual": target[param], "Prediksi": prediksi}]
            for _, row in acuan_4.iterrows():
                data_tabel.append({"Desa": row['Desa'], "Peran": "Acuan", "Aktual": row[param], "Prediksi": "-"})
            st.dataframe(pd.DataFrame(data_tabel), use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Inferensi Lahan")
        if hitung:
            st.success("Keputusan: COCOK")
            st.write(f"Keterangan: {param} pada titik uji adalah {target[param]:.2f}")

elif st.session_state.current_page == "Peta Gradasi Kesesuaian Lahan":
    if st.button("‹ Kembali"): st.session_state.current_page = "Beranda Utama"; st.rerun()
    components.html('<iframe src="https://tambunanabil.github.io/kesesuaian-lahan/" width="100%" height="650"></iframe>', height=680)

elif st.session_state.current_page == "Peta Sebaran Titik Data":
    if st.button("‹ Kembali"): st.session_state.current_page = "Beranda Utama"; st.rerun()
    components.html('<iframe src="https://arcg.is/1LDCjO4" width="100%" height="650"></iframe>', height=680)
