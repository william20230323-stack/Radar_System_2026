import websocket, json, time, requests, os

# 🔱 抓取對應的環境變數
TOKEN = os.environ.get('FINAL_TOKEN')
ID = os.environ.get('FINAL_ID')

def send_msg(text):
    if not TOKEN or not ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

class HunterAgent:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.cooldown = 0

    def on_message(self, ws, message):
        try:
            d = json.loads(message)
            v = float(d['p']) * float(d['q'])
            if d['m']: self.sell_vol += v
            else: self.buy_vol += v
            
            now = time.time()
            if now - self.window_start >= 5:
                # 🔱 穩定大單偵測邏輯
                if self.buy_vol >= 5000:
                    if now > self.cooldown:
                        send_msg(f"✅ *[大單吸籌]*：`{self.buy_vol/1000:.1f}K` USDT")
                        self.cooldown = now + 40
                elif self.sell_vol >= 5000:
                    if now > self.cooldown:
                        send_msg(f"🚨 *[大單拋售]*：`{self.sell_vol/1000:.1f}K` USDT")
                        self.cooldown = now + 40
                
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except:
            pass

if __name__ == "__main__":
    # 點火測試
    send_msg("✅ *[武器庫]*：保險箱對接成功，監控啟動。")
    
    agent = HunterAgent()
    ws = websocket.WebSocketApp(
        "wss://fstream.binance.com/ws/duskusdt@trade",
        on_message=agent.on_message
    )
    ws.run_forever()
