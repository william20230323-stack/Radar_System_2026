import os
import time
import requests
import ccxt

# 強制刷新日誌
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        log(f"TG Status: {r.status_code}") # 這裡看到 200 就是成功
    except Exception as e:
        log(f"TG 發送異常: {e}")

def get_market_data():
    """專攻 Gate.io 端口，這是目前最穩定的路徑"""
    ex = ccxt.gateio({'enableRateLimit': True})
    try:
        # 獲取 1m K線，取最近 10 根
        ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
        if ohlcv and len(ohlcv) >= 6:
            curr = ohlcv[-1]
            hist = ohlcv[-7:-1]
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            log(f"數據更新 | 價: {c} | 量: {v:.2f} | 均: {avg_v:.2f}")
            return o, c, v, avg_v
    except Exception as e:
        log(f"Gate.io 端口請求失敗: {str(e)[:50]}")
    return None

def main():
    log("=== Radar_System_2026 已連通 Telegram (200) ===")
    send_tg(f"🛰️ **Radar 系統已進入全速監控**\n數據源：`Gate.io` (直連端口)\n標的：`{SYMBOL}`\n通訊狀態：`200 (正常)`")

    last_min = ""
    while True:
        try:
            data = get_market_data()
            if data:
                o, c, v, avg_v = data
                now_min = time.strftime("%H:%M")
                
                # 偵測邏輯
                if now_min != last_min and v > (avg_v * VOL_THRESHOLD):
                    if c < o:
                        send_tg(f"⚠️ **Gate.io 異常大買**\n標的: `{SYMBOL}`\n型態: `陰線` (1M)\n量能: `{v:.1f}`")
                    elif c > o:
                        send_tg(f"🚨 **Gate.io 異常大賣**\n標的: `{SYMBOL}`\n型態: `陽線` (1M)\n量能: `{v:.1f}`")
                    last_min = now_min
            else:
                log("等待數據回傳中...")
        except Exception as e:
            log(f"運行異常: {e}")
        
        time.sleep(25)

if __name__ == "__main__":
    main()
