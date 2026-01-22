def analyze_volume(df, symbol):
    # 取得最新一根 K 線數據
    last = df.iloc[-1]
    is_yin = last['close'] < last['open']   # 陰線
    is_yang = last['close'] > last['open']  # 陽線
    
    # 主動買盤 (Taker Buy Base Volume)
    buy_vol = last['taker_buy_quote']
    # 總成交量 (Total Quote Volume)
    total_vol = last['quote_volume']
    
    # 計算主動佔比
    buy_ratio = buy_vol / total_vol if total_vol > 0 else 0
    sell_ratio = (total_vol - buy_vol) / total_vol if total_vol > 0 else 0
    
    # --- 調整門檻為 35% (0.35) ---
    # 陰線 + 高額主動買入 = 逆勢掃貨 (左側信號)
    if is_yin and (buy_ratio > 0.35):
        return f"🏮 <b>左側預警：陰線逆勢掃貨</b>\n標的: {symbol}\n價格: {last['close']}\n主動買入佔比: {buy_ratio:.1%}"
    
    # 陽線 + 高額主動賣出 = 主力撤退 (左側信號)
    elif is_yang and (sell_ratio > 0.35):
        return f"🚨 <b>左側預警：陽線主力出逃</b>\n標的: {symbol}\n價格: {last['close']}\n主動賣出佔比: {sell_ratio:.1%}"
    
    return None
