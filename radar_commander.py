import websocket, json, time, requests, os, sys
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class HunterAgentUltimateRadar:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.last_p, self.current_p = 0.0, 0.0
        self.open_p = 0.0 # 用於判定陰陽線
        self.end_time = time.time() + 330 
        self.cooldown = 0
        
        # MACD 參數 (14, 55, 9)
        self.fast, self.slow = 14, 55
        self.ema_fast = 0.0
        self.ema_slow = 0.0
        self.macd_hist = [] 

    def calculate_macd(self, price):
        if self.ema_fast == 0:
            self.ema_fast = self.ema_slow = price
            return 0.0
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
            if self.open_p == 0: self.open_p = self.current_p # 紀錄窗口開盤價
            
            v = self.current_p * float(d['q'])
            if d['m']: self.sell_vol += v
            else: self.buy_vol += v

            now = time.time()
            if now - self.window_start >= 5: # 5秒偵測窗口
                hist = self.calculate_macd(self.current_p)
                self.macd_hist.append(hist)
                if len(self.macd_hist) > 3: self.macd_hist.pop(0)
                
                # 判定陰陽線狀態
                is_yin = self.current_p < self.open_p  # 陰線 (價格下跌)
                is_yang = self.current_p > self.open_p # 陽線 (價格上漲)
                
                if len(self.macd_hist) >= 2:
                    h1, h2 = self.macd_hist[-2], self.macd_hist[-1]
                    ratio_buy = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
                    ratio_sell = self.sell_vol / self.buy_vol if self.buy_vol > 0 else 1.0
                    
                    # 🔱 判定 A：0 軸下 [實心轉空心] + 陰線狀態 + 強勢買入 (左側吸籌)
                    if h2 < 0 and h2 > h1 and is_yin and ratio_buy >= 2.5 and self.buy_vol >= 4500:
                        if now > self.cooldown:
                            self.send_msg(
                                f"🛡️ *[武器庫 F：左側吸籌預判]*\n"
                                f"📊 標的：`{SYMBOL}` | 價格：`{self.current_p}`\n"
                                f"📉 形態：*陰線狀態* + *0 軸下實轉空*\n"
                                f"🔥 描述：價格下跌中，大戶正強勢左側吃貨\n"
                                f"✅ 吃貨量：`{self.buy_vol / 1000:.1f}K USDT` (強度 {ratio_buy:.1f})"
                            )
                            self.cooldown = now + 40

                    # 🔱 判定 B：0 軸上 [空心轉實心] + 陽線狀態 + 主力出逃 (左側出逃)
                    elif h2 > 0 and h2 < h1 and is_yang and ratio_sell >= 2.5 and self.sell_vol >= 4500:
                        if now > self.cooldown:
                            self.send_msg(
                                f"⚠️ *[武器庫 F：左側出逃預判]*\n"
                                f"📊 標的：`{SYMBOL}` | 價格：`{self.current_p}`\n"
                                f"📈 形態：*陽線狀態* + *0 軸上空轉實*\n"
                                f"🚨 描述：價格上升中，主力正在左側高位拋售\n"
                                f"❌ 拋售量：`{self.sell_vol / 1000:.1f}K USDT` (強度 {ratio_sell:.1f})"
                            )
                            self.cooldown = now + 40
                
                # 重置窗口數據
                self.open_p = self.current_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except Exception: pass

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫：Agent 左側極致版點火*\n⏰ 時間：`[{now_str}]` \n📡 優化：陰陽線判定、0 軸能量轉折、左側攻擊鎖定。",
        "parse_mode": "Markdown"
    })
    radar = HunterAgentUltimateRadar()
    ws = websocket.WebSocketApp(f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade", on_message=radar.on_message)
    ws.run_forever()
