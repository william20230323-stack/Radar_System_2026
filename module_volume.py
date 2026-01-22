def analyze_volume(df, symbol):
    """
    武器庫底層 A：負責異常過濾
    """
    try:
        last = df.iloc[-1]
        buy_vol = last['taker_buy_quote']
        total_vol = last['quote_volume']
        if total_vol <= 0: return None
        
        ratio = buy_vol / total_vol
        is_yin = last['close'] < last['open']
        is_yang = last['close'] > last['open']
        
        # 門檻判定
        if is_yin and ratio > 0.20:
            return f"🏮 <b>逆勢掃貨預警</b>\n標的: {symbol}\n買佔比: {ratio:.1%}"
        elif is_yang and (1 - ratio) > 0.20:
            return f"🚨 <b>主力出逃預警</b>\n標的: {symbol}\n賣佔比: {(1-ratio):.1%}"
    except:
        pass
    return None
