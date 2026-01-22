import os
import requests

# --- 核心：模組獨立具備讀取保險箱鑰匙的代碼 ---
def module_report(text):
    """模組獨立從環境變數讀取鑰匙並回報"""
    token = os.environ.get('TG_TOKEN')
    chat_id = os.environ.get('TG_CHAT_ID')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        except:
            pass

def analyze_volume(df, symbol):
    """武器庫底層 A：判定異常並【直接使用保險箱鑰匙回傳】"""
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
            
        # 發現異常，直接拿保險箱鑰匙發射
        if msg:
            module_report(msg)
    except:
        pass
