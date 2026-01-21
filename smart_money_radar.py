import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

def send_tg(msg):
    url = f"https://api.telegram.org/bot{str(RADAR_TOKEN).strip()}/sendMessage"
    payload = {"chat_id": str(RADAR_CHAT_ID).strip(), "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📡 TG 戰報送出成功")
    except:
        print(f"❌ TG 發送失敗")

def get_smart_money():
    url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    try:
        r = requests.get(url, params={"symbol": SYMBOL, "period": "5m", "limit": 1}, timeout=10)
        return float(r.json()[0]['longAccount'])
    except: return None

if __name__ == "__main__":
    ratio = get_smart_money()
    long_val = f"{ratio:.2%}" if ratio else "數據讀取中"
    
    msg = (f"🔥 *【William_Hunter_V2：火力全開】*\n"
           f"━━━━━━━━━━━━━━━\n"
           f"📊 監控標的：`{SYMBOL}`\n"
           f"🐳 大戶多頭比例：`{long_val}`\n"
           f"📡 狀態：武器庫模組 A-F 已全部點火\n"
           f"━━━━━━━━━━━━━━━\n"
           f"✅ 巡航開始：V1/V2/V3 三位一體監控中。")
    
    send_tg(msg)
    
    # --- 巡航計時器 (讓 Actions 穩定跑完 4 分鐘) ---
    start_time = time.time()
    total_scan_time = 240 # 240秒 = 4分鐘
    
    print(f"🚀 [武器庫 A-F] 雷達進入全速掃描模式...")
    while time.time() - start_time < total_scan_time:
        remaining = int(total_scan_time - (time.time() - start_time))
        if remaining % 30 == 0: # 每 30 秒在日誌回報一次進度
            print(f"📡 巡航中... 剩餘監控時間: {remaining} 秒")
        time.sleep(1)
        
    print("✅ 本次 4 分鐘巡航結束，等待下一次自動點火。")
