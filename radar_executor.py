import os
import time
import requests
import pandas as pd
# 嚴格禁止更改模組名稱
from module_volume import analyze_volume 

# --- 精準對接您保險箱截圖的變數名稱 ---
TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

def independent_report(text):
    """具備獨立讀取與發送能力"""
    if not TOKEN or not CHAT_ID:
        # 如果保險箱讀取失敗，直接在日誌報警
        print(f"❌ 鑰匙讀取失敗！請確認 GitHub Secrets 名稱是否為 TG_TOKEN 和 TG_CHAT_ID")
        return
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ 通訊發送異常: {e}")

def fetch_data():
    """連線 Binance.us 獲取數據"""
    if not SYMBOL: return None
    url = "https://api.binance.us/api/v3/klines"
    params = {'symbol': SYMBOL, 'interval': '1m', 'limit': 100}
    try:
        r = requests.get(url, params=params, timeout=12)
        if r.status_code == 200:
            data = r.json()
            return pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
        return None
    except:
        return None

if __name__ == "__main__":
    start_ts = time.time()
    
    # 啟動時第一時間回報，確認通訊已接通
    print(f"🔱 偵查兵上線 | 目標: {SYMBOL}")
    independent_report(f"🚀 <b>偵查兵上線</b>\n目標: {SYMBOL}\n狀態: 已成功從保險箱提取鑰匙")

    while time.time() - start_ts < 280:
        loop_start = time.time()
        df = fetch_data()
        
        if df is not None and not df.empty:
            # 呼叫底層武器庫判定
            analyze_volume(df, SYMBOL)
            print(f"[{time.strftime('%H:%M:%S')}] 價格: {df.iloc[-1]['close']} | 偵查中...")
            
        time.sleep(max(0, 15 - (time.time() - loop_start)))

    print("🏁 任務結束，交班。")
