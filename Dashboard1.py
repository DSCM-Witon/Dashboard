# ============================================
# 1. IMPORT LIBRARY
# ============================================
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")  # Tampilan lebar

# ============================================
# 2. JUDUL DASHBOARD
# ============================================
st.title("📊 Dashboard DSCM")

# ============================================
# 3. LOAD DATA DARI DATABASE
# ============================================
with sqlite3.connect("data_base_2024.db") as conn_2024:
    df_data_2024 = pd.read_sql("SELECT * FROM Db2024", conn_2024)
with sqlite3.connect("data_base_2025.db") as conn_2025:
    df_data_2025 = pd.read_sql("SELECT * FROM Db2025", conn_2025)
with sqlite3.connect("KO2024.db") as conn_2024:
    df_data_KO_2024 = pd.read_sql("SELECT * FROM KO2024", conn_2024)
with sqlite3.connect("KO2025.db") as conn_2025:
    df_data_KO_2025 = pd.read_sql("SELECT * FROM KO2025", conn_2025)

# ============================================
# 4. GABUNGKAN & NORMALISASI KOLOM DATA
# ============================================
df_all_data = pd.concat([df_data_2024, df_data_2025])
df_all_KO = pd.concat([df_data_KO_2024, df_data_KO_2025])

df_all_data.columns = df_all_data.columns.str.strip().str.lower()
df_all_KO.columns = df_all_KO.columns.str.strip().str.lower()

# ============================================
# 5. FILTER USER (SIDEBAR / LAYAR ATAS)
# ============================================
mode_mobile = st.sidebar.checkbox("Mode Mobile (simulasi)", key="mode_mobile")

if mode_mobile:
    st.markdown("### 📱 Filter (Mode Mobile)")

    tahun_terpilih = st.selectbox("Pilih Tahun", sorted(df_all_data["tahun"].unique()), key="tahun_mobile")

    urutan_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    bulan_tersedia = df_all_data[df_all_data["tahun"] == tahun_terpilih]["bulan"].unique()
    bulan_terurut = [b for b in urutan_bulan if b in bulan_tersedia]

    bulan_terpilih = st.multiselect("Pilih Bulan", options=bulan_terurut, default=bulan_terurut, key="bulan_mobile")
    pabrik_terpilih = st.multiselect("Pilih Pabrik", options=sorted(df_all_data["keterangan_pat"].unique()), default=sorted(df_all_data["keterangan_pat"].unique()), key="pabrik_mobile")

else:
    st.sidebar.title("🔍 Filter")
    tahun_terpilih = st.sidebar.selectbox("Pilih Tahun", sorted(df_all_data["tahun"].unique()), key="tahun_sidebar")

    urutan_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    bulan_tersedia = df_all_data[df_all_data["tahun"] == tahun_terpilih]["bulan"].unique()
    bulan_terurut = [b for b in urutan_bulan if b in bulan_tersedia]

    bulan_terpilih = st.sidebar.multiselect("Pilih Bulan", options=bulan_terurut, default=bulan_terurut, key="bulan_sidebar")
    pabrik_terpilih = st.sidebar.multiselect("Pilih Pabrik", options=sorted(df_all_data["keterangan_pat"].unique()), default=sorted(df_all_data["keterangan_pat"].unique()), key="pabrik_sidebar")

# ============================================
# 6. FILTER DATA SESUAI PILIHAN USER
# ============================================
data_tahun = df_all_data[df_all_data["tahun"] == tahun_terpilih]
data_tahun = data_tahun[data_tahun["keterangan_pat"].isin(pabrik_terpilih)]
data_tahun = data_tahun[data_tahun["bulan"].isin(bulan_terpilih)]

data_akhir_minggu = data_tahun[data_tahun["minggu"].str.lower() == "akhir"]

data_terfilter = df_all_data[
    (df_all_data["tahun"] == tahun_terpilih) &
    (df_all_data["bulan"].isin(bulan_terpilih)) &
    (df_all_data["minggu"].str.lower() == "akhir")
]

df_kebijakan_setahun = df_all_KO[df_all_KO["tahun"] == tahun_terpilih]

df_kebijakan_terpilih = df_all_KO[
    (df_all_KO["tahun"] == tahun_terpilih) &
    (df_all_KO["bulan"].isin(bulan_terpilih)) &
    (df_all_KO["keterangan_pat"].isin(pabrik_terpilih))
]

if data_akhir_minggu.empty:
    st.warning("⚠️ Tidak ada data untuk filter yang dipilih!")
    st.stop()

# ============================================
# 7. OLAH DATA UNTUK KPI DAN CHART
# ============================================
total_ko_min = df_kebijakan_terpilih["ko_minimal"].sum() / 1_000_000
total_ko_maks = df_kebijakan_terpilih["ko_maksimal"].sum() / 1_000_000
total_persediaan = data_akhir_minggu["saldo_akhir_harga"].sum() / 1_000_000

df_pie_chart1 = data_akhir_minggu.groupby("keterangan_pat", as_index=False)["saldo_akhir_harga"].sum()
df_pie_chart1["saldo_akhir_harga"] /= 1_000_000

df_saldo_perbulan = data_akhir_minggu.groupby(["keterangan_pat", "bulan"]).agg({
    "saldo_akhir_harga": "sum"
}).reset_index()

df_persediaan_pabrik = df_saldo_perbulan.groupby("keterangan_pat").agg({
    "saldo_akhir_harga": "sum"
}).reset_index()

df_persediaan_pabrik["saldo_akhir_harga"] /= 1_000_000

# --- Data untuk Chart 3 (Perbandingan per Pabrik)
df_saldo = data_akhir_minggu.groupby("keterangan_pat", as_index=False)["saldo_akhir_harga"].sum()
df_saldo["saldo_akhir_harga"] /= 1_000_000

df_ko = df_kebijakan_terpilih.groupby("keterangan_pat", as_index=False)[["ko_minimal", "ko_maksimal"]].sum()
df_ko["ko_minimal"] /= 1_000_000
df_ko["ko_maksimal"] /= 1_000_000

df_chart3 = pd.merge(df_saldo, df_ko, on="keterangan_pat", how="inner")


# ============================================
# 8. TAMPILKAN KPI
# ============================================
st.subheader("📌 KPI Utama")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Persediaan (Juta)", f"{total_persediaan:,.2f}")
with col2:
    st.metric("Selisih vs KO Minimal", f"{total_persediaan - total_ko_min:,.2f}")
with col3:
    st.metric("Selisih vs KO Maksimal", f"{total_persediaan - total_ko_maks:,.2f}")

# ============================================
# 9. VISUALISASI CHART
# ============================================
tab1 = st.tabs(["📈 Visualisasi"])[0]

with tab1:
    # Pie Chart
    fig_pie = px.pie(
        df_pie_chart1,
        names="keterangan_pat",
        values="saldo_akhir_harga",
        title=f"Persediaan per Pabrik Tahun {tahun_terpilih} (Juta)",
        hole=0.4
    )
    fig_pie.update_layout(
        margin=dict(l=80, r=80, t=50, b=20),
        legend=dict(orientation="h", y=0, yanchor="top", x=0.5, xanchor="center"),
        height=600 if mode_mobile else 700,
        width=600 if mode_mobile else 700
    )
    fig_pie.update_traces(
        hovertemplate='%{label}<br>Jumlah: %{value}<br>Persen: %{percent}<extra></extra>',
        textinfo='percent',
        textposition='inside'
    )

    # Bar Chart (Total)
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=["KO Minimal"], y=[total_ko_min], name="KO Minimal", marker_color="red", text=[total_ko_min], textposition="outside", texttemplate="%{text}"))
    fig_bar.add_trace(go.Bar(x=["Persediaan"], y=[total_persediaan], name="Persediaan", marker_color="blue", text=[total_persediaan], textposition="outside", texttemplate="%{text}"))
    fig_bar.add_trace(go.Bar(x=["KO Maksimal"], y=[total_ko_maks], name="KO Maksimal", marker_color="green", text=[total_ko_maks], textposition="outside", texttemplate="%{text}"))
    fig_bar.update_layout(
        title=f"Perbandingan KO Minimal, Persediaan, dan KO Maksimal - {tahun_terpilih}",
        barmode="group",
        xaxis_title="Kategori",
        yaxis_title="Saldo Akhir Harga (Juta Rupiah)",
        template="plotly_white",
        height=700,
        width=700,
        showlegend=False
    )
    fig_bar.update_yaxes(range=[0, max(total_ko_min, total_persediaan, total_ko_maks) * 1.2])

    # Bar Chart (Chart 3 per pabrik)
    fig_chart3 = go.Figure()
    fig_chart3.add_trace(go.Bar(x=df_chart3["keterangan_pat"], y=df_chart3["ko_minimal"], name="KO Minimal", marker_color="red", hovertemplate="%{y}"))
    fig_chart3.add_trace(go.Bar(x=df_chart3["keterangan_pat"], y=df_chart3["saldo_akhir_harga"], name="Saldo Persediaan", marker_color="blue", hovertemplate="%{y}"))
    fig_chart3.add_trace(go.Bar(x=df_chart3["keterangan_pat"], y=df_chart3["ko_maksimal"], name="KO Maksimal", marker_color="green", hovertemplate="%{y}"))
    fig_chart3.update_layout(
        barmode="group",
        title="Perbandingan KO & Persediaan per Pabrik",
        xaxis_title="Pabrik",
        yaxis_title="Nilai (Juta Rupiah)",
        height=600,
        showlegend=False,
    )

    # Pie Chart (Chart  kondisi suku cadang)


    # TAMPILKAN CHART SESUAI MODE
    if mode_mobile:
        st.plotly_chart(fig_pie, use_container_width=True)
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("### 📊 Chart 3: Rincian Persediaan vs KO per Pabrik")
        st.plotly_chart(fig_chart3, use_container_width=True)
        st.markdown("### 📊 Chart 4: Trend Bulanan Persediaan per Pabrik")
        st.plotly_chart(fig_chart4, use_container_width=True)

        
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("Rincian Persediaan vs KO per Pabrik")
        st.plotly_chart(fig_chart3, use_container_width=True)

