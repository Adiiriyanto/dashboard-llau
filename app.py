import streamlit as st
import pandas as pd

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Dashboard LLAU", layout="wide")

st.title("📊 Dashboard Penumpang LLAU")
st.caption("Default: Lion Air (Berangkat) — fleksibel untuk semua maskapai")

# ========================
# UPLOAD FILE
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
    # RENAME KOLOM (AMAN)
    # ========================
    try:
        df = df.rename(columns={
            df.columns[1]: "Tanggal",
            df.columns[8]: "Maskapai",
            df.columns[17]: "Jenis",
            df.columns[18]: "Dewasa",
            df.columns[19]: "Anak",
            df.columns[20]: "Bayi"
        })
    except:
        st.error("Struktur file tidak sesuai format LLAU")
        st.stop()

    # ========================
    # CLEANING
    # ========================
    df = df[df["Tanggal"].notna()].copy()
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

    # Pastikan kolom numerik aman
    for col in ["Dewasa", "Anak", "Bayi"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    # Total
    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"]

    # ========================
    # AUTO DETECT LION AIR
    # ========================
    default_maskapai = None
    for m in df["Maskapai"].dropna().unique():
        if "LION" in str(m).upper():
            default_maskapai = m
            break

    if default_maskapai is None:
        default_maskapai = df["Maskapai"].dropna().unique()[0]

    # ========================
    # SIDEBAR (FILTER)
    # ========================
    st.sidebar.header("⚙️ Filter Data")

    maskapai_list = df["Maskapai"].dropna().unique().tolist()

    maskapai = st.sidebar.selectbox(
        "Maskapai",
        maskapai_list,
        index=maskapai_list.index(default_maskapai)
    )

    jenis = st.sidebar.selectbox("Jenis", ["D", "A"], index=0)

    tanggal_list = sorted(df["Tanggal"].dropna().dt.date.unique())

    tanggal = st.sidebar.selectbox("Tanggal", tanggal_list)

    # ========================
    # SEARCH & KATEGORI
    # ========================
    st.sidebar.subheader("🔎 Pencarian")
    search = st.sidebar.text_input("Cari (maskapai / flight / dll)")

    st.sidebar.subheader("🎯 Kategori Penumpang")
    kategori = st.sidebar.selectbox(
        "Pilih Kategori",
        ["Semua", "Dewasa", "Dewasa + Anak", "Bayi"]
    )

    # ========================
    # FILTER DATA
    # ========================
    df_filtered = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis) &
        (df["Tanggal"].dt.date == tanggal)
    ].copy()

    # ========================
    # APPLY SEARCH
    # ========================
    if search:
        df_filtered = df_filtered[
            df_filtered.apply(
                lambda row: row.astype(str).str.contains(search, case=False).any(),
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

    else:
        df_filtered["TotalKategori"] = df_filtered["Total"]

    # ========================
    # KPI
    # ========================
    st.subheader("📌 Ringkasan")

    col1, col2, col3 = st.columns(3)

    total = int(df_filtered["TotalKategori"].sum())
    jumlah_flight = len(df_filtered)
    rata2 = int(total / jumlah_flight) if jumlah_flight > 0 else 0

    col1.metric("Total Penumpang", total)
    col2.metric("Jumlah Flight", jumlah_flight)
    col3.metric("Rata-rata / Flight", rata2)

    # ========================
    # TABEL
    # ========================
    st.subheader("📋 Detail Data")
    st.dataframe(df_filtered, use_container_width=True)

    # ========================
    # GRAFIK
    # ========================
    st.subheader("📈 Tren Harian")

    rekap = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis)
    ].groupby(df["Tanggal"].dt.date)["Total"].sum()

    st.line_chart(rekap)

    # ========================
    # DOWNLOAD
    # ========================
    st.download_button(
        label="⬇️ Download Hasil",
        data=df_filtered.to_csv(index=False),
        file_name="hasil_seleksi.csv",
        mime="text/csv"
    )

else:
    st.info("Silakan upload file Excel LLAU terlebih dahulu.")
