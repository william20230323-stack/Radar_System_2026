import websocket, json, time, requests, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class UnifiedRadar:
    def __init__(self):
        # 追蹤短期視窗 (5秒)
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        self.end_time = time.time() + 245
        self.cooldown = 0  # 防止訊息轟炸

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

        # 區分主動買賣
        if d['m']: self.sell_vol += v
        else: self.buy_vol += v

        # 每 5 秒檢查一次瞬時狀態
        now = time.time()
        if now - self.window_start >= 5:
            # 判斷價格是否正在下跌
            is_dropping = curr_p < self.last_p
            ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
            
            # 【核心邏輯：現在正在跌 + 現在有大量買單 (買賣比 > 2.0)】
            # 加入 cooldown 確保 30 秒內不重複報警同一波
            if is_dropping and ratio > 2.0 and now > self.cooldown:
                buy_amount = f"{self.buy_vol / 1000:.1f}K" if self.buy_vol >= 1000 else f"{self.buy_vol:.1f}"
                
                self.send_msg(
                    f"⚠️ *[武器庫 V1：即時隱性支撐]* \n"
                    f"📊 標的：`{SYMBOL}`\n"
                    f"❌ 警報：*偵測到價格正在不斷下跌*\n"
                    f"📉 當前價：`{curr_p}` (低於前波 `{self.last_p}`)\n"
                    f"🔥 吃貨量：偵測到有大量買單 `{buy_amount} USDT` 吃進\n"
                    f"⚖️ 瞬時買賣比：`{ratio:.2f}` (買盤壓制賣盤)"
                )
                self.cooldown = now + 30 # 30秒冷卻
            
            # 更新基準點
            self.last_p = curr_p
            self.buy_vol, self.sell_vol = 0.0, 0.0
            self.window_start = now

if __name__ == "__main__":
    print(f"📡 武器庫模組 F：V1 即時流偵察點火，監控 {SYMBOL}...")
    radar = UnifiedRadar()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
