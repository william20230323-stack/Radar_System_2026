import os
import time
import requests
import pandas as pd
# 嚴格禁止更改模組名稱
from module_volume import analyze_volume 

# --- 強行植入通訊鑰匙讀取 ---
def executor_independent_report(text):
    """執行員專屬：直接讀取鑰匙並回報"""
    token = str(os.environ.get('TG_TOKEN', '')).strip()
    chat_id = str(os.environ.get('TG_CHAT_ID', '')).strip()
    if not token or not chat_id:
        print("❌ 執行員通訊失敗：讀取不到 TG_TOKEN 或 TG_CHAT_ID")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_market_data(symbol):
    """美國幣安數據偵查"""
    url = "https://api.binance.us/api/v3/klines"
    params = {'symbol': symbol, 'interval': '1m', 'limit': 100}
    try:
        r = requests.get(url, params=params, timeout=12)
        if r.status_code == 200:
            res = r.json()
            if not res: return None
            return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return None
    except:
        return None

if __name__ == "__main__":
    SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()
    start_ts = time.time()
    
    # 啟動即時獨立回報
    print(f"🔱 武器庫偵查兵出勤 | 目標: {SYMBOL}")
    executor_independent_report(f"🚀 <b>偵查執行員已上線</b>\n目標標的: {SYMBOL}")

    while time.time() - start_ts < 280:
        loop_start = time.time()
        df = get_market_data(SYMBOL)
        
        if df is not None and not df.empty:
            # 實時日誌監控
            last_price = df.iloc[-1]['close']
            print(f"[{time.strftime('%H:%M:%S')}] 實時價格: {last_price} | 巡邏中...")
            
            # 呼叫底層武器庫
            analyze_volume(df, SYMBOL)
        
        time.sleep(max(0, 15 - (time.time() - loop_start)))
