
# 1. import library dulu
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(layout="wide") # - - - ini untuk tampilan otomatis wide

# 2. Judul Dashboard
st.title("📊 Dashboard DSCM")

# 3. Koneksi ke Database dan KO Persediaan
with sqlite3.connect("data_base_2024.db") as conn_2024:
    df_data_2024 = pd.read_sql("SELECT * FROM Db2024", conn_2024)
with sqlite3.connect("data_base_2025.db") as conn_2025:
    df_data_2025 = pd.read_sql("SELECT * FROM Db2025", conn_2025)
with sqlite3.connect("KO2024.db") as conn_2024:
    df_data_KO_2024 = pd.read_sql("SELECT * FROM KO2024", conn_2024)
with sqlite3.connect("KO2025.db") as conn_2025:
    df_data_KO_2025 = pd.read_sql("SELECT * FROM KO2025", conn_2025)

# 4. Gabung data
    df_all_data = pd.concat([df_data_2024,df_data_2025])
    df_all_KO = pd.concat([df_data_KO_2024,df_data_KO_2025])

# 5. Normalisasi Nama Kolom
    # - - - Untuk menghindari error KeyError karena perbedaan kapitalisasi/spasi
    df_all_data.columns = df_all_data.columns.str.strip().str.lower()
    df_all_KO.columns = df_all_KO.columns.str.strip().str.lower()

# 6. Sidebar Filter
st.sidebar.title("🔍 Filter")

mode_mobile = st.sidebar.checkbox("Mode Mobile (simulasi)") # ini untuk tampilan hape

# - - - Filter tahun
tahun_terpilih = st.sidebar.selectbox(
    "Pilih Tahun", 
    sorted(df_all_data["tahun"].unique())
    )

# - - - Urutan bulan baku
urutan_bulan = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]

# - - - Ambil bulan yang tersedia untuk tahun terpilih dan urutkan sesuai urutan bulan
bulan_tersedia = df_all_data[df_all_data["tahun"] == tahun_terpilih]["bulan"].unique()
bulan_terurut = [b for b in urutan_bulan if b in bulan_tersedia]

# - - - Filter bulan
bulan_terpilih = st.sidebar.multiselect(
    "Pilih Bulan",
    options=bulan_terurut,
    default=bulan_terurut
    )
# - - - Filter pabrik
pabrik_terpilih = st.sidebar.multiselect(
    "Pilih Pabrik", 
    options=sorted(df_all_data["keterangan_pat"].unique()),
    default=sorted(df_all_data["keterangan_pat"].unique())
    )


# 7. INI BAGIAN SETELAH SIDE BAR FILTER
# --- Filter Data
data_tahun = df_all_data[(df_all_data["tahun"] == tahun_terpilih)]
data_tahun = data_tahun[data_tahun["keterangan_pat"].isin(pabrik_terpilih)]

# - - - Filter bulan multiselect
data_tahun = data_tahun[data_tahun["bulan"].isin(bulan_terpilih)]

data_akhir_minggu = data_tahun[data_tahun["minggu"].str.lower() == "akhir"
    ] #---ini untuk total yang terpengaruh bulan dan pabrik

# - - - ini kebijakan yang tepengaruh bulan dan pabrik
df_kebijakan_tahun = df_all_KO[
    (df_all_KO["tahun"] == tahun_terpilih)
    ]

total_ko_min_tahun = df_kebijakan_tahun["ko_minimal"].sum() #/ 1_000_000
total_ko_maks_tahun = df_kebijakan_tahun["ko_maksimal"].sum() #/ 1_000_000

# --- untuk Chart 3: Rincian Saldo Akhir Harga per Pabrik
df_perpabrik = data_akhir_minggu.groupby("kode_pat", as_index=False)["saldo_akhir_harga"].sum()
df_perpabrik["saldo_akhir_harga"] = df_perpabrik["saldo_akhir_harga"] / 1_000_000  # Konversi ke juta


# - - - Cek jika tidak ada data
if data_akhir_minggu.empty:
    st.warning("⚠️ Tidak ada data untuk filter yang dipilih!")
    st.stop()

# --- Hitung Data untuk Visualisasi

df_pie_chart1 = data_akhir_minggu.groupby("keterangan_pat", as_index=False)["saldo_akhir_harga"].sum()####
df_pie_chart1["saldo_akhir_harga"] = df_pie_chart1["saldo_akhir_harga"] / 1_000_000 ####

df_saldo_perbulan = data_akhir_minggu.groupby(["keterangan_pat", "bulan"]).agg({
    "saldo_akhir_harga": "sum"
}).reset_index()

df_persediaan_pabrik = df_saldo_perbulan.groupby("keterangan_pat").agg({
    "saldo_akhir_harga": "sum"
}).reset_index()

df_persediaan_pabrik["saldo_akhir_harga"] = df_persediaan_pabrik["saldo_akhir_harga"] / 1_000_000  # Konversi ke juta

# --- Filter Data Kebijakan Sesuai Tahun dan Bulan
df_kebijakan_terpilih = df_all_KO[
    (df_all_KO["tahun"] == tahun_terpilih) &
    (df_all_KO["bulan"].isin(bulan_terpilih))
]

# Hitung total KO dan persediaan
total_ko_min = df_kebijakan_terpilih["ko_minimal"].sum()
total_ko_maks = df_kebijakan_terpilih["ko_maksimal"].sum()
total_persediaan = data_akhir_minggu["saldo_akhir_harga"].sum()

df_kebijakan_terpilih = df_kebijakan_terpilih[df_kebijakan_terpilih["keterangan_pat"].isin(pabrik_terpilih)]

# --- KPI
total_persediaan = df_pie_chart1["saldo_akhir_harga"].sum()
total_ko_min = df_kebijakan_terpilih["ko_minimal"].sum() / 1_000_000
total_ko_maks = df_kebijakan_terpilih["ko_maksimal"].sum() / 1_000_000

# --- Tampilkan KPI
st.subheader("📌 KPI Utama")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Persediaan (Juta)", f"{total_persediaan:,.2f}")
with col2:
    st.metric("Selisih vs KO Minimal", f"{total_persediaan - total_ko_min:,.2f}")
with col3:
    st.metric("Selisih vs KO Maksimal", f"{total_persediaan - total_ko_maks:,.2f}")


tab1 = st.tabs(["📈 Visualisasi"])[0]

with tab1:
    fig_pie = px.pie(
        df_pie_chart1,
        names="keterangan_pat",
        values="saldo_akhir_harga",
        title=f"Persediaan per Pabrik Tahun {tahun_terpilih} (Juta)",
        hole=0.4
    )
    fig_pie.update_layout(
        margin=dict(l=180, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            y=0,
            yanchor="top",
            x=0.5,
            xanchor="center"
        ),
        height=700,
        width=700
    )
    fig_pie.update_traces(
        hovertemplate='%{label}<br>Jumlah: %{value}<br>Persen: %{percent}<extra></extra>',
        textinfo='percent',
        textposition='inside'
    )
    
    # BAR CHART KO MIN, PERS, KO MAKS
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=["KO Minimal"], y=[total_ko_min], name="KO Minimal", marker_color="red", text=[total_ko_min],textposition="outside", texttemplate="%{text}"))
    fig_bar.add_trace(go.Bar(x=["Persediaan"], y=[total_persediaan], name="Persediaan", marker_color="blue", text=[total_persediaan],textposition="outside", texttemplate="%{text}"))
    fig_bar.add_trace(go.Bar(x=["KO Maksimal"], y=[total_ko_maks], name="KO Maksimal", marker_color="green", text=[total_ko_maks],textposition="outside", texttemplate="%{text}"))
    
    fig_bar.update_layout(
        title=f"Perbandingan KO Minimal, Persediaan, dan KO Maksimal - {tahun_terpilih}",
        barmode="group",
        xaxis_title="Kategori",
        yaxis_title="Saldo Akhir Harga (Juta Rupiah)",
        template="plotly_white",
        height=700,
        width=700,
        showlegend=False,
        uniformtext_minsize=8,
        uniformtext_mode='show',
    )
    fig_bar.update_yaxes(range=[0, max(total_ko_min, total_persediaan, total_ko_maks) * 1.2])
    
    # BAR CHART PER PABRIK
    fig_perpabrik = px.bar(
        df_perpabrik.sort_values("saldo_akhir_harga", ascending=False),
        x="kode_pat",
        y="saldo_akhir_harga",
        text="saldo_akhir_harga",
        title="Saldo Akhir Harga per Pabrik (Juta)",
        color_discrete_sequence=["#EF553B"]
    )
    
    fig_perpabrik.update_layout(
        xaxis_title="Kode PAT / Pabrik",
        yaxis_title="Saldo Akhir Harga (Juta)",
        height=500,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    fig_perpabrik.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    
    # RESPONSIF
    if mode_mobile:
        st.plotly_chart(fig_pie.update_layout(height=400), use_container_width=True)
        st.plotly_chart(fig_bar.update_layout(height=400), use_container_width=True)
        st.plotly_chart(fig_perpabrik.update_layout(height=400), use_container_width=True)
    else:
        tab1, tab2 = st.tabs(["Ringkasan KO", "Rincian per Pabrik"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                st.plotly_chart(fig_bar, use_container_width=True)
    
        with tab2:
            st.plotly_chart(fig_perpabrik, use_container_width=True)
    
