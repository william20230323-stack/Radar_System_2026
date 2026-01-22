def analyze_volume(df, symbol):
    # 取得最新一根 K 線數據
    last = df.iloc[-1]
    is_yin = last['close'] < last['open']   # 陰線
    is_yang = last['close'] > last['open']  # 陽線
    
    # 主動買盤金額 (Taker Buy Quote Volume)
    buy_vol_amount = last['taker_buy_quote']
    # 總成交金額 (Total Quote Volume)
    total_vol_amount = last['quote_volume']
    
    # 防止除以零
    if total_vol_amount == 0:
        return None

    # 計算主動佔比
    buy_ratio = buy_vol_amount / total_vol_amount
    sell_ratio = (total_vol_amount - buy_vol_amount) / total_vol_amount
    
    # --- 調整門檻為 20% (0.20) ---
    
    # 陰線 + 主動買入佔比 > 20% = 懷疑有機構在低位護盤或逆勢吸籌
    if is_yin and (buy_ratio > 0.20):
        return (f"🏮 <b>左側預警：陰線逆勢掃貨</b>\n"
                f"標的: {symbol}\n"
                f"當前價格: {last['close']}\n"
                f"主動買入佔比: {buy_ratio:.1%}\n"
                f"狀態: 資金試探性介入")
    
    # 陽線 + 主動賣出佔比 > 20% = 懷疑主力在拉升過程中邊拉邊撤
    elif is_yang and (sell_ratio > 0.20):
        return (f"🚨 <b>左側預警：陽線主力出逃</b>\n"
                f"標的: {symbol}\n"
                f"當前價格: {last['close']}\n"
                f"主動賣出佔比: {sell_ratio:.1%}\n"
                f"狀態: 警戒拉高派發")
    
    return None
