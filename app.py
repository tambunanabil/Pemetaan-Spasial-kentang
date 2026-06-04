import streamlit as st
import pandas as pd
import numpy as np
import folium
import streamlit.components.v1 as components
import os
from pykrige.ok import OrdinaryKriging

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GIS Pertanian Presisi", layout="wide")

# --- 1. LOAD & PREPARASI DATA ---
@st.cache_data
def load_and_prepare_data():
    # Jalur file disesuaikan untuk deployment cloud (relatif)
    path = 'Data_Kriging.xlsx'
    
    # Fallback ke /content/ jika masih di-run di Colab
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

# --- 2. ARSITEKTUR UI DASHBOARD ---
st.title("Sistem Informasi Spasial Kesesuaian Lahan Kentang")
st.markdown("Implementasi Metode *Ordinary Kriging* untuk Analisis Distribusi Hara Makro")
st.markdown("---")

if df_clean is None or df_clean.empty:
    st.error("Sistem tidak dapat menemukan berkas dataset 'Data_Kriging.xlsx'. Pastikan berkas tersedia pada direktori yang tepat.")
else:
    # PANEL SIDEBAR
    st.sidebar.markdown("### Konfigurasi Geostatistik")
    parameter_terpilih = st.sidebar.selectbox("Parameter Observasi:", ["N", "P", "K", "PH"])
    opsi_desa = [f"{row['Desa']} ({row['Lat']:.5f}, {row['Lon']:.5f})" for _, row in df_clean.iterrows()]
    pilihan_target = st.sidebar.selectbox("Validasi Silang (LOOCV Target):", opsi_desa)
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("### Model Autokorelasi")
    st.sidebar.info("Sistem menggunakan Semivariogram untuk memodelkan autokorelasi spasial antar titik referensi.")
    model_variogram = st.sidebar.selectbox("Fungsi Variogram:", ["linear", "spherical", "exponential", "gaussian"])
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    hitung_btn = st.sidebar.button("Eksekusi Pemodelan Spasial", type="primary", use_container_width=True)
    
    # PERSIAPAN DATA TARGET & BASE
    idx_target = opsi_desa.index(pilihan_target)
    target_node = df_clean.iloc[idx_target]
    t_lat, t_lon = float(target_node['Lat']), float(target_node['Lon'])
    nilai_aktual = float(target_node[parameter_terpilih])
    
    base_data = df_clean.drop(df_clean.index[idx_target]).copy()
    
    # --- 3. ALGORITMA ORDINARY KRIGING ---
    X_base = base_data['Lon'].values
    Y_base = base_data['Lat'].values
    Z_base = base_data[parameter_terpilih].values
    
    prediksi_kriging = 0.0
    kriging_variance = 0.0
    error_mae = 0.0
    status_hitung = ""
    
    if hitung_btn:
        try:
            OK = OrdinaryKriging(
                X_base, Y_base, Z_base,
                variogram_model=model_variogram,
                verbose=False,
                enable_plotting=False
            )
            z_pred, sigmasq = OK.execute('points', [t_lon], [t_lat])
            
            prediksi_kriging = z_pred[0]
            kriging_variance = sigmasq[0]
            error_mae = abs(prediksi_kriging - nilai_aktual)
            status_hitung = "Sukses"
        except Exception as e:
            status_hitung = f"Galat Komputasi: {e}"
            prediksi_kriging = np.nan

    # TATA LETAK UTAMA DASHBOARD
    kolom_kiri, kolom_kanan = st.columns([1.5, 1.5])
    
    with kolom_kiri:
        st.markdown("#### Pemetaan Visual Citra Satelit")
        peta_lahan = folium.Map(
            location=[float(df_clean['Lat'].mean()), float(df_clean['Lon'].mean())], zoom_start=14,
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri'
        )
        
        for _, row in df_clean.iterrows():
            r_lat, r_lon = float(row['Lat']), float(row['Lon'])
            if r_lat == t_lat and r_lon == t_lon:
                folium.Marker([r_lat, r_lon], popup=f"<b>LOKASI UJI: {row['Desa']}</b>", icon=folium.Icon(color='red', icon='info-sign')).add_to(peta_lahan)
            else:
                html_popup = f"""
                <div style="font-family: Arial, sans-serif; font-size: 13px; color: #333; width: 160px;">
                    <div style="background-color: #2c3e50; color: white; padding: 5px; text-align: center; font-weight: bold; border-radius: 3px;">
                        Referensi: {row['Desa']}
                    </div>
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
                with c1: 
                    st.metric("Mean Absolute Error (MAE)", f"{error_mae:.2f} Unit")
                with c2: 
                    mean_lahan = df_clean[parameter_terpilih].mean()
                    nmae = (error_mae / mean_lahan) * 100
                    st.metric("Normalized Error (NMAE)", f"{nmae:.2f} %", delta_color="inverse")
                
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 13px; color: #2c3e50; border-left: 4px solid #2980b9; margin-bottom: 20px;">
                <b style="font-size: 14px;">Interpretasi Geostatistik:</b><br>
                Varians Kriging (Ketidakpastian): <b>{kriging_variance:.4f}</b><br><br>
                <i>Catatan: Tingkat akurasi pemodelan spasial ini direpresentasikan melalui Mean Absolute Error (MAE). Perhitungan NMAE (Normalized Mean Absolute Error) disertakan sebagai metrik pendamping guna menormalisasi efek pembagi bernilai kecil pada data lapangan.</i>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**Matriks Data Referensi Geospasial:**")
                tabel_base = base_data[['Desa', 'Lat', 'Lon', parameter_terpilih]].copy()
                st.dataframe(tabel_base, use_container_width=True)
            else:
                st.error(status_hitung)
                st.warning("Kurva Semivariogram gagal konvergen. Disarankan untuk menggunakan model 'Linear' pada dataset dengan densitas sampel yang rendah.")
        else:
            st.info("Sistem dalam status siaga. Silakan tetapkan parameter dan lahan validasi, kemudian klik tombol eksekusi pada panel sebelah kiri untuk memulai pemodelan spasial.")