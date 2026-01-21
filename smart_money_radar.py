import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

def send_tg(msg):
    # .strip() 確保不會因為複製時多出的空格導致 404
    token = str(RADAR_TOKEN).strip()
    chat_id = str(RADAR_CHAT_ID).strip()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📡 發送狀態: {r.status_code}, 回應: {r.text}")
    except Exception as e:
        print(f"⚠️ 連線失敗: {e}")

def get_whale_data():
    url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    try:
        r = requests.get(url, params={"symbol": SYMBOL, "period": "5m", "limit": 1}, timeout=10)
        data = r.json()
        return float(data[0]['longAccount']) if data else None
    except: return None

if __name__ == "__main__":
    ratio = get_whale_data()
    val = f"{ratio:.2%}" if ratio else "數據讀取中"
    
    # 這是妳的新機器人首報內容
    startup_msg = (f"🔥 *【William_Hunter_V2：火力全開】*\n"
                   f"📊 監控標的：`{SYMBOL}`\n"
                   f"🐳 當前大戶多頭：`{val}`\n"
                   f"📡 三重雷達模組 A-F 已成功對接新機，開始巡航！")
    
    send_tg(startup_msg)
    
    # 保持執行 4 分鐘，支撐背景的 radar_commander 運行
    time.sleep(240)
