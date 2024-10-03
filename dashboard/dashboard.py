import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='white')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_approved_at').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").order_id.count().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return bystate_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_delivered_customer_date": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_delivered_customer_date"].dropna().dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days if pd.notnull(x) else None)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

# load berkas all_data.csv
def load_data():
    all_df = pd.read_csv("all_data.csv")
    datetime_columns = ["order_approved_at", "order_delivered_customer_date"]
    for column in datetime_columns:
        all_df[column] = pd.to_datetime(all_df[column])
    return all_df

all_df = load_data()

min_date = all_df["order_approved_at"].min()
max_date = all_df["order_approved_at"].max()
 
with st.sidebar:
    # Menambahkan logo Olist store
    st.image("https://github.com/syifafatma/Dataset-Proyek-Analisis-Data/blob/main/logo%20olist.png?raw=true")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_approved_at"] >= str(start_date)) & 
                (all_df["order_approved_at"] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('Olist Store Dashboard')

tab1, tab2, tab3 = st.tabs(["Penjualan", "Produk", "Pelanggan"])

with tab1:
    # Penjualan Harian
    st.subheader('Penjualan Harian')
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_orders = daily_orders_df.order_count.sum()
        st.metric("Total Penjualan", value=total_orders)
    
    with col2:
        total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL ", locale='es_CO') 
        st.metric("Total Revenue", value=total_revenue)
    
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(
        daily_orders_df["order_approved_at"],
        daily_orders_df["order_count"],
        marker='o', 
        linewidth=2,
        color="#1838de"
    )
    ax.tick_params(axis='y', labelsize=20)
    ax.tick_params(axis='x', labelsize=15)
    
    st.pyplot(fig)

    # Penjualan dan Revenue 6 bulan terakhir
    st.subheader("Penjualan dan Revenue 6 bulan terakhir")

    monthly_orders_df = all_df.resample(rule='M', on='order_approved_at').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    monthly_orders_df.index = monthly_orders_df.index.strftime('%Y-%m')
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)

    last_6_months_df = monthly_orders_df.tail(6)

    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(16, 6))

    sns.lineplot(x=last_6_months_df["order_approved_at"], y=last_6_months_df["order_count"], marker='o', color="#1838de", ax=ax[0])
    ax[0].set_title("Jumlah Penjualan dalam 6 Bulan Terakhir", fontsize=20)
    ax[0].tick_params(axis='x', labelsize=15)
    ax[0].tick_params(axis='y', labelsize=15)

    sns.lineplot(x=last_6_months_df["order_approved_at"], y=last_6_months_df["revenue"], marker='o', color="#1838de", ax=ax[1])
    ax[1].set_title("Jumlah Revenue dalam 6 Bulan Terakhir", fontsize=20)
    ax[1].tick_params(axis='x', labelsize=15)
    ax[1].tick_params(axis='y', labelsize=15)

    st.pyplot(fig)

with tab2:
    
    # Performa Produk terbaik dan terburuk
    st.subheader("Performa Produk Terbaik & Terburuk")
    
    fig, ax = plt.subplots(figsize=(24, 6))
    colors = ["#1838de", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    
    sns.barplot(x="order_id", y="product_category_name_english", data=sum_order_items_df.head(5), palette=colors, ax=ax)
    ax.set_ylabel(None)
    ax.set_xlabel("Total Penjualan", fontsize=15)
    ax.set_title("Performa Penjualan Terbaik", loc="center", fontsize=15)
    ax.tick_params(axis='y', labelsize=12)
    ax.tick_params(axis='x', labelsize=12)
    
    st.pyplot(fig)
    
    fig, ax = plt.subplots(figsize=(24, 6))
    colors = ["#1838de", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    
    sns.barplot(x="order_id", y="product_category_name_english", data=sum_order_items_df.sort_values(by="order_id", ascending=True).head(5), palette=colors, ax=ax)
    ax.set_ylabel(None)
    ax.set_xlabel("Total Penjualan", fontsize=15)
    ax.invert_xaxis()
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.set_title("Performa Penjualan Terburuk", loc="center", fontsize=15)
    ax.tick_params(axis='y', labelsize=12)
    ax.tick_params(axis='x', labelsize=12)
    
    st.pyplot(fig)
    
    
with tab3:
    
    # Waktu Pengiriman vs Penilaian Pelanggan (menggunakan data points)
    st.subheader("Waktu Pengiriman vs Penilaian Pelanggan")

    fig, ax = plt.subplots(figsize=(12, 6))

    sns.boxplot(x=all_df['review_score'], y=all_df['delivery_time'], palette="Blues")
    sns.stripplot(x=all_df['review_score'], y=all_df['delivery_time'], color='red', alpha=0.3, jitter=True)

    plt.title("Waktu Pengiriman vs. Penilaian Pelanggan (menggunakan data points)", fontsize=15)
    plt.xlabel("Skor", fontsize=15)
    plt.ylabel("Waktu Pengiriman (hari)", fontsize=15)

    st.pyplot(fig)
    
    # Demografi Pelanggan
    st.subheader("Demografi Pelanggan") 
    
    fig, ax = plt.subplots(figsize=(10, 9))
    colors = ["#1838de", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    sns.barplot(
        x="customer_count", 
        y="customer_state",
        data=bystate_df.sort_values(by="customer_count", ascending=False),
        palette=colors,
        ax=ax
    )
    ax.set_title("Jumlah Pelanggan berdasarkan Negara Bagian", loc="center", fontsize=20)
    ax.set_ylabel(None)
    ax.set_xlabel(xlabel='x',fontsize=5)
    ax.tick_params(axis='y', labelsize=15)
    ax.tick_params(axis='x', labelsize=15)

    st.pyplot(fig)

    # Analisis RFM
    st.subheader("Pelanggan Terbaik berdasarkan RFM Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_recency = round(rfm_df.recency.mean(), 1)
        st.metric("Rata-rata Recency (hari)", value=avg_recency)
    
    with col2:
        avg_frequency = round(rfm_df.frequency.mean(), 2)
        st.metric("Rata-rata Frequency", value=avg_frequency)
    
    with col3:
        avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL ", locale='es_CO') 
        st.metric("Rata-rata Monetary", value=avg_frequency)
    
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 10))
    colors = ["#1838de", "#1838de", "#1838de", "#1838de", "#1838de"]
    
    sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
    ax[0].set_ylabel(None)
    ax[0].set_xlabel("customer_id", fontsize=30)
    ax[0].set_title("Berdasarkan Recency (hari)", loc="center", fontsize=50)
    ax[0].tick_params(axis='y', labelsize=30)
    ax[0].tick_params(axis='x', labelsize=35)
    ax[0].set_xticklabels(ax[0].get_xticklabels(), rotation=45, fontstyle='italic')
    
    sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
    ax[1].set_ylabel(None)
    ax[1].set_xlabel("customer_id", fontsize=30)
    ax[1].set_title("Berdasarkan Frequency", loc="center", fontsize=50)
    ax[1].tick_params(axis='y', labelsize=30)
    ax[1].tick_params(axis='x', labelsize=35)
    ax[1].set_xticklabels(ax[1].get_xticklabels(), rotation=45, fontstyle='italic')

    sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
    ax[2].set_ylabel(None)
    ax[2].set_xlabel("customer_id", fontsize=30)
    ax[2].set_title("Berdasarkan Monetary", loc="center", fontsize=50)
    ax[2].tick_params(axis='y', labelsize=30)
    ax[2].tick_params(axis='x', labelsize=35)
    ax[2].set_xticklabels(ax[2].get_xticklabels(), rotation=45, fontstyle='italic')
    
    st.pyplot(fig)
 
st.caption('Made by Syifa Fatmawati')

