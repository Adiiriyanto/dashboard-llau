import streamlit as st
import pandas as pd

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="LLAU Dashboard", layout="wide")

st.title("✈️ Dashboard LLAU Rendani Airport")

uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

if uploaded_file:

    # ========================
    # LOAD DATA
    # ========================
    df = pd.read_excel(uploaded_file, skiprows=9)

    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    # ========================
    # MAPPING KOLOM
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

    if "Tanggal" not in df.columns or "Maskapai" not in df.columns:
        st.error("Format file tidak dikenali")
        st.stop()

    # ========================
    # FIX TANGGAL
    # ========================
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Tanggal"])

    # ========================
    # NUMERIC
    # ========================
    for col in ["Dewasa","Anak","Bayi","Transit","Kargo"]:
        if col not in df.columns:
            df[col] = 0

        if isinstance(df[col], pd.DataFrame):
            df[col] = df[col].iloc[:,0]

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Jenis" not in df.columns:
        df["Jenis"] = "D"

    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # ========================
    # SIDEBAR FILTER
    # ========================
    st.sidebar.header("⚙️ Filter")

    maskapai = st.sidebar.selectbox(
        "Maskapai",
        sorted(df["Maskapai"].dropna().unique())
    )

    jenis = st.sidebar.selectbox("Jenis", ["D","A"])

    # ========================
    # MODE TANGGAL (FIX FINAL)
    # ========================
    mode_tanggal = st.sidebar.radio(
        "Mode Tanggal",
        ["1 Tanggal", "Rentang Tanggal"]
    )

    min_date = df["Tanggal"].min().date()
    max_date = df["Tanggal"].max().date()

    if mode_tanggal == "1 Tanggal":
        single_date = st.sidebar.date_input(
            "Pilih Tanggal",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )

        start_date = pd.to_datetime(single_date)
        end_date = pd.to_datetime(single_date)

    else:
        date_range = st.sidebar.date_input(
            "Pilih Rentang",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date = pd.to_datetime(date_range[0])
            end_date = pd.to_datetime(date_range[1])
        else:
            start_date = pd.to_datetime(min_date)
            end_date = pd.to_datetime(max_date)

    # ========================
    # KATEGORI
    # ========================
    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa + Anak","Bayi","Transit","Kargo"]
    )

    # ========================
    # SEARCH
    # ========================
    st.sidebar.markdown("### 🔍 Pencarian")

    search_input = st.sidebar.text_input("Cari data")
    search_button = st.sidebar.button("🔍 Cari")

    # ========================
    # FILTER DATA
    # ========================
    df_filtered = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis) &
        (df["Tanggal"] >= start_date) &
        (df["Tanggal"] <= end_date)
    ].copy()

    # SEARCH APPLY
    if search_button and search_input:
        df_filtered = df_filtered[
            df_filtered.astype(str)
            .apply(lambda row: row.str.contains(search_input, case=False).any(), axis=1)
        ]

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

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Total Penumpang", int(df["Total"].sum()))
    c2.metric("Flight", len(df))
    c3.metric("Transit", int(df["Transit"].sum()))
    c4.metric("Kargo", int(df["Kargo"].sum()))
    c5.metric("Hasil Pencarian", total_hasil)

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

    st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("Upload file Excel terlebih dahulu")
