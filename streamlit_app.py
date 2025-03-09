import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

def create_daily_orders_df(df):
    df['order_approved_at_y'] = pd.to_datetime(df['order_approved_at_y'])
    daily_orders_df = df.resample(rule='D', on='order_approved_at_y').agg({
        "order_id": "nunique",
        "price_x": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price_x": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name").size().sort_values(ascending=False).reset_index(name='quantity')
    return sum_order_items_df

def create_bygender_df(df):
    bygender_df = df.groupby(by="seller_state").size().reset_index(name="customer_count")
    return bygender_df

def create_byage_df(df):
    byage_df = df.groupby(by="seller_city").size().reset_index(name="customer_count")
    return byage_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="seller_state").size().reset_index(name="customer_count")
    return bystate_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="seller_id_x", as_index=False).agg({
        "order_approved_at_y": "max",
        "order_id": "nunique",
        "price_x": "sum"
    })
    rfm_df.columns = ["seller_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_approved_at_y"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

df = pd.read_csv("main_data.csv")
df['order_approved_at_y'] = pd.to_datetime(df['order_approved_at_y'])
df.sort_values(by="order_approved_at_y", inplace=True)
df.reset_index(inplace=True)

min_date = df["order_approved_at_y"].min()
max_date = df["order_approved_at_y"].max()

with st.sidebar:
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = df[(df["order_approved_at_y"] >= str(start_date)) & 
             (df["order_approved_at_y"] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bygender_df = create_bygender_df(main_df)
byage_df = create_byage_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('Dashboard')

st.subheader('Daily Orders')
col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "IDR", locale='id_ID')
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_approved_at_y"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)

st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

sns.barplot(x="quantity", y="product_category_name", data=sum_order_items_df.head(5), palette="Blues_d", ax=ax[0])
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)

sns.barplot(x="quantity", y="product_category_name", data=sum_order_items_df.tail(5), palette="Reds_d", ax=ax[1])
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)

st.pyplot(fig)

st.subheader("Customer Demographics")
fig, ax = plt.subplots(figsize=(20, 10))
sns.barplot(
    y="customer_count",
    x="seller_state",
    data=bystate_df.sort_values(by="customer_count", ascending=False),
    palette="coolwarm",
    ax=ax
)
ax.set_title("Number of Customer by State", loc="center", fontsize=50)
ax.tick_params(axis='x', labelsize=35)
ax.tick_params(axis='y', labelsize=30)
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")
col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "IDR", locale='id_ID')
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))

sns.barplot(y="recency", x="seller_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette="Blues_d", ax=ax[0])
sns.barplot(y="frequency", x="seller_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette="Greens_d", ax=ax[1])
sns.barplot(y="monetary", x="seller_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette="Oranges_d", ax=ax[2])

st.pyplot(fig)
