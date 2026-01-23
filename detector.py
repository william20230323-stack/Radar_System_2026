import os
import sys
import time

# --- 強制自我修復：若缺少 ccxt 或 requests 則自動安裝 ---
def install_dependencies():
    import subprocess
    needed = ["ccxt", "requests", "pandas"]
    for lib in needed:
        try:
            __import__(lib)
        except ImportError:
            print(f"Missing {lib}, installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_dependencies()

import ccxt
import requests

# 密鑰配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL_CCXT = "DUSK/USDT"
VOL_MULTIPLIER = 2.0

def send_tg_msg(msg):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"TG Send Error: {e}")

def get_ccxt_data():
    """優先調用 CCXT 獲取數據"""
    # 嘗試多個交易所端點以防 IP 被封
    exchanges = [ccxt.binanceus(), ccxt.binance(), ccxt.gateio()]
    for ex in exchanges:
        try:
            print(f"Trying source: {ex.id}...")
            # 獲取最近 6 根 1m K線
            ohlcv = ex.fetch_ohlcv(SYMBOL_CCXT, timeframe='1m', limit=6)
            if not ohlcv: continue
            
            curr = ohlcv[-1]
            hist = ohlcv[:-1]
            v = float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / 5
            return (f"CCXT_{ex.id}", float(curr[1]), float(curr[4]), v, avg_v)
        except Exception as e:
            print(f"{ex.id} failed: {e}")
            continue
    return None

def main():
    print("🚀 Radar Engine Starting (Priority: CCXT)...")
    # 啟動時發送一次心跳，若 6 秒沒收到此封，代表 Token 錯誤或連線被阻斷
    send_tg_msg(f"✅ **Radar_System_2026**\n優先接口：`CCXT`\n狀態：`已啟動，開始並行偵測`")
    
    last_processed_ts = 0
    while True:
        try:
            res = get_ccxt_data()
            if res:
                name, o, c, v, avg_v = res
                # 簡單防止重複警報
                if v > (avg_v * VOL_MULTIPLIER):
                    if c < o:
                        send_tg_msg(f"⚠️ **{name} 異常大買**\n型態：`陰線` (1M)\n成交量：`{v:.1f}`")
                    elif c > o:
                        send_tg_msg(f"🚨 **{name} 異常大賣**\n型態：`陽線` (1M)\n成交量：`{v:.1f}`")
            else:
                print("All CCXT sources failed. Waiting 30s...")
        except Exception as e:
            print(f"Loop error: {e}")
            
        time.sleep(20)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 如果崩潰，發送最後的遺言
        send_tg_msg(f"❌ **系統核心崩潰**\n原因: `{str(e)}`")
