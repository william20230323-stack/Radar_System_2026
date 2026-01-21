    def __init__(self):
        self.token = RADAR_TOKEN
        self.chat_id = RADAR_CHAT_ID
        self.symbol = SYMBOL
        # --- 加入這兩行診斷 ---
        print(f"DEBUG: Token 長度 = {len(str(self.token)) if self.token else '抓不到'}")
        print(f"DEBUG: Chat ID = {self.chat_id if self.chat_id else '抓不到'}")
