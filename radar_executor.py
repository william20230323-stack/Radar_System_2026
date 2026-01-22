import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume 

# 核心：每個檔案直接讀取 Token 實現獨立回傳
def independent_report(text):
    """執行員獨立通訊：直接從 Secrets 讀取 Token 並發射"""
    token = str(os.environ.get('TG_TOKEN', '')).strip()
    chat_id = str(os.environ.get('TG_CHAT_ID', '')).strip()
    if not token or not chat_id: return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_binance_us(symbol):
    """連線美國幣安接口"""
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
    
    # 執行員獨立回報啟動狀態
    print(f"🔱 偵查執行員：{SYMBOL} 獨立就位")
    independent_report(f"🛡️ <b>偵查兵上線</b>\n目標: {SYMBOL}")

    while time.time() - start_ts < 280:
        loop_start = time.time()
        df = fetch_binance_us(SYMBOL)
        
        if df is not None and not df.empty:
            last = df.iloc[-1]
            print(f"[{time.strftime('%H:%M:%S')}] 價格: {last['close']} | 巡邏中...")
            
            # 任務交給底層武器庫
            analyze_volume(df, SYMBOL)
        
        time.sleep(max(0, 15 - (time.time() - loop_start)))
