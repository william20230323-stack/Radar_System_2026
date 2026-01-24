import os
import time
import requests
import hmac
import hashlib
import random
import sys
from datetime import datetime, timedelta, timezone

# ==========================================
# 武器庫 (A-F) 系統底層設定
# 負責實戰、過濾、防禦、撤退
# ==========================================

# 強制即時輸出日誌，確保在 GitHub Actions 介面能即時看到
def log(msg):
    # 統一轉換為台灣時間 (UTC+8) 顯示
    tw_tz = timezone(timedelta(hours=8))
    now_tw = datetime.now(tw_tz).strftime('%H:%M:%S')
    print(f"[{now_tw}] {msg}", flush=True)

# 紀錄啟動時間 (用於計算 5 小時後續命)
START_TIME = time.time()
MAX_RUN_TIME = 18000  # 5 小時 (18000秒)

# 讀取 Secrets 環境變數 (保險箱內容)
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

SYMBOL = "DUSKUSDT"  # 幣安格式不帶斜槓
VOL_THRESHOLD = 2.0  # 成交量翻倍門檻

class BinanceRadar:
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET

    def send_tg(self, msg):
        """呼叫 Telegram API 發送警報"""
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
            log(f"TG Status: {r.status_code}")
        except Exception as e:
            log(f"TG 發送異常: {e}")

    def get_binance_data(self):
        """【搜尋源切換】從幣安加密 API 獲取 K 線與巨鯨數據"""
        try:
            # 1. 獲取行情數據 (1m K線)
            kl_path = "/fapi/v1/klines"
            kl_params = {"symbol": SYMBOL, "interval": "1m", "limit": 10}
            kl_res = requests.get(self.base_url + kl_path, params=kl_params, timeout=10).json()

            # 2. 獲取巨鯨聰明錢數據 (Top Trader Long/Short Ratio)
            whale_path = "/futures/data/topLongShortAccountRatio"
            whale_params = {"symbol": SYMBOL, "period": "5m", "limit": 1}
            whale_res = requests.get(self.base_url + whale_path, params=whale_params, timeout=10).json()

            if len(kl_res) >= 7:
                curr = kl_res[-1]    # 最新 K 線 [時間, 開, 高, 低, 收, 量, ...]
                hist = kl_res[-7:-1] # 前 6 根
                
                o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(hist)
                
                whale_ratio = "N/A"
                if whale_res and len(whale_res) > 0:
                    whale_ratio = whale_res[0].get('longShortRatio', 'N/A')

                log(f"幣安連線 | 價格: {c} | 巨鯨比: {whale_ratio} | 當前量: {v:.2f} | 均量: {avg_v:.2f}")
                return o, c, v, avg_v, whale_ratio
        except Exception as e:
            log(f"幣安加密 API 連線異常: {str(e)[:50]}")
        return None

def main():
    radar = BinanceRadar()
    log("=== Radar_System_2026 保險箱加密版啟動 ===")
    
    # 啟動通知
    radar.send_tg(f"🚀 **Radar 系統加密連線成功**\n搜尋源：`Binance API` (保險箱)\n時區：`台北/台灣 (UTC+8)`\n狀態：`聰明錢數據已接入`")

    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        # 安全退場機制 (5 小時自動重啟)
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 運行已達 5 小時，主動結束以觸發下一次重啟...")
            sys.exit(0)

        try:
            data = radar.get_binance_data()
            if data:
                o, c, v, avg_v, whale_ratio = data
                now_min = datetime.now(tw_tz).strftime("%H:%M")
                
                # 偵測邏輯：成交量翻倍 + 結合巨鯨數據
                if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                    direction = "陽線突破" if c > o else "陰線回落"
                    alert_icon = "🚨" if c > o else "⚠️"
                    
                    msg = (
                        f"{alert_icon} **幣安異常動態偵測**\n"
                        f"標的: `{SYMBOL}`\n"
                        f"型態: `{direction}` (1M)\n"
                        f"成交量: `{v:.1f}` (均: `{avg_v:.1f}`)\n"
                        f"🐋 **巨鯨多空比**: `{whale_ratio}`\n"
                        f"時間: `{datetime.now(tw_tz).strftime('%H:%M:%S')}`"
                    )
                    radar.send_tg(msg)
                    last_min_processed = now_min
            else:
                log("暫無回傳數據，等待下一次隨機輪詢...")
        except Exception as e:
            log(f"主程序崩潰錯誤: {e}")
        
        # 實施 5秒 - 15秒的隨機延遲
        wait_time = random.randint(5, 15)
        log(f"本次掃描結束，隨機休眠 {wait_time} 秒...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
