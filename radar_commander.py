import websocket, json, time, requests, os
from datetime import datetime

# 🔱 核心配置：一次性完善版
SYMBOL = "DUSKUSDT"
TG_TOKEN = os.getenv('RADAR_TOKEN')
TG_ID = os.getenv('RADAR_CHAT_ID')

class HunterAgentiPhone:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.last_p, self.open_p = 0.0, 0.0
        self.ema_fast, self.ema_slow = 0.0, 0.0
        self.macd_hist = []
        # 巡航時間校準，避免 GitHub Action 報錯
        self.end_time = time.time() + 285 
        self.cooldown = 0

    def calculate_macd(self, price):
        if self.ema_fast == 0:
            self.ema_fast = self.ema_slow = price
            return 0.0
        self.ema_fast = (price * (2/15)) + (self.ema_fast * (13/15))
        self.ema_slow = (price * (2/56)) + (self.ema_slow * (54/56))
        return self.ema_fast - self.ema_slow

    def send_msg(self, text):
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": TG_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
        except: pass

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
                    
                    # 🔱 0 軸轉折判定：紅空轉實(左側吸籌)、綠實轉空(左側出逃)
                    # 判定 A：0 軸下實轉空 + 陰線 (價格跌) -> 左側吸籌 (模組 F)
                    if h2 < 0 and h2 > h1 and curr_p < self.open_p and self.buy_vol >= 4000:
                        if now > self.cooldown:
                            self.send_msg(f"🛡️ *[模組 F：左側吸籌]*\n💰 價格：`{curr_p}`\n📉 狀態：陰線 + 0 軸下實轉空\n✅ 吸收：`{self.buy_vol/1000:.1f}K USDT`")
                            self.cooldown = now + 40
                            
                    # 判定 B：0 軸上空轉實 + 陽線 (價格漲) -> 左側出逃 (模組 F)
                    elif h2 > 0 and h2 < h1 and curr_p > self.open_p and self.sell_vol >= 4000:
                        if now > self.cooldown:
                            self.send_msg(f"⚠️ *[模組 F：左側出逃]*\n💰 價格：`{curr_p}`\n📈 狀態：陽線 + 0 軸上空轉實\n🚨 拋售：`{self.sell_vol/1000:.1f}K USDT`")
                            self.cooldown = now + 40
                            
                self.open_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except: pass

if __name__ == "__main__":
    radar = HunterAgentiPhone()
    ws = websocket.WebSocketApp(f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade", on_message=radar.on_message)
    ws.run_forever()
