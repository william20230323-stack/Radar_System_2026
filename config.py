import os
# 從 GitHub Secrets 讀取資料
RADAR_TOKEN = os.getenv("TG_TOKEN")
RADAR_CHAT_ID = os.getenv("TG_CHAT_ID")
SYMBOL = os.getenv("TRADE_SYMBOL")
