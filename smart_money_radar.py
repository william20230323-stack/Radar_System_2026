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
        return r.json()[0]['longAccount']
    except: return None

if __name__ == "__main__":
    ratio = get_whale_data()
    # 啟動首報：確認新 Token 是否成功連線
    startup_text = (f"🚀 *【William_Whale_Hunter】正式上線*\n"
                    f"📊 監控標的：`{SYMBOL}`\n"
                    f"🐳 初始聰明錢多頭：`{ratio:.2% if ratio else '讀取中'}`\n"
                    f"📡 武器庫模組 A-F 已就緒，進入全自動巡航模式")
    send_tg(startup_text)
    
    # 維持 4 分鐘運行
    start = time.time()
    while time.time() - start < 240:
        time.sleep(60)
        print("📡 雷達掃描中...")
