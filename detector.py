import os
import sys
import time
import requests
import ccxt

# 強制不使用緩存，讓日誌立即顯示
def log(msg):
    print(msg, flush=True)

# 參數讀取
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        log(f"TG回傳碼: {r.status_code}")
    except Exception as e:
        log(f"TG連線失敗: {e}")

def get_data():
    # 使用 Bybit 和 Gate.io，這兩家對 GitHub Actions IP 最友善
    exchanges = [ccxt.bybit(), ccxt.gateio()]
    for ex in exchanges:
        try:
            log(f"正在嘗試數據源: {ex.id}")
            ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
            if ohlcv and len(ohlcv) >= 6:
                curr = ohlcv[-1]
                hist = ohlcv[-7:-1]
                v = float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(hist)
                return ex.id, float(curr[1]), float(curr[4]), v, avg_v
        except Exception as e:
            log(f"{ex.id} 請求失敗: {e}")
            continue
    return None

def main():
    log("=== 偵測引擎啟動中 ===")
    # 啟動訊號
    send_tg(f"🚀 **Radar_System_2026 已成功上線**\n監控標的: `{SYMBOL}`\n優先接口: `CCXT`")

    last_min = ""
    while True:
        try:
            res = get_data()
            if res:
                name, o, c, v, avg_v = res
                now_min = time.strftime("%H:%M")
                
                if now_min != last_min:
                    log(f"[{now_min}] {name} 價格: {c} | 量: {v:.2f}")
                    if v > (avg_v * VOL_THRESHOLD):
                        if c < o: # 陰買
                            send_tg(f"⚠️ **{name} 異常大買**\n型態: `陰線` (1M)\n量能: `{v:.1f}` (均: `{avg_v:.1f}`)")
                        elif c > o: # 陽賣
                            send_tg(f"🚨 **{name} 異常大賣**\n型態: `陽線` (1M)\n量能: `{v:.1f}` (均: `{avg_v:.1f}`)")
                    last_min = now_min
            else:
                log("無法獲取行情數據，30秒後重試...")
        except Exception as e:
            log(f"主循環報錯: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    main()
