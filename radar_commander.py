import websocket, json, time, requests, os
from datetime import datetime

# 🔱 核心配置：由 Agent V3.0 優化
SYMBOL = "DUSKUSDT"

class HunterAgentiPhone:
    def __init__(self):
        # 🛡️ 從 GitHub 保險箱讀取鑰匙 (請確保保險箱名稱完全一致)
        self.token = os.getenv('RADAR_TOKEN')
        self.chat_id = os.getenv('RADAR_CHAT_ID')
        
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.open_p = 0.0
        self.ema_fast, self.ema_slow = 0.0, 0.0
        self.macd_hist = []
        self.cooldown = 0
        # 巡航 5.5 小時後自動更換任務
        self.end_time = time.time() + 20000 

    def send_msg(self, text):
        """發送戰報，若鑰匙讀取失敗會列印提示"""
        if not self.token or not self.chat_id:
            print("❌ 警告：GitHub 保險箱鑰匙讀取失敗，請檢查 Secrets 名稱！")
            return
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}, timeout=5)
        except:
            pass

    def calculate_macd(self, price):
        if self.ema_fast == 0:
            self.ema_fast = self.ema_slow = price
            return 0.0
        self.ema_fast = (price * (2/13)) + (self.ema_fast * (11/13))
        self.ema_slow = (price * (2/27)) + (self.ema_slow * (25/27))
        return self.ema_fast - self.ema_slow

    def on_message(self, ws, message):
        if time.time() > self.end_time: ws.close(); return
        try:
            d = json.loads(message)
            curr_p = float(d['p'])
            if self.open_p == 0: self.open_p = curr_p
            v = curr_p * float(d['q'])
            if d['m']: self.sell_vol += v
            else: self.buy_vol += v
            
            now = time.time()
            if now - self.window_start >= 5:
                hist = self.calculate_macd(curr_p)
                self.macd_hist.append(hist)
                if len(self.macd_hist) > 3: self.macd_hist.pop(0)
                
                if len(self.macd_hist) >= 2:
                    h1, h2 = self.macd_hist[-2], self.macd_hist[-1]
                    
                    # 🔱 模組 F：左側吸籌 (0 軸下實轉空 + 陰線)
                    if h2 < 0 and h2 > h1 and curr_p < self.open_p and self.buy_vol >= 4000:
                        if now > self.cooldown:
                            self.send_msg(f"🛡️ *[模組 F：左側吸籌]*\n💰 價格：`{curr_p}`\n📉 狀態：陰線 + 0 軸下實轉空\n✅ 吸收：`{self.buy_vol/1000:.1f}K USDT`")
                            self.cooldown = now + 40
                            
                    # 🔱 模組 F：左側出逃 (0 軸上空轉實 + 陽線)
                    elif h2 > 0 and h2 < h1 and curr_p > self.open_p and self.sell_vol >= 4000:
                        if now > self.cooldown:
                            self.send_msg(f"⚠️ *[模組 F：左側出逃]*\n💰 價格：`{curr_p}`\n📈 狀態：陽線 + 0 軸上空轉實\n🚨 拋售：`{self.sell_vol/1000:.1f}K USDT`")
                            self.cooldown = now + 40

                self.open_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except:
            pass

if __name__ == "__main__":
    agent = HunterAgentiPhone()
    # 點火確認
    agent.send_msg(f"🚀 *[武器庫點火]*：iPhone 指揮端已連線，正在巡航 {SYMBOL}")
    
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=agent.on_message
    )
    ws.run_forever()
