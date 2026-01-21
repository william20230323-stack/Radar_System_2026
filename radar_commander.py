import websocket, json, time, requests, os

# 🔱 這是妳最初最穩定、百分之百能動的抓取結構（絕對不再改動）
TG_TOKEN = os.environ.get('RADAR_TOKEN')
TG_ID = os.environ.get('RADAR_CHAT_ID')

def send_msg(text):
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
                    
                    # 🔱 僅新增：模組 F 核心邏輯 (0 軸轉折判定)
                    if h2 < 0 and h2 > h1 and curr_p < self.open_p and self.buy_vol >= 4000:
                        if now > self.cooldown:
                            send_msg(f"🛡️ *[模組 F：左側吸籌]*\n💰 價格：`{curr_p}`\n📉 狀態：0 軸下能量轉正轉折\n✅ 吸收：`{self.buy_vol/1000:.1f}K`")
                            self.cooldown = now + 40
                            
                    elif h2 > 0 and h2 < h1 and curr_p > self.open_p and self.sell_vol >= 4000:
                        if now > self.cooldown:
                            send_msg(f"⚠️ *[模組 F：左側出逃]*\n💰 價格：`{curr_p}`\n📈 狀態：0 軸上能量衰竭轉折\n🚨 拋售：`{self.sell_vol/1000:.1f}K`")
                            self.cooldown = now + 40

                self.open_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except:
            pass

if __name__ == "__main__":
    # 🔱 啟動即報警（這行也是妳最初能動的證明）
    send_msg("✅ *[武器庫]*：穩定結構已恢復，模組 F 巡航中。")
    
    agent = HunterAgent()
    ws = websocket.WebSocketApp(
        "wss://fstream.binance.com/ws/duskusdt@trade",
        on_message=agent.on_message
    )
    ws.run_forever()
