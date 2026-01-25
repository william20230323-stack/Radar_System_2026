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
        # 1. 獲取 K 線
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=MML_LOOKBACK)
        # 2. 獲取最新成交明細
        trades = ex.fetch_trades(symbol, limit=80)
        
        if ohlcv and len(ohlcv) >= 6:
            curr = ohlcv[-1]   
            hist = ohlcv[-7:-1] 
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            
            # --- 莫里數學位階判定 ---
            highs = [float(x[2]) for x in ohlcv]
            lows = [float(x[3]) for x in ohlcv]
            hi, lo = max(highs), min(lows)
            r = hi - lo
            midline = lo + r * 0.5
            oscillator = (c - midline) / (r / 2) if r != 0 else 0
            is_os = oscillator < -MML_MULT * 6  # 賣超
            is_ob = oscillator > MML_MULT * 6   # 買超
            
            # --- 主動買賣比計算 ---
            buy_v = sum(float(t['amount']) for t in trades if t['side'] == 'buy')
            sell_v = sum(float(t['amount']) for t in trades if t['side'] == 'sell')
            total_trade_v = buy_v + sell_v
            
            buy_pct = (buy_v / total_trade_v * 100) if total_trade_v > 0 else 0
            sell_pct = (sell_v / total_trade_v * 100) if total_trade_v > 0 else 0
            
            log(f"Gate 更新 | {symbol} | 價: {c} | 買比: {buy_pct:.1f}% | MML: {oscillator:.2f}")
            return {
                'symbol': symbol, 'o': o, 'c': c, 'v': v, 'avg_v': avg_v,
                'is_os': is_os, 'is_ob': is_ob,
                'buy_pct': buy_pct, 'sell_pct': sell_pct
            }
    except Exception as e:
        log(f"{symbol} 數據採集異常: {str(e)[:50]}")
    return None

def main():
    log("=== Radar_System_2026 DUSK 專屬版啟動 ===")
    
    send_tg(f"🚀 **Radar 雙向系統實戰啟動**\n標的：`{', '.join(SYMBOLS)}`\n門檻：`主動比 45%`\n頻率：`隨機 3-8s`")

    last_min_processed = {symbol: "" for symbol in SYMBOLS}
    ex = ccxt.gateio({'enableRateLimit': True, 'timeout': 15000})
    
    while True:
        # 安全退場機制 (5 小時續命)
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 運行已達 5 小時，主動結束以觸發重啟...")
            sys.exit(0)

        for symbol in SYMBOLS:
            data = get_market_data(ex, symbol)
            if data:
                o, c, v, avg_v = data['o'], data['c'], data['v'], data['avg_v']
                now_min = time.strftime("%H:%M")
                
                # 成交量翻倍偵測
                if now_min != last_min_processed[symbol] and v > (avg_v * VOL_THRESHOLD):
                    alert_msg = ""
                    
                    # 【核心邏輯 1】：陰線 + 主動買單達 45% = 吃貨警報
                    if c < o and data['buy_pct'] >= 45:
                        extra = "\n📊 **目前賣超**" if data['is_os'] else ""
                        alert_msg = (f"🟡 **當k線是陰線時有大量主動買單進場警報**\n"
                                     f"標的: `{symbol}`\n"
                                     f"主動買進比例: `{data['buy_pct']:.1f}%`"
                                     f"{extra}")
                    
                    # 【核心邏輯 2】：陽線 + 主動賣單達 45% = 出逃警報
                    elif c > o and data['sell_pct'] >= 45:
                        extra = "\n📊 **目前買超**" if data['is_ob'] else ""
                        alert_msg = (f"🟠 **陽線時主動賣單出逃警報**\n"
                                     f"標的: `{symbol}`\n"
                                     f"主動出逃比例: `{data['sell_pct']:.1f}%`"
                                     f"{extra}")
                    
                    if alert_msg:
                        send_tg(alert_msg)
                        last_min_processed[symbol] = now_min
            
            # 幣種掃描微小間隔
            time.sleep(0.5)
        
        # 修正：採集時間改為隨機 3-8 秒
        wait_time = random.randint(3, 8)
        log(f"一輪掃描結束，休眠 {wait_time} 秒...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
