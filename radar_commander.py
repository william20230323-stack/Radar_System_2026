import websocket, json, time, requests, os, sys
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class HunterAgentRadarV2:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        self.current_p = 0.0
        # 巡航時間 330 秒，保證 5 分鐘自動接力
        self.end_time = time.time() + 330 
        self.cooldown_v1 = 0 
        self.cooldown_v2 = 0 
        
        # 【Agent 自主優化參數】
        self.THRESHOLD_USDT = 4000  # 偵測門檻
        self.SUPER_RATIO = 2.5      # 強勢比率門檻

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
            
            if self.last_p == 0: self.last_p = self.current_p
            if d['m']: self.sell_vol += v
            else: self.buy_vol += v

            now = time.time()
            if now - self.window_start >= 3: # 3秒極速掃描
                price_diff = self.current_p - self.last_p
                ratio_buy = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 100.0
                ratio_sell = self.sell_vol / self.buy_vol if self.buy_vol > 0 else 100.0
                
                # --- 邏輯 A：下跌中強勢買入 (V1 強化版) ---
                if price_diff < 0 and ratio_buy >= self.SUPER_RATIO and self.buy_vol >= self.THRESHOLD_USDT:
                    if now > self.cooldown_v1:
                        self.send_msg(
                            f"🛑 *[武器庫 V1：下跌強勢吸籌]*\n"
                            f"📊 標的：`{SYMBOL}`\n"
                            f"💰 觸發價格：`{self.current_p}`\n"
                            f"🔥 狀態：*價格下跌中，大戶正強力吃貨*\n"
                            f"✅ 買入量：`{self.buy_vol / 1000:.1f}K USDT` \n"
                            f"⚖️ 買盤強度：`{ratio_buy:.2f} 倍`"
                        )
                        self.cooldown_v1 = now + 35

                # --- 邏輯 B：上漲中快速出逃 (V2 強化版) ---
                elif price_diff > 0 and ratio_sell >= self.SUPER_RATIO and self.sell_vol >= self.THRESHOLD_USDT:
                    if now > self.cooldown_v2:
                        self.send_msg(
                            f"⚠️ *[武器庫 V2：上漲高位出逃]*\n"
                            f"📊 標的：`{SYMBOL}`\n"
                            f"💰 觸發價格：`{self.current_p}`\n"
                            f"🚨 狀態：*價格上漲中，主力正在反向出貨*\n"
                            f"❌ 拋售量：`{self.sell_vol / 1000:.1f}K USDT` \n"
                            f"⚖️ 拋售強度：`{ratio_sell:.2f} 倍`"
                        )
                        self.cooldown_v2 = now + 35

                # --- 邏輯 C：強勢掃貨 (起漲攻擊) ---
                elif price_diff >= 0 and ratio_buy >= 4.0 and self.buy_vol >= self.THRESHOLD_USDT:
                    if now > self.cooldown_v2:
                        self.send_msg(
                            f"🚀 *[武器庫 V2：多頭發起攻擊]*\n"
                            f"📊 標的：`{SYMBOL}`\n"
                            f"💰 觸發價格：`{self.current_p}`\n"
                            f"🔥 狀態：*買盤暴力掃貨，準備突破*\n"
                            f"✅ 掃貨量：`{self.buy_vol / 1000:.1f}K USDT` \n"
                            f"⚖️ 攻擊力：`{ratio_buy:.2f} 倍`"
                        )
                        self.cooldown_v2 = now + 30
                
                self.last_p = self.current_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except Exception:
            pass

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫：Agent V2.5 直觀版點火*\n⏰ 時間：`[{now_str}]`\n📡 優化：加入價格標註、自動判斷吸籌/出逃狀態。",
        "parse_mode": "Markdown"
    })
    
    radar = HunterAgentRadarV2()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
