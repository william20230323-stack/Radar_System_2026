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
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

SYMBOL = "DUSKUSDT" 
VOL_THRESHOLD = 2.0 

class BinanceDirectRadar:
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        # 使用 Session 預先建立連線池，增加流暢度
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': BINANCE_API_KEY,
            'User-Agent': 'Mozilla/5.0'
        })

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            # TG 發送也必須極短超時，防止卡死
            self.session.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=3)
        except:
            pass

    def get_data(self):
        """直連底層：強制超時機制"""
        try:
            # 1. 抓取 K 線 (設定連線超時 3.05 秒，讀取超時 5 秒)
            kl_url = f"{self.base_url}/fapi/v1/klines"
            kl_params = {"symbol": SYMBOL, "interval": "1m", "limit": 10}
            
            # 使用非常激進的 timeout，一旦卡住立刻斷開重來
            response = self.session.get(kl_url, params=kl_params, timeout=(3.05, 5))
            kl_res = response.json()

            # 2. 抓取巨鯨數據
            whale_url = f"{self.base_url}/futures/data/topLongShortAccountRatio"
            whale_params = {"symbol": SYMBOL, "period": "5m", "limit": 1}
            whale_res = self.session.get(whale_url, params=whale_params, timeout=(3.05, 5)).json()

            if isinstance(kl_res, list) and len(kl_res) >= 7:
                curr, hist = kl_res[-1], kl_res[-7:-1]
                o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(hist)
                
                whale_ratio = whale_res[0].get('longShortRatio', 'N/A') if whale_res else "N/A"
                log(f"⚡ 掃描中 | 價: {c} | 巨鯨: {whale_ratio} | 量: {v:.0f}")
                return o, c, v, avg_v, whale_ratio
        except requests.exceptions.RequestException as e:
            # 如果卡住了，這裡會抓到並打印，不會死等
            log(f"⏳ 連線跳轉中... (網路波動)")
        except Exception as e:
            log(f"⚠️ 異常: {str(e)[:30]}")
        return None

def main():
    radar = BinanceDirectRadar()
    log(f"=== Radar_System_2026 直連偵察啟動 | 目標: {SYMBOL} ===")
    
    radar.send_tg(f"🚀 **Radar 系統直連探針已部署**")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時續命退出")
            sys.exit(0)

        data = radar.get_data()
        if data:
            o, c, v, avg_v, whale_ratio = data
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                direction = "多頭" if c > o else "空頭"
                msg = f"🚨 **DUSK 異動**\n方向: `{direction}`\n巨鯨: `{whale_ratio}`"
                radar.send_tg(msg)
                last_min_processed = now_min
        
        time.sleep(random.randint(5, 12))

if __name__ == "__main__":
    main()
