import websocket, json, time, requests, os, sys
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class HunterAgentMACDFinal:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.last_p, self.current_p = 0.0, 0.0
        self.end_time = time.time() + 330 
        self.cooldown = 0
        
        # MACD 參數 (14, 55, 9)
        self.fast, self.slow, self.signal = 14, 55, 9
        self.ema_fast = 0.0
        self.ema_slow = 0.0
        self.macd_hist = [] 

    def calculate_macd(self, price):
        if self.ema_fast == 0:
            self.ema_fast = self.ema_slow = price
            return 0.0
        # EMA 計算
        self.ema_fast = (price * (2 / (self.fast + 1))) + (self.ema_fast * (1 - (2 / (self.fast + 1))))
        self.ema_slow = (price * (2 / (self.slow + 1))) + (self.ema_slow * (1 - (2 / (self.slow + 1))))
        return self.ema_fast - self.ema_slow

    def send_msg(self, text):
        url = f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage"
        try:
            requests.post(url, json={"chat_id": RADAR_CHAT_ID.strip(), "text": text, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def on_message(self, ws, message):
        if time.time() > self.end_time: 
            ws.close()
            return
        
        try:
            d = json.loads(message)
            self.current_p = float(d['p'])
            v = self.current_p * float(d['q'])
            if d['m']: self.sell_vol += v
            else: self.buy_vol += v

            now = time.time()
            if now - self.window_start >= 5: # 5秒計算窗口
                hist = self.calculate_macd(self.current_p)
                self.macd_hist.append(hist)
                if len(self.macd_hist) > 3: self.macd_hist.pop(0)
                
                if len(self.macd_hist) >= 2:
                    h1, h2 = self.macd_hist[-2], self.macd_hist[-1]
                    ratio_buy = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
                    ratio_sell = self.sell_vol / self.buy_vol if self.buy_vol > 0 else 1.0
                    
                    # 🔱 核心判定 A：0 軸下 [實心轉空心] (空頭減弱) + 大戶吸籌
                    if h2 < 0 and h2 > h1 and ratio_buy >= 2.2 and self.buy_vol >= 4000:
                        if now > self.cooldown:
                            self.send_msg(
                                f"🛡️ *[武器庫 V1：底部分歧吸籌]*\n"
                                f"📊 標的：`{SYMBOL}` | 價格：`{self.current_p}`\n"
                                f"📉 能量：*0 軸下實心轉空心* (減弱)\n"
                                f"🔥 行為：價格跌勢中主力強勢吃貨\n"
                                f"✅ 吃貨量：`{self.buy_vol / 1000:.1f}K USDT` (比率 {ratio_buy:.1f})"
                            )
                            self.cooldown = now + 40

                    # 🔱 核心判定 B：0 軸上 [空心轉實心] (多頭減弱) + 主力出逃
                    elif h2 > 0 and h2 < h1 and self.current_p > self.last_p and ratio_sell >= 2.2 and self.sell_vol >= 4000:
                        if now > self.cooldown:
                            self.send_msg(
                                f"⚠️ *[武器庫 V2：高位動能背離]*\n"
                                f"📊 標的：`{SYMBOL}` | 價格：`{self.current_p}`\n"
                                f"📈 能量：*0 軸上空心轉實心* (減弱)\n"
                                f"🚨 行為：價格升高中主力快速出逃\n"
                                f"❌ 拋售量：`{self.sell_vol / 1000:.1f}K USDT` (比率 {ratio_sell:.1f})"
                            )
                            self.cooldown = now + 40
                
                self.last_p = self.current_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except Exception: pass

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫：0 軸能量校準版點火*\n⏰ 時間：`[{now_str}]` \n📡 判定：0 軸上空轉實(減弱)、0 軸下實轉空(減弱)。",
        "parse_mode": "Markdown"
    })
    radar = HunterAgentMACDFinal()
    ws = websocket.WebSocketApp(f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade", on_message=radar.on_message)
    ws.run_forever()
