import os
import time
import random
import requests
import pandas as pd
from module_volume import analyze_volume
from module_indicators import analyze_indicators

TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

def send_alert(msg):
    """回報中心"""
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_data():
    ENDPOINTS = ["https://api.binance.us/api/v3", "https://api1.binance.us/api/v3"]
    url = f"{random.choice(ENDPOINTS)}/klines?symbol={SYMBOL}&interval=1m&limit=100"
    try:
        res = requests.get(url, timeout=10).json()
        return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
    except:
        return None

if __name__ == "__main__":
    restart_limit = random.randint(540, 600)
    start_time = time.time()
    
    while time.time() - start_time < restart_limit:
        try:
            data = fetch_data()
            if data is not None:
                # 偵測並發送
                vol_alert = analyze_volume(data, SYMBOL)
                if vol_alert: send_alert(vol_alert)
                
                ind_alert = analyze_indicators(data, SYMBOL)
                if ind_alert: send_alert(ind_alert)
        except:
            pass
        time.sleep(15)
    
    time.sleep(random.randint(1, 30))
