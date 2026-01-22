import requests

def analyze_volume(df, symbol, tg_token, tg_chat_id):
    last = df.iloc[-1]
    is_yin = last['close'] < last['open']
    is_yang = last['close'] > last['open']
    buy_vol = last['taker_buy_quote']
    sell_vol = last['quote_volume'] - buy_vol
    
    msg = ""
    if is_yin and (buy_vol > last['quote_volume'] * 0.5):
        msg = f"🏮 <b>陰線逆勢掃貨</b>\n標的: {symbol}\n價格: {last['close']}\n掃貨金額: {buy_vol:.2f}"
    elif is_yang and (sell_vol > last['quote_volume'] * 0.5):
        msg = f"🚨 <b>陽線主力出逃</b>\n標的: {symbol}\n價格: {last['close']}\n出貨金額: {sell_vol:.2f}"
    
    if msg:
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        requests.post(url, json={"chat_id": tg_chat_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
