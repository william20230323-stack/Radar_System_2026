import websocket, json, time, requests, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class UnifiedRadar:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        self.end_time = time.time() + 245
        self.cooldown = 0 
        # 大戶吃貨門檻：5秒內主動買入超過 5000 USDT 才報警 (確保非散戶行為)
        self.WHALE_THRESHOLD = 5000 

    def send_msg(self, text):
        url = f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage"
        try:
            requests.post(url, json={"chat_id": RADAR_CHAT_ID.strip(), "text": text, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def on_message(self, ws, message):
        if time.time() > self.end_time: 
            ws.close()
            return
        
        d = json.loads(message)
        curr_p = float(d['p'])
        v = curr_p * float(d['q'])
        
        if self.last_p == 0: self.last_p = curr_p

        if d['m']: self.sell_vol += v
        else: self.buy_vol += v

        now = time.time()
        if now - self.window_start >= 5:
            # 判定：現在價格相對於 5 秒前是否正在下跌
            is_dropping = curr_p < self.last_p
            ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
            
            # 【武器庫 V1】：價格跌 + 買賣比 > 2.0 + 買單量過門檻
            if is_dropping and ratio > 2.0 and self.buy_vol >= self.WHALE_THRESHOLD and now > self.cooldown:
                buy_amount = f"{self.buy_vol / 1000:.1f}K" if self.buy_vol >= 1000 else f"{self.buy_vol:.1f}"
                
                self.send_msg(
                    f"⚠️ *[武器庫 V1：即時隱性支撐]* \n"
                    f"📊 標的：`{SYMBOL}`\n"
                    f"❌ 警報：*偵測到價格正在不斷下跌*\n"
                    f"📉 當前價：`{curr_p}`\n"
                    f"🔥 吃貨量：偵測到大量買單 `{buy_amount} USDT` 逆勢吃進\n"
                    f"⚖️ 瞬時買賣比：`{ratio:.2f}`\n"
                    f"🛡️ 狀態：模組 F 實戰防禦中"
                )
                self.cooldown = now + 45 # 防止重複報警
            
            self.last_p = curr_p
            self.buy_vol, self.sell_vol = 0.0, 0.0
            self.window_start = now

if __name__ == "__main__":
    print(f"📡 武器庫 A-F：V1/V2 巡航啟動...")
    radar = UnifiedRadar()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
