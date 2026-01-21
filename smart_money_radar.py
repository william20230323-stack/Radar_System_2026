import requests, time, os
from config import RADAR_TOKEN, RADAR_CHAT_ID, SYMBOL

class WhaleMonitor:
    def __init__(self):
        # 從環境變數讀取配置
        self.token = RADAR_TOKEN
        self.chat_id = RADAR_CHAT_ID
        self.symbol = SYMBOL

    def get_top_trader_ratio(self):
        """抓取大戶持倉比 (Top Traders Long/Short Ratio)"""
        # 使用幣安期貨公開數據接口
        url = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
        params = {"symbol": self.symbol, "period": "5m", "limit": 2}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data and len(data) >= 2:
                # data[0] 是最新的一筆，data[1] 是前一筆
                now = data[0]
                prev = data[1]
                return now, prev
        except Exception as e:
            print(f"📡 聰明錢數據抓取異常: {e}")
        return None, None

    def analyze(self):
        now, prev = self.get_top_trader_ratio()
        if not now or not prev:
            return

        now_long = float(now['longAccount'])
        prev_long = float(prev['longAccount'])
        now_short = float(now['shortAccount'])
        
        # 核心判定：當多頭持倉佔比突然變動超過 1% (0.01)
        diff = now_long - prev_long
        
        print(f"🐳 巨鯨動態：多頭 {now_long:.2%} | 變動: {diff:+.2%}")

        if abs(diff) >= 0.01:
            trend = "📈 巨鯨集體加碼多單" if diff > 0 else "📉 巨鯨集體撤退/反手做空"
            msg = (f"🐳 *【武器庫：聰明錢突變】*\n"
                   f"標的：`{self.symbol}`\n"
                   f"核心數據：`{now_long:.2%}`\n"
                   f"變動幅度：`{diff:+.2%}`\n"
                   f"戰術判定：{trend}\n"
                   f"💡 警語：紅色框框數據出現異動，主力正在換手！")
            self.send_telegram(msg)

    def send_telegram(self, msg):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        requests.post(url, json={"chat_id": self.chat_id, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    monitor = WhaleMonitor()
    monitor.analyze()
