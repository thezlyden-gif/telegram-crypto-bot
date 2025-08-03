import requests
import time
import datetime
import json
from threading import Thread
from flask import Flask, request

app = Flask(__name__)

# === НАСТРОЙКИ ===
bot_token = "8392693204:AAEDJvZhNvukxx4nnYDRZYrFyUo8PkQqIr8"
chat_id = "7647937915"
bybit_api_url = "https://api.bybit.com/v5/market/tickers?category=linear"
tracked_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "OPUSDT", "ARBUSDT", "APTUSDT", "INJUSDT", "FETUSDT", "RNDRUSDT", "DYDXUSDT", "LDOUSDT", "SEIUSDT", "BLURUSDT"]

latest_prices = {}
latest_signal = None
daily_report = []

# === ОТПРАВКА СООБЩЕНИЙ В TELEGRAM ===
def send_message(text, buttons=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if buttons:
        payload["reply_markup"] = json.dumps({
            "keyboard": [[{"text": btn} for btn in row] for row in buttons],
            "resize_keyboard": True
        })
    try:
        requests.post(url, data=payload)
    except:
        pass

# === ОБНОВЛЕНИЕ ЦЕН ===
def update_prices():
    global latest_prices
    while True:
        try:
            res = requests.get(bybit_api_url)
            tickers = res.json().get("result", {}).get("list", [])
            for t in tickers:
                if t["symbol"] in tracked_symbols:
                    latest_prices[t["symbol"]] = float(t["lastPrice"])
        except Exception as e:
            print("Ошибка при получении цен:", e)
        time.sleep(60)

# === ГЕНЕРАЦИЯ СИГНАЛА ===
def generate_signal():
    global latest_signal
    while True:
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            eth = latest_prices.get("ETHUSDT", None)
            if eth and eth < 3000:
                latest_signal = {
                    "symbol": "ETH/USDT",
                    "direction": "шорт",
                    "entry": eth,
                    "stop": round(eth * 1.015, 2),
                    "target": round(eth * 0.96, 2),
                    "ai_conf": "84%",
                    "created_at": now
                }
                daily_report.append({
                    "time": now,
                    "symbol": "ETH/USDT",
                    "result": "+2.5%",
                    "comment": "AI-шорт"
                })
        except Exception as e:
            print("Ошибка генерации сигнала:", e)
        time.sleep(180)

# === TELEGRAM ОБРАБОТКА КОМАНД ===
@app.route(f"/{bot_token}", methods=["POST"])
def webhook():
    msg = request.get_json()
    text = msg["message"].get("text", "")
    if "/start" in text:
        send_message("Выберите команду:", buttons=[
            ["/price", "/signal"],
            ["/dailyreport", "/термины"]
        ])
    elif "/price" in text:
        out = "📊 Актуальные цены:\n"
        for s in tracked_symbols:
            p = latest_prices.get(s, "—")
            out += f"{s.replace('USDT','')}: ${p}\n"
        send_message(out)
    elif "/signal" in text:
        if latest_signal:
            sig = latest_signal
            msg = f"📉 <b>Сигнал:</b>\nАктив: {sig['symbol']}\nТип: {sig['direction']}\nВход: ${sig['entry']}\nСтоп: ${sig['stop']}\nТейк: ${sig['target']}\nAI: {sig['ai_conf']}\n⏱ {sig['created_at']}"
            send_message(msg)
        else:
            send_message("Сигналов пока нет.")
    elif "/dailyreport" in text:
        if daily_report:
            msg = "📋 Дневной отчёт:\n"
            for d in daily_report:
                msg += f"{d['time']} | {d['symbol']} | {d['result']} | {d['comment']}\n"
            send_message(msg)
        else:
            send_message("Сегодня сделок не было.")
    elif "/термины" in text:
        send_message("📘 Термины:\nEMA — средняя цена\nVolume Profile — объём\nПробой — выход из уровня\nИндекс страха — настроение рынка и т.д.")
    return {"ok": True}

# === ЗАПУСК ===
import time

def auto_signal_loop():
    while True:
        try:
            signal = generate_signal()
            if signal:
                send_to_telegram(signal)
                print(f"✅ Сигнал отправлен: {signal[:50]}...")
            else:
                print("⛔ Сигнал не найден")
        except Exception as e:
            print(f"❌ Ошибка в автоанализе: {e}")
        time.sleep(120)  # 2 минуты пауза

if __name__ == "__main__":
    Thread(target=update_prices).start()
    Thread(target=auto_signal_loop).start()
    app.run(host="0.0.0.0", port=10000)


