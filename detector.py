import os
import sys
import time
import requests

# 嘗試加載環境變數
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSKUSDT")

def send_tg_msg(msg):
    """通訊診斷：如果發不出去會直接印出原因"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram Log: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_data_binance():
    """備援方案 1: Binance.US (最穩定)"""
    url = f"https://api.binance.us/api/v3/klines?symbol={SYMBOL}&interval=1m&limit=6"
    try:
        r = requests.get(url, timeout=10).json()
        curr, hist = r[-1], r[-6:-1]
        return float(curr[1]), float(curr[4]), float(curr[5]), sum(float(x[5]) for x in hist)/5
    except: return None

def get_data_akshare():
    """主要方案: AKShare (如果出錯會返回 None)"""
    try:
        import akshare as ak
        # 這裡改用更穩定的 crypto_js_spot 獲取實時數據
        df = ak.crypto_js_spot()
        row = df[df['symbol'] == SYMBOL.replace('USDT', '')]
        # 由於 AKShare 部分接口不提供 1m K線歷史，我們優先保證連通
        return None # 暫時回傳 None 觸發備援測試
    except: return None

def main():
    # 啟動時第一秒強制發送，如果 7 秒內沒收到這封，代表代碼報錯
    print("System Starting...")
    send_tg_msg(f"🛰️ **Radar_System_2026**\n系統啟動中...\n檢測標的: `{SYMBOL}`")

    last_min = ""
    while True:
        # 優先從 Binance.US 獲取數據 (GitHub IP 支持度最高)
        result = get_data_binance()
        
        if result:
            o, c, v, avg_v = result
            now_min = time.strftime("%M")
            
            if now_min != last_min:
                print(f"Scanning {SYMBOL}: Price {c}, Vol {v}")
                if v > (avg_v * 2.0):
                    if c < o:
                        send_tg_msg(f"⚠️ **異常大買**\n幣種: `{SYMBOL}`\n型態: `陰線` (1M)\n量: `{v:.1f}`")
                    elif c > o:
                        send_tg_msg(f"🚨 **異常大賣**\n幣種: `{SYMBOL}`\n型態: `陽線` (1M)\n量: `{v:.1f}`")
                last_min = now_min
        else:
            print("Warning: All data sources failed. Retrying...")
            
        time.sleep(20)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 捕捉所有崩潰原因並發送至 TG，防止默默停止
        send_tg_msg(f"❌ **系統崩潰報告**\n原因: `{str(e)}`")
        print(f"CRITICAL ERROR: {e}")
