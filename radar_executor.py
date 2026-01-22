import os
import time
import random
import requests
import pandas as pd
# 引入武器庫模組
from module_volume import analyze_volume
from module_indicators import analyze_indicators

# 鎖死保險箱鑰匙
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

ENDPOINTS = ["https://api.binance.us/api/v3", "https://api1.binance.us/api/v3", "https://api2.binance.us/api/v3"]

def fetch_data():
    base_url = random.choice(ENDPOINTS)
    url = f"{base_url}/klines?symbol={SYMBOL}&interval=1m&limit=100"
    res = requests.get(url, timeout=5).json()
    df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
    return df.astype(float)

if __name__ == "__main__":
    # 10分鐘內隨機重啟 (540-600秒)
    restart_limit = random.randint(540, 600)
    start_time = time.time()
    
    while time.time() - start_time < restart_limit:
        try:
            data = fetch_data()
            # 指揮官調派模組執行任務
            analyze_volume(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
            analyze_indicators(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
        except Exception as e:
            print(f"執行錯誤: {e}")
        
        time.sleep(15) # 15秒掃描一次
    
    # 結束前隨機休息 (30秒內)
    time.sleep(random.randint(1, 30))
