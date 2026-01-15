from flask import Flask
from threading import Thread
import requests
import time

app = Flask('')

@app.route('/')
def home():
    return "Music Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Пинг самого себя для поддержания активности
def ping_self():
    while True:
        try:
            requests.get("https://your-bot-name.replit.app/")
        except:
            pass
        time.sleep(300)  # Пинг каждые 5 минут

keep_alive()
Thread(target=ping_self).start()
