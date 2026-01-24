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

def log(msg):
    tw_tz = timezone(timedelta(hours=8))
    now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_tw}] {msg}", flush=True)

START_TIME = time.time()
MAX_RUN_TIME = 18000  # 5 小時

TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

SYMBOL = "DUSKUSDT" 
VOL_THRESHOLD = 2.0 

class BinanceRadar:
    def __init__(self):
        # 使用國際站 API 底層地址
        self.base_url = "https://fapi.binance.com"
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except:
            log("TG 發送超時")

    def get_binance_data(self):
        """強化連線穩定性，避免在 Execute Radar 階段卡死"""
        try:
            # 1. 獲取行情 (1m K線) - 加入 5 秒強制超時
            kl_path = f"{self.base_url}/fapi/v1/klines"
            kl_params = {"symbol": SYMBOL, "interval": "1m", "limit": 10}
            kl_res = requests.get(kl_path, params=kl_params, timeout=5).json()

            # 2. 獲取巨鯨數據 - 加入 5 秒強制超時
            whale_path = f"{self.base_url}/futures/data/topLongShortAccountRatio"
            whale_params = {"symbol": SYMBOL, "period": "5m", "limit": 1}
            whale_res = requests.get(whale_path, params=whale_params, timeout=5).json()

            if isinstance(kl_res, list) and len(kl_res) >= 7:
                curr = kl_res[-1]
                hist = kl_res[-7:-1]
                o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(hist)
                
                whale_ratio = "N/A"
                if whale_res and len(whale_res) > 0:
                    whale_ratio = whale_res[0].get('longShortRatio', 'N/A')

                log(f"⚡ 掃描中 | 價格: {c} | 巨鯨比: {whale_ratio} | 量: {v:.1} | 均: {avg_v:.1}")
                return o, c, v, avg_v, whale_ratio
        except Exception as e:
            log(f"⚠️ 數據讀取中斷: {str(e)[:30]}... 正在重試")
        return None

def main():
    radar = BinanceRadar()
    log(f"=== Radar_System_2026 啟動 | 目標: {SYMBOL} ===")
    
    # 測試保險箱金鑰
    if not BINANCE_API_KEY:
        log("❌ 錯誤：找不到 API 金鑰，請檢查 GitHub Secrets")
        return

    radar.send_tg(f"🚀 **Radar 系統已進入偵察循環**\n目標：`{SYMBOL}`")
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時續命觸發")
            sys.exit(0)

        data = radar.get_binance_data()
        if data:
            o, c, v, avg_v, whale_ratio = data
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                direction = "多頭" if c > o else "空頭"
                msg = f"🚨 **DUSK 量能警報**\n方向: `{direction}`\n巨鯨比: `{whale_ratio}`"
                radar.send_tg(msg)
                last_min_processed = now_min
        
        # 保持流暢的隨機間隔
        time.sleep(random.randint(5, 15))

if __name__ == "__main__":
    main()
