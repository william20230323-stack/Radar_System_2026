import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class WhaleMonitor:
    def __init__(self):
        self.token = RADAR_TOKEN
        self.chat_id = RADAR_CHAT_ID
        self.symbol = SYMBOL
        self.last_long_ratio = 0.0

    def get_top_trader_ratio(self):
        """抓取大戶持倉比 (Top Traders Long/Short Ratio)"""
        url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
        params = {"symbol": self.symbol, "period": "5m", "limit": 2}
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data and len(data) >= 1:
                return data[0] # 回傳最新的一筆數據
        except Exception as e:
            print(f"📡 聰明錢數據連線異常: {e}")
        return None

    def analyze(self):
        now = self.get_top_trader_ratio()
        if not now:
            return

        now_long = float(now['longAccount'])
        
        # 第一次執行先紀錄數據
        if self.last_long_ratio == 0.0:
            self.last_long_ratio = now_long
            print(f"✅ 初始數據載入：多頭佔比 {now_long:.2%}")
            return

        # 計算變動幅度
        diff = now_long - self.last_long_ratio
        print(f"🐳 實時掃描：目前多頭 {now_long:.2%} | 變動: {diff:+.4%}")

        # 核心判定：當多頭持倉佔比變動超過 0.05% (0.0005) 即發報 (測試期門檻調低)
        if abs(diff) >= 0.0005:
            trend = "📈 巨鯨正在加倉多單" if diff > 0 else "📉 巨鯨正在撤退/轉空"
            msg = (f"🐳 *【武器庫：聰明錢突變】*\n"
                   f"📊 標的：`{self.symbol}`\n"
                   f"核心數據：`{now_long:.2%}`\n"
                   f"變動幅度：`{diff:+.2%}`\n"
                   f"戰術判定：{trend}\n"
                   f"💡 警告：紅色框框數據異動，主力動作中！")
            self.send_telegram(msg)
            # 發報後更新基準值，避免重複報相同變動
            self.last_long_ratio = now_long

    def send_telegram(self, msg):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": self.chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except:
            pass

if __name__ == "__main__":
    monitor = WhaleMonitor()
    print(f"🚀 {SYMBOL} 聰明錢監控啟動 (循環模式)...")
    
    # 讓程式運行 240 秒 (4 分鐘)，每 30 秒抓取一次數據
    # 這能同時支撐背景的 V1, V2 雷達運行
    start_run = time.time()
    while time.time() - start_run < 240:
        monitor.analyze()
        time.sleep(30)
    
    print("🏁 本次監控任務結束。")
