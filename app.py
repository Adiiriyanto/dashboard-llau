import streamlit as st
import pandas as pd

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Dashboard Bandara LLAU", layout="wide")

st.title("✈️ Dashboard Operasional Bandara")
st.caption("Analisis Penumpang & Kargo")

# ========================
# UPLOAD
# ========================
uploaded_file = st.file_uploader("Upload File Excel LLAU", type=["xlsx"])

if uploaded_file:

    # ========================
    # LOAD DATA
    # ========================
    try:
        df = pd.read_excel(uploaded_file, skiprows=9)
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        st.stop()

    # ========================
    # AUTO DETECT KOLOM
    # ========================
    col_map = {}

    for col in df.columns:
        c = str(col).lower()

        if "tanggal" in c:
            col_map[col] = "Tanggal"
        elif "maskapai" in c or "operator" in c:
            col_map[col] = "Maskapai"
        elif "jenis" in c:
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

    # ========================
    # VALIDASI KOLOM WAJIB
    # ========================
    if "Tanggal" not in df.columns or "Maskapai" not in df.columns:
        st.error("Format file tidak dikenali (kolom utama tidak ditemukan)")
        st.stop()

    # ========================
    # CLEANING
    # ========================
    df = df[df["Tanggal"].notna()].copy()
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

    for col in ["Dewasa", "Anak", "Bayi", "Transit", "Kargo"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # ========================
    # SIDEBAR FILTER
    # ========================
    st.sidebar.header("⚙️ Filter")

    maskapai_list = sorted(df["Maskapai"].dropna().unique())
    maskapai = st.sidebar.selectbox("Maskapai", maskapai_list)

    jenis = st.sidebar.selectbox("Jenis", ["D", "A"])

    tanggal_list = sorted(df["Tanggal"].dt.date.dropna().unique())
    tanggal = st.sidebar.selectbox("Tanggal", tanggal_list)

    search = st.sidebar.text_input("🔎 Search")

    kategori = st.sidebar.selectbox(
        "Kategori Data",
        ["Semua", "Dewasa", "Dewasa + Anak", "Bayi", "Transit", "Kargo"]
    )

    # ========================
    # FILTER DATA
    # ========================
    df_filtered = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis) &
        (df["Tanggal"].dt.date == tanggal)
    ].copy()

    if search:
        df_filtered = df_filtered[
            df_filtered.apply(
                lambda x: x.astype(str).str.contains(search, case=False).any(),
                axis=1
            )
        ]

    # ========================
    # HITUNG KATEGORI
    # ========================
    if kategori == "Dewasa":
        df_filtered["TotalKategori"] = df_filtered["Dewasa"]
    elif kategori == "Dewasa + Anak":
        df_filtered["TotalKategori"] = df_filtered["Dewasa"] + df_filtered["Anak"]
    elif kategori == "Bayi":
        df_filtered["TotalKategori"] = df_filtered["Bayi"]
    elif kategori == "Transit":
        df_filtered["TotalKategori"] = df_filtered["Transit"]
    elif kategori == "Kargo":
        df_filtered["TotalKategori"] = df_filtered["Kargo"]
    else:
        df_filtered["TotalKategori"] = df_filtered["Total"]

    # ========================
    # KPI
    # ========================
    st.subheader("📊 KPI Utama")

    total_all = int(df["Total"].sum())
    total_filtered = int(df_filtered["TotalKategori"].sum())
    total_flight = len(df)
    avg = int(total_all / total_flight) if total_flight > 0 else 0

    total_transit = int(df["Transit"].sum())
    total_kargo = int(df["Kargo"].sum())

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Penumpang", total_all)
    col2.metric("Filtered", total_filtered)
    col3.metric("Avg / Flight", avg)
    col4.metric("Transit", total_transit)
    col5.metric("Kargo", total_kargo)

    # ========================
    # GRAFIK
    # ========================
    st.subheader("📈 Tren Penumpang Harian")
    tren = df.groupby(df["Tanggal"].dt.date)["Total"].sum()
    st.line_chart(tren)

    st.subheader("📦 Tren Kargo Harian")
    tren_kargo = df.groupby(df["Tanggal"].dt.date)["Kargo"].sum()
    st.line_chart(tren_kargo)

    st.subheader("🏆 Top Maskapai")
    top = df.groupby("Maskapai")["Total"].sum().sort_values(ascending=False).head(5)
    st.bar_chart(top)

    st.subheader("🧭 Distribusi D vs A")
    dist = df.groupby("Jenis")["Total"].sum()
    st.bar_chart(dist)

    # ========================
    # DATA TABLE
    # ========================
    st.subheader("📋 Detail Data")
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
    st.info("Silakan upload file Excel LLAU terlebih dahulu.")
