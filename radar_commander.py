import websocket, json, time, requests, os
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class HunterAgentRadarV2:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        # 巡航 320 秒，覆蓋 5 分鐘週期
        self.end_time = time.time() + 320 
        self.cooldown_v1 = 0 
        self.cooldown_v2 = 0 
        
        self.WHALE_MIN_V1 = 4500  
        self.WHALE_MIN_V2 = 3000  
        self.V2_RATIO = 3.0       

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
            curr_p = float(d['p'])
            v = curr_p * float(d['q'])
            
            if self.last_p == 0: self.last_p = curr_p
            if d['m']: self.sell_vol += v
            else: self.buy_vol += v

            now = time.time()
            if now - self.window_start >= 3:
                is_dropping = curr_p < self.last_p
                ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
                
                # V1: 隱性支撐
                if is_dropping and ratio >= 2.2 and self.buy_vol >= self.WHALE_MIN_V1:
                    if now > self.cooldown_v1:
                        self.send_msg(f"⚠️ *[武器庫 V1：隱性支撐]*\n📊 標的：`{SYMBOL}`\n🔥 吸收量：`{self.buy_vol / 1000:.1f}K USDT` \n⚖️ 買賣比：`{ratio:.2f}`")
                        self.cooldown_v1 = now + 40

                # V2: 動態掃貨
                elif ratio >= self.V2_RATIO and self.buy_vol >= self.WHALE_MIN_V2:
                    if now > self.cooldown_v2:
                        self.send_msg(f"🚀 *[武器庫 V2：強勢掃貨]*\n📊 標的：`{SYMBOL}`\n💰 掃貨量：`{self.buy_vol / 1000:.1f}K USDT` \n⚖️ 攻擊力：`{ratio:.2f}`")
                        self.cooldown_v2 = now + 30
                
                self.last_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except: pass

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫：接力成功*\n⏰ 時間：`[{now_str}]`\n📡 狀態：Agent V2 加固版巡航中。",
        "parse_mode": "Markdown"
    })
    
    radar = HunterAgentRadarV2()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
