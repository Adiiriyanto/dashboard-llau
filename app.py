import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

# =========================
# STYLE PREMIUM
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}
.metric-card {
    background: #1f2937;
    padding: 20px;
    border-radius: 14px;
    text-align: center;
    border: 1px solid #374151;
}
.metric-title {
    font-size: 14px;
    color: #9ca3af;
}
.metric-value {
    font-size: 32px;
    font-weight: bold;
    color: #22c55e;
}
h1, h2, h3 { color: #e5e7eb; }
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
col1, col2 = st.columns([8,2])

with col1:
    st.title("✈️ Dashboard LLAU Rendani Airport")

with col2:
    if st.button("🔄 Reset"):
        st.rerun()

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("### ✈️ LLAU Rendani Airport")
st.sidebar.markdown("---")

file = st.file_uploader("Upload Data Excel", type=["xlsx"])

if file:

    # =========================
    # LOAD
    # =========================
    try:
        df = pd.read_excel(file, header=[0,1])
        df.columns = [f"{a}_{b}".lower().strip() for a,b in df.columns]
    except:
        df = pd.read_excel(file)
        df.columns = [str(c).lower().strip() for c in df.columns]

    # =========================
    # DETEKSI KOLOM
    # =========================
    def find(k):
        return next((c for c in df.columns if k in c), None)

    col_tgl = find("tanggal")
    col_mask = find("maskapai") or find("operator")
    col_jns = find("pergerakan") or find("jenis")

    col_flight = next((c for c in df.columns if "nomor" in c and "penerbangan" in c), None)

    col_dew = find("dewasa")
    col_anak = find("anak")

    col_transit_dewasa = next((c for c in df.columns if "transit" in c and "dewasa" in c), None)
    col_transit_anak = next((c for c in df.columns if "transit" in c and "anak" in c), None)

    col_kargo = find("kargo")

    # =========================
    # DATAFRAME
    # =========================
    data = pd.DataFrame({
        "Tanggal": df[col_tgl],
        "Maskapai": df[col_mask],
        "Pergerakan": df[col_jns],
        "No Flight": df[col_flight],
        "Dewasa": df[col_dew],
        "Anak": df[col_anak],
        "Transit_Dewasa": df[col_transit_dewasa] if col_transit_dewasa else 0,
        "Transit_Anak": df[col_transit_anak] if col_transit_anak else 0,
        "Kargo": df[col_kargo] if col_kargo else 0
    })

    # =========================
    # CLEAN
    # =========================
    data["Tanggal"] = pd.to_datetime(data["Tanggal"], errors="coerce")
    data = data.dropna()

    data["No Flight"] = data["No Flight"].astype(str).str.extract(r'([A-Z]{1,3}[0-9]{2,4})')

    for c in ["Dewasa","Anak","Transit_Dewasa","Transit_Anak","Kargo"]:
        data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)

    # =========================
    # 🔥 LOGIC FINAL
    # =========================
    data["Dewasa_PJP2U"] = (data["Dewasa"] - data["Transit_Dewasa"]).clip(lower=0)
    data["Anak_PJP2U"] = (data["Anak"] - data["Transit_Anak"]).clip(lower=0)

    data["PJP2U"] = data["Dewasa_PJP2U"] + data["Anak_PJP2U"]

    # =========================
    # FILTER
    # =========================
    st.sidebar.header("Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(data["Maskapai"].unique()))
    flight = st.sidebar.selectbox("No Penerbangan", ["SEMUA"] + sorted(data["No Flight"].dropna().unique()))

    data = data[data["Maskapai"] == maskapai]
    if flight != "SEMUA":
        data = data[data["No Flight"] == flight]

    # =========================
    # KPI (KEMBALI PROFESIONAL)
    # =========================
    st.subheader("📊 Ringkasan")

    c1, c2, c3 = st.columns(3)

    def card(title, value):
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    with c1:
        card("Total PJP2U", int(data["PJP2U"].sum()))

    with c2:
        card("Dewasa PJP2U", int(data["Dewasa_PJP2U"].sum()))

    with c3:
        card("Anak PJP2U", int(data["Anak_PJP2U"].sum()))

    # =========================
    # GRAFIK
    # =========================
    st.subheader("📈 Tren PJP2U")
    st.line_chart(data.groupby(data["Tanggal"].dt.date)["PJP2U"].sum())

    # =========================
    # DETAIL
    # =========================
    st.subheader("📋 Detail Data")
    st.dataframe(data, use_container_width=True)

else:
    st.info("Upload file Excel untuk mulai")
