import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume 

# --- 核心：從保險箱讀取鑰匙的代碼 ---
def independent_report(text):
    """直接從 GitHub Secrets 注入的環境變數讀取鑰匙並回報"""
    # 這就是讀取保險箱鑰匙的指令
    token = os.environ.get('TG_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ 執行員讀取保險箱失敗，鑰匙不存在")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
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
    SYMBOL = os.environ.get('TRADE_SYMBOL', 'BTCUSDT')
    start_ts = time.time()
    
    # 啟動時立刻去保險箱拿鑰匙回報
    independent_report(f"🚀 <b>偵查執行員上線</b>\n目標: {SYMBOL}\n通路: 已成功讀取保險箱鑰匙")

    while time.time() - start_ts < 280:
        loop_start = time.time()
        df = fetch_data(SYMBOL)
        if df is not None and not df.empty:
            # 傳遞數據給模組
            analyze_volume(df, SYMBOL)
            print(f"[{time.strftime('%H:%M:%S')}] 價格: {df.iloc[-1]['close']} | 巡邏中...")
        time.sleep(max(0, 15 - (time.time() - loop_start)))
