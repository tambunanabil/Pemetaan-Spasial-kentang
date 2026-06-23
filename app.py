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

# --- 5. UNIFIED DATA READING ENGINE (Membaca Data Excel Secara Cerdas) ---
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
        mapping_status = {
            'Karangtengah': 'Cocok', 'Bakal': 'Cocok', 'Sikunang': 'Cocok',
            'Kepakisan': 'Tidak Sesuai', 'Dieng Kulon': 'Netral'
        }
        df['Kecocokan'] = df['Desa'].map(mapping_status).fillna('Netral')
        
    return df.dropna(subset=['Lat', 'Lon', 'Desa'])

df_kriging = load_kriging_base_data()

# PALET WARNA OKABE-ITO (Color Universal Design - CUD Friendly)
def dapatkan_warna_cud(status):
    lbl = str(status).lower().strip()
    if 'tidak' in lbl or 'kurang' in lbl:
        return '#d55e00'  # Merah Vermilion (Tidak Sesuai)
    elif 'netral' in lbl:
        return '#e69f00'  # Jingga Terang (Netral)
    return '#009e73'      # Hijau Kebiruan (Cocok)

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
    with col1: st.markdown("<h1 style='font-weight: 300;'>Peta Sebaran Koordinat Titik Data Regional (Makro)</h1>", unsafe_allow_html=True)
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
    # --- MODUL MENU 2: INTERPOLASI & INFERENSI AGRONOMIS ---
    # ==========================================
    st.markdown("<h1 style='font-weight: 300;'>Komputasi Ordinary Kriging & Logika Inferensi Lahan</h1>", unsafe_allow_html=True)
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/id/thumb/0/03/Logo_Telkom_University_potrait.png/250px-Logo_Telkom_University_potrait.png", width=80)
    if st.sidebar.button("‹ Kembali ke Beranda", key="back_from_side", type="secondary", use_container_width=True):
        st.session_state.current_page = "Beranda Utama"; st.rerun()
        
    st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    st.sidebar.markdown("### Parameter Komputasi")
    parameter_terpilih = st.sidebar.selectbox("Variabel Nutrisi:", ["N", "P", "K", "PH"])
    
    df_kriging_unique = df_kriging.groupby(['Desa', 'Lat', 'Lon', 'Kecocokan']).mean(numeric_only=True).reset_index()
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
    delta_elevasi = abs(elevasi_target - elevasi_ref_rata)
    
    prediksi_kriging, kriging_variance, error_mae = 0.0, 0.0, 0.0
    status_hitung = ""
    
    if hitung_btn:
        try:
            # Komputasi model matematika Ordinary Kriging univariat hara
            OK = OrdinaryKriging(X_base, Y_base, Z_base, variogram_model=model_variogram, verbose=False, enable_plotting=False)
            z_pred, sigmasq = OK.execute('points', [t_lon], [t_lat])
            prediksi_kriging, kriging_variance = z_pred[0], sigmasq[0]
            error_mae = abs(prediksi_kriging - nilai_aktual)
            status_hitung = "Sukses"
        except Exception as e:
            status_hitung = f"Galat: {e}"

    kolom_kiri, kolom_kanan = st.columns([1.55, 1.45])
    with kolom_kiri:
        st.markdown("<h4 style='font-weight: 400; color: #d2e7b9;'>Peta Lokasi Titik Uji LOOCV & Parameter Pengukuran</h4>", unsafe_allow_html=True)
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
                <b style="color:#cc3333;">📍 BLIND TARGET UJI</b><br>
                <b>Desa: {t_desa}</b><br>
                pH: {ph_target:.2f}<br>
                Elevasi: {elevasi_target:.0f} mdpl
            </div>""", max_width=250),
            icon=folium.Icon(color='red', icon='location', prefix='fa')
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
                <b style="color:{warna_node_cud}; font-size:12px; display:block; margin-bottom:5px;">🏠 Sentra: {row['Desa']}</b>
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
                {f"<div style='margin-top:5px; color:#333; font-weight:500; font-size:10px; text-align:center;'>🌐 Node Acuan Terdekat</div>" if is_acuan else ""}
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
            
        components.html(peta_lahan._repr_html_(), height=500)
        
    with kolom_kanan:
        st.markdown("<h4 style='font-weight: 400; color: #d2e7b9;'>Karakteristik Titik Geografis & Inferensi</h4>", unsafe_allow_html=True)
        
        # Penentuan batas ambang ekstrim (Min-Max) dari 4 titik acuan spasial terdekat
        min_ph_acuan, max_ph_acuan = titik_acuan_4['PH'].min(), titik_acuan_4['PH'].max()
        min_el_acuan, max_el_acuan = titik_acuan_4['Elevasi'].min(), titik_acuan_4['Elevasi'].max()
        
        ph_masuk_range = min_ph_acuan <= ph_target <= max_ph_acuan
        elevasi_masuk_range = min_el_acuan <= elevasi_target <= max_el_acuan
        
        status_mayoritas = titik_acuan_4['Kecocokan'].mode()[0]

        # =========================================================================
        # 🧠 MESIN INFERENSI BARU: Prioritas Spasial (Range) -> Hukum Agronomi
        # =========================================================================
        if ph_masuk_range and elevasi_masuk_range:
            # Skenario 1: Titik uji identik dengan karakteristik lingkungan 4 tetangganya
            kesimpulan_inferensi = f"DIASUMSIKAN {status_mayoritas.upper()}"
            warna_inferensi = dapatkan_warna_cud(status_mayoritas)
            keterangan_logika = f"Parameter ketinggian dan pH Titik Uji **masuk dalam range** 4 titik acuan terdekat. Titik ini diputuskan mewarisi status mayoritas tetangganya, yaitu: **{status_mayoritas}**."
        else:
            # Skenario 2: Titik uji di luar range spasial -> Evaluasi pakai hukum agronomi
            if elevasi_target < 1000:
                kesimpulan_inferensi = "TIDAK COCOK"
                warna_inferensi = "#d55e00"  # Merah
                keterangan_logika = "Data di luar range referensi. Karena elevasi < 1000 mdpl, maka **kemungkinan tidak cocok** untuk kentang."
            elif 1000 <= elevasi_target <= 1500:
                if ph_target > 7.0:
                    kesimpulan_inferensi = "BERPOTENSI COCOK"
                    warna_inferensi = "#e69f00"  # Jingga
                    keterangan_logika = "Data di luar range referensi. Namun karena elevasi 1000-1500 mdpl didukung pH > 7, maka **berpotensi cocok**."
                else:
                    kesimpulan_inferensi = "TIDAK COCOK"
                    warna_inferensi = "#d55e00"  # Merah
                    keterangan_logika = "Data di luar range referensi. Ketinggian menengah (1000-1500 mdpl) namun terhambat oleh kondisi pH ≤ 7."
            elif elevasi_target > 1500:
                if ph_target > 6.5:
                    kesimpulan_inferensi = "KEMUNGKINAN COCOK"
                    warna_inferensi = "#009e73"  # Hijau
                    keterangan_logika = "Data di luar range referensi. Karena elevasi ideal (>1500 mdpl) dan didukung pH > 6.5, maka **kemungkinan cocok**."
                else:
                    kesimpulan_inferensi = "TIDAK COCOK"
                    warna_inferensi = "#d55e00"  # Merah
                    keterangan_logika = "Data di luar range referensi. Ketinggian ideal (>1500 mdpl) namun kondisi tanah cenderung terlalu masam (pH ≤ 6.5)."

        # Tampilkan visualisasi parameter dasar lokasi
        k1, k2 = st.columns(2)
        with k1: st.metric("pH Lapangan Aktual", f"{ph_target:.2f}")
        with k2: st.metric("Ketinggian Elevasi", f"{elevasi_target:.0f} mdpl")
        
        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 15px 0;'>", unsafe_allow_html=True)
        
        if hitung_btn:
            st.markdown("##### 📊 Hasil Analisis Klasifikasi Inferensi:")
            st.markdown(f"""
            <div style="background-color: rgba(19, 27, 21, 0.7); padding: 18px; border-radius: 6px; border-left: 5px solid {warna_inferensi}; margin-top: 5px; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #8da68c; font-size: 0.85em; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">Keputusan Evaluasi Lahan:</span>
                <b style="color: {warna_inferensi}; font-size: 1.3em; display: block; margin-top: 4px; letter-spacing: 0.5px;">{kesimpulan_inferensi}</b>
                <i style="font-size: 0.88em; color: #cddbc0; display:block; margin-top:8px; line-height: 1.5; text-align: justify;">{keterangan_logika}</i>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📈 Estimasi Kuantitatif Parameter & Metrik Galat:")
            
            if status_hitung == "Sukses":
                m1, m2 = st.columns(2)
                with m1: st.metric(f"Prediksi Estimasi {parameter_terpilih}", f"{prediksi_kriging:.2f}")
                with m2: st.metric(f"Data Aktual Lapangan", f"{nilai_aktual:.2f}")
                
                c1, c2 = st.columns(2)
                with c1: st.metric("Mean Absolute Error (MAE)", f"{error_mae:.2f}")
                with c2: st.metric("Normalized Error (NMAE)", f"{(error_mae / df_kriging_unique[parameter_terpilih].mean()) * 100:.2f} %")
                
                st.markdown(f"""<div style="background-color: rgba(19, 27, 21, 0.45); padding: 15px; border-radius: 6px; border-left: 3px solid #a3bfa2; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.03);"><b style="color: #d2e7b9; font-size:0.95em;">Catatan Validasi Spasial</b><br><i style="font-size: 0.85em; color: #8da68c; display:block; margin-top:5px; line-height: 1.5;">Evaluasi model univariat menunjukkan variabilitas sebaran hara makro pada grid mikro sentra Dieng. Perbedaan \u0394H terbukti tidak berkorelasi linier terhadap fluktuasi galat prediksi.</i></div>""", unsafe_allow_html=True)
            else: 
                st.error(status_hitung)
        else: 
            st.info("Silakan tentukan variabel nutrisi dan target node di sidebar, lalu klik 'Hitung Estimasi Spasial' untuk memulai kalkulasi dan memunculkan hasil inferensi kesesuaian lahan.")
