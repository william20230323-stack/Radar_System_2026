import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor

# 密鑰配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL_DYDX = os.getenv("TRADE_SYMBOL", "DUSK-USD")  # dYdX 格式
SYMBOL_BINANCE = SYMBOL_DYDX.replace("-", "").replace("USD", "USDT") # 轉為 DUSKUSDT
VOL_MULTIPLIER = 2.0

def send_tg_msg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram Status: {res.status_code}")
    except:
        pass

# --- 數據源 1: dYdX v4 (去中心化) ---
def check_dydx():
    url = f"https://indexer.dydx.trade/v4/candles/perpetualMarkets/{SYMBOL_DYDX}?resolution=1MIN"
    try:
        r = requests.get(url, timeout=8).json().get('candles', [])
        curr, hist = r[0], r[1:6]
        o, c, v = float(curr['open']), float(curr['close']), float(curr['baseTokenVolume'])
        avg_v = sum(float(x['baseTokenVolume']) for x in hist) / 5
        return ("dYdX", o, c, v, avg_v)
    except: return None

# --- 數據源 2: Binance.US (美國幣安) ---
def check_binance_us():
    url = f"https://api.binance.us/api/v3/klines?symbol={SYMBOL_BINANCE}&interval=1m&limit=6"
    try:
        r = requests.get(url, timeout=8).json()
        curr, hist = r[-1], r[-6:-1]
        o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
        avg_v = sum(float(x[5]) for x in hist) / 5
        return ("Binance.US", o, c, v, avg_v)
    except: return None

# --- 數據源 3: CryptoCompare (聚合數據中心) ---
def check_cryptocompare():
    fsym = SYMBOL_DYDX.split("-")[0]
    url = f"https://min-api.cryptocompare.com/data/v2/histoMinute?fsym={fsym}&tsym=USDT&limit=6"
    try:
        r = requests.get(url, timeout=8).json()['Data']['Data']
        curr, hist = r[-1], r[-6:-1]
        o, c, v = float(curr['open']), float(curr['close']), float(curr['volumefrom'])
        avg_v = sum(float(x['volumefrom']) for x in hist) / 5
        return ("CryptoCompare", o, c, v, avg_v)
    except: return None

def process_source(source_data):
    if not source_data: return
    name, o, c, v, avg_v = source_data
    if v > (avg_v * VOL_MULTIPLIER):
        if c < o:
            send_tg_msg(f"⚠️ **{name} 警報**\n標的: `{SYMBOL_DYDX}`\n型態: `陰線大買` (1M)\n量: `{v:.1f}` (均: `{avg_v:.1f}`)")
        elif c > o:
            send_tg_msg(f"🚨 **{name} 警報**\n標的: `{SYMBOL_DYDX}`\n型態: `陽線大賣` (1M)\n量: `{v:.1f}` (均: `{avg_v:.1f}`)")

def main():
    send_tg_msg(f"🛰️ **Radar_聚合監控啟動**\n同時掃描: `dYdX`, `Binance.US`, `CryptoCompare`")
    last_processed_min = ""
    
    while True:
        current_min = time.strftime("%H:%M")
        if current_min != last_processed_min:
            # 使用線程池並行請求，節省時間
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(check_dydx), executor.submit(check_binance_us), executor.submit(check_cryptocompare)]
                for f in futures:
                    process_source(f.result())
            last_processed_min = current_min
        time.sleep(20)

if __name__ == "__main__":
    main()
