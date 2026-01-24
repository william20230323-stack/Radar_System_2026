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

# 同時搜索兩個標的
SYMBOLS = ["DUSK/USDT", "RIVER/USDT"]
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
    """獲取特定幣種數據：K線 + 主動買賣分析 + MML 位階"""
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
            is_os = oscillator < -MML_MULT * 6  # 賣超區
            is_ob = oscillator > MML_MULT * 6   # 買超區
            
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
    log("=== Radar_System_2026 雙標的高頻掃描啟動 ===")
    
    send_tg(f"🚀 **Radar 雙向系統實戰啟動**\n標的：`{', '.join(SYMBOLS)}`\n頻率：`5-10s`\n狀態：`背離 + MML 雙重監控中`")

    # 紀錄每個幣種最後處理的分鐘，避免同一分鐘重複報警
    last_min_processed = {symbol: "" for symbol in SYMBOLS}
    ex = ccxt.gateio({'enableRateLimit': True, 'timeout': 15000})
    
    while True:
        # 安全退場機制 (5 小時續命)
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 5小時運行結束，準備重啟...")
            sys.exit(0)

        for symbol in SYMBOLS:
            try:
                data = get_market_data(ex, symbol)
                if data:
                    o, c, v, avg_v = data['o'], data['c'], data['v'], data['avg_v']
                    now_min = time.strftime("%H:%M")
                    
                    # 偵測邏輯：成交量翻倍觸發
                    if now_min != last_min_processed[symbol] and v > (avg_v * VOL_THRESHOLD):
                        alert_msg = ""
                        
                        # 邏輯 A：陰線吃貨
                        if c < o:
                            extra_mml = "\n📊 **額外告知：目前賣超**" if data['is_os'] else ""
                            alert_msg = (f"⚠️ **Gate.io 異常大買**\n"
                                         f"標的: `{symbol}`\n"
                                         f"型態: `陰線大買` (1M)\n"
                                         f"成交量: `{v:.1f}` (均: `{avg_v:.1f}`)\n"
                                         f"主動買進佔比: `{data['buy_pct']:.1f}%`{extra_mml}")
                        
                        # 邏輯 B：陽線出逃
                        elif c > o:
                            extra_mml = "\n📊 **額外告知：目前買超**" if data['is_ob'] else ""
                            alert_msg = (f"🚨 **Gate.io 異常大賣**\n"
                                         f"標的: `{symbol}`\n"
                                         f"型態: `陽線大賣` (1M)\n"
                                         f"成交量: `{v:.1f}` (均: `{avg_v:.1f}`)\n"
                                         f"主動出逃佔比: `{data['sell_pct']:.1f}%`{extra_mml}")
                        
                        if alert_msg:
                            send_tg(alert_msg)
                            last_min_processed[symbol] = now_min
                
                # 幣種間稍微停頓，避免請求過快
                time.sleep(1)
            except Exception as e:
                log(f"{symbol} 循環錯誤: {e}")
        
        # 修正：掃描完一輪後休眠 5-10 秒
        wait_time = random.randint(5, 10)
        log(f"一輪掃描結束，休眠 {wait_time} 秒...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
