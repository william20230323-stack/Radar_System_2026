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

SYMBOL = "DUSK_USDT" 
VOL_THRESHOLD = 2.0 
MML_LENGTH = 100  # 莫里指標回顧長度
MML_MULT = 0.125  # 莫里乘數 (1/8)

class MurreyRadar:
    def __init__(self):
        self.base_url = "https://api.gateio.ws/api/v4"

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def calculate_mml(self):
        """計算莫里數學振盪值 (判定買賣超)"""
        try:
            # 抓取 100 根 K 線計算 MML
            url = f"{self.base_url}/spot/candlesticks"
            res = requests.get(url, params={"currency_pair": SYMBOL, "interval": "1m", "limit": MML_LENGTH}, timeout=10).json()
            if not isinstance(res, list) or len(res) < MML_LENGTH: return 0
            
            highs = [float(x[3]) for x in res]
            lows = [float(x[4]) for x in res]
            close = float(res[-1][2])
            
            hi, lo = max(highs), min(lows)
            r = hi - lo
            midline = lo + r * 0.5
            
            # 莫里振盪公式: (close - midline) / (range / 2)
            oscillator = (close - midline) / (r / 2) if r != 0 else 0
            return oscillator
        except: return 0

    def get_market_data(self):
        """實戰邏輯：背離偵測 + MML 買賣超判定"""
        try:
            # 1. 行情數據
            kl_url = f"{self.base_url}/spot/candlesticks"
            kl_res = requests.get(kl_url, params={"currency_pair": SYMBOL, "interval": "1m", "limit": 11}, timeout=10).json()
            
            # 2. 成交明細
            trades_url = f"{self.base_url}/spot/trades"
            trades_res = requests.get(trades_url, params={"currency_pair": SYMBOL, "limit": 60}, timeout=10).json()

            if isinstance(kl_res, list) and len(kl_res) >= 10:
                curr, hist = kl_res[-1], kl_res[-7:-1]
                v, c, o = float(curr[1]), float(curr[2]), float(curr[5])
                avg_v = sum(float(x[1]) for x in hist) / len(hist)
                
                # 主動買賣分析
                buy_v = sum(float(t['amount']) for t in trades_res if t['side'] == 'buy')
                sell_v = sum(float(t['amount']) for t in trades_res if t['side'] == 'sell')
                buy_ratio = buy_v / (buy_v + sell_v) if (buy_v + sell_v) > 0 else 0.5
                
                # MML 判定
                osc = self.calculate_mml()
                is_oversold = osc < -MML_MULT * 6  # 藍色區域
                is_overbought = osc > MML_MULT * 6 # 橘色區域

                log(f"⚡ 監控中 | 價: {c} | 買比: {buy_ratio:.1%} | MML: {osc:.2f}")
                
                return {
                    "c": c, "v": v, "avg_v": avg_v, "is_red": c < o, "is_green": c > o,
                    "buy_ratio": buy_ratio, "is_oversold": is_oversold, "is_overbought": is_overbought
                }
        except: pass
        return None

def main():
    radar = MurreyRadar()
    log(f"=== Radar_System_2026 背離+MML版啟動 ===")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME: sys.exit(0)

        data = radar.get_market_data()
        if data:
            v, avg_v, buy_ratio = data['v'], data['avg_v'], data['buy_ratio']
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                alert_type = ""
                extra_info = ""

                # 邏輯 A：陰線吃貨 (陰線 + 大量買單)
                if data['is_red'] and buy_ratio > 0.60:
                    alert_type = "🟡 **【陰線吃貨】主動買單進場**"
                    if data['is_oversold']:
                        extra_info = "\n🔥 **注意：目前處於 MML 賣超區域（藍色），反彈機率極高！**"

                # 邏輯 B：陽線出逃 (陽線 + 大量賣單)
                elif data['is_green'] and buy_ratio < 0.40:
                    alert_type = "🟠 **【陽線出逃】主動賣單砸盤**"
                    if data['is_overbought']:
                        extra_info = "\n⚠️ **注意：目前處於 MML 買超區域（橘色），回調風險極大！**"

                if alert_type:
                    msg = (f"{alert_type}\n"
                           f"狀態：主動買佔比 `{buy_ratio:.1%}`"
                           f"{extra_info}\n"
                           f"---"
                           f"\n價格：`{data['c']}`\n量能：`{v:.0f}` (均: `{avg_v:.0f}`)\n"
                           f"時間：`{datetime.now(tw_tz).strftime('%H:%M:%S')}`")
                    radar.send_tg(msg)
                    last_min_processed = now_min
        
        time.sleep(random.randint(5, 10))

if __name__ == "__main__":
    main()
