import streamlit as st
import pandas as pd
import re

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}
section[data-testid="stSidebar"] {
    background-color: #111827;
}
.metric-card {
    background: #1f2937;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #374151;
}
.metric-value {
    font-size: 28px;
    font-weight: bold;
}
.green { color: #22c55e; }
.red { color: #ef4444; }
.blue { color: #3b82f6; }
.orange { color: #f59e0b; }
h1, h2, h3 { color: #e5e7eb; }
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
col1, col2 = st.columns([8,2])

with col1:
    st.title("✈️ Dashboard Rekonsiliasi Data LLAU Rendani Airport")

with col2:
    if st.button("🔄 Reset"):
        st.rerun()

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("### ✈️ LLAU Rendani Airport")
st.sidebar.markdown("---")

# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload Data Excel", type=["xlsx"])

if file:

    # =========================
    # LOAD EXCEL
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

    # =========================
    # DETEKSI KOLOM
    # =========================
    def find(keyword):
        return next((c for c in df.columns if keyword in c), None)

    col_tgl = find("tanggal")
    col_mask = find("maskapai") or find("operator")
    col_jns = find("pergerakan") or find("jenis")

    col_flight = find("nomor penerbangan") or find("flight")

    col_dew = find("dewasa")
    col_anak = find("anak")
    col_bayi = find("bayi")

    col_transit_dewasa = next((c for c in df.columns if "transit" in c and "dewasa" in c), None)
    col_transit_total = find("transit")

    col_kargo = find("kargo")

    # =========================
    # DATAFRAME
    # =========================
    data = pd.DataFrame({
        "Tanggal": df[col_tgl],
        "Maskapai": df[col_mask],
        "Pergerakan": df[col_jns] if col_jns else "D",
        "No Flight Raw": df[col_flight] if col_flight else "",
        "Dewasa": df[col_dew] if col_dew else 0,
        "Anak": df[col_anak] if col_anak else 0,
        "Bayi": df[col_bayi] if col_bayi else 0,
        "Transit_Dewasa": df[col_transit_dewasa] if col_transit_dewasa else 0,
        "Transit_Total": df[col_transit_total] if col_transit_total else 0,
        "Kargo": df[col_kargo] if col_kargo else 0
    })

    # =========================
    # CLEAN
    # =========================
    data["Tanggal"] = pd.to_datetime(data["Tanggal"], errors="coerce")
    data = data.dropna()

    data["Pergerakan"] = data["Pergerakan"].astype(str).str.upper().replace({
        "D":"Departure","A":"Arrival"
    })

    def extract_flight(x):
        x = str(x).upper()
        match = re.search(r'[A-Z]{1,3}[0-9]{2,4}', x)
        return match.group(0) if match else "UNKNOWN"

    data["No Flight"] = data["No Flight Raw"].apply(extract_flight)

    for c in ["Dewasa","Anak","Bayi","Transit_Dewasa","Transit_Total","Kargo"]:
        data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)

    # =========================
    # 🔥 PERHITUNGAN (FIX ANAK SAJA)
    # =========================
    data["Dewasa_Bersih"] = (data["Dewasa"] - data["Transit_Dewasa"]).clip(lower=0)

    # 🔥 tambahan
    data["Transit_Anak"] = (data["Transit_Total"] - data["Transit_Dewasa"]).clip(lower=0)

    # 🔥 FIX UTAMA
    data["Anak_PJP2U"] = (data["Anak"] - data["Transit_Anak"]).abs()

    # 🔥 TOTAL
    data["PJP2U"] = data["Dewasa_Bersih"] + data["Anak_PJP2U"]

    # =========================
    # FILTER
    # =========================
    st.sidebar.header("Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(data["Maskapai"].unique()))
    flight = st.sidebar.selectbox("No Penerbangan", ["SEMUA"] + sorted(data["No Flight"].unique()))
    pergerakan = st.sidebar.selectbox("Pergerakan", ["SEMUA","Departure","Arrival"])

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
        ["Semua","Dewasa","Anak","PJP2U","Bayi","Transit","Kargo"]
    )

    f = data.copy()
    f = f[f["Maskapai"] == maskapai]

    if flight != "SEMUA":
        f = f[f["No Flight"] == flight]

    if pergerakan != "SEMUA":
        f = f[f["Pergerakan"] == pergerakan]

    f = f[(f["Tanggal"] >= start) & (f["Tanggal"] <= end)]

    # =========================
    # HASIL
    # =========================
    if kategori == "Dewasa":
        f["Hasil"] = f["Dewasa_Bersih"]
    elif kategori == "Anak":
        f["Hasil"] = f["Anak_PJP2U"]
    elif kategori == "PJP2U":
        f["Hasil"] = f["PJP2U"]
    elif kategori == "Bayi":
        f["Hasil"] = f["Bayi"]
    elif kategori == "Transit":
        f["Hasil"] = f["Transit_Total"]
    elif kategori == "Kargo":
        f["Hasil"] = f["Kargo"]
    else:
        f["Hasil"] = f["PJP2U"]

    total = int(f["Hasil"].sum())

    # =========================
    # KPI
    # =========================
    st.subheader("📊 KPI Utama")

    c1,c2,c3,c4 = st.columns(4)

    def card(title, value, color):
        st.markdown(f"""
        <div class="metric-card">
            <div>{title}</div>
            <div class="metric-value {color}">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    with c1:
        card("Total PJP2U", int(data["PJP2U"].sum()), "blue")
    with c2:
        card("Flight", len(data), "orange")
    with c3:
        card("Transit", int(data["Transit_Total"].sum()), "green")
    with c4:
        card("Kargo", int(data["Kargo"].sum()), "red")

    st.subheader("📌 Hasil Pencarian")
    card("Total Hasil", total, "green" if total > 0 else "red")

    st.subheader("📈 Tren PJP2U")
    st.line_chart(data.groupby(data["Tanggal"].dt.date)["PJP2U"].sum())

    # =========================
    # DETAIL
    # =========================
    st.subheader("📋 Detail Data")
    st.dataframe(f, use_container_width=True)

    st.markdown("""
    <hr>
    <p style='text-align: center; color: gray;'>
    Copyright © 2026 Data UPBU Rendani Airport
    </p>
    """, unsafe_allow_html=True)

else:
    st.info("Upload file Excel untuk mulai")
