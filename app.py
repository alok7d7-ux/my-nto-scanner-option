import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Index Options NTO Scanner", page_icon="📈", layout="wide"
)

st.title("📊 Index Options Multi-TF NTO Scanner")
st.markdown(
    "Multi-Timeframe NTO scanning for **Nifty 50, Bank Nifty, Sensex, and"
    " Bankex** with automated CE/PE strike price recommendations."
)


@st.cache_data(ttl=300)
def load_data():
  try:
    return pd.read_csv("nto_scan_results.csv")
  except FileNotFoundError:
    return pd.DataFrame()


df = load_data()

if df.empty:
  st.warning("⚠️ No scan results found yet. Please run the scanner action.")
else:
  st.sidebar.header("Filter & Sort Options")
  signal_filter = st.sidebar.selectbox(
      "Filter by Signal",
      [
          "All",
          "FULL BULLISH 🟢 (CE Bias)",
          "FULL BEARISH 🔴 (PE Bias)",
          "Mixed / Neutral",
      ],
  )

  sort_column = st.sidebar.selectbox(
      "Sort By", ["Index", "Spot Price", "5m", "15m", "1h", "1d", "Signal"]
  )
  sort_order = st.sidebar.radio(
      "Direction", ["Highest first ⬇️", "Lowest first ⬆️"]
  )
  ascending_bool = True if "Lowest" in sort_order else False

  filtered_df = df.copy()
  if signal_filter != "All":
    filtered_df = filtered_df[filtered_df["Signal"] == signal_filter]

  if sort_column in filtered_df.columns:
    filtered_df = filtered_df.sort_values(
        by=sort_column, ascending=ascending_bool
    )

  col1, col2 = st.columns(2)
  with col1:
    st.metric(label="Total Indices Scanned", value=len(df))
  with col2:
    st.metric(label="Matching Bias Count", value=len(filtered_df))

  st.markdown("---")

  st.dataframe(
      filtered_df,
      column_config={
          "TradingView": st.column_config.LinkColumn(
              "TradingView Chart",
              help="Click to open direct index chart on TradingView",
              display_text="📈 Open Chart",
          ),
          "Spot Price": st.column_config.NumberColumn(
              "Spot Price", format="₹%.2f"
          ),
          "Suggested Strikes": st.column_config.TextColumn(
              "Suggested CE / PE Strikes",
              help="Recommended ATM and OTM strike options based on NTO alignment",
          ),
      },
      use_container_width=True,
      hide_index=True,
  )

  if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
