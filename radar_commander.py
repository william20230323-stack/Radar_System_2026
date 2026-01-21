import websocket, json, time, requests, os

# 🔱 頂層強制讀取（不准放在類別內）
# 確保這裡的變數名稱與 YAML 裡的 env: 名稱完全一致
TOKEN = os.getenv('RADAR_TOKEN')
CHAT_ID = os.getenv('RADAR_CHAT_ID')

class HunterAgentiPhone:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.open_p = 0.0
        self.ema_fast, self.ema_slow = 0.0, 0.0
        self.macd_hist = []
        self.cooldown = 0
        self.end_time = time.time() + 20000 

    def send_msg(self, text):
        # 🛡️ 雙重檢查
        if not TOKEN or not CHAT_ID:
            print(f"❌ 嚴重警告：代碼無法從環境讀取到鑰匙。目前變數狀態: TOKEN={TOKEN}, ID={CHAT_ID}")
            return
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            print(f"❌ 發送請求失敗: {e}")

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
                    # 🔱 模組 F：0 軸轉折 (門檻設為 2000 以確保容易觸發)
                    if h2 < 0 and h2 > h1 and curr_p < self.open_p and self.buy_vol >= 2000:
                        if now > self.cooldown:
                            self.send_msg(f"🛡️ *[模組 F：左側吸籌]*\n💰 價格：`{curr_p}`\n✅ 買盤已吸收")
                            self.cooldown = now + 40
                    elif h2 > 0 and h2 < h1 and curr_p > self.open_p and self.sell_vol >= 2000:
                        if now > self.cooldown:
                            self.send_msg(f"⚠️ *[模組 F：左側出逃]*\n💰 價格：`{curr_p}`\n🚨 賣盤已拋售")
                            self.cooldown = now + 40

                self.open_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except:
            pass

if __name__ == "__main__":
    print(f"🔥 系統初始化... TOKEN 檢查: {'OK' if TOKEN else 'FAIL'}")
    agent = HunterAgentiPhone()
    
    # 🔱 啟動即回報 (強制點火)
    agent.send_msg(f"✅ *[武器庫]*：通訊連通，巡航啟動。")
    
    ws = websocket.WebSocketApp(
        "wss://fstream.binance.com/ws/duskusdt@trade",
        on_message=agent.on_message
    )
    ws.run_forever()
