import os
import time
import requests

# 從 GitHub Secrets 獲取設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSK-USD")

# 定義異常成交量倍數 (例如：成交量高於前 5 根平均值的 2 倍)
VOL_MULTIPLIER = 2.0

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_data():
    """獲取 dYdX v4 1分鐘 K線數據"""
    try:
        url = f"https://indexer.dydx.exchange/v4/candles/perpetualMarkets/{SYMBOL}?resolution=1MIN"
        response = requests.get(url, timeout=10)
        return response.json().get('candles', [])
    except:
        return []

def monitor():
    print(f"開始掃描 {SYMBOL}...")
    last_processed_time = ""

    while True:
        candles = get_data()
        if not candles:
            time.sleep(10)
            continue
        
        # 獲取最新完成的 K 線 (candles[0] 為當前未完成, [1] 為剛結束)
        current = candles[0]
        prev_candles = candles[1:6] # 用於計算平均成交量
        
        if current['startedAt'] == last_processed_time:
            time.sleep(15)
            continue

        open_p = float(current['open'])
        close_p = float(current['close'])
        volume = float(current['baseTokenVolume'])
        avg_vol = sum(float(c['baseTokenVolume']) for c in prev_candles) / len(prev_candles)

        # 邏輯判斷
        is_red = close_p < open_p  # 陰線
        is_green = close_p > open_p # 陽線
        high_vol = volume > (avg_vol * VOL_MULTIPLIER)

        if high_vol:
            if is_red:
                # 陰線 + 異常大成交量 = 可能有大買單在低位承接或洗盤
                send_alert(f"⚠️ **DUSK 異常警報 (1M)**\n型態：`陰線 (Red)`\n狀態：`大量買單承接/異常放量`\n成交量：`{volume:.2f}` (均值: {avg_vol:.2f})")
            elif is_green:
                # 陽線 + 異常大成交量 = 可能有大賣單在高位出逃
                send_alert(f"🚨 **DUSK 異常警報 (1M)**\n型態：`陽線 (Green)`\n狀態：`大量賣單拋售/出逃`\n成交量：`{volume:.2f}` (均值: {avg_vol:.2f})")

        last_processed_time = current['startedAt']
        time.sleep(20) # 避免過度請求 API

if __name__ == "__main__":
    monitor()
