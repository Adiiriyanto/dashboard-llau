import streamlit as st
import pandas as pd
import re

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Dashboard LLAU Rendani", layout="wide")

# =========================
# STYLE (PRO)
# =========================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0b132b, #1c2541); }
section[data-testid="stSidebar"] { background-color: #111827; }
.header { display: flex; align-items: center; gap: 15px; }
.metric-card {
    background: #1f2937; padding: 18px; border-radius: 12px;
    text-align: center; border: 1px solid #374151;
}
.metric-value { font-size: 30px; font-weight: bold; }
.blue { color: #3b82f6; }
.green { color: #22c55e; }
.red { color: #ef4444; }
.orange { color: #f59e0b; }
h1, h2, h3 { color: #e5e7eb; }
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER + RESET
# =========================
col1, col2 = st.columns([8,2])
with col1:
    st.markdown("""
    <div class="header">
        <img src="logo.png" width="60">
        <div>
            <h2>Dashboard Operasional</h2>
            <h3>LLAU Rendani Airport</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    if st.button("🔄 Reset"):
        st.rerun()

# =========================
# SIDEBAR
# =========================
st.sidebar.image("logo.png", width=120)
st.sidebar.markdown("### LLAU Rendani")

# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload Data Excel", type=["xlsx"])

if file:

    # =========================
    # LOAD (support multi-header)
    # =========================
    try:
        df = pd.read_excel(file, header=[0,1])
        multi = True
    except:
        df = pd.read_excel(file)
        multi = False

    def clean(x):
        return re.sub(r'\s+', ' ', str(x)).strip().lower()

    if multi:
        df.columns = [clean(a) + "_" + clean(b) for a,b in df.columns]
    else:
        df.columns = [clean(c) for c in df.columns]

    def find(k):
        for c in df.columns:
            if k in c:
                return c
        return None

    # Kolom utama
    col_tgl   = find("tanggal")
    col_mask  = find("operator") or find("maskapai")
    col_jns   = find("jenis") or find("pergerakan")

    col_dew   = find("dewasa")
    col_anak  = find("anak")
    col_bayi  = find("bayi")

    # Transit (coba deteksi per kategori dulu)
    col_t_dew  = None
    col_t_anak = None
    col_t_bayi = None
    for c in df.columns:
        if "transit" in c and "dewasa" in c:
            col_t_dew = c
        if "transit" in c and "anak" in c:
            col_t_anak = c
        if "transit" in c and "bayi" in c:
            col_t_bayi = c

    # Fallback: transit total (jika tidak ada rinciannya)
    col_t_total = find("transit")

    col_kargo = find("kargo")

    # Validasi minimal
    if not col_tgl or not col_mask:
        st.error("Format kolom tidak dikenali")
        st.write(df.columns)
        st.stop()

    # =========================
    # BENTUK DATA BERSIH
    # =========================
    data = pd.DataFrame({
        "Tanggal": df[col_tgl],
        "Maskapai": df[col_mask],
        "Jenis": df[col_jns] if col_jns else "D",
        "Dewasa": df[col_dew] if col_dew else 0,
        "Anak": df[col_anak] if col_anak else 0,
        "Bayi": df[col_bayi] if col_bayi else 0,
        "Transit_Dewasa": df[col_t_dew] if col_t_dew else 0,
        "Transit_Anak": df[col_t_anak] if col_t_anak else 0,
        "Transit_Bayi": df[col_t_bayi] if col_t_bayi else 0,
        "Transit_Total_Fallback": df[col_t_total] if col_t_total else 0,
        "Kargo": df[col_kargo] if col_kargo else 0
    })

    # =========================
    # CLEAN TIPE DATA
    # =========================
    data["Tanggal"] = pd.to_datetime(data["Tanggal"], errors="coerce", dayfirst=True)
    data = data.dropna(subset=["Tanggal"])

    data["Maskapai"] = data["Maskapai"].astype(str).str.upper().str.strip()
    data["Jenis"] = data["Jenis"].astype(str).str.upper().str.strip()

    for c in ["Dewasa","Anak","Bayi","Transit_Dewasa","Transit_Anak","Transit_Bayi","Transit_Total_Fallback","Kargo"]:
        data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)

    # =========================
    # PERHITUNGAN FINAL (FIX)
    # =========================
    # Tentukan transit total yang dipakai
    if data[["Transit_Dewasa","Transit_Anak","Transit_Bayi"]].sum().sum() > 0:
        data["Transit_Total"] = data["Transit_Dewasa"] + data["Transit_Anak"] + data["Transit_Bayi"]
    else:
        data["Transit_Total"] = data["Transit_Total_Fallback"]

    # 🔴 PERBAIKAN ANDA:
    # Dewasa bersih = Dewasa - Transit Dewasa
    data["Dewasa_Bersih"] = (data["Dewasa"] - data["Transit_Dewasa"]).clip(lower=0)

    # Dewasa + Anak bersih = (Dewasa + Anak) - Transit Total
    data["Total_Penumpang"] = ((data["Dewasa"] + data["Anak"]) - data["Transit_Total"]).clip(lower=0)

    # =========================
    # FILTER SIDEBAR
    # =========================
    st.sidebar.header("Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(data["Maskapai"].unique()))
    jenis = st.sidebar.selectbox("Jenis", ["SEMUA","D","A"])

    mode = st.sidebar.radio("Tanggal", ["1 Hari","Rentang"])

    min_d = data["Tanggal"].min().date()
    max_d = data["Tanggal"].max().date()

    if mode == "1 Hari":
        d = st.sidebar.date_input("Tanggal", min_d)
        start = pd.to_datetime(d)
        end = start
    else:
        dr = st.sidebar.date_input("Rentang", (min_d, max_d))
        start = pd.to_datetime(dr[0])
        end = pd.to_datetime(dr[1])

    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa + Anak","Bayi","Transit","Kargo"]
    )

    # =========================
    # FILTER DATA
    # =========================
    f = data.copy()
    f = f[f["Maskapai"] == maskapai]

    if jenis != "SEMUA":
        f = f[f["Jenis"] == jenis]

    f = f[(f["Tanggal"] >= start) & (f["Tanggal"] <= end)]

    # =========================
    # HASIL (SESUAI KATEGORI)
    # =========================
    if kategori == "Dewasa":
        f["Hasil"] = f["Dewasa_Bersih"]               # 🔴 pakai rumus baru
    elif kategori == "Dewasa + Anak":
        f["Hasil"] = f["Total_Penumpang"]             # 🔴 pakai rumus baru
    elif kategori == "Bayi":
        f["Hasil"] = f["Bayi"]
    elif kategori == "Transit":
        f["Hasil"] = f["Transit_Total"]
    elif kategori == "Kargo":
        f["Hasil"] = f["Kargo"]
    else:
        f["Hasil"] = f["Total_Penumpang"]

    total = int(f["Hasil"].sum())

    # =========================
    # KPI
    # =========================
    st.subheader("📊 KPI Utama")

    c1, c2, c3, c4 = st.columns(4)

    def card(title, value, color):
        st.markdown(f"""
        <div class="metric-card">
            <div>{title}</div>
            <div class="metric-value {color}">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    with c1:
        card("Total Penumpang", int(data["Total_Penumpang"].sum()), "blue")
    with c2:
        card("Flight", len(data), "orange")
    with c3:
        card("Transit", int(data["Transit_Total"].sum()), "green")
    with c4:
        card("Kargo", int(data["Kargo"].sum()), "red")

    # =========================
    # HASIL PENCARIAN
    # =========================
    st.subheader("📌 Hasil Pencarian")
    card("Total Hasil", total, "green" if total > 0 else "red")

    # =========================
    # GRAFIK
    # =========================
    st.subheader("📈 Tren Penumpang")
    st.line_chart(data.groupby(data["Tanggal"].dt.date)["Total_Penumpang"].sum())

    # =========================
    # TABEL
    # =========================
    st.subheader("📋 Detail Data")
    st.dataframe(f, use_container_width=True)

else:
    st.info("Upload file Excel untuk mulai")
