import websocket, json, time, requests, os
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class InfiniteRadar:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        # 設定巡航 280 秒，確保在 5 分鐘週期內優雅結束，好讓下一個任務接力
        self.end_time = time.time() + 280 
        self.cooldown = 0 
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
            is_dropping = curr_p < self.last_p
            ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
            
            # V1：偵測價格下跌中的隱性支撐
            if is_dropping and ratio > 2.0 and self.buy_vol >= self.WHALE_THRESHOLD and now > self.cooldown:
                buy_amount = f"{self.buy_vol / 1000:.1f}K"
                self.send_msg(
                    f"⚠️ *[武器庫 V1：隱性支撐]*\n"
                    f"📊 標的：`{SYMBOL}`\n"
                    f"❌ 警報：*偵測到價格正在下跌中*\n"
                    f"🔥 吃貨量：大量買單 `{buy_amount} USDT` 吃進\n"
                    f"⚖️ 瞬時買賣比：`{ratio:.2f}`"
                )
                self.cooldown = now + 40 
            
            self.last_p = curr_p
            self.buy_vol, self.sell_vol = 0.0, 0.0
            self.window_start = now

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    # 開機通知
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫 A-F：自動無限接力啟動*\n⏰ 時間：`[{now_str}]`\n📡 狀態：循環系統已鎖定，監控不間斷。",
        "parse_mode": "Markdown"
    })
    
    radar = InfiniteRadar()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
