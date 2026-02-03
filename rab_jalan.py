import streamlit as st
import pandas as pd

# ==========================================
# 1. DATABASE KOEFISIEN (ENGINEERING CORE)
# Referensi: AHSP Bidang Bina Marga (SE PUPR)
# Item: Beton Mutu Sedang fc’ 30 MPa (Setara K-350) untuk Perkerasan Kaku
# ==========================================

DB_KOEFISIEN = {
    "Beton K-350 (Rigid Pavement)": {
        "Tenaga": [
            {"item": "Pekerja", "koef": 1.650, "satuan": "OH"},
            {"item": "Tukang Batu", "koef": 0.275, "satuan": "OH"},
            {"item": "Mandor", "koef": 0.083, "satuan": "OH"},
        ],
        "Bahan": [
            {"item": "Semen Portland", "koef": 386.00, "satuan": "Kg"},
            {"item": "Pasir Beton", "koef": 692.00, "satuan": "Kg"},
            {"item": "Agregat Kasar (Split)", "koef": 1039.00, "satuan": "Kg"},
            {"item": "Air", "koef": 215.00, "satuan": "Liter"},
            {"item": "Plastic Sheet (50 micron)", "koef": 1.05, "satuan": "m2"}, # Bekisting lantai kerja
        ],
        "Alat": [
            {"item": "Concrete Vibrator", "koef": 0.150, "satuan": "Jam"},
            {"item": "Water Tanker", "koef": 0.050, "satuan": "Jam"},
            {"item": "Alat Bantu (Sekop/Gerobak)", "koef": 1.000, "satuan": "Ls"},
        ]
    },
    "Lean Concrete (Lantai Kerja) K-125": {
        "Tenaga": [
            {"item": "Pekerja", "koef": 1.200, "satuan": "OH"},
            {"item": "Tukang Batu", "koef": 0.200, "satuan": "OH"},
        ],
        "Bahan": [
            {"item": "Semen Portland", "koef": 276.00, "satuan": "Kg"},
            {"item": "Pasir Beton", "koef": 828.00, "satuan": "Kg"},
            {"item": "Agregat Kasar (Split)", "koef": 1012.00, "satuan": "Kg"},
             {"item": "Air", "koef": 215.00, "satuan": "Liter"},
        ],
        "Alat": [
             {"item": "Concrete Mixer (Molen)", "koef": 0.250, "satuan": "Jam"},
        ]
    }
}

# ==========================================
# 2. FRONTEND & LOGIC (STREAMLIT)
# ==========================================

st.set_page_config(page_title="GEMS AHSP Calculator", layout="wide")

st.title("🛣️ GEMS: RAB Jalan Beton (Rigid Pavement)")
st.caption("Engineered by The GEMS Grandmaster | Standard: AHSP Bina Marga (SE PUPR No.182)")
st.markdown("---")

# --- SIDEBAR: INPUT DIMENSI JALAN ---
with st.sidebar:
    st.header("📐 Dimensi Jalan")
    panjang = st.number_input("Panjang Jalan (m)", value=100.0, step=10.0)
    lebar = st.number_input("Lebar Jalan (m)", value=5.0, step=0.5)
    tebal = st.number_input("Tebal Beton K-350 (cm)", value=25.0, step=1.0) / 100 # Konversi ke m
    tebal_lc = st.number_input("Tebal Lantai Kerja (LC) (cm)", value=10.0, step=1.0) / 100 # Konversi ke m

    vol_beton = panjang * lebar * tebal
    vol_lc = panjang * lebar * tebal_lc
    
    st.info(f"🔢 **Volume Beton K-350:** {vol_beton:.2f} m³")
    st.info(f"🔢 **Volume LC:** {vol_lc:.2f} m³")

# --- TAB SETUP ---
tab1, tab2 = st.tabs(["💰 Database Harga Dasar", "📊 Hasil RAB & AHSP"])

# --- TAB 1: INPUT HARGA DASAR (DATABASE) ---
with tab1:
    st.subheader("Update Harga Satuan Dasar (HSD) - Lokasi Proyek")
    col1, col2, col3 = st.columns(3)
    
    # Default values (Simulasi Harga Lampung 2026)
    with col1:
        st.markdown("**🛠️ Upah Tenaga (HOK)**")
        h_pekerja = st.number_input("Pekerja / hari", value=120000)
        h_tukang = st.number_input("Tukang / hari", value=150000)
        h_mandor = st.number_input("Mandor / hari", value=180000)

    with col2:
        st.markdown("**🧱 Harga Material**")
        h_semen = st.number_input("Semen (per Kg)", value=1800) # ~90rb/sak
        h_pasir = st.number_input("Pasir Beton (per Kg)", value=250) # ~350rb/m3
        h_split = st.number_input("Split/Kerikil (per Kg)", value=300) # ~400rb/m3
        h_air = st.number_input("Air (per Liter)", value=50)
        h_plastic = st.number_input("Plastic Sheet (per m2)", value=5000)

    with col3:
        st.markdown("**🚜 Harga Sewa Alat**")
        h_vibrator = st.number_input("Vibrator (per Jam)", value=75000)
        h_mixer = st.number_input("Molen/Mixer (per Jam)", value=85000)
        h_tanker = st.number_input("Water Tanker (per Jam)", value=150000)
        h_alatbantu = st.number_input("Alat Bantu (Lumpsum)", value=50000)

    # Dictionary Map untuk mempermudah pemanggilan harga
    HARGA_DASAR = {
        "Pekerja": h_pekerja, "Tukang Batu": h_tukang, "Mandor": h_mandor,
        "Semen Portland": h_semen, "Pasir Beton": h_pasir, "Agregat Kasar (Split)": h_split,
        "Air": h_air, "Plastic Sheet (50 micron)": h_plastic,
        "Concrete Vibrator": h_vibrator, "Water Tanker": h_tanker, 
        "Concrete Mixer (Molen)": h_mixer, "Alat Bantu (Sekop/Gerobak)": h_alatbantu
    }

# --- LOGIKA HITUNG AHSP (BACKEND) ---
def hitung_ahsp(item_pekerjaan):
    data_analisa = DB_KOEFISIEN[item_pekerjaan]
    rincian = []
    total_ahsp = 0
    
    # Loop semua kategori (Tenaga, Bahan, Alat)
    for kategori, items in data_analisa.items():
        subtotal_kategori = 0
        for i in items:
            nama = i["item"]
            koef = i["koef"]
            satuan = i["satuan"]
            
            # Ambil harga dari input user
            harga_satuan = HARGA_DASAR.get(nama, 0)
            
            # Hitung total
            jumlah_harga = koef * harga_satuan
            subtotal_kategori += jumlah_harga
            
            rincian.append({
                "Kategori": kategori,
                "Uraian": nama,
                "Koefisien": koef,
                "Satuan": satuan,
                "Harga Satuan (Rp)": harga_satuan,
                "Jumlah Harga (Rp)": jumlah_harga
            })
        total_ahsp += subtotal_kategori
        
    return total_ahsp, pd.DataFrame(rincian)

# --- TAB 2: HASIL PERHITUNGAN ---
with tab2:
    if st.button("🚀 HITUNG RAB SEKARANG", type="primary"):
        
        # 1. Hitung AHSP Rigid
        hsp_rigid, df_rigid = hitung_ahsp("Beton K-350 (Rigid Pavement)")
        total_rigid = hsp_rigid * vol_beton
        
        # 2. Hitung AHSP LC
        hsp_lc, df_lc = hitung_ahsp("Lean Concrete (Lantai Kerja) K-125")
        total_lc = hsp_lc * vol_lc
        
        # TAMPILKAN REKAPITULASI
        st.subheader("📑 Rekapitulasi RAB")
        
        rekap_data = [
            {"Uraian": "Pekerjaan Beton K-350 (Rigid)", "Vol": vol_beton, "Sat": "m³", "Harga Satuan": hsp_rigid, "Total": total_rigid},
            {"Uraian": "Pekerjaan Lantai Kerja (LC)", "Vol": vol_lc, "Sat": "m³", "Harga Satuan": hsp_lc, "Total": total_lc},
        ]
        df_rekap = pd.DataFrame(rekap_data)
        grand_total = df_rekap["Total"].sum()
        
        # Format Currency
        st.metric(label="GRAND TOTAL RAB", value=f"Rp {grand_total:,.0f}")
        st.table(df_rekap.style.format({"Harga Satuan": "Rp {:,.2f}", "Total": "Rp {:,.2f}"}))
        
        # TAMPILKAN DETAIL AHSP (ANALISA)
        with st.expander("🔍 Lihat Detail Analisa Harga Satuan (AHSP) K-350"):
            st.write(f"**Harga Satuan per m³: Rp {hsp_rigid:,.2f}**")
            st.dataframe(df_rigid.style.format({"Harga Satuan (Rp)": "{:,.2f}", "Jumlah Harga (Rp)": "{:,.2f}"}))
            
        with st.expander("🔍 Lihat Detail Analisa Harga Satuan (AHSP) LC"):
            st.write(f"**Harga Satuan per m³: Rp {hsp_lc:,.2f}**")
            st.dataframe(df_lc.style.format({"Harga Satuan (Rp)": "{:,.2f}", "Jumlah Harga (Rp)": "{:,.2f}"}))
            
        st.success("✅ Perhitungan selesai menggunakan Standar AHSP & Harga Real-time.")
