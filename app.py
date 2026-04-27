import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.title("✈️ Dashboard LLAU Rendani Airport")

file = st.file_uploader("Upload File Excel (Format Standar)", type=["xlsx"])

if file:

    # =========================
    # LOAD DATA FLEKSIBEL
    # =========================
    try:
        df = pd.read_excel(file, header=[0,1])
        multi = True
    except:
        df = pd.read_excel(file)
        multi = False

    # =========================
    # NORMALISASI HEADER
    # =========================
    def clean_text(x):
        x = str(x)
        x = re.sub(r'\s+', ' ', x)
        return x.strip().lower()

    if multi:
        df.columns = [
            clean_text(a) + "_" + clean_text(b)
            for a,b in df.columns
        ]
    else:
        df.columns = [clean_text(c) for c in df.columns]

    # =========================
    # CARI KOLOM OTOMATIS
    # =========================
    def find(keyword):
        for col in df.columns:
            if keyword in col:
                return col
        return None

    col_tanggal = find("tanggal")
    col_maskapai = find("operator") or find("maskapai")
    col_jenis = find("pergerakan") or find("jenis")

    col_dewasa = find("dewasa")
    col_anak = find("anak")
    col_bayi = find("bayi")
    col_transit = find("transit")
    col_kargo = find("kargo")

    # =========================
    # VALIDASI
    # =========================
    if not col_tanggal or not col_maskapai:
        st.error("Format Excel tidak sesuai")
        st.write("Kolom terbaca:", df.columns)
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
    # FIX DATA
    # =========================
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Tanggal"])

    df["Maskapai"] = df["Maskapai"].astype(str).str.upper().str.strip()
    df["Jenis"] = df["Jenis"].astype(str).str.upper().str.strip()

    for col in ["Dewasa","Anak","Bayi","Transit","Kargo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # =========================
    # FILTER
    # =========================
    st.sidebar.header("Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(df["Maskapai"].unique()))
    jenis = st.sidebar.selectbox("Jenis", ["SEMUA","D","A"])

    mode = st.sidebar.radio("Tanggal", ["1 Hari","Rentang"])

    min_d = df["Tanggal"].min().date()
    max_d = df["Tanggal"].max().date()

    if mode == "1 Hari":
        d = st.sidebar.date_input("Tanggal", min_d)
        start = pd.to_datetime(d)
        end = start
    else:
        dr = st.sidebar.date_input("Rentang", (min_d, max_d))
        if isinstance(dr, tuple):
            start = pd.to_datetime(dr[0])
            end = pd.to_datetime(dr[1])
        else:
            start = pd.to_datetime(min_d)
            end = pd.to_datetime(max_d)

    keyword = st.sidebar.text_input("Search")
    btn = st.sidebar.button("Cari")

    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa + Anak","Bayi","Transit","Kargo"]
    )

    # =========================
    # FILTER DATA
    # =========================
    f = df.copy()

    f = f[f["Maskapai"] == maskapai]

    if jenis != "SEMUA":
        f = f[f["Jenis"] == jenis]

    f = f[(f["Tanggal"] >= start) & (f["Tanggal"] <= end)]

    if btn and keyword:
        f = f[
            f.astype(str)
            .apply(lambda r: r.str.contains(keyword, case=False).any(), axis=1)
        ]

    # =========================
    # HASIL
    # =========================
    if kategori == "Dewasa":
        f["Hasil"] = f["Dewasa"]
    elif kategori == "Dewasa + Anak":
        f["Hasil"] = f["Dewasa"] + f["Anak"]
    elif kategori == "Bayi":
        f["Hasil"] = f["Bayi"]
    elif kategori == "Transit":
        f["Hasil"] = f["Transit"]
    elif kategori == "Kargo":
        f["Hasil"] = f["Kargo"]
    else:
        f["Hasil"] = f["Total"]

    total = int(f["Hasil"].sum())

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

    if f.empty:
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
    st.dataframe(f, use_container_width=True)

else:
    st.info("Upload file terlebih dahulu")
