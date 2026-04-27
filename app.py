import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("✈️ Dashboard LLAU Rendani Airport")

uploaded_file = st.file_uploader("Upload File Excel LLAU", type=["xlsx"])

if uploaded_file:

    # =========================
    # LOAD DATA SUPER AMAN
    # =========================
    try:
        df = pd.read_excel(uploaded_file, header=[8,9])
    except:
        df = pd.read_excel(uploaded_file)

    # =========================
    # FIX HEADER MULTI LEVEL
    # =========================
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(i).strip() for i in col if str(i) != "nan"])
            for col in df.columns
        ]

    df.columns = [str(c).strip() for c in df.columns]

    # =========================
    # HAPUS KOLOM DUPLIKAT
    # =========================
    df = df.loc[:, ~df.columns.duplicated()]

    # =========================
    # DETEKSI KOLOM OTOMATIS
    # =========================
    def find_col(keyword):
        for col in df.columns:
            if keyword in col.lower():
                return col
        return None

    col_tanggal = find_col("tanggal")
    col_maskapai = find_col("maskapai") or find_col("operator")
    col_jenis = find_col("jenis") or find_col("a_d")

    col_dewasa = find_col("dewasa")
    col_anak = find_col("anak")
    col_bayi = find_col("bayi")
    col_transit = find_col("transit")
    col_kargo = find_col("cargo") or find_col("kargo")

    # =========================
    # VALIDASI MINIMAL
    # =========================
    if col_tanggal is None or col_maskapai is None:
        st.error("Format file tidak dikenali")
        st.write("Kolom terbaca:", df.columns.tolist())
        st.stop()

    # =========================
    # BENTUK DATA BERSIH
    # =========================
    clean = pd.DataFrame()

    clean["Tanggal"] = df[col_tanggal]
    clean["Maskapai"] = df[col_maskapai]

    clean["Jenis"] = df[col_jenis] if col_jenis else "D"

    clean["Dewasa"] = df[col_dewasa] if col_dewasa else 0
    clean["Anak"] = df[col_anak] if col_anak else 0
    clean["Bayi"] = df[col_bayi] if col_bayi else 0
    clean["Transit"] = df[col_transit] if col_transit else 0
    clean["Kargo"] = df[col_kargo] if col_kargo else 0

    df = clean.copy()

    # =========================
    # FIX TIPE DATA (ANTI ERROR)
    # =========================
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Tanggal"])

    df["Maskapai"] = df["Maskapai"].astype(str).str.strip().str.upper()
    df["Jenis"] = df["Jenis"].astype(str).str.strip().str.upper()

    for col in ["Dewasa","Anak","Bayi","Transit","Kargo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.header("Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(df["Maskapai"].unique()))
    jenis = st.sidebar.selectbox("Jenis", ["SEMUA","D","A"])

    mode = st.sidebar.radio("Tanggal", ["1 Hari","Rentang"])

    min_date = df["Tanggal"].min().date()
    max_date = df["Tanggal"].max().date()

    if mode == "1 Hari":
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

    keyword = st.sidebar.text_input("Search")
    tombol = st.sidebar.button("Cari")

    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa + Anak","Bayi","Transit","Kargo"]
    )

    # =========================
    # FILTER DATA
    # =========================
    df_f = df.copy()

    df_f = df_f[df_f["Maskapai"] == maskapai]

    if jenis != "SEMUA":
        df_f = df_f[df_f["Jenis"] == jenis]

    df_f = df_f[
        (df_f["Tanggal"] >= start_date) &
        (df_f["Tanggal"] <= end_date)
    ]

    if tombol and keyword:
        df_f = df_f[
            df_f.astype(str)
            .apply(lambda r: r.str.contains(keyword, case=False).any(), axis=1)
        ]

    # =========================
    # HITUNG HASIL
    # =========================
    if kategori == "Dewasa":
        df_f["Hasil"] = df_f["Dewasa"]
    elif kategori == "Dewasa + Anak":
        df_f["Hasil"] = df_f["Dewasa"] + df_f["Anak"]
    elif kategori == "Bayi":
        df_f["Hasil"] = df_f["Bayi"]
    elif kategori == "Transit":
        df_f["Hasil"] = df_f["Transit"]
    elif kategori == "Kargo":
        df_f["Hasil"] = df_f["Kargo"]
    else:
        df_f["Hasil"] = df_f["Total"]

    total = int(df_f["Hasil"].sum())

    # =========================
    # KPI
    # =========================
    st.subheader("📊 KPI Utama")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Penumpang", int(df["Total"].sum()))
    c2.metric("Flight", len(df))
    c3.metric("Transit", int(df["Transit"].sum()))
    c4.metric("Kargo", int(df["Kargo"].sum()))

    # =========================
    # HASIL PENCARIAN
    # =========================
    st.subheader("📌 Hasil Pencarian")
    st.metric("Total Hasil", total)

    if df_f.empty:
        st.warning("Data tidak ditemukan")

    # =========================
    # GRAFIK
    # =========================
    st.subheader("📈 Tren Penumpang")
    st.line_chart(df.groupby(df["Tanggal"].dt.date)["Total"].sum())

    # =========================
    # TABEL
    # =========================
    st.subheader("📋 Detail Data")
    st.dataframe(df_f, use_container_width=True)

else:
    st.info("Upload file Excel terlebih dahulu")
