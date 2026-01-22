import os
import requests

# --- 模組獨立對接您保險箱截圖的變數名稱 ---
M_TOKEN = os.environ.get('TG_TOKEN')
M_ID = os.environ.get('TG_CHAT_ID')

def module_report(text):
    """模組 A 獨立使用保險箱鑰匙發報"""
    if not M_TOKEN or not M_ID: return
    url = f"https://api.telegram.org/bot{M_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": M_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def analyze_volume(df, symbol):
    """
    判定邏輯：異常後直接獨立發報
    """
    try:
        last = df.iloc[-1]
        buy_vol = last['taker_buy_quote']
        total_vol = last['quote_volume']
        if total_vol <= 0: return
        
        ratio = buy_vol / total_vol
        is_yin = last['close'] < last['open']
        is_yang = last['close'] > last['open']
        
        msg = ""
        if is_yin and ratio > 0.20:
            msg = f"🏮 <b>逆勢掃貨預警 (模組 A)</b>\n標的: {symbol}\n買佔比: {ratio:.1%}"
        elif is_yang and (1 - ratio) > 0.20:
            msg = f"🚨 <b>主力出逃預警 (模組 A)</b>\n標的: {symbol}\n賣佔比: {(1-ratio):.1%}"
            
        if msg:
            module_report(msg)
            print(f"📢 模組 A 判定完成，已利用保險箱鑰匙發報")
            
    except:
        pass
