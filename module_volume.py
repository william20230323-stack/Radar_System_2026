import requests

# --- 直接給予通訊鑰匙，讓模組判定後能獨立發送 ---
TOKEN = "7961234988:AAHcl_N4k_K9YkO08C6G6l6E5F8x6X6X6X"
CHAT_ID = "6348600000"

def module_report(text):
    """模組專屬實體鑰匙通路"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def analyze_volume(df, symbol):
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
            msg = f"🏮 <b>逆勢掃貨預警 (A)</b>\n標的: {symbol}\n買佔比: {ratio:.1%}"
        elif is_yang and (1 - ratio) > 0.20:
            msg = f"🚨 <b>主力出逃預警 (A)</b>\n標的: {symbol}\n賣佔比: {(1-ratio):.1%}"
            
        if msg:
            module_report(msg)
    except:
        pass
