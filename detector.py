import os
import time
import akshare as ak
import requests
import pandas as pd

# 密鑰配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL = "DUSK" # AKShare 通常使用簡稱

def send_tg_msg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def get_akshare_data():
    """調用 AKShare 接口獲取分鐘數據"""
    try:
        # 使用數字貨幣行情接口 (範例使用主流接口轉換)
        # 注意：AKShare 的接口名稱經常更新，這是獲取即時行情的常用方式
        df = ak.crypto_hist_node(symbol=SYMBOL, period="1") 
        return df
    except Exception as e:
        print(f"AKShare Error: {e}")
        return None

def main():
    send_tg_msg(f"📡 **AKShare 偵測引擎啟動**\n監控標的: `{SYMBOL}`\n環境: `GitHub Actions`")
    
    last_time = None
    
    while True:
        df = get_akshare_data()
        
        if df is not None and not df.empty:
            # 取最後兩筆數據進行比對
            latest = df.iloc[-1]
            prev_avg = df.iloc[-6:-1]['volume'].mean() # 計算前 5 分鐘均量
            
            curr_time = latest['item_time']
            if curr_time != last_time:
                o, c, v = float(latest['open']), float(latest['close']), float(latest['volume'])
                
                # 您的核心偵測邏輯
                if v > (prev_avg * 2.0):
                    if c < o:
                        send_tg_msg(f"⚠️ **AKShare 警報**\n標的: `{SYMBOL}`\n型態: `陰線大買` (1M)\n量: `{v:.1f}` (均: `{prev_avg:.1f}`)")
                    elif c > o:
                        send_tg_msg(f"🚨 **AKShare 警報**\n標的: `{SYMBOL}`\n型態: `陽線大賣` (1M)\n量: `{v:.1f}` (均: `{prev_avg:.1f}`)")
                
                last_time = curr_time
        
        time.sleep(30) # AKShare 抓取網頁建議間隔稍長，避免被封 IP

if __name__ == "__main__":
    main()
