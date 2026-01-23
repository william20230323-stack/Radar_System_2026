import os
import time
import requests

# 從 GitHub Secrets 讀取 (請確保名稱完全一致)
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSK-USD")
VOL_MULTIPLIER = 2.0  # 成交量翻倍定義

def send_tg_msg(msg):
    """發送訊息至 Telegram"""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Missing Secrets: Check TG_TOKEN and TG_CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        print(f"TG Status: {res.status_code}")
    except Exception as e:
        print(f"TG Error: {e}")

def get_market_data():
    """獲取 dYdX v4 公開 K線數據 (無 IP 限制)"""
    # 使用 v4 官方推薦穩定端點
    url = f"https://indexer.dydx.trade/v4/candles/perpetualMarkets/{SYMBOL}?resolution=1MIN"
    try:
        response = requests.get(url, timeout=10)
        return response.json().get('candles', [])
    except Exception as e:
        print(f"API Error: {e}")
        return []

def main():
    # 啟動通知
    send_tg_msg(f"🚀 **Radar_System_2026**\n已成功在 GitHub 啟動\n監控標的：`{SYMBOL}`\n狀態：`24/7 偵測中`")
    
    last_candle_time = ""
    while True:
        candles = get_market_data()
        if not candles or len(candles) < 6:
            time.sleep(10)
            continue
            
        current = candles[0]
        history = candles[1:6]

        if current['startedAt'] == last_candle_time:
            time.sleep(15)
            continue
            
        # 數據提取
        o, c = float(current['open']), float(current['close'])
        v = float(current['baseTokenVolume'])
        avg_v = sum(float(x['baseTokenVolume']) for x in history) / 5
        
        # 偵測條件
        is_red = c < o
        is_green = c > o
        high_vol = v > (avg_v * VOL_MULTIPLIER)

        if high_vol:
            if is_red:
                send_tg_msg(f"⚠️ **DUSK 偵測警報**\n型態：`陰線 (1M)`\n訊號：`低位異常放量/買單承接`\n當前量：`{v:.2f}`")
            elif is_green:
                send_tg_msg(f"🚨 **DUSK 偵測警報**\n型態：`陽線 (1M)`\n訊號：`高位異常放量/賣單出逃`\n當前量：`{v:.2f}`")

        last_candle_time = current['startedAt']
        time.sleep(15)

if __name__ == "__main__":
    main()
