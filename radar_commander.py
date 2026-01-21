import websocket, json, time, requests, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class LiveRadar:
    def __init__(self):
        self.end_time = time.time() + 250 # 運行 4 分鐘
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_price = 0.0

    def send_tg(self, msg):
        url = f"https://api.telegram.org/bot{RADAR_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": RADAR_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

    def on_message(self, ws, message):
        if time.time() > self.end_time: ws.close(); return
        
        data = json.loads(message)
        price = float(data['p'])
        amount = price * float(data['q'])

        if data['m']: self.sell_vol += amount  # 主動拋售
        else: self.buy_vol += amount           # 主動掃貨

        # 每 60 秒計算一次背離
        if int(time.time()) % 60 == 0:
            ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
            if ratio > 1.8:
                self.send_tg(f"⚠️ *【量價預警】*\n標的：`{SYMBOL}`\n🔥 買盤強勁 (Ratio: {ratio:.2f})\n價格下跌但有人大量吃貨！")
            elif ratio < 0.6:
                self.send_tg(f"🚨 *【賣壓預警】*\n標的：`{SYMBOL}`\n💸 賣盤沉重 (Ratio: {ratio:.2f})\n上漲無力，主力正在撤退！")
            self.buy_vol, self.sell_vol = 0.0, 0.0 # 重置

    def on_open(self, ws):
        print(f"📡 {SYMBOL} 量價實時雷達已啟動...")

radar = LiveRadar()
ws = websocket.WebSocketApp(f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade", on_message=radar.on_message, on_open=radar.on_open)
ws.run_forever()
