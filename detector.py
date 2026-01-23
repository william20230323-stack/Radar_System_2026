import os
import time
import requests
import pandas as pd
import ccxt
from alpha_vantage.cryptocurrencies import CryptoCurrencies

# 密鑰配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
AV_KEY = os.getenv("AV_API_KEY")
SYMBOL_BASE = "DUSK"
SYMBOL_PAIR = "DUSK/USDT"
VOL_MULTIPLIER = 2.0

def send_tg_msg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

# --- 數據源: CCXT (支援數百家交易所，預設使用 Binance) ---
def get_ccxt_data():
    try:
        # 使用不需 API Key 的公開接口
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        # 獲取 1 分鐘 K 線 (最近 6 根)
        ohlcv = exchange.fetch_ohlcv(SYMBOL_PAIR, timeframe='1m', limit=6)
        # ohlcv 格式: [timestamp, open, high, low, close, volume]
        curr = ohlcv[-1]
        hist = ohlcv[:-1]
        v = float(curr[5])
        avg_v = sum(float(x[5]) for x in hist) / 5
        return ("CCXT_Binance", float(curr[1]), float(curr[4]), v, avg_v)
    except Exception as e:
        print(f"CCXT Error: {e}")
        return None

# --- 數據源: Alpha Vantage ---
def get_alpha_vantage():
    if not AV_KEY: return None
    try:
        cc = CryptoCurrencies(key=AV_KEY)
        data, _ = cc.get_digital_currency_daily(symbol=SYMBOL_BASE, market='USD')
        latest_date = list(data.keys())[0]
        latest = data[latest_date]
        return ("AlphaVantage", float(latest['1a. open (USD)']), float(latest['4a. close (USD)']), float(latest['5. volume']), 0)
    except: return None

# --- 數據源: AKShare ---
def get_akshare():
    try:
        import akshare as ak
        df = ak.crypto_js_spot()
        row = df[df['symbol'] == SYMBOL_BASE]
        if not row.empty:
            return ("AKShare", float(row['open'].values[0]), float(row['last'].values[0]), float(row['vol'].values[0]), 0)
    except: return None

def main():
    # 啟動通知
    send_tg_msg(f"🚀 **Radar_全數據引擎啟動**\n整合接口: `CCXT`, `AlphaVantage`, `AKShare`, `Binance.US`\n監控標的: `{SYMBOL_PAIR}`")
    
    last_min = ""
    while True:
        # 優先級順序: CCXT -> AKShare -> AlphaVantage
        sources = [get_ccxt_data, get_akshare, get_alpha_vantage]
        
        for get_func in sources:
            res = get_func()
            if res:
                name, o, c, v, avg_v = res
                now_min = time.strftime("%M")
                
                if now_min != last_min:
                    # 核心偵測邏輯：成交量翻倍 + 陰買/陽賣
                    if avg_v > 0 and v > (avg_v * VOL_MULTIPLIER):
                        if c < o:
                            send_tg_msg(f"⚠️ **{name} 偵測警報**\n型態: `陰線大買` (1M)\n當前量: `{v:.1f}`\n均量: `{avg_v:.1f}`")
                        elif c > o:
                            send_tg_msg(f"🚨 **{name} 偵測警報**\n型態: `陽線大賣` (1M)\n當前量: `{v:.1f}`\n均量: `{avg_v:.1f}`")
                    last_min = now_min
                    break # 成功獲取任一源則跳過，防止重複警報
        
        time.sleep(20)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 崩潰診斷發送
        send_tg_msg(f"❌ **系統崩潰臨界報錯**\n原因: `{str(e)}`")
