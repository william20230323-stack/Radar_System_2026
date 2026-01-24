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

TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()

# Gate.io 標的格式
SYMBOL = "DUSK_USDT" 
VOL_THRESHOLD = 2.0 

class GateRadar:
    def __init__(self):
        # 使用 Gate.io 作為穩定搜尋源，避開幣安對 GitHub 的封鎖
        self.base_url = "https://api.gateio.ws/api/v4"

    def send_tg(self, msg):
        if not TG_TOKEN or not TG_CHAT_ID: return
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def get_data(self):
        """實戰邏輯：從 Gate.io 截取行情數據"""
        try:
            # 獲取 1m K線數據
            url = f"{self.base_url}/spot/candlesticks"
            params = {"currency_pair": SYMBOL, "interval": "1m", "limit": 10}
            
            # Gate.io 的 API 在 GitHub Actions 環境通常非常流暢
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                kl_res = res.json()
                if isinstance(kl_res, list) and len(kl_res) >= 7:
                    # Gate 格式: [時間, 成交量, 收盤價, 最高, 最低, 開盤價]
                    # 注意：Gate 的回傳欄位順序與幣安不同
                    curr = kl_res[-1]
                    hist = kl_res[-7:-1]
                    
                    v = float(curr[1])
                    c = float(curr[2])
                    o = float(curr[5])
                    
                    avg_v = sum(float(x[1]) for x in hist) / len(hist)
                    log(f"✅ Gate 掃描 | 價: {c} | 量: {v:.1f} | 均: {avg_v:.1f}")
                    return o, c, v, avg_v
            else:
                log(f"⚠️ Gate 響應異常: {res.status_code}")
        except Exception as e:
            log(f"❌ Gate 連線失敗: {str(e)[:30]}")
        return None

def main():
    radar = GateRadar()
    log(f"=== Radar_System_2026 穩定掃描版啟動 | 目標: {SYMBOL} ===")
    
    radar.send_tg(f"🚀 **Radar 系統搜尋源切換成功**\n目標：`DUSK`\n模式：`Gate.io 穩定通道`")
    
    last_min_processed = ""
    tw_tz = timezone(timedelta(hours=8))
    
    while True:
        # 5 小時續命防禦機制
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時續命觸發")
            sys.exit(0)

        data = radar.get_data()
        if data:
            o, c, v, avg_v = data
            now_min = datetime.now(tw_tz).strftime("%H:%M")
            
            # 偵測邏輯：成交量翻倍偵測
            if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                direction = "多頭放量" if c > o else "空頭放量"
                msg = (f"🚨 **DUSK 量能警報 (Gate)**\n"
                       f"方向: `{direction}`\n"
                       f"價格: `{c}`\n"
                       f"成交量: `{v:.1f}` (均: `{avg_v:.1f}`)\n"
                       f"時間: `{datetime.now(tw_tz).strftime('%H:%M:%S')}`")
                radar.send_tg(msg)
                last_min_processed = now_min
        
        # 5-15秒隨機休眠
        time.sleep(random.randint(5, 15))

if __name__ == "__main__":
    main()
