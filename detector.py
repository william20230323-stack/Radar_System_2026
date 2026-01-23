import os
import time
import requests

# 從 GitHub Secrets 獲取設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSK-USD")
VOL_THRESHOLD_MULTIPLIER = 2.0 

def send_tg_msg(msg):
    """發送訊息至 Telegram"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"發送失敗: {e}")

def get_candles():
    """獲取 dYdX v4 1分鐘 K線數據"""
    url = f"https://indexer.dydx.exchange/v4/candles/perpetualMarkets/{SYMBOL}?resolution=1MIN"
    try:
        response = requests.get(url, timeout=10)
        return response.json().get('candles', [])
    except:
        return []

def run_logic():
    # 1. 啟動通知
    start_time = time.strftime('%Y-%m-%d %H:%M:%S')
    send_tg_msg(f"🚀 **Radar_System_2026 啟動**\n監控幣種：`{SYMBOL}`\n掃描頻率：`1m`\n啟動時間：`{start_time}`\n狀態：`24/7 持續偵測中`")

    last_candle_time = ""
    
    while True:
        data = get_candles()
        if not data or len(data) < 6:
            time.sleep(10)
            continue
        
        current = data[0]   # 當前 K 線
        history = data[1:6] # 前 5 根 K 線

        if current['startedAt'] == last_candle_time:
            time.sleep(10)
            continue

        o = float(current['open'])
        c = float(current['close'])
        v = float(current['baseTokenVolume'])
        avg_v = sum(float(i['baseTokenVolume']) for i in history) / len(history)

        is_red = c < o
        is_green = c > o
        is_high_vol = v > (avg_v * VOL_THRESHOLD_MULTIPLIER)

        # 2. 偵測邏輯通知
        if is_high_vol:
            if is_red:
                send_alert_msg = (
                    f"⚠️ **量價背離警報 (DUSK)**\n"
                    f"型態：`陰線 (Red Candle)`\n"
                    f"訊號：`低位大量買單進場`\n"
                    f"當前成交量：`{v:.2f}`\n"
                    f"平均成交量：`{avg_v:.2f}`"
                )
                send_tg_msg(send_alert_msg)
            elif is_green:
                send_alert_msg = (
                    f"🚨 **量價背離警報 (DUSK)**\n"
                    f"型態：`陽線 (Green Candle)`\n"
                    f"訊號：`高位大量賣單出逃`\n"
                    f"當前成交量：`{v:.2f}`\n"
                    f"平均成交量：`{avg_v:.2f}`"
                )
                send_tg_msg(send_alert_msg)

        last_candle_time = current['startedAt']
        time.sleep(10)

if __name__ == "__main__":
    run_logic()
