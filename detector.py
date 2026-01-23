import os
import time
import requests

# 從 GitHub Secrets 讀取 (請確保名稱完全一致)
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# Binance.US 交易對通常為 DUSKUSDT
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSKUSDT")
VOL_MULTIPLIER = 2.0 

def send_tg_msg(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Missing TG Secrets.")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e:
        print(f"TG Error: {e}")

def get_binance_us_data():
    """獲取 Binance.US 1分鐘 K線數據"""
    # 使用 Binance.US 官方公開 API
    url = f"https://api.binance.us/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=6"
    try:
        response = requests.get(url, timeout=10)
        return response.json() # 回傳格式: [[open_time, open, high, low, close, volume, ...], ...]
    except Exception as e:
        print(f"Binance.US API Error: {e}")
        return []

def main():
    # 啟動即通知
    send_tg_msg(f"🚀 **Radar_System_2026 啟動 (Binance.US)**\n監控標的：`{SYMBOL}`\n狀態：`24/7 持續監控中`")
    
    last_candle_time = 0
    while True:
        data = get_binance_us_data()
        if not data or len(data) < 6:
            time.sleep(10)
            continue
            
        # Binance K線數據解析 (最後一根是 [5], 前面是 [0-4])
        # [0]開盤時間, [1]開盤價, [4]收盤價, [5]成交量
        current = data[-1]
        history = data[-6:-1]
        
        current_time = current[0]
        if current_time == last_candle_time:
            time.sleep(15)
            continue
            
        o, c = float(current[1]), float(current[4])
        v = float(current[5])
        avg_v = sum(float(x[5]) for x in history) / 5
        
        is_red = c < o
        is_green = c > o
        high_vol = v > (avg_v * VOL_MULTIPLIER)

        if high_vol:
            if is_red:
                send_tg_msg(f"⚠️ **Binance.US 警報**\n標的：`{SYMBOL}`\n型態：`陰線` (1M)\n訊號：`低位大量買單進場`\n成交量：`{v:.2f}`")
            elif is_green:
                send_tg_msg(f"🚨 **Binance.US 警報**\n標的：`{SYMBOL}`\n型態：`陽線` (1M)\n訊號：`高位大量賣單出逃`\n成交量：`{v:.2f}`")

        last_candle_time = current_time
        time.sleep(15)

if __name__ == "__main__":
    main()
