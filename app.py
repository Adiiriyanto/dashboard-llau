import streamlit as st
import pandas as pd

# ========================
# CONFIG + STYLE
# ========================
st.set_page_config(page_title="LLAU Dashboard", layout="wide")

st.markdown("""
<style>
.card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}
.kpi-green { color: #22c55e; font-size: 28px; font-weight: bold; }
.kpi-red { color: #ef4444; font-size: 28px; font-weight: bold; }
.kpi-title { font-size: 14px; color: #9ca3af; }
.big-number { font-size: 40px; font-weight: bold; color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

st.title("✈️ Dashboard LLAU Rendani Airport")

# ========================
# UPLOAD
# ========================
uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

if uploaded_file:

    # ========================
    # LOAD DATA
    # ========================
    df = pd.read_excel(uploaded_file, skiprows=9)

    # CLEAN HEADER
    df.columns = [str(col).strip() for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    # ========================
    # AUTO MAPPING
    # ========================
    col_map = {}
    for col in df.columns:
        c = col.lower()

        if "tanggal" in c:
            col_map[col] = "Tanggal"
        elif "maskapai" in c or "operator" in c:
            col_map[col] = "Maskapai"
        elif "jenis" in c or "a/d" in c:
            col_map[col] = "Jenis"
        elif "dewasa" in c:
            col_map[col] = "Dewasa"
        elif "anak" in c:
            col_map[col] = "Anak"
        elif "bayi" in c:
            col_map[col] = "Bayi"
        elif "transit" in c:
            col_map[col] = "Transit"
        elif "cargo" in c or "kargo" in c:
            col_map[col] = "Kargo"

    df = df.rename(columns=col_map)

    # VALIDASI
    if "Tanggal" not in df.columns or "Maskapai" not in df.columns:
        st.error("Format file tidak dikenali")
        st.stop()

    # ========================
    # FIX TANGGAL (ANTI ERROR)
    # ========================
    df["Tanggal"] = pd.to_datetime(
        df["Tanggal"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["Tanggal"].notna()]

    # ========================
    # NUMERIC SAFE
    # ========================
    for col in ["Dewasa", "Anak", "Bayi", "Transit", "Kargo"]:
        if col not in df.columns:
            df[col] = 0

        if isinstance(df[col], pd.DataFrame):
            df[col] = df[col].iloc[:, 0]

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Jenis" not in df.columns:
        df["Jenis"] = "D"

    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # ========================
    # SIDEBAR
    # ========================
    st.sidebar.header("⚙️ Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(df["Maskapai"].unique()))
    jenis = st.sidebar.selectbox("Jenis", ["D", "A"])

    # ========================
    # RANGE DATE FIX (INI KUNCI)
    # ========================
    min_date = df["Tanggal"].min()
    max_date = df["Tanggal"].max()

    start_date, end_date = st.sidebar.date_input(
        "Rentang Tanggal",
        value=(min_date, max_date)
    )

    # convert ke datetime biar aman
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa + Anak","Bayi","Transit","Kargo"]
    )

    # ========================
    # FILTER DATA (FIX TOTAL)
    # ========================
    df_filtered = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis) &
        (df["Tanggal"] >= start_date) &
        (df["Tanggal"] <= end_date)
    ].copy()

    # ========================
    # HASIL
    # ========================
    if kategori == "Dewasa":
        df_filtered["Hasil"] = df_filtered["Dewasa"]
    elif kategori == "Dewasa + Anak":
        df_filtered["Hasil"] = df_filtered["Dewasa"] + df_filtered["Anak"]
    elif kategori == "Bayi":
        df_filtered["Hasil"] = df_filtered["Bayi"]
    elif kategori == "Transit":
        df_filtered["Hasil"] = df_filtered["Transit"]
    elif kategori == "Kargo":
        df_filtered["Hasil"] = df_filtered["Kargo"]
    else:
        df_filtered["Hasil"] = df_filtered["Total"]

    total_hasil = int(df_filtered["Hasil"].sum())

    # ========================
    # KPI
    # ========================
    st.subheader("📊 KPI Utama")

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Total Penumpang", int(df["Total"].sum()))
    k2.metric("Flight", len(df))
    k3.metric("Transit", int(df["Transit"].sum()))
    k4.metric("Kargo", int(df["Kargo"].sum()))

    warna = "kpi-green" if total_hasil > 0 else "kpi-red"

    k5.markdown(f"""
    <div class="card">
        <div class="kpi-title">Hasil Pencarian</div>
        <div class="{warna}">{total_hasil}</div>
    </div>
    """, unsafe_allow_html=True)

    # ========================
    # HIGHLIGHT
    # ========================
    st.subheader("📌 Ringkasan Hasil Pencarian")

    st.markdown(f"""
    <div class="card">
        <div class="kpi-title">Kategori: {kategori}</div>
        <div class="big-number">{total_hasil}</div>
    </div>
    """, unsafe_allow_html=True)

    # ========================
    # GRAFIK
    # ========================
    st.subheader("📈 Tren Penumpang")
    st.line_chart(df.groupby(df["Tanggal"].dt.date)["Total"].sum())

    st.subheader("📦 Tren Kargo")
    st.line_chart(df.groupby(df["Tanggal"].dt.date)["Kargo"].sum())

    # ========================
    # TABEL
    # ========================
    st.subheader("📋 Detail Data")

    cols = ["Hasil"] + [c for c in df_filtered.columns if c != "Hasil"]
    df_filtered = df_filtered[cols]

    st.dataframe(df_filtered, use_container_width=True)

    # ========================
    # DOWNLOAD
    # ========================
    st.download_button(
        "⬇️ Download Data",
        df_filtered.to_csv(index=False),
        "hasil_dashboard.csv"
    )

else:
    st.info("Upload file Excel terlebih dahulu")
