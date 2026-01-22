import os
import time
import random
import requests
import pandas as pd
from module_volume import analyze_volume
from module_indicators import analyze_indicators

# 1. 讀取保險箱鑰匙並進行強制格式化
TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

ENDPOINTS = [
    "https://api.binance.us/api/v3",
    "https://api1.binance.us/api/v3",
    "https://api2.binance.us/api/v3"
]

def check_env():
    """診斷環境變數是否成功載入"""
    print(f"--- 系統診斷中 ---")
    print(f"交易標的: {SYMBOL}")
    print(f"TG_CHAT_ID 長度: {len(TG_CHAT_ID)}")
    print(f"TG_TOKEN 長度: {len(TG_TOKEN)}")
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 錯誤：GitHub Secrets 讀取失敗，請檢查保險箱設定名稱是否完全一致。")
        return False
    return True

def send_test_msg():
    """啟動時強制發送一次測試，並捕獲錯誤內容"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": f"🚀 <b>Radar_System_2026 聯通成功</b>\n偵測點：GitHub Cloud\n監控標的：{SYMBOL}",
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print("✅ Telegram 測試訊息發送成功！")
        else:
            print(f"❌ TG 發送失敗。錯誤碼: {r.status_code}, 原因: {r.text}")
    except Exception as e:
        print(f"❌ 網路連線至 Telegram 失敗: {e}")

def fetch_data():
    base_url = random.choice(ENDPOINTS)
    url = f"{base_url}/klines?symbol={SYMBOL}&interval=1m&limit=100"
    try:
        res = requests.get(url, timeout=10).json()
        if isinstance(res, list):
            return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        else:
            print(f"幣安 API 報錯: {res}")
    except Exception as e:
        print(f"連線幣安失敗: {e}")
    return None

if __name__ == "__main__":
    # 執行診斷與啟動通知
    if check_env():
        send_test_msg()
    
    # 10分鐘隨機重啟邏輯
    restart_limit = random.randint(540, 600)
    start_time = time.time()
    
    while time.time() - start_time < restart_limit:
        try:
            data = fetch_data()
            if data is not None:
                # 執行分開的模組功能
                analyze_volume(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
                analyze_indicators(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
        except Exception as e:
            print(f"循環監控異常: {e}")
        
        time.sleep(15) # 15秒掃描
    
    time.sleep(random.randint(1, 30))
