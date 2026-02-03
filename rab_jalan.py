import streamlit as st
import pandas as pd
import math

# ==========================================
# GEMS ENGINE V2.5 - ROAD ESTIMATOR PRO (FULL TRANSPARENCY)
# Fitur: Beton + Besi + Bekisting + Detail AHSP + Daftar Harga
# ==========================================

st.set_page_config(page_title="GEMS Road Estimator Pro", layout="wide")

# --- STYLE & HEADER ---
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🛣️ GEMS: RAB Jalan Beton (Rigid Pavement) V2.5")
st.caption("Engineered by The GEMS Grandmaster | Standard: AHSP Bina Marga (SE PUPR 182)")
st.markdown("---")

# ==========================================
# 1. DATABASE KOEFISIEN (ENGINEERING CORE)
# ==========================================
DB_KOEFISIEN = {
    "Beton K-350 (Rigid)": {
        "Semen Portland": {"koef": 386.00, "sat": "Kg"},
        "Pasir Beton": {"koef": 692.00, "sat": "Kg"},
        "Agregat Kasar (Split)": {"koef": 1039.00, "sat": "Kg"},
        "Air": {"koef": 215.00, "sat": "Liter"},
        # Note: Vibrator dll diasumsikan masuk dalam upah borong untuk simplifikasi input user
    },
    "Lean Concrete (LC) K-125": {
        "Semen Portland": {"koef": 276.00, "sat": "Kg"},
        "Pasir Beton": {"koef": 828.00, "sat": "Kg"},
        "Agregat Kasar (Split)": {"koef": 1012.00, "sat": "Kg"},
        "Air": {"koef": 215.00, "sat": "Liter"},
    }
}

# ==========================================
# 2. SIDEBAR INPUT
# ==========================================
with st.sidebar:
    st.header("📐 1. Dimensi Fisik Jalan")
    panjang = st.number_input("Panjang Jalan (m)", value=100.0, step=10.0)
    lebar = st.number_input("Lebar Jalan (m)", value=5.0, step=0.5)
    col_a, col_b = st.columns(2)
    with col_a:
        tebal = st.number_input("Tebal K-350 (cm)", value=25.0) / 100
    with col_b:
        tebal_lc = st.number_input("Tebal LC (cm)", value=10.0) / 100

    st.header("⚙️ 2. Spesifikasi Tulangan")
    # Dowel
    st.markdown("**A. Dowel (Melintang)**")
    jarak_dowel = st.number_input("Jarak Segmen (m)", value=5.0)
    dia_dowel = st.number_input("Dia. Dowel (mm)", value=32)
    pjg_dowel = st.number_input("Pjg Dowel (cm)", value=45) / 100
    jarak_pasang_dowel = st.number_input("Jarak Pasang (cm)", value=30) / 100

    # Tie Bar
    st.markdown("**B. Tie Bar (Memanjang)**")
    pakai_tiebar = st.checkbox("Pakai Tie Bar?", value=True)
    dia_tiebar = st.number_input("Dia. Tie Bar (mm)", value=16)
    pjg_tiebar = st.number_input("Pjg Tie Bar (cm)", value=70) / 100
    jarak_pasang_tiebar = st.number_input("Jarak Pasang TB (cm)", value=75) / 100

    # Wiremesh
    st.markdown("**C. Wiremesh**")
    pakai_wiremesh = st.checkbox("Pakai Wiremesh?", value=False)
    jenis_wiremesh = st.selectbox("Jenis", ["M-6", "M-8", "M-10"])
    berat_wiremesh_map = {"M-6": 2.5, "M-8": 4.5, "M-10": 6.8}

    # Kalkulasi Volume Fisik
    vol_beton = panjang * lebar * tebal
    vol_lc = panjang * lebar * tebal_lc
    luas_bekisting = panjang * tebal * 2 

# ==========================================
# 3. TABS UTAMA
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["💰 Input Harga", "📊 Rekap RAB", "🔍 Detail AHSP", "📋 Daftar Sumber Daya"])

# --- TAB 1: INPUT ---
with tab1:
    st.subheader("Update Harga Satuan Dasar (HSD)")
    st.info("💡 Masukkan harga material real di lokasi proyek (Toko Bangunan/Quarry).")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Material Beton**")
        h_semen = st.number_input("Semen (per Kg)", value=1800, help="Contoh: Semen 50kg = 90rb -> 1800/kg")
        h_pasir = st.number_input("Pasir (per Kg)", value=250, help="Contoh: 1 m3 = 350rb. Berat isi 1400kg -> 250/kg")
        h_split = st.number_input("Split (per Kg)", value=300)
        h_air = st.number_input("Air (per Liter)", value=50)
        
        st.markdown("**Upah & Bekisting**")
        h_upah_cor = st.number_input("Upah Cor + Alat (per m3)", value=150000, help="Harga borong tenaga + sewa molen/vibrator")
        h_bekisting = st.number_input("Bekisting Jadi (per m2)", value=185000, help="Material papan + kaso + paku + upah")

    with c2:
        st.markdown("**Besi & Tulangan**")
        h_besi_polos = st.number_input("Besi Polos (per Kg)", value=14500)
        h_besi_ulir = st.number_input("Besi Ulir (per Kg)", value=15500)
        h_wiremesh = st.number_input("Wiremesh (per Kg)", value=16000)
        h_dudukan = st.number_input("Dudukan/Chair (Ls)", value=2500000)

# --- FUNGSI BANTUAN ---
def hitung_berat_besi(dia, pjg, jml):
    return 0.006165 * (dia ** 2) * pjg * jml

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# --- LOGIKA HITUNG (Global Variables for use in all tabs) ---
# 1. Beton Rigid
mat_rigid = DB_KOEFISIEN["Beton K-350 (Rigid)"]
biaya_mat_rigid = (mat_rigid["Semen Portland"]["koef"] * h_semen) + \
                  (mat_rigid["Pasir Beton"]["koef"] * h_pasir) + \
                  (mat_rigid["Agregat Kasar (Split)"]["koef"] * h_split) + \
                  (mat_rigid["Air"]["koef"] * h_air)
hs_rigid = biaya_mat_rigid + h_upah_cor
total_rigid = hs_rigid * vol_beton

# 2. LC
mat_lc = DB_KOEFISIEN["Lean Concrete (LC) K-125"]
biaya_mat_lc = (mat_lc["Semen Portland"]["koef"] * h_semen) + \
               (mat_lc["Pasir Beton"]["koef"] * h_pasir) + \
               (mat_lc["Agregat Kasar (Split)"]["koef"] * h_split) + \
               (mat_lc["Air"]["koef"] * h_air)
hs_lc = biaya_mat_lc + h_upah_cor
total_lc = hs_lc * vol_lc

# 3. Besi
jml_segmen = math.ceil(panjang / jarak_dowel)
btg_per_segmen = math.ceil(lebar / jarak_pasang_dowel)
berat_dowel = hitung_berat_besi(dia_dowel, pjg_dowel, jml_segmen * btg_per_segmen)
biaya_dowel = berat_dowel * h_besi_polos

berat_tiebar = 0
biaya_tiebar = 0
if pakai_tiebar:
    jml_baris_tiebar = math.ceil(panjang / jarak_pasang_tiebar)
    berat_tiebar = hitung_berat_besi(dia_tiebar, pjg_tiebar, jml_baris_tiebar)
    biaya_tiebar = berat_tiebar * h_besi_ulir

berat_wm = 0
biaya_wm = 0
if pakai_wiremesh:
    berat_wm = (panjang * lebar) * berat_wiremesh_map[jenis_wiremesh]
    biaya_wm = berat_wm * h_wiremesh

# 4. Bekisting
biaya_bekisting = luas_bekisting * h_bekisting

# 5. Grand Total
grand_total = total_rigid + total_lc + biaya_dowel + biaya_tiebar + biaya_wm + biaya_bekisting + h_dudukan


# --- TAB 2: REKAPITULASI ---
with tab2:
    st.subheader("📑 Rekapitulasi Biaya Proyek")
    col_metric1, col_metric2 = st.columns(2)
    col_metric1.metric("GRAND TOTAL RAB", format_rupiah(grand_total))
    col_metric2.metric("Harga per Meter Lari", format_rupiah(grand_total / panjang))

    data_rab = [
        ["1. Beton K-350 (Rigid)", f"{vol_beton:.2f} m³", format_rupiah(hs_rigid), format_rupiah(total_rigid)],
        ["2. Lantai Kerja (LC)", f"{vol_lc:.2f} m³", format_rupiah(hs_lc), format_rupiah(total_lc)],
        ["3. Besi Dowel (Polos)", f"{berat_dowel:.1f} Kg", format_rupiah(h_besi_polos), format_rupiah(biaya_dowel)],
        ["4. Besi Tie Bar (Ulir)", f"{berat_tiebar:.1f} Kg", format_rupiah(h_besi_ulir), format_rupiah(biaya_tiebar)],
        ["5. Wiremesh", f"{berat_wm:.1f} Kg", format_rupiah(h_wiremesh), format_rupiah(biaya_wm)],
        ["6. Bekisting Samping", f"{luas_bekisting:.2f} m²", format_rupiah(h_bekisting), format_rupiah(biaya_bekisting)],
        ["7. Alat Bantu/Dudukan", "1.00 Ls", format_rupiah(h_dudukan), format_rupiah(h_dudukan)],
    ]
    df_rekap = pd.DataFrame(data_rab, columns=["Uraian Pekerjaan", "Volume", "Harga Satuan", "Total Harga"])
    st.table(df_rekap)


# --- TAB 3: DETAIL AHSP ---
with tab3:
    st.subheader("🔍 Analisa Harga Satuan Pekerjaan (AHSP)")
    st.caption("Berikut adalah perhitungan detail bagaimana harga per m³ didapatkan.")
    
    # 1. Detail Rigid
    st.markdown("### 1. Analisa Beton K-350 (Rigid Pavement) per 1 m³")
    
    # Buat Data Dictionary untuk Detail
    ahsp_rigid_data = [
        ["Semen Portland", f"{mat_rigid['Semen Portland']['koef']} Kg", format_rupiah(h_semen), format_rupiah(mat_rigid['Semen Portland']['koef'] * h_semen)],
        ["Pasir Beton", f"{mat_rigid['Pasir Beton']['koef']} Kg", format_rupiah(h_pasir), format_rupiah(mat_rigid['Pasir Beton']['koef'] * h_pasir)],
        ["Split / Kerikil", f"{mat_rigid['Agregat Kasar (Split)']['koef']} Kg", format_rupiah(h_split), format_rupiah(mat_rigid['Agregat Kasar (Split)']['koef'] * h_split)],
        ["Air", f"{mat_rigid['Air']['koef']} Liter", format_rupiah(h_air), format_rupiah(mat_rigid['Air']['koef'] * h_air)],
        ["Upah Cor & Alat (Borong)", "1.00 m³", format_rupiah(h_upah_cor), format_rupiah(h_upah_cor)]
    ]
    
    df_ahsp_rigid = pd.DataFrame(ahsp_rigid_data, columns=["Komponen", "Koefisien", "Harga Dasar", "Jumlah Harga"])
    st.table(df_ahsp_rigid)
    st.success(f"**Total Harga Satuan Jadi K-350 = {format_rupiah(hs_rigid)} / m³**")

    st.markdown("---")

    # 2. Detail LC
    st.markdown("### 2. Analisa Lantai Kerja (LC K-125) per 1 m³")
    ahsp_lc_data = [
        ["Semen Portland", f"{mat_lc['Semen Portland']['koef']} Kg", format_rupiah(h_semen), format_rupiah(mat_lc['Semen Portland']['koef'] * h_semen)],
        ["Pasir Beton", f"{mat_lc['Pasir Beton']['koef']} Kg", format_rupiah(h_pasir), format_rupiah(mat_lc['Pasir Beton']['koef'] * h_pasir)],
        ["Split / Kerikil", f"{mat_lc['Agregat Kasar (Split)']['koef']} Kg", format_rupiah(h_split), format_rupiah(mat_lc['Agregat Kasar (Split)']['koef'] * h_split)],
        ["Air", f"{mat_lc['Air']['koef']} Liter", format_rupiah(h_air), format_rupiah(mat_lc['Air']['koef'] * h_air)],
        ["Upah Cor & Alat (Borong)", "1.00 m³", format_rupiah(h_upah_cor), format_rupiah(h_upah_cor)]
    ]
    
    df_ahsp_lc = pd.DataFrame(ahsp_lc_data, columns=["Komponen", "Koefisien", "Harga Dasar", "Jumlah Harga"])
    st.table(df_ahsp_lc)
    st.success(f"**Total Harga Satuan Jadi LC = {format_rupiah(hs_lc)} / m³**")


# --- TAB 4: DAFTAR SUMBER DAYA ---
with tab4:
    st.subheader("📋 Daftar Harga Satuan Dasar (HSD)")
    st.caption("Rekapitulasi harga dasar Upah, Bahan, dan Alat yang digunakan dalam perhitungan ini.")
    
    data_sumber_daya = [
        # Bahan
        {"Kategori": "Bahan", "Uraian": "Semen Portland", "Satuan": "Kg", "Harga": h_semen},
        {"Kategori": "Bahan", "Uraian": "Pasir Beton", "Satuan": "Kg", "Harga": h_pasir},
        {"Kategori": "Bahan", "Uraian": "Split / Agregat", "Satuan": "Kg", "Harga": h_split},
        {"Kategori": "Bahan", "Uraian": "Air Kerja", "Satuan": "Liter", "Harga": h_air},
        {"Kategori": "Bahan", "Uraian": "Besi Polos", "Satuan": "Kg", "Harga": h_besi_polos},
        {"Kategori": "Bahan", "Uraian": "Besi Ulir", "Satuan": "Kg", "Harga": h_besi_ulir},
        {"Kategori": "Bahan", "Uraian": "Wiremesh", "Satuan": "Kg", "Harga": h_wiremesh},
        # Upah
        {"Kategori": "Upah & Alat", "Uraian": "Upah Cor + Alat (Borong)", "Satuan": "m³", "Harga": h_upah_cor},
        {"Kategori": "Upah & Bahan", "Uraian": "Bekisting (Terpasang)", "Satuan": "m²", "Harga": h_bekisting},
        {"Kategori": "Lumpsum", "Uraian": "Dudukan/Chair/Alat Bantu", "Satuan": "Ls", "Harga": h_dudukan},
    ]
    
    df_sd = pd.DataFrame(data_sumber_daya)
    
    # Tampilkan dengan format
    st.dataframe(
        df_sd.style.format({"Harga": "Rp {:,.0f}"}),
        use_container_width=True,
        hide_index=True
    )
    
    st.info("ℹ️ Daftar ini bisa Anda print sebagai lampiran 'Daftar Harga Satuan Dasar' dalam dokumen penawaran.")
