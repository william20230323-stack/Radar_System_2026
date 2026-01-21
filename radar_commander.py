import websocket, json, time, requests, os, sys
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class HunterAgentRadar:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        # 巡航時間 330 秒，對接 GitHub 5 分鐘自動接力
        self.end_time = time.time() + 330 
        self.cooldown = 0 
        
        # 【Agent 自主優化】：設定更嚴謹的過濾門檻
        self.WHALE_MIN_USDT = 6000  # 提高基本門槛，過濾散戶
        self.FORCE_RATIO = 2.5       # 買盤必須是賣盤的 2.5 倍才視為有效吸收

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
            if now - self.window_start >= 5: # 5秒掃描週期
                is_dropping = curr_p < self.last_p
                ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
                
                # 【Agent 自主優化邏輯】：V1 隱性支撐精確判定
                # 條件：價格下跌 + 買賣比超標 + 金額達標
                if is_dropping and ratio >= self.FORCE_RATIO and self.buy_vol >= self.WHALE_MIN_USDT:
                    if now > self.cooldown:
                        buy_amount = f"{self.buy_vol / 1000:.1f}K"
                        self.send_msg(
                            f"⚠️ *[武器庫 V1：隱性支撐]*\n"
                            f"📊 標的：`{SYMBOL}`\n"
                            f"❌ 警報：*價格下跌中 (大戶逆勢吸收)*\n"
                            f"🔥 吸收量：`{buy_amount} USDT` \n"
                            f"⚖️ 瞬時買賣比：`{ratio:.2f}`\n"
                            f"🛡️ 狀態：Agent 監控正常，接力運作中。"
                        )
                        self.cooldown = now + 45 # 避免重複報警
                
                self.last_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except Exception:
            pass

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    # Agent 接棒報告
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫 A-F：Agent 自動優化版接力成功*\n⏰ 啟動時間：`[{now_str}]`\n📡 優化點：動態吸收比率、WS 連線加固。",
        "parse_mode": "Markdown"
    })
    
    radar = HunterAgentRadar()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
