def analyze_volume(df, symbol):
    """
    負責判斷 20% 門檻
    """
    try:
        if df is None or df.empty: return None
        last = df.iloc[-1]
        
        is_yin = last['close'] < last['open']
        is_yang = last['close'] > last['open']
        buy_vol = last['taker_buy_quote']
        total_vol = last['quote_volume']
        
        if total_vol <= 0: return None
        ratio = buy_vol / total_vol
        
        # 20% 門檻
        if is_yin and ratio > 0.20:
            return f"🏮 <b>逆勢掃貨預警 (A)</b>\n標的: {symbol}\n買佔比: {ratio:.1%}"
        elif is_yang and (1 - ratio) > 0.20:
            return f"🚨 <b>主力出逃預警 (A)</b>\n標的: {symbol}\n賣佔比: {(1-ratio):.1%}"
    except:
        pass
    return None
