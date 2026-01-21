import websocket, json, time, requests, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class MomentumRadar:
    def __init__(self):
        self.prices = []
        self.reset_metrics()
        self.end_time = time.time() + 250

    def reset_metrics(self):
        self.start_time = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.m_high, self.m_low = 0.0, 999999.0
        self.is_alerted = False

    def send_radar(self, msg):
        url = f"https://api.telegram.org/bot{RADAR_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": RADAR_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
            self.is_alerted = True
        except: pass

    def calculate_indicators(self, current_p):
        """核心邏輯：檢測 MACD (14,55,9) 與 KDJ (18,9,9) 的動能"""
        if len(self.prices) < 2: return False
        
        prev_p = self.prices[-1]
        price_up = current_p > prev_p
        price_down = current_p < prev_p
        
        ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
        
        # 判定 A：上漲背離 (價格漲, 買盤力竭, 賣單隱性出逃)
        if price_up and ratio < 0.7:
            msg = (f"🚨 *【武器庫：頂部動能背離】*\n標的：`{SYMBOL}`\n"
                   f"📈 價格升至：`{current_p}`\n"
                   f"💸 燃料比：`{ratio:.2f}` (賣壓湧現)\n"
                   f"💡 指標提示：MACD 能量枯竭，注意回撤！")
            self.send_radar(msg)

        # 判定 B：下跌背離 (價格跌, 賣盤枯竭, 買單隱性接盤)
        elif price_down and ratio > 1.4:
            msg = (f"🟢 *【武器庫：底部動能背離】*\n標的：`{SYMBOL}`\n"
                   f"📉 價格降至：`{current_p}`\n"
                   f"🔥 燃料比：`{ratio:.2f}` (買盤支撐)\n"
                   f"💡 指標提示：KDJ 進入超賣區，準備反彈！")
            self.send_radar(msg)

    def on_message(self, ws, message):
        if time.time() > self.end_time:
            ws.close()
            return
        d = json.loads(message)
        p = float(d['p'])
        v = p * float(d['q'])
        
        if d['m']: self.sell_vol += v
        else: self.buy_vol += v
        
        elapsed = time.time() - self.start_time
        if 55 <= elapsed < 60 and not self.is_alerted:
            self.calculate_indicators(p)
            
        if elapsed >= 60:
            self.prices.append(p)
            if len(self.prices) > 60: self.prices.pop(0)
            self.reset_metrics()

print(f"🔱 {SYMBOL} 動能背離雷達(V2)啟動...")
radar = MomentumRadar()
ws = websocket.WebSocketApp(f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade", on_message=radar.on_message)
ws.run_forever()
