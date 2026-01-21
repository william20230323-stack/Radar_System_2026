import websocket, json, time, requests, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class UnifiedRadar:
    def __init__(self):
        self.prices = []
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.end_time = time.time() + 245  # 巡航約 4 分鐘
        self.start_time = time.time()
        self.last_p = 0.0

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
        p = float(d['p'])
        # 計算成交額 (USDT)
        v = p * float(d['q'])
        
        # 紀錄多空量
        if d['m']: self.sell_vol += v  # 主動拋售
        else: self.buy_vol += v        # 主動掃貨

        # --- 每 60 秒進行一次「背離與量價」掃描 ---
        elapsed = time.time() - self.start_time
        if elapsed >= 60:
            ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
            
            # 獲取價格變化 (與上一分鐘對比)
            if self.last_p == 0: self.last_p = p
            price_change = ((p - self.last_p) / self.last_p) * 100
            
            # 【測試模式：大幅調低門檻】
            # 原本可能要 1.8 倍才報警，現在只要買賣比超過 1.2 就報，確保妳能收到訊息
            if ratio > 1.2:
                self.send_msg(f"📡 *[武器庫 V1：多頭佔優]* \n標的：`{SYMBOL}`\n🔥 買賣比：`{ratio:.2f}`\n📈 價格變動：`{price_change:.2%}`")
            elif ratio < 0.8:
                self.send_msg(f"📡 *[武器庫 V1：空頭佔優]* \n標的：`{SYMBOL}`\n❄️ 買賣比：`{ratio:.2f}`\n📉 價格變動：`{price_change:.2%}`")
            
            # 重置計時器與數據
            print(f"📡 巡航結算：價格 {p}, 買賣比 {ratio:.2f}")
            self.last_p = p
            self.buy_vol, self.sell_vol = 0.0, 0.0
            self.start_time = time.time()

if __name__ == "__main__":
    print(f"📡 武器庫模組 A-F：V1/V2 雷達已掛載實時流，鎖定 {SYMBOL}")
    radar = UnifiedRadar()
    # 建立幣安實時成交數據連線
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
