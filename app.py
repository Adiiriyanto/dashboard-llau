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
    # LOAD
    # ========================
    df = pd.read_excel(uploaded_file, skiprows=9)

    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    # ========================
    # MAPPING
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

    if "Tanggal" not in df.columns:
        st.error("Kolom Tanggal tidak ditemukan")
        st.stop()

    # ========================
    # FIX DATA
    # ========================
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Tanggal"])

    df["Maskapai"] = df.get("Maskapai", "UNKNOWN").astype(str).str.strip().str.upper()
    df["Jenis"] = df.get("Jenis", "D").astype(str).str.strip().str.upper()

    for col in ["Dewasa","Anak","Bayi","Transit","Kargo"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # ========================
    # SIDEBAR
    # ========================
    st.sidebar.header("⚙️ Filter")

    # OPTIONAL FILTER (INI KUNCI)
    maskapai = st.sidebar.selectbox(
        "Maskapai (Opsional)",
        ["SEMUA"] + sorted(df["Maskapai"].unique())
    )

    jenis = st.sidebar.selectbox(
        "Jenis (Opsional)",
        ["SEMUA", "D", "A"]
    )

    # ========================
    # MODE TANGGAL
    # ========================
    mode = st.sidebar.radio("Mode Tanggal", ["1 Tanggal","Rentang"])

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
    st.sidebar.markdown("### 🔍 Pencarian")
    keyword = st.sidebar.text_input("Cari bebas")
    cari = st.sidebar.button("🔍 Cari")

    # ========================
    # FILTER DATA (FLEXIBLE)
    # ========================
    df_filtered = df.copy()

    if maskapai != "SEMUA":
        df_filtered = df_filtered[df_filtered["Maskapai"].str.contains(maskapai)]

    if jenis != "SEMUA":
        df_filtered = df_filtered[df_filtered["Jenis"] == jenis]

    df_filtered = df_filtered[
        (df_filtered["Tanggal"] >= start_date) &
        (df_filtered["Tanggal"] <= end_date)
    ]

    if cari and keyword:
        df_filtered = df_filtered[
            df_filtered.astype(str)
            .apply(lambda x: x.str.contains(keyword, case=False).any(), axis=1)
        ]

    # ========================
    # HASIL
    # ========================
    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa+Anak","Bayi","Transit","Kargo"]
    )

    if kategori == "Dewasa":
        df_filtered["Hasil"] = df_filtered["Dewasa"]
    elif kategori == "Dewasa+Anak":
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
    # 🔥 HASIL PENCARIAN (BALIK LAGI)
    # ========================
    st.subheader("📌 Hasil Pencarian")
    st.metric("Total Hasil", total)

    # ========================
    # GRAFIK
    # ========================
    st.subheader("📈 Tren Penumpang")
    st.line_chart(df.groupby(df["Tanggal"].dt.date)["Total"].sum())

    # ========================
    # TABEL
    # ========================
    st.subheader("📋 Data Detail")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("Upload file Excel terlebih dahulu")
