import os
import time
import requests
import pandas as pd

# 1. 直接從啟動項 (YAML) 獲取最底層通訊權限
# 這裡必須確保 YAML 裡的 env 名稱與這裡完全一致
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

# --- 連結偵查模組 (模組名稱嚴禁更改) ---
from module_volume import analyze_volume
# ------------------------------------

def broadcast_to_base(msg):
    """
    核心通訊通路：將偵查到的異常直接從執行員傳遞給老闆
    """
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通路斷裂：未偵測到 Telegram Secrets，請檢查 YAML 設定")
        return
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ 通路回報：異常訊息已成功傳遞至 Telegram")
        else:
            print(f"❌ 通路故障：Telegram 回傳錯誤碼 {response.status_code}")
    except Exception as e:
        print(f"❌ 通路崩潰：無法連線至 Telegram API: {e}")

def fetch_us_data():
    """連線美國幣安伺服器接口"""
    # 確保針對美國幣安接口
    base_url = "https://api.binance.us/api/v3/klines"
    params = {
        'symbol': str(SYMBOL).strip().upper(),
        'interval': '1m',
        'limit': 50
    }
    try:
        r = requests.get(base_url, params=params, timeout=15)
        if r.status_code == 200:
            res = r.json()
            if not res: return None
            return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return None
    except:
        return None

if __name__ == "__main__":
    MAX_DETECTION_TIME = 280 
    start_time = time.time()
    
    # 啟動時在日誌確認通路狀態
    print(f"🔱 武器庫偵查兵出勤 | 目標: {SYMBOL}")
    print(f"🔑 通訊密鑰狀態: {'已就緒' if TG_TOKEN and TG_CHAT_ID else '缺失'}")

    while time.time() - start_time < MAX_DETECTION_TIME:
        loop_start = time.time()
        
        data = fetch_us_data()
        
        if data is not None and not data.empty:
            last = data.iloc[-1]
            buy_ratio = last['taker_buy_quote'] / last['quote_volume'] if last['quote_volume'] > 0 else 0
            
            # 日誌即時數據顯示
            print(f"[{time.strftime('%H:%M:%S')}] 偵查中... 價格: {last['close']} | 買佔比: {buy_ratio:.2%}")

            # 執行模組判定 (模組 A: 單邊攻擊)
            alert_content = analyze_volume(data, SYMBOL)
            
            if alert_content:
                print("🚨 偵查兵發現異常，正在通過通路回傳...")
                broadcast_to_base(alert_content)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 無法取得美國幣安數據，通路檢查中...")

        time.sleep(max(0, 15 - (time.time() - loop_start)))

    print("🏁 偵查交班。")
