"""Interactive read-only cryptocurrency analytics dashboard.

Run: streamlit run dashboard.py
Requires DATABASE_URL or DB_* variables pointing to the ETL PostgreSQL database.
"""
import os
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

st.set_page_config(page_title="Crypto Insights Explorer", page_icon="📈", layout="wide")
st.title("Crypto Insights Explorer")
st.caption("Historical hourly snapshots from your own ETL pipeline · Educational analytics, not investment advice")


def database_url():
    if os.getenv("DATABASE_URL"):
        # Name the installed driver: SQLAlchemy rejects postgres:// and may
        # default postgresql:// to a driver this project does not install.
        url = os.environ["DATABASE_URL"]
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg2://" + url[len(prefix):]
        return url
    if not os.getenv("DB_PASSWORD"):
        raise ValueError("Set DATABASE_URL or DB_PASSWORD and the DB_* connection variables.")
    return URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER") or "postgres",
        password=os.environ["DB_PASSWORD"],
        host=os.getenv("DB_HOST") or "localhost",
        port=int(os.getenv("DB_PORT") or "5432"),
        database=os.getenv("DB_NAME") or "crypto_etl",
    )


@st.cache_data(ttl=3600, show_spinner="Loading historical prices…")
def fetch_prices():
    engine = create_engine(database_url(), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text("""
                SELECT coin, currency, price, created_at
                FROM crypto_prices
                WHERE price IS NOT NULL AND created_at IS NOT NULL
                ORDER BY created_at ASC, id ASC
            """), connection)
    finally:
        engine.dispose()


if st.sidebar.button("Refresh data now"):
    fetch_prices.clear()

try:
    df = fetch_prices()
except Exception as error:
    # Show only the error type: driver messages can repeat parts of the URL,
    # including the password, and this page may be public.
    st.error("Could not load historical prices. Check DATABASE_URL or the DB_* variables, and run the ETL first.")
    st.code(type(error).__name__)
    st.stop()

if df.empty:
    st.info("No snapshots yet. Run the ETL pipeline to collect prices.")
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df = df.dropna(subset=["price", "created_at"])
df = df[df["price"] >= 0]
if df.empty:
    st.warning("No valid price snapshots found.")
    st.stop()

coins = sorted(df["coin"].unique())
coin = st.sidebar.selectbox("Explore a coin", coins)
period = st.sidebar.selectbox("History", ["24 hours", "7 days", "30 days", "All time"], index=1)
show_average = st.sidebar.checkbox("Show 7-snapshot moving average", value=True)

history = df[df["coin"] == coin].copy()
# Keep one latest observation per hour to avoid treating reruns as extra periods.
history["hour"] = history["created_at"].dt.floor("h")
history = history.sort_values("created_at").drop_duplicates("hour", keep="last")
latest_timestamp = history["created_at"].max()
hours = {"24 hours": 24, "7 days": 168, "30 days": 720}
if period in hours:
    history = history[history["created_at"] >= latest_timestamp - pd.Timedelta(hours=hours[period])].copy()

history["moving_average"] = history["price"].rolling(7, min_periods=7).mean()
latest = history.iloc[-1]
previous = history.iloc[-2] if len(history) > 1 else None
change = ((latest["price"] / previous["price"]) - 1) * 100 if previous is not None and previous["price"] > 0 else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest USD", f"${latest['price']:,.4f}")
c2.metric("Change vs prior snapshot", f"{change:+.2f}%" if change is not None else "N/A")
c3.metric("Period low", f"${history['price'].min():,.4f}")
c4.metric("Period high", f"${history['price'].max():,.4f}")

st.caption(f"Latest stored snapshot: {latest_timestamp.strftime('%Y-%m-%d %H:%M UTC')} · {len(history)} hourly observations")
plot = history[["created_at", "price"]].rename(columns={"price": "Price"})
if show_average:
    plot["7-snapshot average"] = history["moving_average"].values
fig = px.line(plot, x="created_at", y=[c for c in plot.columns if c != "created_at"], labels={"created_at": "Time (UTC)", "value": "USD", "variable": "Series"})
fig.update_layout(legend_title_text="")
st.plotly_chart(fig, use_container_width=True)

if len(history) >= 2:
    history["hourly_return_pct"] = history["price"].pct_change(fill_method=None) * 100
    st.subheader("Movement patterns")
    a, b = st.columns(2)
    a.metric("Observed range", f"${history['price'].max() - history['price'].min():,.4f}")
    b.metric("Return volatility (std. dev.)", f"{history['hourly_return_pct'].std():.2f}%" if history['hourly_return_pct'].notna().sum() > 1 else "N/A")
    st.bar_chart(history.set_index("created_at")["hourly_return_pct"], y_label="Change (%)")
else:
    st.info("Collect at least two hourly snapshots to see changes and patterns.")

st.subheader("Latest snapshots across coins")
latest_coins = df.sort_values("created_at").groupby("coin", as_index=False).tail(1)
st.dataframe(latest_coins[["coin", "price", "created_at"]].sort_values("coin"), use_container_width=True, hide_index=True)
st.caption("Data refreshes from PostgreSQL at most once per hour or when manually refreshed. New market observations require the ETL job to run hourly. Snapshot changes are not necessarily true 1-hour returns if ingestion was delayed.")
