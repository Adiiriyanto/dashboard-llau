import streamlit as st
import pandas as pd

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Dashboard Bandara", layout="wide")

st.title("✈️ Dashboard Operasional Bandara")
st.caption("Penumpang & Kargo (Stabil & Anti Error)")

# ========================
# UPLOAD
# ========================
uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

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
    # CLEAN HEADER (WAJIB)
    # ========================
    df.columns = [str(col).strip() for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    # ========================
    # MAPPING PRESISI + FLEX
    # ========================
    col_map = {}

    for col in df.columns:
        c = col.lower()

        if "tanggal" in c:
            col_map[col] = "Tanggal"
        elif "maskapai" in c or "operator" in c:
            col_map[col] = "Maskapai"
        elif "jenis" in c or "a/d" in c or "dep" in c:
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
    # VALIDASI
    # ========================
    if "Tanggal" not in df.columns or "Maskapai" not in df.columns:
        st.error("Format file tidak dikenali")
        st.write("Kolom terbaca:", df.columns.tolist())
        st.stop()

    # ========================
    # NORMALISASI DATA
    # ========================
    df = df[df["Tanggal"].notna()].copy()
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

    if "Jenis" not in df.columns:
        df["Jenis"] = "D"

    # ========================
    # NUMERIC SAFE CONVERSION
    # ========================
    for col in ["Dewasa", "Anak", "Bayi", "Transit", "Kargo"]:
        if col not in df.columns:
            df[col] = 0

        # Hindari error DataFrame (duplikat)
        if isinstance(df[col], pd.DataFrame):
            df[col] = df[col].iloc[:, 0]

        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(0)

    # ========================
    # TOTAL
    # ========================
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
    # FILTER DATA (SAFE)
    # ========================
    df_filtered = df.copy()

    if "Maskapai" in df.columns:
        df_filtered = df_filtered[df_filtered["Maskapai"] == maskapai]

    if "Jenis" in df.columns:
        df_filtered = df_filtered[df_filtered["Jenis"] == jenis]

    if "Tanggal" in df.columns:
        df_filtered = df_filtered[df_filtered["Tanggal"].dt.date == tanggal]

    # SEARCH
    if search:
        df_filtered = df_filtered[
            df_filtered.apply(
                lambda x: x.astype(str).str.contains(search, case=False).any(),
                axis=1
            )
        ]

    # ========================
    # KATEGORI
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

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Penumpang", int(df["Total"].sum()))
    col2.metric("Filtered", int(df_filtered["TotalKategori"].sum()))
    col3.metric("Flight", len(df))
    col4.metric("Transit", int(df["Transit"].sum()))
    col5.metric("Kargo", int(df["Kargo"].sum()))

    # ========================
    # GRAFIK
    # ========================
    st.subheader("📈 Tren Penumpang")
    st.line_chart(df.groupby(df["Tanggal"].dt.date)["Total"].sum())

    st.subheader("📦 Tren Kargo")
    st.line_chart(df.groupby(df["Tanggal"].dt.date)["Kargo"].sum())

    st.subheader("🏆 Top Maskapai")
    st.bar_chart(
        df.groupby("Maskapai")["Total"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    st.subheader("🧭 Distribusi D vs A")
    st.bar_chart(df.groupby("Jenis")["Total"].sum())

    # ========================
    # TABLE
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
