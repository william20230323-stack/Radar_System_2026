import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume

# 連結啟動項通路
TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

# 美國幣安專用接口池
API_POOL = [
    "https://api.binance.us/api/v3/klines",
    "https://api.binance.us/api/v3/klines" # 接口輪替邏輯預留
]
api_index = 0

def broadcast_exception(msg):
    """異常信息傳遞回啟動項並發送"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_market_data():
    """執行偵查：嚴格鎖定美國幣安接口"""
    global api_index
    target_url = API_POOL[api_index]
    api_index = (api_index + 1) % len(API_POOL)
    
    params = {'symbol': SYMBOL, 'interval': '1m', 'limit': 100}
    
    try:
        response = requests.get(target_url, params=params, timeout=12)
        if response.status_code == 200:
            res = response.json()
            if not res or len(res) == 0: return None
            return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return None
    except:
        return None

if __name__ == "__main__":
    MAX_RUN = 280 
    start_ts = time.time()
    
    print(f"🕵️ 偵查執行員就位 | 目標：{SYMBOL} | 來源：Binance.us")

    while time.time() - start_ts < MAX_RUN:
        loop_start = time.time()
        data = fetch_market_data()
        
        # 安全判定：攔截空值防止 IndexError
        if data is not None and not data.empty:
            last = data.iloc[-1]
            t_vol = last['quote_volume']
            b_ratio = last['taker_buy_quote'] / t_vol if t_vol > 0 else 0
            
            # 日誌輸出
            print(f"[{time.strftime('%H:%M:%S')}] 偵查中... 價格: {last['close']} | 買佔比: {b_ratio:.2%}")

            # 連結 模組 A：單邊攻擊 (判定邏輯)
            alert_msg = analyze_volume(data, SYMBOL)
            if alert_msg:
                broadcast_exception(alert_msg)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 數據抓取失敗，等待輪替接口...")
        
        time.sleep(max(0, 15 - (time.time() - loop_start)))

    print("🏁 偵查交班。")
