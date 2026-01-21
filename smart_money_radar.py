import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

def send_tg(msg):
    token = str(RADAR_TOKEN).strip()
    chat_id = str(RADAR_CHAT_ID).strip()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📡 V3 發送結果: {r.status_code}")
    except Exception as e:
        print(f"❌ 發送失敗: {e}")

def get_smart_money():
    url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    try:
        r = requests.get(url, params={"symbol": SYMBOL, "period": "5m", "limit": 1}, timeout=10)
        data = r.json()
        return float(data[0]['longAccount']) if data else None
    except:
        return None

if __name__ == "__main__":
    print("🚀 正在喚醒 V3 聰明錢偵測核心...")
    ratio = get_smart_money()
    long_val = f"{ratio:.2%}" if ratio else "數據讀取中"
    
    startup_report = (
        f"🔥 *【William_Hunter_V2：火力全開】*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 監控標的：`{SYMBOL}`\n"
        f"🐳 大戶多頭比例：`{long_val}`\n"
        f"📡 狀態：武器庫模組 A-F 全線巡航中\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ 系統已鎖定盤口，開啟 4 分鐘深度掃描。"
    )
    
    send_tg(startup_report)
    
    # --- 這是最重要的部分：守住執行緒 240 秒，確保 V1/V2 活著 ---
    print("📡 進入全速掃描模式，請留意 Telegram 警報...")
    time.sleep(240)
    print("✅ 本次巡航任務圓滿結束。")
