import websocket, json, time, requests, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class DivergenceRadar:
    def __init__(self):
        self.reset_metrics()
        # 設定 GitHub Actions 執行時間上限 (約 4.5 分鐘)
        self.end_time = time.time() + 260 

    def reset_metrics(self):
        self.start_time = time.time()
        self.open_price = 0.0
        self.buy_vol = 0.0     # 主動買入總金額 (USDT)
        self.sell_vol = 0.0    # 主動賣出總金額 (USDT)
        self.is_alerted = False

    def send_radar_msg(self, msg):
        """發送戰訊至 Telegram"""
        url = f"https://api.telegram.org/bot{RADAR_TOKEN}/sendMessage"
        payload = {
            "chat_id": RADAR_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=5)
            self.is_alerted = True
        except Exception as e:
            print(f"❌ 訊號發送失敗: {e}")

    def on_message(self, ws, message):
        if time.time() > self.end_time:
            ws.close()
            return

        data = json.loads(message)
        price = float(data['p'])
        amount = price * float(data['q'])

        # 紀錄分鐘開盤價
        if self.open_price == 0:
            self.open_price = price

        # 分類統計買賣單 (燃料比偵測)
        if data['m']: # 主動拋售
            self.sell_vol += amount
        else: # 主動掃貨
            self.buy_vol += amount

        elapsed = time.time() - self.start_time

        # 在每分鐘最後 5 秒 (收盤前) 進行邏輯判定
        if 55 <= elapsed < 60 and not self.is_alerted:
            price_change_pct = (price - self.open_price) / self.open_price * 100
            ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
            
            # 日誌輸出 (GitHub Actions 終端機可見)
            print(f"📡 掃描: 價格變動 {price_change_pct:.2f}% | 燃料比 {ratio:.2f}")

            # 情況 A：價格下跌，但出現大量買單吃進 (隱性支撐 - 模組 F)
            if price_change_pct < -0.15 and ratio > 1.7:
                msg = (f"⚠️ *【武器庫：隱性支撐預警】*\n"
                       f"📊 標的：`{SYMBOL}`\n"
                       f"📉 價格：下跌 `{price_change_pct:.2f}%`\n"
                       f"🔥 燃料比：`{ratio:.2f}` (買盤強勁)\n"
                       f"💡 價格下跌但主力強硬吃單，小心低位反轉！")
                self.send_radar_msg(msg)

            # 情況 B：價格上漲，但出現大量賣單拋出 (拉高出貨 - 模組 E)
            elif price_change_pct > 0.15 and ratio < 0.6:
                msg = (f"🚨 *【武器庫：拉高出貨預警】*\n"
                       f"📊 標的：`{SYMBOL}`\n"
                       f"📈 價格：上漲 `{price_change_pct:.2f}%`\n"
                       f"💸 燃料比：`{ratio:.2f}` (賣壓沉重)\n"
                       f"💡 價格拉升但大資金正在拋售，小心見頂回落！")
                self.send_radar_msg(msg)

        # 滿一分鐘後重置數據
        if elapsed >= 60:
            self.reset_metrics()

    def on_open(self, ws):
        print(f"🚀 {SYMBOL} 量價背離雷達上線，正在實時監控燃料比...")

# 執行連線
radar = DivergenceRadar()
ws = websocket.WebSocketApp(
    f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
    on_message=radar.on_message,
    on_open=radar.on_open
)
ws.run_forever()
