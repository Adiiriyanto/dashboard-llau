import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard LLAU", layout="wide")

st.title("📊 Dashboard Penumpang LLAU")
st.caption("Default: Lion Air (Berangkat) — bisa diubah")

uploaded_file = st.file_uploader("Upload File Excel LLAU", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, skiprows=9)

    df = df.rename(columns={
        df.columns[1]: "Tanggal",
        df.columns[8]: "Maskapai",
        df.columns[17]: "Jenis",
        df.columns[18]: "Dewasa",
        df.columns[19]: "Anak",
        df.columns[20]: "Bayi"
    })

    df = df[df["Tanggal"].notna()]
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors='coerce')

    df["Total"] = (
        df["Dewasa"].fillna(0) +
        df["Anak"].fillna(0) +
        df["Bayi"].fillna(0)
    )

    # Auto Lion Air
    default_maskapai = None
    for m in df["Maskapai"].dropna().unique():
        if "LION" in str(m).upper():
            default_maskapai = m
            break

    if default_maskapai is None:
        default_maskapai = df["Maskapai"].dropna().unique()[0]

    st.sidebar.header("Filter Data")

    maskapai = st.sidebar.selectbox(
        "Maskapai",
        df["Maskapai"].dropna().unique(),
        index=list(df["Maskapai"].dropna().unique()).index(default_maskapai)
    )

    jenis = st.sidebar.selectbox("Jenis", ["D", "A"], index=0)

    tanggal_list = sorted(df["Tanggal"].dropna().dt.date.unique())
    tanggal = st.sidebar.selectbox("Tanggal", tanggal_list)

    df_filtered = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis) &
        (df["Tanggal"].dt.date == tanggal)
    ]

    st.subheader("Ringkasan")

    col1, col2, col3 = st.columns(3)

    total = int(df_filtered["Total"].sum())
    jumlah_flight = len(df_filtered)
    rata2 = int(total / jumlah_flight) if jumlah_flight > 0 else 0

    col1.metric("Total Penumpang", total)
    col2.metric("Jumlah Flight", jumlah_flight)
    col3.metric("Rata-rata / Flight", rata2)

    st.dataframe(df_filtered)

    rekap = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis)
    ].groupby(df["Tanggal"].dt.date)["Total"].sum()

    st.line_chart(rekap)

    st.download_button(
        "Download CSV",
        df_filtered.to_csv(index=False),
        "hasil.csv"
    )
else:
    st.info("Upload file Excel terlebih dahulu")
