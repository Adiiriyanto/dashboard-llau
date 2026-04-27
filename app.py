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
h1, h2, h3 {
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
col1, col2 = st.columns([8,2])

with col1:
    st.title("✈️ Dashboard Operasional LLAU Rendani Airport")

with col2:
    if st.button("🔄 Reset"):
        st.rerun()

# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload Data Excel", type=["xlsx"])

if file:

    # =========================
    # LOAD DATA
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

    col_tgl = find("tanggal")
    col_mask = find("operator") or find("maskapai")
    col_jns = find("pergerakan") or find("jenis")

    col_dew = find("dewasa")
    col_anak = find("anak")
    col_bayi = find("bayi")
    col_transit = find("transit")
    col_kargo = find("kargo")

    if not col_tgl or not col_mask:
        st.error("Format tidak dikenali")
        st.write(df.columns)
        st.stop()

    # =========================
    # CLEAN DATA
    # =========================
    data = pd.DataFrame({
        "Tanggal": df[col_tgl],
        "Maskapai": df[col_mask],
        "Jenis": df[col_jns] if col_jns else "D",
        "Dewasa": df[col_dew] if col_dew else 0,
        "Anak": df[col_anak] if col_anak else 0,
        "Bayi": df[col_bayi] if col_bayi else 0,
        "Transit": df[col_transit] if col_transit else 0,
        "Kargo": df[col_kargo] if col_kargo else 0
    })

    data["Tanggal"] = pd.to_datetime(data["Tanggal"], errors="coerce", dayfirst=True)
    data = data.dropna(subset=["Tanggal"])

    data["Maskapai"] = data["Maskapai"].astype(str).str.upper().str.strip()
    data["Jenis"] = data["Jenis"].astype(str).str.upper().str.strip()

    for c in ["Dewasa","Anak","Bayi","Transit","Kargo"]:
        data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)

    # =========================
    # PERHITUNGAN BARU (FIX)
    # =========================
    # Transit diasumsikan sudah total (dewasa+anak+bayi)
    data["Total_Penumpang"] = (data["Dewasa"] + data["Anak"]) - data["Transit"]
    data["Total_Penumpang"] = data["Total_Penumpang"].clip(lower=0)

    # =========================
    # SIDEBAR
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
    # FILTER
    # =========================
    f = data.copy()
    f = f[f["Maskapai"] == maskapai]

    if jenis != "SEMUA":
        f = f[f["Jenis"] == jenis]

    f = f[(f["Tanggal"] >= start) & (f["Tanggal"] <= end)]

    # =========================
    # HASIL
    # =========================
    if kategori == "Dewasa":
        f["Hasil"] = f["Dewasa"]
    elif kategori == "Dewasa + Anak":
        f["Hasil"] = f["Total_Penumpang"]   # pakai rumus baru
    elif kategori == "Bayi":
        f["Hasil"] = f["Bayi"]
    elif kategori == "Transit":
        f["Hasil"] = f["Transit"]
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
        card("Transit", int(data["Transit"].sum()), "green")
    with c4:
        card("Kargo", int(data["Kargo"].sum()), "red")

    # =========================
    # HASIL
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
