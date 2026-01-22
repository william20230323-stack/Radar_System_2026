import os
import requests

def module_direct_report(text):
    """武器庫模組獨立通訊：具備專屬 Token 讀取與發送通路"""
    token = str(os.environ.get('TG_TOKEN', '')).strip()
    chat_id = str(os.environ.get('TG_CHAT_ID', '')).strip()
    if not token or not chat_id: return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def analyze_volume(df, symbol):
    """
    武器庫底層 A：判定異常並【直接、獨立回傳】
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
        # 判定邏輯
        if is_yin and ratio > 0.20:
            msg = f"🏮 <b>逆勢掃貨預警 (模組 A)</b>\n標的: {symbol}\n買佔比: {ratio:.1%}"
        elif is_yang and (1 - ratio) > 0.20:
            msg = f"🚨 <b>主力出逃預警 (模組 A)</b>\n標的: {symbol}\n賣佔比: {(1-ratio):.1%}"
            
        # 核心：判定完畢，使用模組自帶的通訊模組發射訊息
        if msg:
            module_direct_report(msg)
            print(f"📢 模組 A 偵測到異常，已獨立向 Telegram 發報")
            
    except:
        pass
