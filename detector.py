import os
import sys
import time
import subprocess

# --- 1. 環境自修復邏輯 ---
def setup_env():
    libs = ["requests", "ccxt", "pandas"]
    for lib in libs:
        try:
            __import__(lib)
        except ImportError:
            print(f"環境缺失 {lib}，正在強制安裝...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# 立即執行安裝
setup_env()

import requests
import ccxt

# --- 2. 參數讀取 ---
# 這裡使用最直接的 os.environ 讀取，並移除任何可能的空格
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0

def send_signal(msg):
    """最底層的發送函數"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        print(f"發送狀態: {r.status_code} | 回傳: {r.text}")
    except Exception as e:
        print(f"網路異常: {e}")

# --- 3. 數據獲取 (CCXT 為優先) ---
def get_market_data():
    # 優先嘗試對數據中心最友善的交易所
    ex_list = [ccxt.gateio(), ccxt.bybit(), ccxt.binanceus()]
    for ex in ex_list:
        try:
            print(f"嘗試數據源: {ex.id}")
            ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
            if ohlcv and len(ohlcv) >= 6:
                curr = ohlcv[-1]
                hist = ohlcv[-7:-1]
                v = float(curr[5])
                avg_v = sum(float(x[5]) for x in hist) / len(history)
                return ex.id, float(curr[1]), float(curr[4]), v, avg_v
        except:
            continue
    return None

# --- 4. 主程序 ---
def run_engine():
    # ！！！關鍵：啟動的第一秒必須發出訊息！！！
    print(f"開始執行偵測程序... 目標: {SYMBOL}")
    send_signal(f"🚀 **Radar_System_2026 啟動測試**\n接口：`CCXT` (Gate/Bybit)\n狀態：`已進入監控循環`")

    last_min = ""
    while True:
        try:
            data = get_market_data()
            if data:
                name, o, c, v, avg_v = data
                now_min = time.strftime("%M")
                
                if now_min != last_min:
                    if v > (avg_v * VOL_THRESHOLD):
                        if c < o: # 陰買
                            send_signal(f"⚠️ **{name} 異常大買**\n標的: `{SYMBOL}`\n量能: `{v:.1f}` (均: `{avg_v:.1f}`)")
                        elif c > o: # 陽賣
                            send_signal(f"🚨 **{name} 異常大賣**\n標的: `{SYMBOL}`\n量能: `{v:.1f}` (均: `{avg_v:.1f}`)")
                    last_min = now_min
            else:
                print("目前所有數據源無回應，等待中...")
        except Exception as e:
            print(f"循環錯誤: {e}")
        
        time.sleep(20)

if __name__ == "__main__":
    run_engine()
