# ========================
# FILTER TAMBAHAN
# ========================

st.sidebar.subheader("🔎 Pencarian")

search = st.sidebar.text_input("Cari data (maskapai / flight / dll)")

st.sidebar.subheader("🎯 Pilih Jenis Data")

kategori = st.sidebar.selectbox(
    "Kategori Penumpang",
    ["Semua", "Dewasa", "Dewasa + Anak", "Bayi", "Transit"]
)

# ========================
# FILTER UTAMA
# ========================

df_filtered = df[
    (df["Maskapai"] == maskapai) &
    (df["Jenis"] == jenis) &
    (df["Tanggal"].dt.date == tanggal)
]

# ========================
# APPLY SEARCH
# ========================
if search:
    df_filtered = df_filtered[df_filtered.apply(
        lambda row: row.astype(str).str.contains(search, case=False).any(),
        axis=1
    )]

# ========================
# HITUNG TOTAL SESUAI PILIHAN
# ========================
if kategori == "Dewasa":
    df_filtered["TotalKategori"] = df_filtered["Dewasa"]

elif kategori == "Dewasa + Anak":
    df_filtered["TotalKategori"] = (
        df_filtered["Dewasa"].fillna(0) +
        df_filtered["Anak"].fillna(0)
    )

elif kategori == "Bayi":
    df_filtered["TotalKategori"] = df_filtered["Bayi"]

elif kategori == "Transit":
    if "Transit" in df.columns:
        df_filtered["TotalKategori"] = df_filtered["Transit"]
    else:
        st.warning("Kolom Transit tidak ditemukan")
        df_filtered["TotalKategori"] = 0

else:  # Semua
    df_filtered["TotalKategori"] = df_filtered["Total"]

# ========================
# KPI UPDATE
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
st.dataframe(df_filtered, use_container_width=True)
