import telebot
from telebot import types
from flask import Flask, request
import os
import uuid

TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
OWNER_ID = int(os.environ.get("OWNER_ID"))

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

CATEGORY_SHORT_IDS = {str(i): name for i, name in enumerate(CATEGORY_GROUPS)}

PHOTO_QUEUE = {}

def save_temp_file(raw_bytes):
    filename = f"temp_{uuid.uuid4()}.jpg"
    with open(filename, 'wb') as f:
        f.write(raw_bytes)
    return filename

def remove_temp_file(filename):
    try:
        os.remove(filename)
    except Exception:
        pass

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

@app.route("/", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "ok", 200
    return "unsupported", 403

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "👋 Привет! Отправь фото изделия, и выбери категорию для размещения.")

@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    user_id = message.chat.id
    file_id = message.photo[-1].file_id
    PHOTO_QUEUE[user_id] = {"file_id": file_id}

    markup = types.InlineKeyboardMarkup()
    for cat_name, group_id in CATEGORY_GROUPS.items():
        markup.add(types.InlineKeyboardButton(cat_name, callback_data=f"choose_cat:{user_id}:{group_id}"))

    bot.send_photo(user_id, file_id, caption="🧵 Выберите категорию пошива:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_cat:"))
def category_selected(call):
    try:
        _, user_id_str, group_id = call.data.split(":")
        user_id = int(user_id_str)
        data = PHOTO_QUEUE.get(user_id)
        if not data:
            bot.answer_callback_query(call.id, "❌ Фото не найдено.")
            return
        file_id = data['file_id']

        caption = (
            "✂️ НОВЫЙ ЗАКАЗ ✂️\n\n"
            "Если вы готовы взять пошив — ответьте на это сообщение со своей ценой и сроками.\n\n"
            "💬 Напишите цену пошива прямо здесь."
        )
        bot.send_photo(group_id, file_id, caption=caption)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Фото успешно отправлено в выбранную категорию.")
        del PHOTO_QUEUE[user_id]

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {e}")

if __name__ == "__main__":
    bot.remove_webhook()
    if bot.set_webhook(url=WEBHOOK_URL):
        print("Webhook установлен успешно")
    else:
        print("Ошибка установки webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
