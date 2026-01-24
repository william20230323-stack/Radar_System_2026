import os
import time
import ccxt
import random
import sys
import requests
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

SYMBOL = "DUSK/USDT" # CCXT 格式帶斜槓
VOL_THRESHOLD = 2.0 

class BinanceRadar:
    def __init__(self):
        # 回歸你最開始使用的 CCXT 初始化方式，這對 GitHub Actions 環境最穩定
        self.exchange = ccxt.binance({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'} # 鎖定合約市場
        })

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        except:
            pass

    def get_whale_ratio(self, symbol):
        """抓取巨鯨多空比 (CCXT 不支援此私有數據，改用直連 API)"""
        try:
            # 將 DUSK/USDT 轉為 DUSKUSDT
            clean_symbol = symbol.replace("/", "")
            url = f"https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={clean_symbol}&period=5m&limit=1"
            res = requests.get(url, timeout=5).json()
            if res and len(res) > 0:
                return res[0].get('longShortRatio', 'N/A')
        except:
            return "N/A"
        return "N/A"

    def get_market_data(self):
        """使用 CCXT 獲取 K 線數據 (最穩定的搜尋源)"""
        try:
            # 獲取 1m K線
            ohlcv = self.exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
            if ohlcv and len(ohlcv) >= 7:
                curr = ohlcv[-1]
                hist = ohlcv[-7:-1]
                o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(hist)
                
                # 同步獲取巨鯨比
                whale_ratio = self.get_whale_ratio(SYMBOL)
                
                log(f"幣安連線 | 價: {c} | 巨鯨: {whale_ratio} | 量: {v:.1f} | 均: {avg_v:.1f}")
                return o, c, v, avg_v, whale_ratio
        except Exception as e:
            log(f"⚠️ 幣安連線異常: {str(e)[:50]}")
        return None

def main():
    radar = BinanceRadar()
    log(f"=== Radar_System_2026 穩定連線版啟動 | 目標: {SYMBOL} ===")
    
    radar.send_tg(f"🚀 **Radar 系統已切換 CCXT 穩定源**\n目標：`{SYMBOL}`")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時續命觸發")
            sys.exit(0)

        data = radar.get_market_data()
        if data:
            o, c, v, avg_v, whale_ratio = data
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                direction = "多頭" if c > o else "空頭"
                msg = f"🚨 **DUSK 量能警報**\n方向: `{direction}`\n巨鯨比: `{whale_ratio}`\n時間: `{datetime.now(tw_tz).strftime('%H:%M:%S')}`"
                radar.send_tg(msg)
                last_min_processed = now_min
        
        # 保持隨機間隔 5-15 秒
        time.sleep(random.randint(5, 15))

if __name__ == "__main__":
    main()
