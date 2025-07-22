# set_webhook.py
import telebot
import os

# 👉 ВСТАВЬ СЮДА СВОЙ ТОКЕН И URL
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = "https://shvei-photo-bot.onrender.com"

bot = telebot.TeleBot(TOKEN)

# Удалим старый webhook (на всякий случай)
bot.remove_webhook()

# Установим новый
success = bot.set_webhook(url=WEBHOOK_URL)

if success:
    print("✅ Webhook установлен")
else:
    print("❌ Ошибка установки Webhook")
