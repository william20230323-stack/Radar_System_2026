import os
import requests

def send_startup():
    token = str(os.environ.get('TG_TOKEN', '')).strip()
    chat_id = str(os.environ.get('TG_CHAT_ID', '')).strip()
    symbol = str(os.environ.get('TRADE_SYMBOL', '')).strip()

    if not token or not chat_id:
        print("❌ 錯誤：無法讀取 Secrets 鑰匙")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = f"🛡️ <b>Radar_System 總指揮已啟動</b>\n監控標的：{symbol}\n狀態：指揮鏈路正常"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ 啟動訊息已發送至 Telegram")
        else:
            print(f"❌ 發送失敗，錯誤碼：{r.status_code}, 內容：{r.text}")
    except Exception as e:
        print(f"❌ 網路異常：{e}")

if __name__ == "__main__":
    send_startup()
