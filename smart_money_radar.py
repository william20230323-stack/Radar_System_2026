import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

def send_tg(msg):
    url = f"https://api.telegram.org/bot{str(RADAR_TOKEN).strip()}/sendMessage"
    payload = {"chat_id": str(RADAR_CHAT_ID).strip(), "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📡 TG 發送狀態: {r.status_code}")
    except: pass

def get_whale():
    url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    try:
        r = requests.get(url, params={"symbol": SYMBOL, "period": "5m", "limit": 1}, timeout=10)
        return float(r.json()[0]['longAccount'])
    except: return None

if __name__ == "__main__":
    ratio = get_whale()
    val = f"{ratio:.2%}" if ratio else "偵測中"
    
    msg = (f"🔥 *【William_Hunter_V2：火力全開】*\n"
           f"━━━━━━━━━━━━━━━\n"
           f"📊 監控標的：`{SYMBOL}`\n"
           f"🐳 大戶多頭比例：`{val}`\n"
           f"📡 狀態：武器庫模組 A-F 全線巡航\n"
           f"━━━━━━━━━━━━━━━\n"
           f"✅ 三重雷達已鎖定盤口，開始深度掃描。")
    
    send_tg(msg)
    
    # 強制守住 240 秒，確保背景的 V1/V2 雷達有足夠時間運作
    print("🚀 巡航警戒中... V1/V2/V3 三位一體運作中")
    time.sleep(240)
    print("✅ 本次巡航任務完成。")
