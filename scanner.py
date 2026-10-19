import concurrent.futures
import time
import pandas as pd
import yfinance as yf

# Major Indices Configuration & Strike Steps
INDEX_UNIVERSE = {
    "Nifty 50": {"symbol": "^NSEI", "step": 50, "tv_prefix": "NIFTY"},
    "Bank Nifty": {"symbol": "^NSEBANK", "step": 100, "tv_prefix": "BANKNIFTY"},
    "Sensex": {"symbol": "^BSESN", "step": 100, "tv_prefix": "SENSEX"},
    "Bankex": {"symbol": "^BSEBANK", "step": 100, "tv_prefix": "BANKEX"},
}

TIMEFRAMES = {
    "5m": {"interval": "5m", "period": "5d"},
    "15m": {"interval": "15m", "period": "1mo"},
    "1h": {"interval": "60m", "period": "3mo"},
    "1d": {"interval": "1d", "period": "6mo"},
}

NTO_LENGTH = 14
NTO_SMOOTH = 80


def calculate_nto(df, length=14, smooth=80):
  if df is None or len(df) < max(length, smooth):
    return None

  close = df["Close"]
  high = df["High"]
  low = df["Low"]

  highest_high = high.rolling(window=length).max()
  lowest_low = low.rolling(window=length).min()

  range_val = highest_high - lowest_low
  range_val = range_val.replace(0, 0.0001)

  raw_nto = ((close - lowest_low) / range_val) * 100
  nto_line = raw_nto.rolling(window=smooth).mean()

  return round(float(nto_line.iloc[-1]), 2)


def scan_index(name, config):
  symbol = config["symbol"]
  step = config["step"]
  tv_prefix = config["tv_prefix"]

  results = {
      "Index": name,
      "Spot Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{tv_prefix}",
  }

  latest_spot = None
  for tf_name, tf_config in TIMEFRAMES.items():
    try:
      df = yf.download(
          symbol,
          period=tf_config["period"],
          interval=tf_config["interval"],
          progress=False,
          threads=False,
      )
      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
      results[tf_name] = calculate_nto(df, NTO_LENGTH, NTO_SMOOTH)

      if tf_name == "5m" and not df.empty:
        latest_spot = float(df["Close"].iloc[-1])
    except:
      results[tf_name] = None

  results["Spot Price"] = round(latest_spot, 2) if latest_spot else None

  # Determine NTO signal alignment
  try:
    vals = [results["5m"], results["15m"], results["1h"], results["1d"]]
    if all(v is not None for v in vals):
      if all(v > 50 for v in vals):
        results["Signal"] = "FULL BULLISH 🟢"
        atm = round(latest_spot / step) * step if latest_spot else 0
        results["Actionable Option"] = f"CE (ATM: {int(atm)} | OTM: {int(atm+step)})"
        results.update({
            "Option TV Search": f"https://www.tradingview.com/symbols/search/?q={tv_prefix}%20{int(atm)}%20CE"
        })
      elif all(v < 50 for v in vals):
        results["Signal"] = "FULL BEARISH 🔴"
        atm = round(latest_spot / step) * step if latest_spot else 0
        results["Actionable Option"] = f"PE (ATM: {int(atm)} | OTM: {int(atm-step)})"
        results.update({
            "Option TV Search": f"https://www.tradingview.com/symbols/search/?q={tv_prefix}%20{int(atm)}%20PE"
        })
      else:
        results["Signal"] = "Mixed / Neutral"
        results["Actionable Option"] = "No Bias - Avoid Trade"
        results["Option TV Search"] = (
            f"https://www.tradingview.com/chart/?symbol=NSE:{tv_prefix}"
        )
    else:
      results["Signal"] = "Data Error"
      results["Actionable Option"] = "N/A"
      results["Option TV Search"] = (
          f"https://www.tradingview.com/chart/?symbol=NSE:{tv_prefix}"
      )
  except:
    results["Signal"] = "Error"
    results["Actionable Option"] = "N/A"
    results["Option TV Search"] = (
        f"https://www.tradingview.com/chart/?symbol=NSE:{tv_prefix}"
    )

  return results


def run_scanner():
  print("🚀 Running Index Options & Strike NTO Scanner...")
  start_time = time.time()
  scan_results = []

  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(scan_index, name, config)
        for name, config in INDEX_UNIVERSE.items()
    ]
    for future in concurrent.futures.as_completed(futures):
      scan_results.append(future.result())

  df_results = pd.DataFrame(scan_results)
  df_results.to_csv("nto_scan_results.csv", index=False)
  print(
      "✅ Scan complete in"
      f" {round(time.time() - start_time, 2)}s. Saved to nto_scan_results.csv"
  )


if __name__ == "__main__":
  run_scanner()
