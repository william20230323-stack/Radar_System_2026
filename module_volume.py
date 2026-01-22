def analyze_volume(df, symbol):
    try:
        last = df.iloc[-1]
        t_vol = last['quote_volume']
        b_vol = last['taker_buy_quote']
        
        if t_vol <= 0: return None
        
        ratio = b_vol / t_vol
        is_yin = last['close'] < last['open']
        is_yang = last['close'] > last['open']
        
        # 維持老闆設定的 20% 門檻
        if is_yin and ratio > 0.20:
            return f"🏮 <b>左側預警：陰線逆勢掃貨</b>\n標的: {symbol}\n佔比: {ratio:.1%}"
        elif is_yang and (1 - ratio) > 0.20:
            return f"🚨 <b>左側預警：陽線主力出逃</b>\n標的: {symbol}\n佔比: {(1-ratio):.1%}"
    except:
        pass
    return None
