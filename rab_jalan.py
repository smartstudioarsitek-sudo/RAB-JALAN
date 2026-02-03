import streamlit as st
import pandas as pd
import math

# ==========================================
# GEMS ENGINE V2.0 - ROAD ESTIMATOR PRO
# Fitur: Beton + LC + Tulangan (Dowel/Tie Bar/Wiremesh) + Bekisting
# ==========================================

st.set_page_config(page_title="GEMS Road Estimator Pro", layout="wide")

# --- JUDUL APLIKASI ---
st.title("🛣️ GEMS: RAB Jalan Beton (Rigid Pavement) V2.0")
st.caption("Engineered by The GEMS Grandmaster | Includes: Dowel, Tie Bar, Wiremesh & Formwork")
st.markdown("---")

# ==========================================
# 1. DATABASE KOEFISIEN (ENGINEERING CORE)
# ==========================================
DB_KOEFISIEN = {
    "Beton K-350 (Rigid)": {
        "Semen Portland": 386.00, "Pasir Beton": 692.00, 
        "Agregat Kasar (Split)": 1039.00, "Air": 215.00,
        "Concrete Vibrator": 0.150, "Upah Cor (Borong)": 1.0 
    },
    "Lean Concrete (LC) K-125": {
        "Semen Portland": 276.00, "Pasir Beton": 828.00, 
        "Agregat Kasar (Split)": 1012.00, "Air": 215.00,
        "Upah Cor (Borong)": 1.0
    }
}

# ==========================================
# 2. SIDEBAR INPUT (DIMENSI & TEKNIS)
# ==========================================
with st.sidebar:
    st.header("📐 1. Dimensi Fisik Jalan")
    panjang = st.number_input("Panjang Jalan (m)", value=100.0, step=10.0)
    lebar = st.number_input("Lebar Jalan (m)", value=5.0, step=0.5)
    tebal = st.number_input("Tebal Beton K-350 (cm)", value=25.0) / 100
    tebal_lc = st.number_input("Tebal LC (cm)", value=10.0) / 100

    st.header("⚙️ 2. Spesifikasi Tulangan")
    # Dowel Specs
    st.markdown("**A. Dowel (Sambungan Melintang)**")
    jarak_dowel = st.number_input("Jarak Antar Sambungan/Segmen (m)", value=5.0)
    dia_dowel = st.number_input("Diameter Dowel (mm) - Polos", value=32)
    pjg_dowel = st.number_input("Panjang 1 btg Dowel (cm)", value=45) / 100
    jarak_pasang_dowel = st.number_input("Jarak pemasangan Dowel (cm)", value=30) / 100

    # Tie Bar Specs
    st.markdown("**B. Tie Bar (Sambungan Memanjang)**")
    pakai_tiebar = st.checkbox("Pakai Tie Bar?", value=True)
    dia_tiebar = st.number_input("Diameter Tie Bar (mm) - Ulir", value=16)
    pjg_tiebar = st.number_input("Panjang 1 btg Tie Bar (cm)", value=70) / 100
    jarak_pasang_tiebar = st.number_input("Jarak pemasangan Tie Bar (cm)", value=75) / 100

    # Wiremesh Specs
    st.markdown("**C. Wiremesh & Bekisting**")
    pakai_wiremesh = st.checkbox("Pakai Wiremesh (1 Lapis)?", value=False)
    jenis_wiremesh = st.selectbox("Jenis Wiremesh", ["M-6", "M-8", "M-10"])
    
    # Mapping berat wiremesh (kg/m2) estimasi
    berat_wiremesh_map = {"M-6": 2.5, "M-8": 4.5, "M-10": 6.8}
    
    # Hitung Volume Basic
    vol_beton = panjang * lebar * tebal
    vol_lc = panjang * lebar * tebal_lc
    luas_bekisting = panjang * tebal * 2 # Kiri dan Kanan

    st.info(f"Volume Beton: {vol_beton:.2f} m³")
    st.info(f"Luas Bekisting: {luas_bekisting:.2f} m²")

# ==========================================
# 3. INPUT HARGA & LOGIKA
# ==========================================
tab1, tab2 = st.tabs(["💰 Input Harga Satuan", "📊 Hasil RAB Lengkap"])

with tab1:
    st.subheader("Update Harga Satuan Dasar (HSD)")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Material Beton**")
        h_semen = st.number_input("Semen (per Kg)", value=1800)
        h_pasir = st.number_input("Pasir (per Kg)", value=250)
        h_split = st.number_input("Split (per Kg)", value=300)
        h_air = st.number_input("Air (per Liter)", value=50)
        
        st.markdown("**Upah & Bekisting**")
        h_upah_cor = st.number_input("Upah Cor Borongan (per m3)", value=150000, help="Termasuk alat")
        h_bekisting = st.number_input("Bekisting Jadi (per m2)", value=185000, help="Material kayu/baja + upah pasang")

    with c2:
        st.markdown("**Besi & Tulangan**")
        h_besi_polos = st.number_input("Besi Polos (per Kg)", value=14500)
        h_besi_ulir = st.number_input("Besi Ulir (per Kg)", value=15500)
        h_wiremesh = st.number_input("Wiremesh (per Kg)", value=16000)
        h_dudukan = st.number_input("Dudukan/Chair (Lumpsum)", value=2500000, help="Biaya kawat, dudukan besi, plastik cor")

# --- FUNGSI HITUNG BERAT BESI ---
def hitung_berat_besi(diameter_mm, panjang_m, jumlah_batang):
    # Rumus: 0.006165 * D^2 * L * Jml
    berat_per_m = 0.006165 * (diameter_mm ** 2)
    return berat_per_m * panjang_m * jumlah_batang

# --- LOGIKA UTAMA ---
with tab2:
    if st.button("🚀 HITUNG RAB LENGKAP", type="primary"):
        
        # A. HITUNG BETON (RIGID + LC)
        # Simple AHSP Logic for Material
        biaya_mat_rigid = (DB_KOEFISIEN["Beton K-350 (Rigid)"]["Semen Portland"] * h_semen) + \
                          (DB_KOEFISIEN["Beton K-350 (Rigid)"]["Pasir Beton"] * h_pasir) + \
                          (DB_KOEFISIEN["Beton K-350 (Rigid)"]["Agregat Kasar (Split)"] * h_split) + \
                          (DB_KOEFISIEN["Beton K-350 (Rigid)"]["Air"] * h_air)
        
        harga_satuan_rigid = biaya_mat_rigid + h_upah_cor
        total_rigid = harga_satuan_rigid * vol_beton

        biaya_mat_lc = (DB_KOEFISIEN["Lean Concrete (LC) K-125"]["Semen Portland"] * h_semen) + \
                       (DB_KOEFISIEN["Lean Concrete (LC) K-125"]["Pasir Beton"] * h_pasir) + \
                       (DB_KOEFISIEN["Lean Concrete (LC) K-125"]["Agregat Kasar (Split)"] * h_split)
        
        harga_satuan_lc = biaya_mat_lc + h_upah_cor
        total_lc = harga_satuan_lc * vol_lc

        # B. HITUNG BESI DOWEL (Polos)
        jml_segmen = math.ceil(panjang / jarak_dowel) # Pembulatan ke atas
        btg_per_segmen = math.ceil(lebar / jarak_pasang_dowel)
        total_btg_dowel = jml_segmen * btg_per_segmen
        berat_dowel = hitung_berat_besi(dia_dowel, pjg_dowel, total_btg_dowel)
        biaya_dowel = berat_dowel * h_besi_polos

        # C. HITUNG BESI TIE BAR (Ulir)
        berat_tiebar = 0
        biaya_tiebar = 0
        if pakai_tiebar:
            jml_baris_tiebar = math.ceil(panjang / jarak_pasang_tiebar)
            total_btg_tiebar = jml_baris_tiebar # Asumsi 1 lajur tengah
            berat_tiebar = hitung_berat_besi(dia_tiebar, pjg_tiebar, total_btg_tiebar)
            biaya_tiebar = berat_tiebar * h_besi_ulir

        # D. HITUNG WIREMESH
        biaya_wiremesh = 0
        berat_total_wm = 0
        if pakai_wiremesh:
            luas_area = panjang * lebar
            kg_per_m2 = berat_wiremesh_map[jenis_wiremesh]
            berat_total_wm = luas_area * kg_per_m2
            biaya_wiremesh = berat_total_wm * h_wiremesh

        # E. HITUNG BEKISTING
        biaya_bekisting = luas_bekisting * h_bekisting

        # F. REKAPITULASI
        grand_total = total_rigid + total_lc + biaya_dowel + biaya_tiebar + biaya_wiremesh + biaya_bekisting + h_dudukan

        # --- TAMPILAN HASIL ---
        st.subheader("📑 Rekapitulasi Biaya Proyek")
        st.metric("ESTIMASI BIAYA TOTAL", f"Rp {grand_total:,.0f}")

        # Dataframe Tampilan
        data_rab = [
            ["1. Pekerjaan Beton K-350", f"{vol_beton:.2f} m³", f"Rp {harga_satuan_rigid:,.0f}", f"Rp {total_rigid:,.0f}"],
            ["2. Pekerjaan Lantai Kerja (LC)", f"{vol_lc:.2f} m³", f"Rp {harga_satuan_lc:,.0f}", f"Rp {total_lc:,.0f}"],
            ["3. Besi Dowel (Ruji)", f"{berat_dowel:.1f} Kg", f"Rp {h_besi_polos:,.0f}", f"Rp {biaya_dowel:,.0f}"],
            ["4. Besi Tie Bar (Pengikat)", f"{berat_tiebar:.1f} Kg", f"Rp {h_besi_ulir:,.0f}", f"Rp {biaya_tiebar:,.0f}"],
            ["5. Wiremesh", f"{berat_total_wm:.1f} Kg", f"Rp {h_wiremesh:,.0f}", f"Rp {biaya_wiremesh:,.0f}"],
            ["6. Bekisting Samping", f"{luas_bekisting:.2f} m²", f"Rp {h_bekisting:,.0f}", f"Rp {biaya_bekisting:,.0f}"],
            ["7. Alat Bantu & Dudukan", "1.00 Ls", f"Rp {h_dudukan:,.0f}", f"Rp {h_dudukan:,.0f}"],
        ]

        df_show = pd.DataFrame(data_rab, columns=["Uraian Pekerjaan", "Volume", "Harga Satuan", "Total Harga"])
        st.table(df_show)

        # Download Button Placeholder
        st.caption("✅ Perhitungan V2.0 mencakup struktur besi & bekisting.")
