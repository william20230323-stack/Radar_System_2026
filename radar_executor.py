import os
import time
import random
import requests
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- 鎖死保險箱鑰匙 ---
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
SYMBOL = os.environ.get('TRADE_SYMBOL')

# 美國幣安多端口
ENDPOINTS = [
    "https://api.binance.us/api/v3",
    "https://api1.binance.us/api/v3",
    "https://api2.binance.us/api/v3",
    "https://api3.binance.us/api/v3"
]

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def fetch_data():
    # 輪流更換端口避免封鎖
    base_url = random.choice(ENDPOINTS)
    url = f"{base_url}/klines?symbol={SYMBOL}&interval=1m&limit=100"
    res = requests.get(url, timeout=5).json()
    df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
    return df.astype(float)

def core_logic():
    df = fetch_data()
    last = df.iloc[-1]
    
    # 1. 陰陽線異常量能偵測
    is_yin = last['close'] < last['open']
    is_yang = last['close'] > last['open']
    # 掃貨/出逃判斷 (主動買入 vs 總成交)
    buy_vol = last['taker_buy_quote']
    sell_vol = last['quote_volume'] - buy_vol
    
    if is_yin and (buy_vol > last['quote_volume'] * 0.5):
        send_tg(f"🏮 <b>陰線逆勢掃貨</b>\n標的: {SYMBOL}\n價格: {last['close']}\n掃貨金額: {buy_vol:.2f}")
    elif is_yang and (sell_vol > last['quote_volume'] * 0.5):
        send_tg(f"🚨 <b>陽線主力出逃</b>\n標的: {SYMBOL}\n價格: {last['close']}\n出貨金額: {sell_vol:.2f}")

    # 2. 雙指標共振 (MACD 14,55,9 | KDJ 18,9,9)
    # MACD
    macd = ta.macd(df['close'], fast=14, slow=55, signal=9)
    # KDJ (使用 pandas_ta 的 stoch)
    kdj = ta.stoch(df['high'], df['low'], df['close'], k=18, d=9, smooth_k=9)
    
    m_val = macd['MACD_14_55_9'].iloc[-1]
    s_val = macd['MACDs_14_55_9'].iloc[-1]
    k_val = kdj['STOCHk_18_9_9'].iloc[-1]
    d_val = kdj['STOCHd_18_9_9'].iloc[-1]

    # 提前一分鐘共振判斷 (趨勢接近且方向一致)
    if abs(m_val - s_val) < (m_val * 0.01) and abs(k_val - d_val) < 2:
        direction = "金叉共振" if m_val > s_val else "死叉共振"
        send_tg(f"🎯 <b>指標提前預警</b>\n標的: {SYMBOL}\n狀態: {direction} 即將發生")

if __name__ == "__main__":
    # 設定重啟週期：10分鐘內隨機 (例如 540~600 秒)
    restart_limit = random.randint(540, 600)
    start_time = time.time()
    
    while time.time() - start_time < restart_limit:
        try:
            core_logic()
        except Exception as e:
            print(f"運行錯誤: {e}")
        
        # 15秒掃描一次
        time.sleep(15)
    
    # 結束前隨機休息 (不超過30秒)
    time.sleep(random.randint(1, 30))
