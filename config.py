import os
# 對接 GitHub 上的 TG_TOKEN
RADAR_TOKEN = os.getenv("TG_TOKEN")
# 對接 GitHub 上的 TG_CHAT_ID
RADAR_CHAT_ID = os.getenv("TG_CHAT_ID")
# 對接標的名稱
SYMBOL = os.getenv("TRADE_SYMBOL", "DUSKUSDT")
