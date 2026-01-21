import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

def send_tg(msg):
    token = str(RADAR_TOKEN).strip()
    chat_id = str(RADAR_CHAT_ID).strip()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📡 TG 發送結果: {r.status_code}")
    except Exception as e:
        print(f"❌ 發送失敗: {e}")

def get_smart_money():
    # 抓取幣安大戶多空比數據
    url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    try:
        r = requests.get(url, params={"symbol": SYMBOL, "period": "5m", "limit": 1}, timeout=10)
        data = r.json()
        if data:
            return float(data[0]['longAccount'])
        return None
    except:
        return None

if __name__ == "__main__":
    print("🚀 正在喚醒 V3 聰明錢偵測核心...")
    ratio = get_smart_money()
    
    # 格式化數據
    long_val = f"{ratio:.2%}" if ratio else "數據讀取中"
    
    # 建立戰報
    startup_report = (
        f"🔥 *【William_Hunter_V2：火力全開】*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 監控標的：`{SYMBOL}`\n"
        f"🐳 大戶多頭比例：`{long_val}`\n"
        f"📡 狀態：三重雷達模組 A-F 已就位\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ 武器庫系統連線成功，開始全天候巡航。"
    )
    
    # 強制發送
    send_tg(startup_report)
    print("✅ 啟動戰報已送出。")
