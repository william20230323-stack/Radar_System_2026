import os
import time
import requests
import ccxt
import random
import sys

# 強制即時輸出
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0

# 獲取啟動時間，用於 5 小時後自動重啟
START_TIME = time.time()

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        # 加入 10 秒硬超時，防止 TG 伺服器卡住腳本
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def get_market_data():
    # 加入底層連線超時設定
    ex = ccxt.gateio({
        'enableRateLimit': True,
        'timeout': 10000  # 10 秒強制超時
    })
    try:
        ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
        if ohlcv and len(ohlcv) >= 6:
            curr = ohlcv[-1]
            hist = ohlcv[-7:-1]
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            return o, c, v, avg_v
    except Exception as e:
        log(f"數據端口超時或異常: {str(e)[:30]}")
    return None

def main():
    log("=== Radar_System_2026 安全運行版啟動 ===")
    send_tg(f"🛰️ **Radar 系統已重置啟動**\n保護機制：`5小時自動重啟` + `硬性超時`")

    last_min_processed = ""
    
    while True:
        # --- 安全機制 1: 運行超過 5 小時自動退出，交給 GitHub Schedule 重新拉起 ---
        if time.time() - START_TIME > 18000: # 5 小時
            log("運行時間達上限，準備自動退出以供系統重啟...")
            sys.exit(0)

        try:
            data = get_market_data()
            if data:
                o, c, v, avg_v = data
                now_min = time.strftime("%H:%M")
                
                if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                    if c < o:
                        send_tg(f"⚠️ **Gate.io 異常大買**\n標的: `{SYMBOL}`\n量能: `{v:.1f}`")
                    elif c > o:
                        send_tg(f"🚨 **Gate.io 異常大賣**\n標的: `{SYMBOL}`\n量能: `{v:.1f}`")
                    last_min_processed = now_min
            
            # --- 安全機制 2: 隨機休眠 5-15 秒 ---
            wait_time = random.randint(5, 15)
            log(f"掃描結束，休眠 {wait_time}s")
            time.sleep(wait_time)
            
        except Exception as e:
            log(f"主程序異常重試: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
