import os
import time
import random
import requests
import pandas as pd
# 引入武器庫模組
from module_volume import analyze_volume
from module_indicators import analyze_indicators

# 鎖死保險箱鑰匙
TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

def commander_report(msg):
    """指揮官層級回報函數"""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("致命錯誤：保險箱鑰匙缺失")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"通訊失敗: {e}")

def fetch_data():
    ENDPOINTS = ["https://api.binance.us/api/v3", "https://api1.binance.us/api/v3", "https://api2.binance.us/api/v3"]
    url = f"{random.choice(ENDPOINTS)}/klines?symbol={SYMBOL}&interval=1m&limit=100"
    try:
        res = requests.get(url, timeout=10).json()
        return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
    except:
        return None

if __name__ == "__main__":
    # --- 啟動項回報：第一時間測試聯通 ---
    startup_msg = f"🛡️ <b>Radar_System_2026 指揮體系已上線</b>\n標的：{SYMBOL}\n頻率：15s/次\n重啟機制：10min 隨機切換"
    commander_report(startup_msg)
    
    restart_limit = random.randint(540, 600)
    start_time = time.time()
    
    while time.time() - start_time < restart_limit:
        try:
            data = fetch_data()
            if data is not None:
                # 調用各個偵測模組
                analyze_volume(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
                analyze_indicators(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
        except Exception as e:
            print(f"執行異常: {e}")
        
        time.sleep(15)
    
    # 關機前隨機休眠
    time.sleep(random.randint(1, 30))
