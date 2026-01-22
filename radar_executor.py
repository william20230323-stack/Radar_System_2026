import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume
from module_indicators import analyze_indicators

TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

def send_alert(msg):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_data():
    url = f"https://api.binance.us/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=100"
    try:
        res = requests.get(url, timeout=10).json()
        return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
    except:
        return None

if __name__ == "__main__":
    # 鎖定 290 秒，確保在 GitHub 下次觸發前結束，避免 overlap 導致的鎖死
    RUN_DURATION = 290 
    start_time = time.time()
    
    print(f"📡 雷達執行員已上線，預計巡航 {RUN_DURATION} 秒...")
    
    while time.time() - start_time < RUN_DURATION:
        loop_start = time.time()
        try:
            data = fetch_data()
            if data is not None:
                # 執行偵測
                vol_alert = analyze_volume(data, SYMBOL)
                if vol_alert: send_alert(vol_alert)
                
                ind_alert = analyze_indicators(data, SYMBOL)
                if ind_alert: send_alert(ind_alert)
        except Exception as e:
            print(f"偵測異常: {e}")
        
        # 精確 15 秒間隔
        elapsed = time.time() - loop_start
        sleep_time = max(0, 15 - elapsed)
        time.sleep(sleep_time)

    print("🏁 任務週期結束，移交指揮權。")
