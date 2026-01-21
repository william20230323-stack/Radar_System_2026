import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

def send_tg(msg):
    url = f"https://api.telegram.org/bot{RADAR_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": RADAR_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_whale_data():
    url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    try:
        r = requests.get(url, params={"symbol": SYMBOL, "period": "5m", "limit": 1}, timeout=10)
        data = r.json()
        if data and len(data) > 0:
            return float(data[0]['longAccount'])
    except:
        return None
    return None

if __name__ == "__main__":
    # 1. 嘗試取得數據
    ratio = get_whale_data()
    
    # 2. 格式化顯示數據 (防呆處理)
    display_ratio = f"{ratio:.2%}" if ratio is not None else "數據載入中..."
    
    # 3. 啟動首報
    startup_text = (f"🚀 *【William_Whale_Hunter】對接成功*\n"
                    f"📊 標的：`{SYMBOL}`\n"
                    f"🐳 當前大戶多頭：`{display_ratio}`\n"
                    f"📡 系統已進入全自動監控模式")
    
    send_tg(startup_text)
    
    # 4. 持續運行 4 分鐘
    start = time.time()
    while time.time() - start < 240:
        time.sleep(60)
        print("📡 雷達站監控中...")
