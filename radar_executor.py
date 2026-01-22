import os
import time
import random
import requests
import pandas as pd
from module_volume import analyze_volume
from module_indicators import analyze_indicators

# 鎖死保險箱鑰匙
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

ENDPOINTS = [
    "https://api.binance.us/api/v3",
    "https://api1.binance.us/api/v3",
    "https://api2.binance.us/api/v3"
]

def fetch_data():
    base_url = random.choice(ENDPOINTS)
    url = f"{base_url}/klines?symbol={SYMBOL}&interval=1m&limit=100"
    res = requests.get(url, timeout=5).json()
    df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
    return df.astype(float)

def send_startup_notify():
    """新增：啟動成功通知"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    msg = f"🚀 <b>Radar_System_2026 啟動成功</b>\n監控標的: {SYMBOL}\n狀態: 15秒掃描模式已就緒"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
    except:
        pass

if __name__ == "__main__":
    # 發送啟動成功通知
    send_startup_notify()
    
    # 10分鐘內隨機重啟間隔
    restart_limit = random.randint(540, 600)
    start_time = time.time()
    
    while time.time() - start_time < restart_limit:
        try:
            data = fetch_data()
            # 調用獨立模組
            analyze_volume(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
            analyze_indicators(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
        except Exception as e:
            print(f"調度異常: {e}")
        
        # 15秒掃描一次
        time.sleep(15)
    
    time.sleep(random.randint(1, 30))
