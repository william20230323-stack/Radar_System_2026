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
    tw_tz = timezone(timedelta(hours=8))
    now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_tw}] {msg}", flush=True)

START_TIME = time.time()
MAX_RUN_TIME = 18000 

TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')

SYMBOL = "DUSKUSDT" 
VOL_THRESHOLD = 2.0 

class BinanceProbe:
    def __init__(self):
        # 嘗試使用幣安不同的 API 備援入口，避開 GitHub 被封鎖的節點
        self.endpoints = [
            "https://fapi.binance.com",
            "https://fapi1.binance.com",
            "https://fapi2.binance.com",
            "https://fapi3.binance.com"
        ]
        self.current_url = self.endpoints[0]

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def fetch_data(self):
        """底層探針：輪詢多個 API 節點直到連通"""
        # 隨機打亂節點嘗試
        random.shuffle(self.endpoints)
        
        for url in self.endpoints:
            try:
                # 激進的連線策略：1.5秒連不上就換下一個入口
                kl_url = f"{url}/fapi/v1/klines"
                kl_params = {"symbol": SYMBOL, "interval": "1m", "limit": 10}
                
                log(f"🔍 正在嘗試底層節點: {url} ...")
                res = requests.get(kl_url, params=kl_params, timeout=(1.5, 3.5))
                
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list) and len(data) >= 7:
                        self.current_url = url # 記住這個通的節點
                        return data
            except:
                continue
        return None

    def get_whale_ratio(self):
        """截取巨鯨數據"""
        try:
            url = f"{self.current_url}/futures/data/topLongShortAccountRatio"
            params = {"symbol": SYMBOL, "period": "5m", "limit": 1}
            res = requests.get(url, params=params, timeout=3).json()
            return res[0].get('longShortRatio', 'N/A') if res else "N/A"
        except:
            return "N/A"

def main():
    probe = BinanceProbe()
    log(f"=== Radar_System_2026 探針模式啟動 | 目標: {SYMBOL} ===")
    
    probe.send_tg(f"📡 **Radar 探針已發射**\n目標：`{SYMBOL}`\n模式：`多節點自動切換`")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時續命重啟")
            sys.exit(0)

        klines = probe.fetch_data()
        if klines:
            curr, hist = klines[-1], klines[-7:-1]
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            
            whale_ratio = probe.get_whale_ratio()
            log(f"✅ 連線成功 | 價: {c} | 巨鯨: {whale_ratio} | 量: {v:.0f}")

            now_min = datetime.now(tw_tz).strftime("%H:%M")
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                direction = "多頭" if c > o else "空頭"
                msg = f"🚨 **DUSK 異動**\n方向: `{direction}`\n巨鯨: `{whale_ratio}`"
                probe.send_tg(msg)
                last_min_processed = now_min
        else:
            log("❌ 所有 API 節點暫時無法連通，GitHub 網路受阻，5秒後重試...")
        
        time.sleep(5)

if __name__ == "__main__":
    main()
