import os
import time
import requests
import ccxt
import random
import sys

# 強制刷新緩衝區，確保 GitHub Actions 日誌即時顯示
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# 讀取 Secrets
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0

# 紀錄啟動時間
START_TIME = time.time()
MAX_RUN_TIME = 18000  # 5 小時 (18000秒) 後自動退出，讓系統重啟

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        # 設定 10 秒強制超時，防止 Telegram API 延遲卡死腳本
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        log(f"TG 發送失敗: {e}")

def get_market_data():
    """連線 Gate.io 端口"""
    # 在實例化時加入超時機制
    ex = ccxt.gateio({
        'enableRateLimit': True,
        'timeout': 15000  # 15 秒連線超時
    })
    try:
        # 獲取最近 10 根 1m K線
        ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
        if ohlcv and len(ohlcv) >= 6:
            curr = ohlcv[-1]   # 當前 K 線
            hist = ohlcv[-7:-1] # 前 6 根計算平均量
            
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            
            return o, c, v, avg_v
    except Exception as e:
        log(f"數據獲取超時或失敗: {str(e)[:50]}")
    return None

def main():
    log("=== Radar_System_2026 穩定版啟動 ===")
    send_tg(f"🛰️ **Radar 系統已重啟**\n狀態：`穩定模式` (5小時自動續命)\n數據源：`Gate.io` (直連)\n隨機頻率：`5-15s`")

    last_min_processed = ""
    
    while True:
        # 檢查是否到達運行上限，主動退出觸發 GitHub 重啟
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("達 5 小時運行上限，執行安全退出以利重啟...")
            sys.exit(0)

        try:
            data = get_market_data()
            if data:
                o, c, v, avg_v = data
                now_min = time.strftime("%H:%M")
                
                # 偵測邏輯：成交量翻倍偵測
                if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                    if c < o:
                        send_tg(f"⚠️ **Gate.io 異常大買**\n標的: `{SYMBOL}`\n量能: `{v:.1f}` (均: `{avg_v:.1f}`)")
                    elif c > o:
                        send_tg(f"🚨 **Gate.io 異常大賣**\n標的: `{SYMBOL}`\n量能: `{v:.1f}` (均: `{avg_v:.1f}`)")
                    last_min_processed = now_min
            else:
                log("暫無回傳數據，等待下一次輪詢...")

        except Exception as e:
            log(f"主循環異常: {e}")
            time.sleep(10)

        # 隨機延遲 5-15 秒
        wait_time = random.randint(5, 15)
        log(f"掃描結束，隨機休眠 {wait_time} 秒...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
