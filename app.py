import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}
section[data-testid="stSidebar"] {
    background-color: #111827;
}
.metric-card {
    background: #1f2937;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #374151;
}
.metric-value {
    font-size: 28px;
    font-weight: bold;
}
.green { color: #22c55e; }
.red { color: #ef4444; }
.blue { color: #3b82f6; }
.orange { color: #f59e0b; }
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

    try:
        df = pd.read_excel(file, header=[0,1])
        multi = True
    except:
        df = pd.read_excel(file)
        multi = False

    def clean(x):
        return re.sub(r'\s+', ' ', str(x)).strip().lower()

    if multi:
        df.columns = [clean(a) + "_" + clean(b) for a,b in df.columns]
    else:
        df.columns = [clean(c) for c in df.columns]

    # =========================
    # DETEKSI KOLOM
    # =========================
    col_tgl = next((c for c in df.columns if "tanggal" in c), None)
    col_mask = next((c for c in df.columns if "maskapai" in c or "operator" in c), None)
    col_jns = next((c for c in df.columns if "pergerakan" in c or "jenis" in c), None)

    col_flight = None
    for c in df.columns:
        if "nomor" in c and "penerbangan" in c:
            col_flight = c
            break

    col_dew = next((c for c in df.columns if "dewasa" in c), None)
    col_anak = next((c for c in df.columns if "anak" in c), None)
    col_bayi = next((c for c in df.columns if "bayi" in c), None)

    col_transit_dewasa = next((c for c in df.columns if "transit" in c and "dewasa" in c), None)
    col_transit_anak = next((c for c in df.columns if "transit" in c and "anak" in c), None)
    col_transit_total = next((c for c in df.columns if "transit" in c), None)

    col_kargo = next((c for c in df.columns if "kargo" in c), None)

    if not col_tgl or not col_mask:
        st.error("Format file tidak dikenali")
        st.write(df.columns)
        st.stop()

    # =========================
    # DATAFRAME
    # =========================
    data = pd.DataFrame({
        "Tanggal": df[col_tgl],
        "Maskapai": df[col_mask],
        "Pergerakan": df[col_jns] if col_jns else "D",
        "No Flight Raw": df[col_flight] if col_flight else "",
        "Dewasa": df[col_dew] if col_dew else 0,
        "Anak": df[col_anak] if col_anak else 0,
        "Bayi": df[col_bayi] if col_bayi else 0,
        "Transit_Dewasa": df[col_transit_dewasa] if col_transit_dewasa else 0,
        "Transit_Anak": df[col_transit_anak] if col_transit_anak else 0,
        "Transit_Total": df[col_transit_total] if col_transit_total else 0,
        "Kargo": df[col_kargo] if col_kargo else 0
    })

    # =========================
    # CLEAN
    # =========================
    data["Tanggal"] = pd.to_datetime(data["Tanggal"], errors="coerce", dayfirst=True)
    data = data.dropna(subset=["Tanggal"])

    data["Pergerakan"] = data["Pergerakan"].astype(str).str.upper().replace({"D":"Departure","A":"Arrival"})

    # =========================
    # PARSE FLIGHT
    # =========================
    def extract_flight(x):
        if pd.isna(x):
            return "UNKNOWN"
        x = str(x).upper().strip()
        m = re.search(r'[A-Z]{1,3}[0-9]{2,4}', x)
        return m.group(0) if m else "UNKNOWN"

    data["No Flight"] = data["No Flight Raw"].apply(extract_flight)

    for c in ["Dewasa","Anak","Bayi","Transit_Dewasa","Transit_Anak","Transit_Total","Kargo"]:
        data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)

    # =========================
    # 🔥 PERHITUNGAN FINAL PJP2U
    # =========================
    data["Dewasa_PJP2U"] = (data["Dewasa"] - data["Transit_Dewasa"]).clip(lower=0)
    data["Anak_PJP2U"] = (data["Anak"] - data["Transit_Anak"]).clip(lower=0)

    data["PJP2U"] = data["Dewasa_PJP2U"] + data["Anak_PJP2U"]

    # =========================
    # FILTER
    # =========================
    st.sidebar.header("Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(data["Maskapai"].unique()))
    flight = st.sidebar.selectbox("No Penerbangan", ["SEMUA"] + sorted(data["No Flight"].unique()))
    pergerakan = st.sidebar.selectbox("Pergerakan", ["SEMUA","Departure","Arrival"])

    mode = st.sidebar.radio("Tanggal", ["1 Hari","Rentang"])

    min_d = data["Tanggal"].min().date()
    max_d = data["Tanggal"].max().date()

    if mode == "1 Hari":
        d = st.sidebar.date_input("Tanggal", min_d)
        start = pd.to_datetime(d)
        end = start
    else:
        dr = st.sidebar.date_input("Rentang", (min_d, max_d))
        start = pd.to_datetime(dr[0])
        end = pd.to_datetime(dr[1])

    f = data.copy()
    f = f[f["Maskapai"] == maskapai]

    if flight != "SEMUA":
        f = f[f["No Flight"] == flight]

    if pergerakan != "SEMUA":
        f = f[f["Pergerakan"] == pergerakan]

    f = f[(f["Tanggal"] >= start) & (f["Tanggal"] <= end)]

    total = int(f["PJP2U"].sum())

    # =========================
    # HASIL
    # =========================
    st.subheader("📌 Total PJP2U")
    st.markdown(f"<h2 style='color:#22c55e'>{total}</h2>", unsafe_allow_html=True)

    # =========================
    # DETAIL
    # =========================
    st.subheader("📋 Detail Data")
    st.dataframe(f, use_container_width=True)

else:
    st.info("Upload file Excel untuk mulai")
