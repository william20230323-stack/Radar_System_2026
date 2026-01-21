import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

def get_whale_ratio():
    url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    try:
        r = requests.get(url, params={"symbol": SYMBOL, "period": "5m", "limit": 1}, timeout=10)
        return float(r.json()[0]['longAccount']) if r.json() else None
    except: return None

def send_startup_notice(ratio):
    msg = (f"🚀 *【William_Whale_Hunter 啟動】*\n"
           f"📊 標的：`{SYMBOL}`\n"
           f"🐳 當前大戶多頭：`{ratio:.2%}`\n"
           f"🛡️ 三重防禦雷達已就位，持續監控中...")
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN}/sendMessage", json={"chat_id": RADAR_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    initial_ratio = get_whale_ratio()
    if initial_ratio:
        send_startup_notice(initial_ratio)
        
        # 循環運行 4 分鐘，保持伺服器在線
        start_time = time.time()
        while time.time() - start_time < 240:
            current_ratio = get_whale_ratio()
            print(f"🐳 聰明錢掃描中... 目前多頭: {current_ratio:.2%}")
            time.sleep(30)
