import telebot
from telebot import types
from flask import Flask, request
from io import BytesIO
import os

TOKEN = os.environ.get("TOKEN")  # Обязательно установить в Render
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

CATEGORY_GROUPS = {
    "👚 Блузки и рубашки": "-1002606758634",
    "👖 Брюки": "-1002878121543",
    "🧥 Верхняя одежда": "-1002708682492",
    "🧶 Джемперы и кардиганы": "-1002879108725",
    "👖 Джинсы": "-1002836744118",
    "🧵 Комбинезоны": "-1002656275181",
    "🩲 Полукомбинезоны": "-1002150521388",
    "🧳 Костюмы": "-1002608986444",
    "🎩 Пиджаки и жакеты": "-1002742850789",
    "🎽 Лонгсливы": "-1002755396225",
    "👘 Туники": "-1002678676027",
    "🧥 Худи и свитшоты": "-1002771480706",
    "🧥 Халаты": "-1002854636960",
    "🩳 Шорты": "-1002835220487",
    "👗 Юбки": "-1002625493646",
    "👙 Белье": "-1002819820386",
    "🎭 Карнавальные костюмы": "-1002408380902",
    "👕 Футболки и топы": "-1002674261873",
    "👗 Платья и сарафаны": "-1002897926896"
}

PHOTO_QUEUE = {}

@app.route('/photo', methods=['POST'])
def receive_photo():
    user_id = int(request.form['user_id'])
    caption = (
        f"📩 Новый заказ от @{request.form['username']} "
        f"({request.form['first_name']})\n📞 {request.form['phone']}"
    )
    img = BytesIO(request.files['photo'].read())
    PHOTO_QUEUE[user_id] = {'file': img, 'caption': caption}

    markup = types.InlineKeyboardMarkup()
    for cat in CATEGORY_GROUPS:
        markup.add(types.InlineKeyboardButton(cat, callback_data=f"cat:{user_id}:{cat}"))

    bot.send_photo(user_id, img, caption=caption, reply_markup=markup)
    return "ok", 200

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat:"))
def choose_category(call):
    _, user_id_str, cat = call.data.split(":", 2)
    user_id = int(user_id_str)
    data = PHOTO_QUEUE.get(user_id)
    if not data:
        bot.send_message(call.message.chat.id, "❌ Фото не найдено или уже отправлено.")
        return
    group_id = CATEGORY_GROUPS.get(cat)
    bot.send_photo(group_id, data['file'], caption=data['caption'])
    bot.send_message(call.message.chat.id, f"✅ Фото отправлено в «{cat}».")
    del PHOTO_QUEUE[user_id]

@bot.message_handler(commands=['start'])
def bot_start(message):
    bot.send_message(message.chat.id, "Бот запущен и ждёт команды от первого бота.")

if __name__ == '__main__':
    from threading import Thread
    Thread(target=bot.polling, kwargs={'none_stop': True}).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
