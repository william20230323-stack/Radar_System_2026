import os
import time
import requests
import pandas as pd
# 嚴格禁止更改名稱：匯入既有模組
from module_volume import analyze_volume
from module_indicators import analyze_indicators

TG_TOKEN = str(os.environ.get('TG_TOKEN', '')).strip()
TG_CHAT_ID = str(os.environ.get('TG_CHAT_ID', '')).strip()
SYMBOL = str(os.environ.get('TRADE_SYMBOL', '')).strip()

def send_alert(msg):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_data():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=100"
    try:
        res = requests.get(url, timeout=10).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return df
    except:
        return None

if __name__ == "__main__":
    MAX_RUN = 280 
    start_time = time.time()
    
    print(f"📡 雷達執行員上線 | 標的: {SYMBOL} | 巡航: {MAX_RUN}秒")
    
    while time.time() - start_time < MAX_RUN:
        loop_start = time.time()
        try:
            data = fetch_data()
            if data is not None:
                # --- 核心：日誌監控輸出 ---
                last = data.iloc[-1]
                total_vol = last['quote_volume']
                buy_vol = last['taker_buy_quote']
                buy_ratio = buy_vol / total_vol if total_vol > 0 else 0
                
                # 同步顯示在 GitHub 日誌
                print(f"[{time.strftime('%H:%M:%S')}] 價格: {last['close']} | 主動買佔比: {buy_ratio:.2%}")
                
                # 執行武器庫模組 (修正參數傳遞)
                vol_alert = analyze_volume(data, SYMBOL)
                if vol_alert: send_alert(vol_alert)
                
                # 這裡修正了 09:53 截圖中的參數缺失報錯
                ind_alert = analyze_indicators(data, SYMBOL, TG_TOKEN, TG_CHAT_ID)
                if ind_alert: send_alert(ind_alert)
        except Exception as e:
            print(f"⚠️ 偵測過程出現異常: {e}")
        
        elapsed = time.time() - loop_start
        time.sleep(max(0, 15 - elapsed))

    print("🏁 本棒任務結束。")
