import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("✈️ Dashboard LLAU Rendani Airport")

file = st.file_uploader("Upload File Excel LLAU", type=["xlsx"])

if file:

    # =========================
    # LOAD FIX (HEADER 2 BARIS)
    # =========================
    df = pd.read_excel(file, header=[0,1])

    # =========================
    # FLATTEN HEADER
    # =========================
    df.columns = [
        f"{str(a).strip()}_{str(b).strip()}"
        for a, b in df.columns
    ]

    # =========================
    # AMBIL KOLOM SESUAI POSISI ASLI LLAU
    # =========================
    clean = pd.DataFrame()

    clean["Tanggal"] = df["TANGGAL PENERBANGAN\n(DD-MM-YYYY)\n** Wajib Diisi_nan"]
    clean["Maskapai"] = df["OPERATOR PENERBANGAN\n** Wajib Diisi_Nama Operator"]
    clean["Jenis"] = df["Pergerakan Penerbangan_(A / D)"]

    # Penumpang
    clean["Dewasa"] = df["Data Penumpang\n** Wajib Diisi_Dewasa"]
    clean["Anak"] = df["Data Penumpang\n** Wajib Diisi_Anak"]
    clean["Bayi"] = df["Data Penumpang\n** Wajib Diisi_Bayi"]

    # Transit
    clean["Transit"] = df["Data Penumpang Transit\n** Wajib Diisi Apabila..._Dewasa"]

    # Kargo
    clean["Kargo"] = df["Kargo (Kg)\n**Wajib Diisi_nan"]

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
    # HASIL
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
    st.info("Upload file Excel terlebih dahulu")
