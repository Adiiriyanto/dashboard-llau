import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a, #1e293b); }
section[data-testid="stSidebar"] { background-color: #111827; }
.metric-card {
    background: #1f2937; padding: 15px; border-radius: 12px;
    text-align: center; border: 1px solid #374151;
}
.metric-value { font-size: 28px; font-weight: bold; }
.green { color: #22c55e; }
.red { color: #ef4444; }
.blue { color: #3b82f6; }
.orange { color: #f59e0b; }
h1, h2, h3 { color: #e5e7eb; }
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([8,2])
with col1:
    st.title("✈️ Dashboard Operasional LLAU Rendani Airport")
with col2:
    if st.button("🔄 Reset"):
        st.rerun()

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

    def find(k):
        for c in df.columns:
            if k in c:
                return c
        return None

    col_tgl = find("tanggal")
    col_mask = find("operator") or find("maskapai")
    col_jns = find("pergerakan") or find("jenis")

    col_dew = find("dewasa")
    col_anak = find("anak")
    col_bayi = find("bayi")

    col_transit_dewasa = None
    for c in df.columns:
        if "transit" in c and "dewasa" in c:
            col_transit_dewasa = c

    col_transit_total = find("transit")
    col_kargo = find("kargo")

    data = pd.DataFrame({
        "Tanggal": df[col_tgl],
        "Maskapai": df[col_mask],
        "Pergerakan": df[col_jns] if col_jns else "D",
        "Dewasa": df[col_dew] if col_dew else 0,
        "Anak": df[col_anak] if col_anak else 0,
        "Bayi": df[col_bayi] if col_bayi else 0,
        "Transit_Dewasa": df[col_transit_dewasa] if col_transit_dewasa else 0,
        "Transit_Total": df[col_transit_total] if col_transit_total else 0,
        "Kargo": df[col_kargo] if col_kargo else 0
    })

    data["Tanggal"] = pd.to_datetime(data["Tanggal"], errors="coerce", dayfirst=True)
    data = data.dropna(subset=["Tanggal"])

    # 🔥 PERGERAKAN FIX
    data["Pergerakan"] = data["Pergerakan"].astype(str).str.upper().str.strip()
    data["Pergerakan"] = data["Pergerakan"].replace({
        "D": "Departure",
        "A": "Arrival"
    })

    for c in ["Dewasa","Anak","Bayi","Transit_Dewasa","Transit_Total","Kargo"]:
        data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)

    data["Dewasa_Bersih"] = (data["Dewasa"] - data["Transit_Dewasa"]).clip(lower=0)
    data["PJP2U"] = ((data["Dewasa"] + data["Anak"]) - data["Transit_Total"]).clip(lower=0)

    st.sidebar.header("Filter")

    maskapai = st.sidebar.selectbox("Maskapai", sorted(data["Maskapai"].unique()))
    pergerakan = st.sidebar.selectbox("Pergerakan", ["SEMUA","Departure","Arrival"])

    if pergerakan != "SEMUA":
        data = data[data["Pergerakan"] == pergerakan]

    st.dataframe(data)

else:
    st.info("Upload file Excel untuk mulai")
