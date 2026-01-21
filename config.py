import os

# 1. 對接 GitHub Secrets 裡的機器人 Token
RADAR_TOKEN = os.getenv("TG_TOKEN")

# 2. 對接 GitHub Secrets 裡的聊天室 ID
RADAR_CHAT_ID = os.getenv("TG_CHAT_ID")

# 3. 預設監控幣種 (如果 Secret 沒設定則用 DUSK)
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSKUSDT")

# 啟動診斷印出
if not RADAR_TOKEN:
    print("❌ 錯誤：找不到 TG_TOKEN，請檢查 GitHub Secrets 設定")
else:
    print(f"✅ 已成功讀取 Token，準備發送訊號至: {RADAR_CHAT_ID}")
