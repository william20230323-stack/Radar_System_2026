import websocket, json, time, requests, os
from datetime import datetime

# 🔱 核心通訊基因
TOKEN = os.environ.get('TG_TOKEN')
ID = os.environ.get('TG_CHAT_ID')
SYMBOL = "DUSKUSDT"

def send_msg(text):
    if not TOKEN or not ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

class HunterAgent:
    def __init__(self):
        self.window_start = time.time()
        self.buy_vol, self.sell_vol = 0.0, 0.0
        self.prices = []
        self.ema_12, self.ema_26 = 0.0, 0.0
        self.cooldown = 0

    def get_macd(self, price):
        if self.ema_12 == 0:
            self.ema_12 = self.ema_26 = price
            return 0.0
        self.ema_12 = price * (2/13) + self.ema_12 * (11/13)
        self.ema_26 = price * (2/27) + self.ema_26 * (25/27)
        return self.ema_12 - self.ema_26

    def on_message(self, ws, message):
        try:
            d = json.loads(message)
            curr_p = float(d['p'])
            v_usdt = curr_p * float(d['q'])
            
            if d['m']: self.sell_vol += v_usdt
            else: self.buy_vol += v_usdt
            
            self.prices.append(curr_p)
            if len(self.prices) > 100: self.prices.pop(0)

            now = time.time()
            if now - self.window_start >= 5:
                macd = self.get_macd(curr_p)
                open_p = self.prices[0]
                ratio = round(self.buy_vol / self.sell_vol, 1) if self.sell_vol > 0 else 1.0
                
                # 🔱 18:00 正常運轉之【左側極致版】判斷邏輯
                # 判斷：0軸下實心轉空心 (吸籌)
                if macd < 0 and curr_p < open_p and self.buy_vol >= 4000:
                    if now > self.cooldown:
                        msg = (
                            f"🛡️ *[武器庫 V1：底部分歧吸籌]*\n"
                            f"📊 標的：`{SYMBOL}`\n"
                            f"｜價格：`{curr_p}`\n"
                            f"📉 能量：*0 軸下實心轉空心 (減弱)*\n"
                            f"🔥 行為：價格跌勢中主力強勢吃貨\n"
                            f"✅ 吃貨量：`{self.buy_vol/1000:.1f}K` USDT (比率 {ratio})"
                        )
                        send_msg(msg)
                        self.cooldown = now + 40

                self.window_start = now
                self.buy_vol, self.sell_vol = 0.0, 0.0
                self.prices = [curr_p]
        except:
            pass

if __name__ == "__main__":
    t_str = datetime.now().strftime('%H:%M:%S')
    send_msg(f"🔱 *武器庫：Agent 左側極致版點火*\n⏰ 時間：`[{t_str}]`\n📡 優化：陰陽線判定、0 軸能量轉折、左側攻擊鎖定。")
    
    agent = HunterAgent()
    ws = websocket.WebSocketApp(
        f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade",
        on_message=agent.on_message
    )
    ws.run_forever()
