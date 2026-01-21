import websocket, json, time, requests, os, sys
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class HunterRelayRadar:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        # 巡航 330 秒，覆蓋 5 分鐘的自動週期
        self.end_time = time.time() + 330 
        self.cooldown = 0 
        self.WHALE_THRESHOLD = 5000 

    def send_msg(self, text):
        url = f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage"
        try:
            requests.post(url, json={"chat_id": RADAR_CHAT_ID.strip(), "text": text, "parse_mode": "Markdown"}, timeout=5)
        except: pass

    def on_message(self, ws, message):
        # 正常時間到點關閉
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
            if now - self.window_start >= 5:
                # 核心監控邏輯：價格正在下跌 且 買盤強勢
                is_dropping = curr_p < self.last_p
                ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
                
                if is_dropping and ratio > 2.0 and self.buy_vol >= self.WHALE_THRESHOLD and now > self.cooldown:
                    buy_amount = f"{self.buy_vol / 1000:.1f}K"
                    self.send_msg(
                        f"⚠️ *[武器庫 V1：隱性支撐]*\n"
                        f"📊 標的：`{SYMBOL}`\n"
                        f"❌ 警報：*偵測到價格正在下跌中*\n"
                        f"🔥 吃貨量：偵測到大量買單 `{buy_amount} USDT` 吃進\n"
                        f"⚖️ 瞬時買賣比：`{ratio:.2f}`"
                    )
                    self.cooldown = now + 40 
                
                self.last_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except Exception:
            pass

    def on_error(self, ws, error):
        pass

    def on_close(self, ws, close_status_code, close_msg):
        pass

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    # 啟動報告
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫 A-F：接力巡航中*\n⏰ 啟動時間：`[{now_str}]`\n📡 狀態：循環系統運作正常，全面監控中。",
        "parse_mode": "Markdown"
    })
    
    radar = HunterRelayRadar()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message,
        on_error=radar.on_error,
        on_close=radar.on_close
    )
    ws.run_forever()
