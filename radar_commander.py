import websocket, json, time, requests, os

# 🔱 這裡改回最原始的寫法，保證抓得到
TG_TOKEN = os.environ.get('RADAR_TOKEN')
TG_ID = os.environ.get('RADAR_CHAT_ID')

def send_msg(text):
    if not TG_TOKEN or not TG_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

class HunterAgent:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.open_p = 0.0
        self.ema_fast, self.ema_slow = 0.0, 0.0
        self.macd_hist = []
        self.cooldown = 0

    def calculate_macd(self, price):
        if self.ema_fast == 0:
            self.ema_fast = self.ema_slow = price
            return 0.0
        self.ema_fast = (price * (2/13)) + (self.ema_fast * (11/13))
        self.ema_slow = (price * (2/27)) + (self.ema_slow * (25/27))
        return self.ema_fast - self.ema_slow

    def on_message(self, ws, message):
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
                    
                    # 🔱 模組 F：左側轉折 (只保留您要的功能，不動結構)
                    if h2 < 0 and h2 > h1 and curr_p < self.open_p and self.buy_vol >= 4000:
                        if now > self.cooldown:
                            send_msg(f"🛡️ *[模組 F：左側吸籌]*\n💰 價格：`{curr_p}`")
                            self.cooldown = now + 40
                    elif h2 > 0 and h2 < h1 and curr_p > self.open_p and self.sell_vol >= 4000:
                        if now > self.cooldown:
                            send_msg(f"⚠️ *[模組 F：左側出逃]*\n💰 價格：`{curr_p}`")
                            self.cooldown = now + 40
                
                self.open_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except:
            pass

if __name__ == "__main__":
    # 這裡會立刻發送訊息，確認運轉正常
    send_msg("✅ *[武器庫]*：系統已恢復正常運轉。")
    agent = HunterAgent()
    ws = websocket.WebSocketApp(
        "wss://fstream.binance.com/ws/duskusdt@trade",
        on_message=agent.on_message
    )
    ws.run_forever()
