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
    [data-testid="stDataFrame"] {{
        background-color: rgba(19, 27, 21, 0.6);
        border-radius: 6px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. CSS CONDITIONAL: SIDEBAR LOCKER MANAGEMENT ---
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

# --- 5. UNIFIED DATA READING ENGINE ---
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
    
    if 'Kecocokan' not in df.columns:
        df['Kecocokan'] = 'Cocok'
        
    return df.dropna(subset=['Lat', 'Lon', 'Desa'])

df_kriging = load_kriging_base_data()

def dapatkan_warna_cud(status):
    lbl = str(status).lower().strip()
    if 'tidak' in lbl or 'kurang' in lbl: return '#d55e00'
    elif 'netral' in lbl: return '#e69f00'
    return '#009e73'

# --- 6. INTERACTIVE ROUTING CONTROLLER ---

if st.session_state.current_page == "Beranda Utama":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2.8em; letter-spacing: 2px; color: #f2f8ea; font-weight: 300;'>SISTEM INFORMASI GEOSPASIAL<br>SENTRA PRODUKSI KENTANG PULAU JAWA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #8da68c; font-weight: 400; letter-spacing: 0.5px; margin-bottom: 50px;'>Integrasi Pemetaan Spasial Makro dan Komputasi Estimasi Ragam Hara Lapangan</h4>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); width: 85%; margin: 0 auto;'><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class='feature-card'><span class="material-symbols-outlined premium-icon">public</span><h3 style='color: #d2e7b9; margin-top:0; font-weight: 400; font-size:1.3em;'>Peta Sebaran Titik Data</h3><p style='font-size: 0.93em; color: #9ab098; text-align: justify; line-height:1.6;'>Visualisasi spasial regional sebaran koordinat observasi pada 12 sentra produksi kentang di Pulau Jawa melalui platform ArcGIS Online.</p></div>""", unsafe_allow_html=True)
        if st.button("Buka Peta Sebaran Titik  ›", key="go_to_gis", use_container_width=True):
            st.session_state.current_page = "Peta Sebaran Titik Data"; st.rerun()
    with col2:
        st.markdown("""<div class='feature-card'><span class="material-symbols-outlined premium-icon">architecture</span><h3 style='color: #d2e7b9; margin-top:0; font-weight: 400; font-size:1.3em;'>Interpolasi Geostatistik</h3><p style='font-size: 0.93em; color: #9ab098; text-align: justify; line-height:1.6;'>Mesin komputasi menggunakan pemodelan matematika <i>Ordinary Kriging</i> univariat guna mengestimasi hara tak tersampel via LOOCV dilengkapi asersi inferensi hara.</p></div>""", unsafe_allow_html=True)
        if st.button("Jalankan Modul Kriging  ›", key="go_to_kriging", use_container_width=True):
            st.session_state.current_page = "Analisis Kriging (Mikro)"; st.rerun()
    with col3:
        st.markdown("""<div class='feature-card'><span class="material-symbols-outlined premium-icon">layers</span><h3 style='color: #d2e7b9; margin-top:0; font-weight: 400; font-size:1.3em;'>Kesesuaian Lahan Bergradasi</h3><p style='font-size: 0.93em; color: #9ab098; text-align: justify; line-height:1.6;'>Pemetaan mikro spasial hasil interpolasi Inverse Distance Weighting (IDW) kuadratis dengan penguncian konstan berbasis geografis absolut dari QGIS.</p></div>""", unsafe_allow_html=True)
        if st.button("Lihat Gradasi Kesesuaian Lahan ›", key="go_to_suitability", use_container_width=True):
            st.session_state.current_page = "Peta Gradasi Kesesuaian Lahan"; st.rerun()
            
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.03); width: 100%;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #5b6b5c; font-size: 0.85em; letter-spacing: 1px; text-transform: uppercase;'>Tugas Akhir S1 Teknik Fisika &nbsp;|&nbsp; Universitas Telkom</p>", unsafe_allow_html=True)

elif st.session_state.current_page == "Peta Sebaran Titik Data":
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown("<h1 style='font-weight: 300;'>Peta Sebaran Koordinat Titik Data Regional</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("‹  Kembali ke Beranda", use_container_width=True): st.session_state.current_page = "Beranda Utama"; st.rerun()
    components.html(f'<iframe src="https://arcg.is/1LDCjO4" width="100%" height="650" style="border: 1px solid rgba(163, 191, 162, 0.2); border-radius: 6px; box-shadow: 0px 8px 30px rgba(0,0,0,0.85);"></iframe>', height=680)

elif st.session_state.current_page == "Peta Gradasi Kesesuaian Lahan":
    col1, col2 = st.columns([3, 1])
    with col1: 
        st.markdown("<h1 style='font-weight: 300;'>Peta Gradasi Kontinu Kesesuaian Lahan Hortikultura</h1>", unsafe_allow_html=True)
        st.write("Visualisasi Hasil Analisis Spasial QGIS dengan Metode Inverse Distance Weighting (IDW) Berbasis Warna Inklusif CUD.")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("‹  Kembali ke Beranda", key="back_from_suit", use_container_width=True): st.session_state.current_page = "Beranda Utama"; st.rerun()
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    
    link_peta_gradasi_nabil = "https://tambunanabil.github.io/kesesuaian-lahan/#13/-7.8998/112.5033"
    components.html(f'<iframe src="{link_peta_gradasi_nabil}" width="100%" height="650" style="border: none; border-radius: 6px; box-shadow: 0px 8px 30px rgba(0,0,0,0.65);"></iframe>', height=680)

elif st.session_state.current_page == "Analisis Kriging (Mikro)":
    # ==========================================
    # --- MODUL MENU 2: INTERPOLASI & INFERENSI ---
    # ==========================================
    st.markdown("<h1 style='font-weight: 300;'>Komputasi Ordinary Kriging & Logika Inferensi Lahan</h1>", unsafe_allow_html=True)
    if st.sidebar.button("‹ Kembali ke Beranda", key="back_from_side", type="secondary", use_container_width=True):
        st.session_state.current_page = "Beranda Utama"; st.rerun()
        
    st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    st.sidebar.markdown("<h3 style='font-size: 1.1em; font-weight:400;'>Parameter Komputasi</h3>", unsafe_allow_html=True)
    parameter_terpilih = st.sidebar.selectbox("Variabel Nutrisi:", ["N", "P", "K", "PH"])
    
    # ---------------------------------------------------------
    # PERBAIKAN FATAL: GROUPBY HANYA BERDASARKAN DESA
    # Ini memastikan 2-4 titik pengukuran dirata-ratakan jadi 1
    # ---------------------------------------------------------
    df_kriging_unique = df_kriging.groupby('Desa').agg({
        'Lat': 'mean',
        'Lon': 'mean',
        'Elevasi': 'mean',
        'N': 'mean',
        'P': 'mean',
        'K': 'mean',
        'PH': 'mean',
        'Kecocokan': 'first' # Mengambil status kesesuaian pertama karena diasumsikan sama se-desa
    }).reset_index()
    # ---------------------------------------------------------

    opsi_desa = [f"{row['Desa']} ({row['Lat']:.5f}, {row['Lon']:.5f})" for _, row in df_kriging_unique.iterrows()]
    pilihan_target = st.sidebar.selectbox("LOOCV Target Node:", opsi_desa)
    model_variogram = st.sidebar.selectbox("Fungsi Variogram:", ["linear", "spherical", "exponential", "gaussian"])
    hitung_btn = st.sidebar.button("Hitung Estimasi Spasial", type="primary", use_container_width=True)
    
    idx_target = opsi_desa.index(pilihan_target)
    target_node = df_kriging_unique.iloc[idx_target]
    t_lat, t_lon = float(target_node['Lat']), float(target_node['Lon'])
    t_desa = str(target_node['Desa'])
    nilai_aktual = float(target_node[parameter_terpilih])
    elevasi_target = float(target_node['Elevasi'])
    ph_target = float(target_node['PH'])
    status_aktual_target = str(target_node['Kecocokan'])
    
    base_data = df_kriging_unique.drop(df_kriging_unique.index[idx_target]).copy()
    base_data['jarak'] = np.sqrt((base_data['Lon'] - t_lon)**2 + (base_data['Lat'] - t_lat)**2)
    titik_acuan_4 = base_data.nsmallest(4, 'jarak')
    
    X_base, Y_base, Z_base = base_data['Lon'].values, base_data['Lat'].values, base_data[parameter_terpilih].values
    elevasi_ref_rata = base_data['Elevasi'].mean()
    
    # Pre-calculate Inferensi Logika Agronomi
    min_ph_acuan, max_ph_acuan = titik_acuan_4['PH'].min(), titik_acuan_4['PH'].max()
    min_el_acuan, max_el_acuan = titik_acuan_4['Elevasi'].min(), titik_acuan_4['Elevasi'].max()
    ph_masuk_range = min_ph_acuan <= ph_target <= max_ph_acuan
    elevasi_masuk_range = min_el_acuan <= elevasi_target <= max_el_acuan
    status_mayoritas = titik_acuan_4['Kecocokan'].mode()[0]
    status_unik = titik_acuan_4['Kecocokan'].str.lower().unique()

    if ph_masuk_range and elevasi_masuk_range:
        kesimpulan_inferensi = status_mayoritas.title()
        warna_inferensi = dapatkan_warna_cud(kesimpulan_inferensi)
        keterangan_logika = f"Parameter ketinggian dan pH Titik Uji masuk dalam range batas 4 titik acuan terdekat. Titik ini secara rasional mewarisi status mayoritas dari tetangganya: {kesimpulan_inferensi}."
    elif len(status_unik) == 1 and status_unik[0] == 'cocok':
        kesimpulan_inferensi = "Cocok"
        warna_inferensi = dapatkan_warna_cud("Cocok")
        keterangan_logika = "Kondisi lingkungan berada di luar range referensi. Namun, karena ke-4 titik acuan terdekat secara mutlak berstatus 'Cocok', berdasarkan Autokorelasi Spasial Absolut titik uji ini secara logis dipertahankan berstatus COCOK."
    else:
        if elevasi_target < 1000:
            kesimpulan_inferensi = "Tidak Cocok"
            warna_inferensi = "#d55e00"
            keterangan_logika = "Sifat lingkungan di luar range referensi. Karena titik uji berada di elevasi rendah (< 1000 mdpl), kemungkinan besar tidak cocok untuk pertumbuhan kentang."
        elif 1000 <= elevasi_target <= 1500:
            if ph_target > 7.0:
                kesimpulan_inferensi = "Berpotensi Cocok"
                warna_inferensi = "#e69f00"
                keterangan_logika = "Sifat lingkungan di luar range referensi. Elevasi menengah (1000-1500 mdpl) didukung oleh keasaman tanah yang baik (pH > 7), area ini berpotensi cocok."
            else:
                kesimpulan_inferensi = "Tidak Cocok"
                warna_inferensi = "#d55e00"
                keterangan_logika = "Sifat lingkungan di luar range referensi. Berada di ketinggian menengah (1000-1500 mdpl) namun pertumbuhan terhambat oleh kondisi tanah yang sangat masam (pH ≤ 7)."
        elif elevasi_target > 1500:
            if ph_target > 6.5:
                kesimpulan_inferensi = "Kemungkinan Cocok"
                warna_inferensi = "#009e73"
                keterangan_logika = "Sifat lingkungan di luar range referensi. Karena berada di elevasi yang ideal (>1500 mdpl) dan didukung pH > 6.5, area ini kemungkinan besar cocok."
            else:
                kesimpulan_inferensi = "Tidak Cocok"
                warna_inferensi = "#d55e00"
                keterangan_logika = "Sifat lingkungan di luar range referensi. Berada di ketinggian yang ideal (>1500 mdpl), tetapi gagal memenuhi syarat kelayakan akibat kondisi tanah yang sangat masam (pH ≤ 6.5)."

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
        st.markdown("<h4 style='font-weight: 400; color: #d2e7b9; letter-spacing: 0.5px;'>Peta Lokasi Titik Uji LOOCV</h4>", unsafe_allow_html=True)
        peta_lahan = folium.Map(
            location=[float(df_kriging_unique['Lat'].mean()), float(df_kriging_unique['Lon'].mean())], 
            zoom_start=14, 
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', 
            attr='Esri Topographic Map'
        )
        
        warna_target_cud = dapatkan_warna_cud(status_aktual_target)
        folium.Marker(
            [t_lat, t_lon], 
            popup=folium.Popup(f"""
            <div style="font-family:'Segoe UI'; font-size:12px; width:180px; padding:5px;">
                <b style="color:#cc3333;">[ TARGET UJI LOOCV ]</b><br>
                <b>Desa: {t_desa}</b><br>
                pH: {ph_target:.2f}<br>
                Elevasi: {elevasi_target:.0f} mdpl
            </div>""", max_width=250),
            icon=folium.Icon(color='red')
        ).add_to(peta_lahan)
        
        for _, row in df_kriging_unique.iterrows():
            r_lat, r_lon = float(row['Lat']), float(row['Lon'])
            if r_lat == t_lat and r_lon == t_lon:
                continue
                
            is_acuan = r_lat in titik_acuan_4['Lat'].values and r_lon in titik_acuan_4['Lon'].values
            border_color = '#ffffff' if is_acuan else 'rgba(0,0,0,0.2)'
            border_weight = 2.5 if is_acuan else 1.0
            radius_size = 10 if is_acuan else 6
            warna_node_cud = dapatkan_warna_cud(row['Kecocokan'])
            
            html_table_popup = f"""
            <div style="font-family: 'Segoe UI', Arial; font-size: 11px; width: 180px; padding: 5px;">
                <b style="color:{warna_node_cud}; font-size:12px; display:block; margin-bottom:5px;">Sentra: {row['Desa']}</b>
                <span style="display:block; padding:2px 4px; background-color:{warna_node_cud}; color:white; border-radius:3px; text-align:center; font-weight:bold; margin-bottom:6px; font-size:10px;">
                    {str(row['Kecocokan']).upper()}
                </span>
                <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                    <tr style="border-bottom: 1px solid #ddd; background:#f9f9f9;"><td><b>Parameter</b></td><td style="text-align:right;"><b>Nilai</b></td></tr>
                    <tr style="border-bottom: 1px solid #ddd;"><td>Nitrogen (N)</td><td style="text-align: right;">{row.get('N', 0):.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #ddd;"><td>Fosfor (P)</td><td style="text-align: right;">{row.get('P', 0):.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #ddd;"><td>Kalium (K)</td><td style="text-align: right;">{row.get('K', 0):.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #ddd;"><td>pH Tanah</td><td style="text-align: right;">{row.get('PH', 0):.2f}</td></tr>
                    <tr><td>Elevasi</td><td style="text-align: right;">{row.get('Elevasi', 0):.0f} m</td></tr>
                </table>
                {f"<div style='margin-top:5px; color:#333; font-weight:500; font-size:10px; text-align:center;'>[ Node Acuan Spasial ]</div>" if is_acuan else ""}
            </div>
            """
            
            folium.CircleMarker(
                [r_lat, r_lon], 
                radius=radius_size, 
                color=border_color, 
                weight=border_weight, 
                fill_color=warna_node_cud, 
                fill_opacity=0.95, 
                popup=folium.Popup(html_table_popup, max_width=220)
            ).add_to(peta_lahan)
            
        components.html(peta_lahan._repr_html_(), height=450)

       # TABEL PARAMETER (Dipindah ke Kolom Kiri di Bawah Peta agar ruang termanfaatkan maksimal)
        if hitung_btn and status_hitung == "Sukses":
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h5 style='font-weight: 400; color: #d2e7b9;'>Detail Parameter Geostatistik</h5>", unsafe_allow_html=True)
            
            # Membuat list of dict agar terhindar dari error duplikasi nama kolom (InvalidIndexError)
            tabel_data = []
            
            # 1. Baris Target (Titik Uji)
            row_target = {
                'Desa': f"Target: {t_desa}",
                'Peran': 'Uji',
                'Elevasi': elevasi_target,
                'PH (Aktual)': ph_target,
            }
            # Jika parameter yang dipilih bukan PH, tambahkan kolom aktual untuk parameter tsb
            if parameter_terpilih != 'PH':
                row_target[f"{parameter_terpilih} (Aktual)"] = nilai_aktual
            
            # Tambahkan kolom prediksi dan kecocokan
            row_target[f"Prediksi {parameter_terpilih}"] = round(prediksi_kriging, 2)
            row_target['Kecocokan'] = kesimpulan_inferensi.title()
            tabel_data.append(row_target)
            
            # 2. Baris Acuan (Nearest Neighbors)
            for _, row in titik_acuan_4.iterrows():
                row_acuan = {
                    'Desa': row['Desa'],
                    'Peran': 'Acuan',
                    'Elevasi': row['Elevasi'],
                    'PH (Aktual)': row['PH'],
                }
                # Jika parameter yang dipilih bukan PH, tambahkan kolom aktual untuk parameter tsb
                if parameter_terpilih != 'PH':
                    row_acuan[f"{parameter_terpilih} (Aktual)"] = row[parameter_terpilih]
                    
                # Titik acuan tidak memiliki prediksi, jadi kita beri tanda strip
                row_acuan[f"Prediksi {parameter_terpilih}"] = "-"
                row_acuan['Kecocokan'] = str(row['Kecocokan']).title()
                tabel_data.append(row_acuan)
                
            # Konversi ke DataFrame dan tampilkan
            df_gabungan = pd.DataFrame(tabel_data)
            st.dataframe(df_gabungan, use_container_width=True, hide_index=True)
