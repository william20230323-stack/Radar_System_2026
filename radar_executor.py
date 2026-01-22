import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume

# 從啟動項獲取環境變數
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

def send_to_commander(msg):
    """
    核心聯通：不僅發送 Telegram，更將異常狀態寫入 GitHub 系統環境
    讓啟動項明確知道現在有異常發生
    """
    # 1. 外部通訊通路 (Telegram)
    if TG_TOKEN and TG_CHAT_ID:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        except:
            pass

    # 2. 內部聯通通路 (寫入 GitHub Step Output)
    # 這行代碼會讓啟動項 (YAML) 接收到來自執行員的異常信號
    with open(os.environ.get('GITHUB_ENV', 'log.txt'), 'a') as f:
        f.write(f"DETECTION_ALERT=true\n")
    print(f"📡 已將異常信號同步至啟動項系統流")

def fetch_us_data():
    """鎖定美國幣安接口"""
    url = "https://api.binance.us/api/v3/klines"
    params = {'symbol': SYMBOL, 'interval': '1m', 'limit': 100}
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
    MAX_RUN = 280
    start_ts = time.time()
    
    print(f"🔱 偵查執行員：{SYMBOL} | 連結啟動項中...")

    while time.time() - start_ts < MAX_RUN:
        loop_start = time.time()
        data = fetch_us_data()
        
        if data is not None and not data.empty:
            last = data.iloc[-1]
            ratio = last['taker_buy_quote'] / last['quote_volume'] if last['quote_volume'] > 0 else 0
            print(f"✅ [{time.strftime('%H:%M:%S')}] 價格: {last['close']} | 買佔比: {ratio:.2%}")

            # 連結 模組 A 判定
            alert = analyze_volume(data, SYMBOL)
            if alert:
                send_to_commander(alert)
        
        time.sleep(max(0, 15 - (time.time() - loop_start)))
