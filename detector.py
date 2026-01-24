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

# 強制即時輸出日誌
def log(msg):
    # 統一轉換為台灣時間 (UTC+8)
    tw_tz = timezone(timedelta(hours=8))
    now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_tw}] {msg}", flush=True)

# 紀錄啟動時間 (用於計算 5 小時後續命)
START_TIME = time.time()
MAX_RUN_TIME = 18000  # 5 小時

# 讀取保險箱環境變數
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# 設定偵察目標
SYMBOL = "DUSKUSDT" 
VOL_THRESHOLD = 2.0  # 成交量翻倍門檻

class BinanceRadar:
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET

    def send_tg(self, msg):
        """發送警報至 Telegram"""
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
            log(f"TG 狀態碼: {r.status_code}")
        except Exception as e:
            log(f"TG 發送異常: {e}")

    def get_binance_data(self):
        """從幣安 API 截取 K 線與巨鯨數據"""
        try:
            # 1. 獲取行情數據 (1m K線)
            kl_path = "/fapi/v1/klines"
            kl_params = {"symbol": SYMBOL, "interval": "1m", "limit": 10}
            kl_res = requests.get(self.base_url + kl_path, params=kl_params, timeout=10).json()

            # 2. 獲取巨鯨數據 (5分鐘級別多空比)
            whale_path = "/futures/data/topLongShortAccountRatio"
            whale_params = {"symbol": SYMBOL, "period": "5m", "limit": 1}
            whale_res = requests.get(self.base_url + whale_path, params=whale_params, timeout=10).json()

            if isinstance(kl_res, list) and len(kl_res) >= 7:
                curr = kl_res[-1]    # 最新 K 線
                hist = kl_res[-7:-1] # 前 6 根
                
                o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(hist)
                
                whale_ratio = "N/A"
                if whale_res and len(whale_res) > 0:
                    whale_ratio = whale_res[0].get('longShortRatio', 'N/A')

                log(f"偵察中 | 價格: {c} | 巨鯨比: {whale_ratio} | 量: {v:.1f} | 均量: {avg_v:.1f}")
                return o, c, v, avg_v, whale_ratio
        except Exception as e:
            log(f"API 請求異常: {str(e)[:50]}")
        return None

def main():
    radar = BinanceRadar()
    log(f"=== Radar_System_2026 啟動 | 目標: {SYMBOL} ===")
    
    # 啟動心跳通知
    tw_tz = timezone(timedelta(hours=8))
    radar.send_tg(f"🚀 **Radar 系統上線**\n目標：`{SYMBOL}`\n來源：`Binance 加密 API`\n時區：`台北 (UTC+8)`")

    last_min_processed = ""
    
    while True:
        # 5 小時自動續命機制
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 運行達 5 小時，觸發自動重啟...")
            sys.exit(0)

        try:
            data = radar.get_binance_data()
            if data:
                o, c, v, avg_v, whale_ratio = data
                now_min = datetime.now(tw_tz).strftime("%H:%M")
                
                # 成交量翻倍偵測邏輯
                if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                    direction = "多頭放量" if c > o else "空頭放量"
                    alert_icon = "🚨" if c > o else "⚠️"
                    
                    msg = (
                        f"{alert_icon} **幣安量能異常警報**\n"
                        f"標的: `{SYMBOL}`\n"
                        f"動作: `{direction}` (1M)\n"
                        f"當前量: `{v:.1f}` (均: `{avg_v:.1f}`)\n"
                        f"🐋 **巨鯨多空比**: `{whale_ratio}`\n"
                        f"時間: `{datetime.now(tw_tz).strftime('%H:%M:%S')}`"
                    )
                    radar.send_tg(msg)
                    last_min_processed = now_min
        except Exception as e:
            log(f"程序執行錯誤: {e}")
        
        # 5-15秒隨機輪詢，維持連線流暢且不被封鎖
        wait_time = random.randint(5, 15)
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
