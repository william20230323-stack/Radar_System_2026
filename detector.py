import os
import sys
import time

# 強制安裝 requests 確保環境不出錯
try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# 取得 Secrets 並印出長度檢查 (不顯示內容)
TG_TOKEN = str(os.getenv("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.getenv("TG_CHAT_ID", "")).strip()
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSK-USD")

def force_send(msg):
    """強制發送測試"""
    if not TG_TOKEN or not TG_CHAT_ID:
        print(f"DEBUG: Token 長度 {len(TG_TOKEN)}, ID 長度 {len(TG_CHAT_ID)}")
        return
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"TG回傳: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"連線失敗: {e}")

def get_data():
    # 使用 v4 主網穩定 API
    url = f"https://indexer.dydx.trade/v4/candles/perpetualMarkets/{SYMBOL}?resolution=1MIN"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get('candles', [])
    except:
        return []

def main():
    # --- 第一時間強制通知 ---
    print("正在執行啟動測試...")
    force_send(f"✅ **Radar_System_2026** 已成功連接\n監控標的：`{SYMBOL}`")

    last_time = ""
    while True:
        candles = get_data()
        if not candles or len(candles) < 6:
            time.sleep(10)
            continue
            
        current = candles[0]
        if current['startedAt'] == last_time:
            time.sleep(15)
            continue
            
        o, c = float(current['open']), float(current['close'])
        v = float(current['baseTokenVolume'])
        avg_v = sum(float(x['baseTokenVolume']) for x in candles[1:6]) / 5
        
        # 邏輯：陰線大買 / 陽線大賣
        if v > (avg_v * 2.0):
            if c < o:
                force_send(f"⚠️ **DUSK 異常大買**\n型態：`陰線`\n當前量：`{v:.2f}`")
            elif c > o:
                force_send(f"🚨 **DUSK 異常大賣**\n型態：`陽線`\n當前量：`{v:.2f}`")
        
        last_time = current['startedAt']
        time.sleep(20)

if __name__ == "__main__":
    main()
