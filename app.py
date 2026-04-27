import streamlit as st
import pandas as pd

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="LLAU Dashboard", layout="wide")

st.title("✈️ Dashboard LLAU Rendani Airport")

uploaded_file = st.file_uploader("Upload File Excel LLAU", type=["xlsx"])

if uploaded_file:

    # ========================
    # LOAD DATA (FORMAT LLAU)
    # ========================
    df = pd.read_excel(uploaded_file, skiprows=9)

    df.columns = df.columns.str.strip()

    # ========================
    # VALIDASI KOLOM WAJIB
    # ========================
    required_cols = [
        "Tanggal","Maskapai","Jenis",
        "Dewasa","Anak","Bayi","Transit","Kargo"
    ]

    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Kolom tidak lengkap: {missing}")
        st.write("Kolom tersedia:", df.columns.tolist())
        st.stop()

    # ========================
    # FIX DATA
    # ========================
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Tanggal"])

    df["Maskapai"] = df["Maskapai"].astype(str).str.strip().str.upper()
    df["Jenis"] = df["Jenis"].astype(str).str.strip().str.upper()

    for col in ["Dewasa","Anak","Bayi","Transit","Kargo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # ========================
    # SIDEBAR FILTER
    # ========================
    st.sidebar.header("⚙️ Filter")

    maskapai = st.sidebar.selectbox(
        "Maskapai",
        sorted(df["Maskapai"].unique())
    )

    jenis = st.sidebar.selectbox(
        "Jenis",
        ["SEMUA","D","A"]
    )

    # ========================
    # MODE TANGGAL
    # ========================
    mode = st.sidebar.radio(
        "Mode Tanggal",
        ["1 Tanggal","Rentang"]
    )

    min_date = df["Tanggal"].min().date()
    max_date = df["Tanggal"].max().date()

    if mode == "1 Tanggal":
        d = st.sidebar.date_input("Tanggal", min_date)
        start_date = pd.to_datetime(d)
        end_date = pd.to_datetime(d)

    else:
        dr = st.sidebar.date_input("Rentang", (min_date, max_date))

        if isinstance(dr, tuple) and len(dr) == 2:
            start_date = pd.to_datetime(dr[0])
            end_date = pd.to_datetime(dr[1])
        else:
            start_date = pd.to_datetime(min_date)
            end_date = pd.to_datetime(max_date)

    # ========================
    # SEARCH
    # ========================
    keyword = st.sidebar.text_input("🔍 Cari")
    cari = st.sidebar.button("Cari")

    # ========================
    # FILTER DATA (PRESISI)
    # ========================
    df_filtered = df.copy()

    df_filtered = df_filtered[
        df_filtered["Maskapai"] == maskapai
    ]

    if jenis != "SEMUA":
        df_filtered = df_filtered[
            df_filtered["Jenis"] == jenis
        ]

    df_filtered = df_filtered[
        (df_filtered["Tanggal"] >= start_date) &
        (df_filtered["Tanggal"] <= end_date)
    ]

    if cari and keyword:
        df_filtered = df_filtered[
            df_filtered.astype(str)
            .apply(lambda r: r.str.contains(keyword, case=False).any(), axis=1)
        ]

    # ========================
    # KATEGORI HASIL
    # ========================
    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa + Anak","Bayi","Transit","Kargo"]
    )

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

    total = int(df_filtered["Hasil"].sum())

    # ========================
    # KPI
    # ========================
    st.subheader("📊 KPI Utama")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Total Penumpang", int(df["Total"].sum()))
    c2.metric("Flight", len(df))
    c3.metric("Transit", int(df["Transit"].sum()))
    c4.metric("Kargo", int(df["Kargo"].sum()))

    # ========================
    # HASIL PENCARIAN
    # ========================
    st.subheader("📌 Hasil Pencarian")
    st.metric("Total Hasil", total)

    if df_filtered.empty:
        st.warning("⚠️ Data tidak ditemukan, cek filter")

    # ========================
    # GRAFIK
    # ========================
    st.subheader("📈 Tren Penumpang")
    st.line_chart(df.groupby(df["Tanggal"].dt.date)["Total"].sum())

    # ========================
    # TABEL
    # ========================
    st.subheader("📋 Detail Data")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("Upload file Excel terlebih dahulu")
