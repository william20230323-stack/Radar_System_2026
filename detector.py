import os
import time
import requests
import ccxt
import random
import sys

# 強制即時輸出日誌
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# 紀錄啟動時間 (用於 5 小時續命)
START_TIME = time.time()
MAX_RUN_TIME = 18000 # 5 小時

# 讀取 Secrets 環境變數
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()

# 僅監控 DUSK
SYMBOLS = ["DUSK/USDT"]
VOL_THRESHOLD = 2.0 # 成交量翻倍門檻

# MML 莫里數學參數
MML_LOOKBACK = 100 
MML_MULT = 0.125

def send_tg(msg):
    """呼叫 Telegram API 發送警報"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        log(f"TG Status: {r.status_code}")
    except Exception as e:
        log(f"TG 發送異常: {e}")

def get_market_data(ex, symbol):
    """獲取數據邏輯：K線 + 主動買賣分析 + MML 位階"""
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=MML_LOOKBACK)
        trades = ex.fetch_trades(symbol, limit=80)
        
        if ohlcv and len(ohlcv) >= 6:
            curr = ohlcv[-1]   
            hist = ohlcv[-7:-1] 
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            
            highs = [float(x[2]) for x in ohlcv]
            lows = [float(x[3]) for x in ohlcv]
            hi, lo = max(highs), min(lows)
            r = hi - lo
            midline = lo + r * 0.5
            oscillator = (c - midline) / (r / 2) if r != 0 else 0
            is_os = oscillator < -MML_MULT * 6
            is_ob = oscillator > MML_MULT * 6
            
            buy_v = sum(float(t['amount']) for t in trades if t['side'] == 'buy')
            sell_v = sum(float(t['amount']) for t in trades if t['side'] == 'sell')
            total_trade_v = buy_v + sell_v
            
            buy_pct = (buy_v / total_trade_v * 100) if total_trade_v > 0 else 0
            sell_pct = (sell_v / total_trade_v * 100) if total_trade_v > 0 else 0
            
            # 這裡調整為同時顯示買賣比
            log(f"Gate 更新 | {symbol} | 價: {c} | 買: {buy_pct:.1f}% 賣: {sell_pct:.1f}% | MML: {oscillator:.2f}")
            return {
                'symbol': symbol, 'o': o, 'c': c, 'v': v, 'avg_v': avg_v,
                'is_os': is_os, 'is_ob': is_ob,
                'buy_pct': buy_pct, 'sell_pct': sell_pct,
                'mml_val': oscillator
            }
    except Exception as e:
        log(f"{symbol} 數據採集異常: {str(e)[:50]}")
    return None

def main():
    log("=== Radar_System_2026 DUSK 雙向強化版啟動 ===")
    send_tg(f"🚀 **Radar 雙向系統實戰啟動**\n標的：`{', '.join(SYMBOLS)}`\n監控：`買賣雙向比例 & MML 零軸反轉`")

    last_min_processed = {symbol: "" for symbol in SYMBOLS}
    prev_mml_state = {symbol: 0 for symbol in SYMBOLS} 
    ex = ccxt.gateio({'enableRateLimit': True, 'timeout': 15000})
    
    while True:
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 運行已達 5 小時，主動結束以觸發重啟...")
            sys.exit(0)

        for symbol in SYMBOLS:
            data = get_market_data(ex, symbol)
            if data:
                o, c, v, avg_v = data['o'], data['c'], data['v'], data['avg_v']
                buy_pct, sell_pct, mml = data['buy_pct'], data['sell_pct'], data['mml_val']
                now_min = time.strftime("%H:%M")
                
                current_mml_state = 1 if mml > 0 else 0
                
                # 反轉向下預警 (賣比 > 60% + 由正轉負)
                if sell_pct >= 60 and prev_mml_state[symbol] == 1 and current_mml_state == 0:
                    down_msg = (f"📉 **反轉向下預警**\n標的: `{symbol}`\n狀態: `MML 由正轉負 ({mml:.2f})`\n賣出比例: `{sell_pct:.1f}%`")
                    send_tg(down_msg)
                
                # 反轉向上預警 (買比 > 60% + 由負轉正)
                elif buy_pct >= 60 and prev_mml_state[symbol] == 0 and current_mml_state == 1:
                    up_msg = (f"🔥 **反轉向上預警**\n標的: `{symbol}`\n狀態: `MML 由負轉正 ({mml:.2f})`\n買入比例: `{buy_pct:.1f}%`")
                    send_tg(up_msg)
                
                prev_mml_state[symbol] = current_mml_state

                if now_min != last_min_processed[symbol] and v > (avg_v * VOL_THRESHOLD):
                    alert_msg = ""
                    if c < o and buy_pct >= 45:
                        alert_msg = (f"🟡 **陰線主動買單吃貨警報**\n標的: `{symbol}`\n買進比例: `{buy_pct:.1f}%`")
                    elif c > o and sell_pct >= 45:
                        alert_msg = (f"🟠 **陽線主動賣單出逃警報**\n標的: `{symbol}`\n出逃比例: `{sell_pct:.1f}%`")
                    
                    if alert_msg:
                        send_tg(alert_msg)
                        last_min_processed[symbol] = now_min
            
            time.sleep(0.5)
        
        wait_time = random.randint(3, 8)
        log(f"一輪掃描結束，休眠 {wait_time} 秒...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
