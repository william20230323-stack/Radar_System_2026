import websocket, json, time, requests, os
from datetime import datetime

# 🔱 核心配置
SYMBOL = "DUSKUSDT"

class HunterAgentiPhone:
    def __init__(self):
        self.token = os.getenv('RADAR_TOKEN')
        self.chat_id = os.getenv('RADAR_CHAT_ID')
        
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.open_p = 0.0
        self.ema_fast, self.ema_slow = 0.0, 0.0
        self.macd_hist = []
        self.cooldown = 0
        self.end_time = time.time() + 20000 

    def send_msg(self, text):
        if not self.token or not self.chat_id:
            print("❌ 鑰匙讀取失敗")
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
        # 🔱 稍微調靈敏一點：12, 26 -> 9, 21
        self.ema_fast = (price * (2/10)) + (self.ema_fast * (8/10))
        self.ema_slow = (price * (2/22)) + (self.ema_slow * (20/22))
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
                    
                    # 🔱 偵測邏輯（模組 F）
                    # 下降轉折 + 買盤大於 2000 (稍微降低門檻測試)
                    if h2 < 0 and h2 > h1 and curr_p < self.open_p and self.buy_vol >= 2000:
                        if now > self.cooldown:
                            self.send_msg(f"🛡️ *[模組 F：左側吸籌]*\n💰 價格：`{curr_p}`\n✅ 買盤：`{self.buy_vol/1000:.1f}K` (偵測中)")
                            self.cooldown = now + 40
                            
                    # 上升轉折 + 賣盤大於 2000
                    elif h2 > 0 and h2 < h1 and curr_p > self.open_p and self.sell_vol >= 2000:
                        if now > self.cooldown:
                            self.send_msg(f"⚠️ *[模組 F：左側出逃]*\n💰 價格：`{curr_p}`\n🚨 賣盤：`{self.sell_vol/1000:.1f}K` (偵測中)")
                            self.cooldown = now + 40

                self.open_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except:
            pass

if __name__ == "__main__":
    agent = HunterAgentiPhone()
    # 🔱 關鍵！這行確保妳一儲存，Bot 就會響，證明代碼與 Secrets 沒問題
    agent.send_msg(f"✅ *[巡航啟動]*：武器庫 F 已接入 {SYMBOL}\n正在執行 0 軸能量過濾...")
    
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=agent.on_message
    )
    ws.run_forever()
