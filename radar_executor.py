import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume 

# --- 直接給予通訊鑰匙，讓檔案具備獨立回報能力 ---
TOKEN = "7961234988:AAHcl_N4k_K9YkO08C6G6l6E5F8x6X6X6X" # 範例，請替換為您的實體 Token
CHAT_ID = "6348600000" # 範例，請替換為您的實體 ID

def independent_report(text):
    """具備實體鑰匙的獨立通訊模組"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def fetch_data(symbol):
    url = "https://api.binance.us/api/v3/klines"
    params = {'symbol': symbol, 'interval': '1m', 'limit': 100}
    try:
        r = requests.get(url, params=params, timeout=12)
        if r.status_code == 200:
            return pd.DataFrame(r.json(), columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return None
    except:
        return None

if __name__ == "__main__":
    SYMBOL = str(os.environ.get('TRADE_SYMBOL', 'BTCUSDT')).strip()
    start_ts = time.time()
    
    # 啟動時立刻回報，確認通訊打通
    independent_report(f"🛡️ <b>偵查兵上線</b>\n目標: {SYMBOL}\n通訊狀態: 實體鑰匙已載入")

    while time.time() - start_ts < 280:
        loop_start = time.time()
        df = fetch_data(SYMBOL)
        if df is not None and not df.empty:
            analyze_volume(df, SYMBOL)
            print(f"[{time.strftime('%H:%M:%S')}] 價格: {df.iloc[-1]['close']} | 巡邏中...")
        time.sleep(max(0, 15 - (time.time() - loop_start)))
