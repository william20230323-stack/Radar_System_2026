import os
import time
import requests
import pandas as pd

# 從啟動項 (.yml) 接收環境變數
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

# --- 連結模組通路 (以後新增檔案就在這裡 import) ---
from module_volume import analyze_volume
# -----------------------------------------------

def broadcast_exception(msg):
    """將偵查到的異常信息傳遞出來給老闆"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_market_data():
    """執行偵查：向幣安獲取數據"""
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=100"
    try:
        res = requests.get(url, timeout=10).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return df
    except:
        return None

if __name__ == "__main__":
    # 每一棒偵查 280 秒，確保與啟動項的 5 分鐘派遣銜接
    MAX_DETECTION_TIME = 280 
    start_ts = time.time()
    
    print(f"🕵️ 偵查執行員就位 | 目標：{SYMBOL}")

    while time.time() - start_ts < MAX_DETECTION_TIME:
        loop_start = time.time()
        data = fetch_market_data()
        
        if data is not None:
            # 日誌輸出：確保老闆在後台能看到偵查兵在工作
            last = data.iloc[-1]
            buy_ratio = last['taker_buy_quote'] / last['quote_volume'] if last['quote_volume'] > 0 else 0
            print(f"[{time.strftime('%H:%M:%S')}] 偵查中... 價格: {last['close']} | 買佔比: {buy_ratio:.2%}")

            # --- 偵查邏輯鏈條 (連結模組) ---
            # 模組 A：單邊攻擊 (量能偵測)
            alert_msg = analyze_volume(data, SYMBOL)
            
            # 如果任何模組偵查到異常，立刻將訊息遞交給啟動項傳遞出來
            if alert_msg:
                print("🚨 偵查兵發現異常！立刻傳遞訊息...")
                broadcast_exception(alert_msg)
            # ----------------------------
        
        # 15 秒偵查一次
        time.sleep(max(0, 15 - (time.time() - loop_start)))

    print("🏁 偵查結束，等待下一輪接力。")
