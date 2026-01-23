import os
import time
import requests
import ccxt
from concurrent.futures import ThreadPoolExecutor

# 強制即時輸出日誌
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# 讀取 Secrets
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        log(f"TG Status: {r.status_code}")
    except Exception as e:
        log(f"TG Error: {e}")

def fetch_from_exchange(exchange_id):
    """單獨針對指定交易所獲取數據"""
    try:
        # 動態初始化交易所類別
        ex_class = getattr(ccxt, exchange_id)
        ex = ex_class({'enableRateLimit': True})
        
        ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
        if ohlcv and len(ohlcv) >= 6:
            curr = ohlcv[-1]
            hist = ohlcv[-7:-1]
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            return exchange_id, o, c, v, avg_v
    except Exception as e:
        log(f"[{exchange_id}] 連線失敗: {str(e)[:50]}")
    return None

def main():
    log("=== Radar_System_2026 雙源模式啟動 ===")
    send_tg(f"🛰️ **Radar 雙源同步啟動**\n端口 1：`Gate.io`\n端口 2：`Bybit`\n監控標的：`{SYMBOL}`")

    last_min_processed = ""
    while True:
        now_min = time.strftime("%H:%M")
        
        # 使用線程池同時請求兩個數據源，提高效率
        with ThreadPoolExecutor(max_workers=2) as executor:
            targets = ['gateio', 'bybit']
            results = list(executor.map(fetch_from_exchange, targets))

        for res in results:
            if res:
                name, o, c, v, avg_v = res
                
                # 偵測邏輯：成交量翻倍且為分鐘首發
                if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                    if c < o: # 陰買
                        send_tg(f"⚠️ **{name} 異常大買**\n標的: `{SYMBOL}`\n型態: `陰線大買`\n當前量: `{v:.1f}` (均: `{avg_v:.1f}`)")
                    elif c > o: # 陽賣
                        send_tg(f"🚨 **{name} 異常大賣**\n標的: `{SYMBOL}`\n型態: `陽線大賣`\n當前量: `{v:.1f}` (均: `{avg_v:.1f}`)")
        
        last_min_processed = now_min
        time.sleep(30) # 每 30 秒輪詢一次

if __name__ == "__main__":
    main()
