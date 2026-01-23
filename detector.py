import os
import time
import requests
import ccxt
import random
import sys  # 修正：加入 sys 模組以執行退出重啟

# 強制即時輸出日誌，確保在 GitHub Actions 介面能即時看到
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# 紀錄啟動時間 (新增：用於計算 5 小時後續命)
START_TIME = time.time()
MAX_RUN_TIME = 18000 # 5 小時 (18000秒)

# 讀取 Secrets 環境變數
TG_TOKEN = str(os.environ.get("TG_TOKEN", "")).strip()
TG_CHAT_ID = str(os.environ.get("TG_CHAT_ID", "")).strip()
SYMBOL = "DUSK/USDT"
VOL_THRESHOLD = 2.0 # 成交量翻倍門檻

def send_tg(msg):
    """呼叫 Telegram API 發送警報"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        # 修正：加入 10 秒超時，防止 TG 伺服器延遲卡死整個腳本
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        log(f"TG Status: {r.status_code}") # 看到 200 代表發送成功
    except Exception as e:
        log(f"TG 發送異常: {e}")

def get_market_data():
    """直連 Gate.io 端口獲取 K 線數據 (保留原本邏輯)"""
    # 初始化 Gate.io 接口 (CCXT)
    # 修正：加入 timeout 保護，防止接口請求卡住
    ex = ccxt.gateio({'enableRateLimit': True, 'timeout': 15000})
    try:
        # 獲取 1m K線，取最近 10 根
        ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe='1m', limit=10)
        if ohlcv and len(ohlcv) >= 6:
            curr = ohlcv[-1]   # 最新一根 K 線
            hist = ohlcv[-7:-1] # 前 6 根 K 線計算平均成交量
            
            o, c, v = float(curr[1]), float(curr[4]), float(curr[5])
            avg_v = sum(float(x[5]) for x in hist) / len(hist)
            
            log(f"Gate.io 更新 | 價格: {c} | 當前量: {v:.2f} | 均量: {avg_v:.2f}")
            return o, c, v, avg_v
    except Exception as e:
        log(f"Gate.io 端口連線異常: {str(e)[:50]}")
    return None

def main():
    log("=== Radar_System_2026 穩定重啟版啟動 ===")
    
    # 啟動時發送一次心跳訊息
    send_tg(f"🚀 **Radar 系統上線通知**\n優先數據源：`Gate.io` (直連)\n隨機頻率：`5-15s`\n狀態：`5小時自動續命防護中`")

    last_min_processed = ""
    
    while True:
        # --- 新增：安全退場機制 ---
        # 如果運行超過 5 小時，主動退出。GitHub Actions 會在下一個 cron 重啟它。
        if time.time() - START_TIME > MAX_RUN_TIME:
            log("[安全機制] 運行已達 5 小時，主動結束以觸發下一次重啟...")
            sys.exit(0)

        try:
            data = get_market_data()
            if data:
                o, c, v, avg_v = data
                now_min = time.strftime("%H:%M")
                
                # 偵測邏輯：成交量翻倍偵測 (保留原本邏輯)
                if now_min != last_min_processed and v > (avg_v * VOL_THRESHOLD):
                    if c < o: # 陰線
                        send_tg(f"⚠️ **Gate.io 異常大買**\n標的: `{SYMBOL}`\n型態: `陰線大買` (1M)\n成交量: `{v:.1f}` (均: `{avg_v:.1f}`)")
                    elif c > o: # 陽線
                        send_tg(f"🚨 **Gate.io 異常大賣**\n標的: `{SYMBOL}`\n型態: `陽線大賣` (1M)\n成交量: `{v:.1f}` (均: `{avg_v:.1f}`)")
                    last_min_processed = now_min
            else:
                log("暫無回傳數據，等待下一次隨機輪詢...")
        except Exception as e:
            log(f"主程序崩潰錯誤: {e}")
        
        # 實施 5秒 - 15秒的隨機延遲 (保留原本邏輯)
        wait_time = random.randint(5, 15)
        log(f"本次掃描結束，隨機休眠 {wait_time} 秒...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
