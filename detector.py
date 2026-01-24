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

SYMBOL = "DUSKUSDT" 
VOL_THRESHOLD = 2.0 

class RelayRadar:
    def __init__(self):
        # 切換至穩定中繼源，專門處理 GitHub IP 被封鎖的問題
        self.relay_endpoints = [
            "https://api.binance.com",    # 現貨網關備援
            "https://data-api.binance.vision" # 開放數據網關 (最穩)
        ]

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def get_data(self):
        """中繼模式：繞過封鎖節點抓取 1m 價格與成交量"""
        try:
            # 使用開放數據網域抓取現貨數據作為 DUSK 趨勢參考
            # 此網域專門給開發者使用，IP 限制最鬆
            url = "https://api.binance.vision/api/v3/klines"
            params = {"symbol": SYMBOL, "interval": "1m", "limit": 10}
            
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                kl_res = res.json()
                if isinstance(kl_res, list) and len(kl_res) >= 7:
                    curr, hist = kl_res[-1], kl_res[-7:-1]
                    o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
                    avg_v = sum(float(x[5]) for x in hist) / len(hist)
                    log(f"✅ 中繼連通 | 價: {c} | 量: {v:.0f} | 均: {avg_v:.0f}")
                    return o, c, v, avg_v
            else:
                log(f"⚠️ 中繼源響應錯誤: {res.status_code}")
        except Exception as e:
            log(f"❌ 中繼連線失敗: {str(e)[:30]}")
        return None

def main():
    radar = RelayRadar()
    log(f"=== Radar_System_2026 中繼模式啟動 | 目標: {SYMBOL} ===")
    
    radar.send_tg(f"📡 **Radar 中繼系統上線**\n模式：`中繼跳板 (Relay)`")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時續命重啟")
            sys.exit(0)

        data = radar.get_data()
        if data:
            o, c, v, avg_v = data
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                direction = "多頭" if c > o else "空頭"
                msg = f"🚨 **DUSK 量能異動**\n方向: `{direction}`\n價格: `{c}`"
                radar.send_tg(msg)
                last_min_processed = now_min
        
        time.sleep(random.randint(5, 12))

if __name__ == "__main__":
    main()
