import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume

TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_data():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=50"
    try:
        res = requests.get(url, timeout=10).json()
        return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
    except:
        return None

if __name__ == "__main__":
    # 核心：280 秒後自動結束，等待 GitHub 5 分鐘排程重啟
    MAX_RUN = 280 
    start_time = time.time()
    
    print(f"📡 雷達接力啟動 | 標的: {SYMBOL} | 預計巡航: {MAX_RUN}秒")
    
    while time.time() - start_time < MAX_RUN:
        loop_start = time.time()
        data = fetch_data()
        if data is not None:
            # 偵測並印出數據（方便您在日誌監控）
            last = data.iloc[-1]
            buy_ratio = last['taker_buy_quote'] / last['quote_volume'] if last['quote_volume'] > 0 else 0
            print(f"[{time.strftime('%H:%M:%S')}] 價格: {last['close']} | 主動買佔比: {buy_ratio:.2%}")
            
            alert = analyze_volume(data, SYMBOL)
            if alert:
                send_alert(alert)
        
        # 維持 15 秒一跳
        elapsed = time.time() - loop_start
        time.sleep(max(0, 15 - elapsed))

    print("🏁 時間到，本棒結束，等待下一棒啟動。")
