import websocket, json, time, requests, os, sys
from datetime import datetime
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class HunterAgentRadarV2:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol = 0.0
        self.sell_vol = 0.0
        self.last_p = 0.0
        # 巡航時間 330 秒，保證 5 分鐘自動接力不中斷
        self.end_time = time.time() + 330 
        self.cooldown_v1 = 0 
        self.cooldown_v2 = 0 
        
        # 【Agent 自主優化參數】
        self.WHALE_MIN_V1 = 4500  # V1 隱性支撐門檻調降，增加靈敏度
        self.WHALE_MIN_V2 = 3000  # V2 掃貨門檻 (階梯式)
        self.V2_RATIO = 3.0       # V2 需要更強的買單壓倒性優勢

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
            # 【Agent 優化】：縮短掃描窗口至 3 秒，捕捉極速掃貨
            if now - self.window_start >= 3:
                is_dropping = curr_p < self.last_p
                is_rising = curr_p > self.last_p
                ratio = self.buy_vol / self.sell_vol if self.sell_vol > 0 else 1.0
                
                # --- 武器庫 V1：隱性支撐 (跌勢吸籌) ---
                if is_dropping and ratio >= 2.2 and self.buy_vol >= self.WHALE_MIN_V1:
                    if now > self.cooldown_v1:
                        self.send_msg(
                            f"⚠️ *[武器庫 V1：隱性支撐]*\n"
                            f"📊 標的：`{SYMBOL}`\n"
                            f"❌ 狀態：價格下跌中，但有大戶逆勢吃貨\n"
                            f"🔥 吸收量：`{self.buy_vol / 1000:.1f}K USDT` \n"
                            f"⚖️ 買賣比：`{ratio:.2f}`"
                        )
                        self.cooldown_v1 = now + 40

                # --- 武器庫 V2：動態掃貨 (起漲訊號) ---
                # 優化：偵測價格微升或平盤，但買盤呈現 3 倍以上壓倒性攻擊
                elif ratio >= self.V2_RATIO and self.buy_vol >= self.WHALE_MIN_V2:
                    if now > self.cooldown_v2:
                        self.send_msg(
                            f"🚀 *[武器庫 V2：強勢掃貨]*\n"
                            f"📊 標的：`{SYMBOL}`\n"
                            f"🔥 訊號：偵測到連續主動買盤掃貨\n"
                            f"💰 掃貨量：`{self.buy_vol / 1000:.1f}K USDT` \n"
                            f"⚖️ 攻擊力：`{ratio:.2f}`"
                        )
                        self.cooldown_v2 = now + 30
                
                self.last_p = curr_p
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.window_start = now
        except Exception:
            pass

if __name__ == "__main__":
    now_str = datetime.now().strftime("%H:%M:%S")
    # Agent 優化版報告
    requests.post(f"https://api.telegram.org/bot{RADAR_TOKEN.strip()}/sendMessage", json={
        "chat_id": RADAR_CHAT_ID.strip(), 
        "text": f"🔱 *武器庫：V2 雷達優化版啟動*\n⏰ 時間：`[{now_str}]`\n📡 優化點：3s 高頻掃描、V1/V2 雙軌門檻、增加起漲偵測。",
        "parse_mode": "Markdown"
    })
    
    radar = HunterAgentRadarV2()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=radar.on_message
    )
    ws.run_forever()
