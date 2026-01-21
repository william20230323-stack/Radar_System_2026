import websocket, json, time, requests, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class UnifiedRadar:
    def __init__(self):
        self.prices = []
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.end_time = time.time() + 250
        self.start_time = time.time()

    def send_msg(self, text):
        url = f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage"
        try:
            requests.post(url, json={"chat_id": RADAR_CHAT_ID.strip(), "text": text, "parse_mode": "Markdown"})
        except: pass

    def on_message(self, ws, message):
        if time.time() > self.end_time: ws.close(); return
        d = json.loads(message)
        p, v = float(d['p']), float(d['p']) * float(d['q'])
        if d['m']: self.sell_vol += v
        else: self.buy_vol += v

        if time.time() - self.start_time >= 60:
            ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
            print(f"📡 V1/V2 巡航中 - 成交比: {ratio:.2f}")
            self.buy_vol, self.sell_short = 0.0, 0.0
            self.start_time = time.time()

if __name__ == "__main__":
    print(f"📡 V1/V2 實時雷達啟動，目標：{SYMBOL}")
    radar = UnifiedRadar()
    ws = websocket.WebSocketApp(f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade", on_message=radar.on_message)
    ws.run_forever()
