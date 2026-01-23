import os
import time
import requests
import ccxt

# 配置區
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL_CCXT = "DUSK/USDT"
VOL_MULTIPLIER = 2.0

def send_tg_msg(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def get_data_from_ccxt():
    """
    優先嘗試對 GitHub Actions IP 較友善的交易所
    1. Gate.io (最鬆) 2. Bybit 3. Bitget
    """
    # 初始化交易所列表
    exchange_list = [
        ccxt.gateio({'enableRateLimit': True}),
        ccxt.bybit({'enableRateLimit': True}),
        ccxt.bitget({'enableRateLimit': True})
    ]
    
    for ex in exchange_list:
        try:
            print(f"嘗試從 {ex.id} 獲取數據...")
            ohlcv = ex.fetch_ohlcv(SYMBOL_CCXT, timeframe='1m', limit=10)
            
            if ohlcv and len(ohlcv) >= 6:
                current = ohlcv[-1]   # 當前 K 線
                history = ohlcv[-7:-1] # 前 6 根 K 線 (取平均)
                
                o, c, v = float(current[1]), float(current[4]), float(current[5])
                avg_v = sum(float(x[5]) for x in history) / len(history)
                
                return ex.id, o, c, v, avg_v
            else:
                print(f"{ex.id} 返回數據長度不足")
        except Exception as e:
            print(f"{ex.id} 請求出錯: {str(e)[:50]}")
            continue
    return None

def main():
    # 啟動回報
    print("Radar Engine v2.0 Starting...")
    send_tg_msg(f"✅ **Radar_System_2026 已啟動**\n優先檢測：`CCXT (Gate/Bybit/Bitget)`\n監控標的：`{SYMBOL_CCXT}`")
    
    empty_data_count = 0
    
    while True:
        try:
            result = get_data_from_ccxt()
            
            if result:
                empty_data_count = 0 # 重置空數據計數
                source_name, o, c, v, avg_v = result
                
                # 核心偵測邏輯：陰線大買 / 陽線大賣
                if v > (avg_v * VOL_MULTIPLIER):
                    if c < o:
                        send_tg_msg(f"⚠️ **{source_name} 異常大買**\n幣種: `{SYMBOL_CCXT}`\n型態: `陰線` (1M)\n當前量: `{v:.1f}`\n均量: `{avg_v:.1f}`")
                    elif c > o:
                        send_tg_msg(f"🚨 **{source_name} 異常大賣**\n幣種: `{SYMBOL_CCXT}`\n型態: `陽線` (1M)\n當前量: `{v:.1f}`\n均量: `{avg_v:.1f}`")
            else:
                empty_data_count += 1
                # 如果連續 5 次拿不到數據 (約 2 分鐘)，發送警告
                if empty_data_count >= 5:
                    send_tg_msg(f"❓ **數據源警告**：所有交易所接口皆無返回數據，可能是 GitHub IP 被臨時屏蔽。")
                    empty_data_count = 0
                
        except Exception as e:
            print(f"Loop Error: {e}")
            
        time.sleep(25) # 稍微延長間隔避免觸發頻率限制

if __name__ == "__main__":
    main()
