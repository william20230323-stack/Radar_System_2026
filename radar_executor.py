import os
import time
import requests
import pandas as pd
# 嚴格禁止更改模組名稱，連結武器庫 A
from module_volume import analyze_volume 

SYMBOL = os.environ.get('TRADE_SYMBOL')

def fetch_binance_us():
    """連線美國幣安接口"""
    url = "https://api.binance.us/api/v3/klines"
    params = {'symbol': SYMBOL, 'interval': '1m', 'limit': 100}
    try:
        # 加上 Timeout 避免卡死日誌
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if not res: return None
            return pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return None
    except:
        return None

if __name__ == "__main__":
    start_time = time.time()
    # 這是打通日誌的第一步，確保老闆看到程式有動
    print(f"🔱 武器庫偵查兵出勤：{SYMBOL} | 聯通模式：啟動項接收站")

    while time.time() - start_time < 280:
        loop_start = time.time()
        data = fetch_binance_us()
        
        if data is not None and not data.empty:
            # 呼叫底層武器庫模組 A 判定
            alert_msg = analyze_volume(data, SYMBOL)
            
            # --- 核心打通：訊息傳遞給啟動項 ---
            if alert_msg:
                # 將異常寫入一個固定檔案，讓啟動項 (YAML) 下一步能讀取
                with open("radar_alert.log", "w", encoding="utf-8") as f:
                    f.write(alert_msg)
                print(f"🚨 偵查兵發現異常，已遞交報告至啟動項")
            
            # 日誌即時輸出，確保通信路沒斷
            last = data.iloc[-1]
            print(f"[{time.strftime('%H:%M:%S')}] 價格: {last['close']} | 偵查中...")
        
        # 15 秒偵查一次
        time.sleep(max(0, 15 - (time.time() - loop_start)))
