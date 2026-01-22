import os
import time
import requests
import pandas as pd
# 嚴格禁止更改模組名稱
from module_volume import analyze_volume 

# --- 這就是您截圖中缺少的「讀取保險箱鑰匙」代碼 ---
def independent_report(text):
    # 對接 YAML 裡的 TG_TOKEN 和 TG_CHAT_ID
    token = os.environ.get('TG_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        except:
            pass

def fetch_data(symbol):
    """鎖定美國幣安接口"""
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
    # 對接 YAML 裡的 TRADE_SYMBOL
    SYMBOL = os.environ.get('TRADE_SYMBOL', 'BTCUSDT')
    start_ts = time.time()
    
    # 啟動時立刻拿鑰匙回報
    independent_report(f"🚀 <b>偵查兵上線</b>\n目標: {SYMBOL}")

    while time.time() - start_ts < 280:
        loop_start = time.time()
        df = fetch_data(SYMBOL)
        if df is not None and not df.empty:
            # 任務交給底層武器庫
            analyze_volume(df, SYMBOL)
            print(f"[{time.strftime('%H:%M:%S')}] 價格: {df.iloc[-1]['close']} | 巡邏中...")
        time.sleep(max(0, 15 - (time.time() - loop_start)))
