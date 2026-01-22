import os
import time
import requests
import pandas as pd

# 從啟動項 (.yml) 接收環境變數
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

# --- 連結模組通路 ---
from module_volume import analyze_volume
# ------------------

# 建立接口池：輪流切換，降低單一接口被封鎖機率
API_POOL = [
    f"https://api.binance.us/api/v3/klines",
    f"https://api.binance.com/api/v3/klines",
    f"https://api1.binance.com/api/v3/klines",
    f"https://api2.binance.com/api/v3/klines"
]
current_api_index = 0

def broadcast_exception(msg):
    """將偵查到的異常信息傳遞出來"""
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def fetch_market_data():
    """執行市場偵查：接口輪替邏輯"""
    global current_api_index
    target_symbol = str(SYMBOL).strip().upper()
    
    # 選取當前接口
    base_url = API_POOL[current_api_index]
    url = f"{base_url}?symbol={target_symbol}&interval=1m&limit=100"
    
    # 準備下一輪換接口
    current_api_index = (current_api_index + 1) % len(API_POOL)
    
    try:
        response = requests.get(url, timeout=12)
        if response.status_code == 200:
            res = response.json()
            if not res: return None
            df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']).astype(float)
            return df
        else:
            print(f"⚠️ 接口 {base_url} 響應異常: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ 接口連線失敗: {e}")
        return None

if __name__ == "__main__":
    MAX_DETECTION_TIME = 280 
    start_ts = time.time()
    
    print(f"🕵️ 偵查執行員就位 | 目標：{SYMBOL} | 模式：多接口輪替偵查")

    while time.time() - start_ts < MAX_DETECTION_TIME:
        loop_start = time.time()
        try:
            data = fetch_market_data()
            
            # 數據空值防護
            if data is not None and not data.empty:
                last = data.iloc[-1]
                t_vol = last['quote_volume']
                b_ratio = last['taker_buy_quote'] / t_vol if t_vol > 0 else 0
                
                # 顯示當前使用的接口編號 (API Pool Index)
                print(f"[{time.strftime('%H:%M:%S')}] 偵查中(接口{current_api_index})... 價格: {last['close']} | 買佔比: {b_ratio:.2%}")

                # 模組判定
                alert_msg = analyze_volume(data, SYMBOL)
                if alert_msg:
                    broadcast_exception(alert_msg)
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 數據抓取為空，接口嘗試切換中...")
        
        except Exception as e:
            print(f"⚠️ 偵查流程異常: {e}")
        
        # 15 秒偵查一次
        time.sleep(max(0, 15 - (time.time() - loop_start)))

    print("🏁 偵查結束。")
