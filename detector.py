import os
import time
import requests
import ccxt
import random
import sys

# 強制即時輸出日誌
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# 紀錄啟動時間 (用於計算 5 小時後續命)
START_TIME = time.time()
MAX_RUN_TIME = 18000 # 5 小時

# 讀取 Secrets 環境變數
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0 # 成交量翻倍門檻

# MML 莫里數學參數
MML_LOOKBACK = 100 
MML_MULT = 0.125

def send_tg(msg):
    """呼叫 Telegram API 發送警報"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        log(f"TG Status: {r.status_code}")
    except Exception as e:
        log(f"TG 發送異常: {e}")

def get_market_data():
    """獲取 K 線數據並計算 MML 空間位階"""
    ex = ccxt.gateio({'enableRateLimit': True, 'timeout': 15000})
    try:
        # 獲取 100 根 K 線以計算 MML 振盪值
        ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=MML_LOOKBACK)
        if ohlcv and len(ohlcv) >= 6:
            # --- 1. 原有功能數據提取 ---
            curr = ohlcv[-1]   
            hist = ohlcv[-7:-1] 
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            
            # --- 2. 新增 MML 買賣超判定邏輯 ---
            highs = [float(x[2]) for x in ohlcv]
            lows = [float(x[3]) for x in ohlcv]
            hi, lo = max(highs), min(lows)
            r = hi - lo
            midline = lo + r * 0.5
            # 計算莫里數學振盪值
            oscillator = (c - midline) / (r / 2) if r != 0 else 0
            
            is_oversold = oscillator < -MML_MULT * 6  # 賣超區 (Blue)
            is_overbought = oscillator > MML_MULT * 6 # 買超區 (Orange)
            
            log(f"Gate.io 更新 | 價: {c} | 量: {v:.1f} | MML: {oscillator:.2f}")
            return o, c, v, avg_v, is_oversold, is_overbought
            
    except Exception as e:
        log(f"Gate.io 端口連線異常: {str(e)[:50]}")
    return None

def main():
    log("=== Radar_System_2026 MML 增強版啟動 ===")
    
    send_tg(f"🚀 **Radar 系統全功能上線**\n數據源：`Gate.io` (MML 增強版)\n監控：`陰陽背離 + 空間買賣超`")

    last_min_processed = ""
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 運行已達 5 小時，主動結束以觸發下一次重啟...")
            sys.exit(0)

        try:
            data = get_market_data()
            if data:
                o, c, v, avg_v, is_os, is_ob = data
                now_min = time.strftime("%H:%M")
                
                # 偵測邏輯：成交量翻倍觸發
                if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                    alert_msg = ""
                    
                    # 邏輯 A：陰線吃貨 (陰線大買)
                    if c < o:
                        extra = "\n📊 **額外告知：目前賣超**" if is_os else ""
                        alert_msg = f"⚠️ **Gate.io 異常大買**\n標的: `{SYMBOL}`\n型態: `陰線大買` (1M)\n成交量: `{v:.1f}` (均: `{avg_v:.1f}`){extra}"
                    
                    # 邏輯 B：陽線出逃 (陽線大賣)
                    elif c > o:
                        extra = "\n📊 **額外告知：目前買超**" if is_ob else ""
                        alert_msg = f"🚨 **Gate.io 異常大賣**\n標的: `{SYMBOL}`\n型態: `陽線大賣` (1M)\n成交量: `{v:.1f}` (均: `{avg_v:.1f}`){extra}"
                    
                    if alert_msg:
                        send_tg(alert_msg)
                        last_min_processed = now_min
            else:
                log("暫無回傳數據，等待下一次隨機輪詢...")
        except Exception as e:
            log(f"主程序崩潰錯誤: {e}")
        
        wait_time = random.randint(5, 15)
        log(f"休眠 {wait_time} 秒...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
