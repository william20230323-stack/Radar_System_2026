import os
import time
import requests
import random
import sys
from datetime import datetime, timedelta, timezone

# ==========================================
# 武器庫 (A-F) 系統底層設定
# 負責實戰、過濾、防禦、撤退
# ==========================================

def log(msg):
    # 統一顯示台灣時間 (UTC+8)
    tw_tz = timezone(timedelta(hours=8))
    now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_tw}] {msg}", flush=True)

START_TIME = time.time()
MAX_RUN_TIME = 18000  # 5 小時

# 讀取 GitHub 保險箱金鑰
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

SYMBOL = "DUSKUSDT" 
VOL_THRESHOLD = 2.0 

class BinanceDirectRadar:
    def __init__(self):
        # 核心搜尋源：幣安合約國際站底層接口 (fapi)
        self.base_url = "https://fapi.binance.com"
        self.headers = {
            'X-MBX-APIKEY': BINANCE_API_KEY,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except:
            pass

    def get_data(self):
        """系統底層：繞過 CCXT 直接抓取幣安數據"""
        try:
            # 1. 抓取 1m K線 (行情搜尋源)
            kl_url = f"{self.base_url}/fapi/v1/klines"
            kl_params = {"symbol": SYMBOL, "interval": "1m", "limit": 10}
            kl_res = requests.get(kl_url, params=kl_params, headers=self.headers, timeout=10).json()

            # 2. 抓取巨鯨數據 (聰明錢搜尋源)
            whale_url = f"{self.base_url}/futures/data/topLongShortAccountRatio"
            whale_params = {"symbol": SYMBOL, "period": "5m", "limit": 1}
            whale_res = requests.get(whale_url, params=whale_params, headers=self.headers, timeout=10).json()

            if isinstance(kl_res, list) and len(kl_res) >= 7:
                curr = kl_res[-1]
                hist = kl_res[-7:-1]
                # 幣安 K 線解析: 4=收盤價, 5=成交量
                o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(hist)
                
                whale_ratio = "N/A"
                if whale_res and isinstance(whale_res, list) and len(whale_res) > 0:
                    whale_ratio = whale_res[0].get('longShortRatio', 'N/A')

                log(f"⚡ 直連掃描 | 價: {c} | 巨鯨: {whale_ratio} | 量: {v:.1f} | 均: {avg_v:.1f}")
                return o, c, v, avg_v, whale_ratio
        except Exception as e:
            log(f"⚠️ 幣安直連失敗: {str(e)[:50]}")
        return None

def main():
    radar = BinanceDirectRadar()
    log(f"=== Radar_System_2026 直連底層啟動 | 目標: {SYMBOL} ===")
    
    # 啟動心跳通知
    radar.send_tg(f"🚀 **Radar 系統直連連線成功**\n搜尋源：`Binance Fapi` (合約底層)")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        # 5 小時自動續命機制 (防禦管理)
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時運行結束，觸發續命重啟")
            sys.exit(0)

        data = radar.get_data()
        if data:
            o, c, v, avg_v, whale_ratio = data
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            # 成交量翻倍偵測 (實戰邏輯)
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                direction = "多頭放量" if c > o else "空頭砸盤"
                msg = (f"🚨 **DUSK 量能警報**\n"
                       f"方向: `{direction}`\n"
                       f"巨鯨多空比: `{whale_ratio}`\n"
                       f"價格: `{c}`\n"
                       f"時間: `{datetime.now(tw_tz).strftime('%H:%M:%S')}`")
                radar.send_tg(msg)
                last_min_processed = now_min
        
        # 5-15秒隨機休眠，保持搜尋流暢
        time.sleep(random.randint(5, 15))

if __name__ == "__main__":
    main()
