import os
import time
import requests
import pandas as pd
from module_volume import analyze_volume
from module_indicators import analyze_indicators

# 環境變數獲取
TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

def send_alert(msg):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except: pass

def fetch_data():
    # 改用標準 API 路徑，增加超時容錯
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=50"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(f"❌ API 響應錯誤: {response.status_code}")
            return None
        res = response.json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return df
    except Exception as e:
        print(f"❌ 網路連線或解析失敗: {e}")
        return None

if __name__ == "__main__":
    MAX_RUN = 280 
    start_time = time.time()
    
    print(f"📡 雷達執行員上線 | 標的: {SYMBOL}")
    print(f"--- 開始進入 280 秒循環監控 ---")
    
    while time.time() - start_time < MAX_RUN:
        loop_start = time.time()
        try:
            data = fetch_data()
            if data is not None:
                # 取得最新一根 K 線
                last = data.iloc[-1]
                t_vol = last['quote_volume']
                b_vol = last['taker_buy_quote']
                ratio = b_vol / t_vol if t_vol > 0 else 0
                
                # 強制輸出到日誌，這行沒出來代表程式死在 fetch_data
                print(f"✅ [{time.strftime('%H:%M:%S')}] 價格: {last['close']} | 主動佔比: {ratio:.2%}")

                # 模組檢測
                v_alert = analyze_volume(data, SYMBOL)
                if v_alert: send_alert(v_alert)
                
                # 帶參數呼叫指標模組，防止 missing argument 報錯
                i_alert = analyze_indicators(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
                if i_alert: send_alert(i_alert)
            else:
                print("⚠️ 本次掃描未能獲取數據...")
        except Exception as e:
            print(f"⚠️ 循環內執行錯誤: {e}")
        
        # 維持 15 秒頻率
        wait = max(0, 15 - (time.time() - loop_start))
        time.sleep(wait)

    print("🏁 接力週期結束。")
