import pandas_ta as ta
import requests

def analyze_indicators(df, symbol, tg_token, tg_chat_id):
    # MACD 14, 55, 9
    macd = ta.macd(df['close'], fast=14, slow=55, signal=9)
    # KDJ 18, 9, 9
    kdj = ta.stoch(df['high'], df['low'], df['close'], k=18, d=9, smooth_k=9)
    
    m_val = macd['MACD_14_55_9'].iloc[-1]
    s_val = macd['MACDs_14_55_9'].iloc[-1]
    k_val = kdj['STOCHk_18_9_9'].iloc[-1]
    d_val = kdj['STOCHd_18_9_9'].iloc[-1]

    # 提前共振判斷
    if abs(m_val - s_val) < (abs(m_val) * 0.1) and abs(k_val - d_val) < 3:
        direction = "金叉" if m_val > s_val else "死叉"
        msg = f"🎯 <b>指標提前預警</b>\n標的: {symbol}\n狀態: {direction}共振即將發生"
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        requests.post(url, json={"chat_id": tg_chat_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
