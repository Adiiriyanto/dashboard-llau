import streamlit as st
import pandas as pd

# ========================
# CONFIG + STYLE
# ========================
st.set_page_config(page_title="LLAU Dashboard", layout="wide")

st.markdown("""
<style>
.card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}
.kpi-green { color: #22c55e; font-size: 28px; font-weight: bold; }
.kpi-red { color: #ef4444; font-size: 28px; font-weight: bold; }
.kpi-title { font-size: 14px; color: #9ca3af; }
.big-number { font-size: 40px; font-weight: bold; color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

st.title("✈️ Dashboard LLAU Rendani Airport")

# ========================
# UPLOAD
# ========================
uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

if uploaded_file:

    # ========================
    # LOAD DATA
    # ========================
    df = pd.read_excel(uploaded_file, skiprows=9)

    # Bersihkan header
    df.columns = [str(col).strip() for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    # ========================
    # AUTO MAPPING
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

    # ========================
    # VALIDASI
    # ========================
    if "Tanggal" not in df.columns or "Maskapai" not in df.columns:
        st.error("Format file tidak dikenali")
        st.write("Kolom terbaca:", df.columns.tolist())
        st.stop()

    # ========================
    # NORMALISASI TANGGAL (FIX UTAMA)
    # ========================
    df["Tanggal"] = pd.to_datetime(
        df["Tanggal"],
        errors="coerce",
        dayfirst=True  # 🔥 penting
    )

    df = df[df["Tanggal"].notna()]

    if "Jenis" not in df.columns:
        df["Jenis"] = "D"

    # ========================
    # NUMERIC SAFE
    # ========================
    for col in ["Dewasa", "Anak", "Bayi", "Transit", "Kargo"]:
        if col not in df.columns:
            df[col] = 0

        if isinstance(df[col], pd.DataFrame):
            df[col] = df[col].iloc[:, 0]

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ========================
    # TOTAL
    # ========================
    df["Total"] = df["Dewasa"] + df["Anak"] + df["Bayi"] + df["Transit"]

    # ========================
    # SIDEBAR FILTER
    # ========================
    st.sidebar.header("⚙️ Filter")

    maskapai = st.sidebar.selectbox(
        "Maskapai",
        sorted(df["Maskapai"].dropna().unique())
    )

    jenis = st.sidebar.selectbox("Jenis", ["D", "A"])

    # ========================
    # RANGE TANGGAL (FITUR BARU)
    # ========================
    min_date = df["Tanggal"].min().date()
    max_date = df["Tanggal"].max().date()

    date_range = st.sidebar.date_input(
        "Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # handle jika user pilih 1 tanggal saja
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    kategori = st.sidebar.selectbox(
        "Kategori",
        ["Semua","Dewasa","Dewasa + Anak","Bayi","Transit","Kargo"]
    )

    # ========================
    # FILTER DATA
    # ========================
    df_filtered = df[
        (df["Maskapai"] == maskapai) &
        (df["Jenis"] == jenis) &
        (df["Tanggal"].dt.date >= start_date) &
        (df["Tanggal"].dt.date <= end_date)
    ].copy()

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

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Total Penumpang", int(df["Total"].sum()))
    k2.metric("Flight", len(df))
    k3.metric("Transit", int(df["Transit"].sum()))
    k4.metric("Kargo", int(df["Kargo"].sum()))

    warna = "kpi-green" if total_hasil > 0 else "kpi-red"

    k5.markdown(f"""
    <div class="card">
        <div class="kpi-title">Hasil Pencarian</div>
        <div class="{warna}">{total_hasil}</div>
    </div>
    """, unsafe_allow_html=True)

    # ========================
    # RINGKASAN BESAR
    # ========================
    st.subheader("📌 Ringkasan Hasil Pencarian")

    st.markdown(f"""
    <div class="card">
        <div class="kpi-title">Kategori: {kategori}</div>
        <div class="big-number">{total_hasil}</div>
    </div>
    """, unsafe_allow_html=True)

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

    cols = ["Hasil"] + [c for c in df_filtered.columns if c != "Hasil"]
    df_filtered = df_filtered[cols]

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
    st.info("Upload file Excel terlebih dahulu")
