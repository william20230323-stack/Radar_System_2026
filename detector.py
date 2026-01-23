import os
import time
import requests

# 嚴格對接截圖中的密鑰名稱
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSK-USD")
VOL_MULTIPLIER = 2.0

def send_tg_msg(msg):
    """直接發送訊息至 Telegram 並打印結果"""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Error: Missing TG_TOKEN or TG_CHAT_ID in Secrets.")
        return
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Telegram response: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Telegram connection error: {e}")

def get_market_data():
    """使用 dYdX v4 穩定版 Indexer API"""
    # 切換至更穩定的主網端點
    url = f"https://indexer.dydx.trade/v4/candles/perpetualMarkets/{SYMBOL}?resolution=1MIN"
    try:
        response = requests.get(url, timeout=10)
        return response.json().get('candles', [])
    except Exception as e:
        print(f"API Error: {e}")
        return []

def run_radar():
    # --- 啟動立即通知 ---
    print(f"Radar System Initializing for {SYMBOL}...")
    send_tg_msg(f"🚀 **Radar_System_2026 已成功啟動**\n監控標的：`{SYMBOL}`\n掃描頻率：`1m`\n環境：`GitHub US Server`\n狀態：`24/7 持續監控中`")
    
    last_candle_time = ""
    
    while True:
        candles = get_market_data()
        if not candles or len(candles) < 6:
            time.sleep(15)
            continue
        
        current = candles[0]   # 當前 K 線
        history = candles[1:6] # 前 5 根 K 線

        if current['startedAt'] == last_candle_time:
            time.sleep(15)
            continue

        # 價格與成交量計算
        o, c = float(current['open']), float(current['close'])
        v = float(current['baseTokenVolume'])
        avg_v = sum(float(x['baseTokenVolume']) for x in history) / 5

        is_red = c < o
        is_green = c > o
        high_vol = v > (avg_v * VOL_MULTIPLIER)

        # 偵測條件：陰線大買 / 陽線大賣
        if high_vol:
            if is_red:
                send_tg_msg(f"⚠️ **DUSK 異常大買警報**\n型態：`陰線 (價格跌)`\n訊號：`底部放量/大單承接`\n當前量：`{v:.2f}`\n平均量：`{avg_v:.2f}`")
            elif is_green:
                send_tg_msg(f"🚨 **DUSK 異常大賣警報**\n型態：`陽線 (價格漲)`\n訊號：`高位放量/大單出逃`\n當前量：`{v:.2f}`\n平均量：`{avg_v:.2f}`")

        last_candle_time = current['startedAt']
        time.sleep(20)

if __name__ == "__main__":
    run_radar()
