import os
import requests

# --- 強行植入通訊鑰匙讀取 ---
def module_independent_report(text):
    """模組 A 專屬：直接讀取鑰匙並回報"""
    token = str(os.environ.get('TG_TOKEN', '')).strip()
    chat_id = str(os.environ.get('TG_CHAT_ID', '')).strip()
    if not token or not chat_id:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def analyze_volume(df, symbol):
    """
    武器庫底層 A：單邊攻擊判定
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
            
        # 核心：發現異常直接調用內建鑰匙發送，不經過任何人
        if msg:
            module_independent_report(msg)
            print(f"📢 模組 A 已成功獲取鑰匙並獨立發報")
            
    except:
        pass
