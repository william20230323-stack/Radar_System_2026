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

# 標的設定
SYMBOL = "DUSK_USDT" 
VOL_THRESHOLD = 2.0 

class DivergenceRadar:
    def __init__(self):
        self.base_url = "https://api.gateio.ws/api/v4"

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def get_market_data(self):
        """實戰邏輯：精確捕捉陰陽線背離數據"""
        try:
            # 1. 獲取 K 線
            kl_url = f"{self.base_url}/spot/candlesticks"
            kl_params = {"currency_pair": SYMBOL, "interval": "1m", "limit": 11}
            kl_res = requests.get(kl_url, params=kl_params, timeout=10).json()
            
            # 2. 獲取成交細節 (用於分析主動買賣單)
            trades_url = f"{self.base_url}/spot/trades"
            trades_params = {"currency_pair": SYMBOL, "limit": 60}
            trades_res = requests.get(trades_url, params=trades_params, timeout=10).json()

            if isinstance(kl_res, list) and len(kl_res) >= 10:
                curr = kl_res[-1]
                hist = kl_res[-7:-1]
                
                # Gate 解析: [1]量, [2]收盤, [5]開盤
                v = float(curr[1])
                c = float(curr[2])
                o = float(curr[5])
                avg_v = sum(float(x[1]) for x in hist) / len(hist)
                
                is_red = c < o   # 陰線
                is_green = c > o  # 陽線

                # 計算主動買賣佔比 (成交明細解析)
                buy_vol = sum(float(t['amount']) for t in trades_res if t['side'] == 'buy')
                sell_vol = sum(float(t['amount']) for t in trades_res if t['side'] == 'sell')
                total_v = buy_vol + sell_vol
                buy_ratio = buy_vol / total_v if total_v > 0 else 0.5

                log(f"⚡ 監控中 | 價: {c} | 買佔比: {buy_ratio:.1%} | 量: {v:.0f}")
                return {
                    "c": c, "v": v, "avg_v": avg_v,
                    "is_red": is_red, "is_green": is_green,
                    "buy_ratio": buy_ratio
                }
        except Exception as e:
            log(f"⚠️ 搜尋源暫時中斷，重試中...")
        return None

def main():
    radar = DivergenceRadar()
    log(f"=== Radar_System_2026 背離邏輯回歸版啟動 ===")
    
    radar.send_tg(f"🚀 **Radar 系統背離邏輯已掛載**\n監控：`DUSK` (Gate 通道)")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            sys.exit(0)

        data = radar.get_market_data()
        if data:
            v, avg_v, buy_ratio = data['v'], data['avg_v'], data['buy_ratio']
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            # 觸發門檻：成交量需大於均量 2 倍
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                alert_msg = ""
                
                # 邏輯 A：陰線 + 大量主動買單 (陰線吃貨)
                if data['is_red'] and buy_ratio > 0.60:
                    alert_msg = (f"🟡 **【陰線吃貨】主動買單進場**\n"
                                 f"狀態：價格下跌但出現大量主動買單\n"
                                 f"主動買佔比：`{buy_ratio:.1%}`")

                # 邏輯 B：陽線 + 大量主動賣單 (陽線出逃)
                elif data['is_green'] and buy_ratio < 0.40:
                    alert_msg = (f"🟠 **【陽線出逃】主動賣單砸盤**\n"
                                 f"狀態：價格上漲但出現大量主動賣單\n"
                                 f"主動賣佔比：`{(1-buy_ratio):.1%}`")

                if alert_msg:
                    full_content = (
                        f"{alert_msg}\n"
                        f"當前價格：`{data['c']}`\n"
                        f"成交量：`{v:.0f}` (均量: `{avg_v:.0f}`)\n"
                        f"時間：`{datetime.now(tw_tz).strftime('%H:%M:%S')}`"
                    )
                    radar.send_tg(full_content)
                    last_min_processed = now_min
        
        time.sleep(random.randint(5, 10))

if __name__ == "__main__":
    main()
