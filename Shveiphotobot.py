import telebot
from telebot import types
from flask import Flask, request
from io import BytesIO
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
    temp_filename = f"temp_photo_{uuid.uuid4()}.jpg"
    with open(temp_filename, 'wb') as f:
        f.write(raw_bytes)
    return temp_filename

def remove_temp_file(filename):
    try:
        os.remove(filename)
    except Exception:
        pass

@app.route("/", methods=["GET"])
def index():
    return "ShveiBot is alive!", 200

@app.route("/", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "ok", 200
    return "unsupported", 403

@app.route('/photo', methods=['POST'])
def receive_photo():
    try:
        user_id = int(request.form['user_id'])
        raw_bytes = request.files['photo'].read()
        caption = (
            "✂️ НОВЫЙ ЗАКАЗ ✂️\n\n"
            "Если вы готовы взять пошив — ответьте на это сообщение со своей ценой и сроками.\n\n"
            "💬 Напишите цену пошива прямо здесь."
        )
        photo_id = str(uuid.uuid4())
        photo_data = {"id": photo_id, "raw": raw_bytes, "caption": caption}

        if user_id not in PHOTO_QUEUE:
            PHOTO_QUEUE[user_id] = []
        PHOTO_QUEUE[user_id].append(photo_data)

        markup = types.InlineKeyboardMarkup()
        for cat_id, cat_name in CATEGORY_SHORT_IDS.items():
            markup.add(types.InlineKeyboardButton(cat_name, callback_data=f"cat:{user_id}:{photo_id}:{cat_id}"))

        temp_filename = save_temp_file(raw_bytes)
        with open(temp_filename, 'rb') as photo_file:
            bot.send_photo(OWNER_ID, photo_file, caption=caption, reply_markup=markup)
        remove_temp_file(temp_filename)

        return "ok", 200
    except Exception as e:
        return f"Error: {e}", 400

@bot.message_handler(commands=['start'])
def bot_start(message):
    bot.send_message(message.chat.id, "👋 Отправьте фото изделия, чтобы выбрать категорию для размещения.")

@bot.message_handler(content_types=['photo'])
def handle_photo_from_user(message):
    user_id = message.chat.id
    file_id = message.photo[-1].file_id
    PHOTO_QUEUE[user_id] = {'file_id': file_id}

    markup = types.InlineKeyboardMarkup()
    for cat_name, group_id in CATEGORY_GROUPS.items():
        markup.add(types.InlineKeyboardButton(cat_name, callback_data=f"cat_user:{user_id}:{group_id}"))

    bot.send_photo(user_id, file_id, caption="🧵 Выберите категорию пошива:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_user:"))
def handle_user_category(call):
    _, user_id_str, group_id = call.data.split(":")
    user_id = int(user_id_str)
    data = PHOTO_QUEUE.get(user_id)
    if not data:
        bot.answer_callback_query(call.id, "❌ Фото не найдено.")
        return

    file_id = data['file_id']
    try:
        bot.send_photo(group_id, file_id,
                       caption="✂️ НОВЫЙ ЗАКАЗ ✂️\n\n"
                               "Если вы готовы взять пошив — ответьте на это сообщение со своей ценой и сроками.\n\n"
                               "💬 Напишите цену пошива прямо здесь.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"✅ Фото успешно отправлено.")
        del PHOTO_QUEUE[user_id]
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка отправки: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat:"))
def choose_category(call):
    try:
        _, user_id_str, photo_id, cat_id = call.data.split(":")
        user_id = int(user_id_str)
        cat_name = CATEGORY_SHORT_IDS.get(cat_id)
        if not cat_name:
            bot.send_message(call.message.chat.id, "❌ Категория не найдена.")
            return

        photos = PHOTO_QUEUE.get(user_id)
        if not photos:
            bot.send_message(call.message.chat.id, "❌ Фото не найдено.")
            return

        photo_entry = next((p for p in photos if p['id'] == photo_id), None)
        if not photo_entry:
            bot.send_message(call.message.chat.id, "❌ Фото не найдено.")
            return

        group_id = CATEGORY_GROUPS.get(cat_name)

        temp_file = save_temp_file(photo_entry['raw'])
        with open(temp_file, 'rb') as photo_file:
            bot.send_photo(group_id, photo_file, caption=photo_entry['caption'])
        remove_temp_file(temp_file)

        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"✅ Фото успешно отправлено в категорию «{cat_name}».")

        photos.remove(photo_entry)
        if not photos:
            del PHOTO_QUEUE[user_id]

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {e}")

if __name__ == '__main__':
    bot.remove_webhook()
    result = bot.set_webhook(url=WEBHOOK_URL)
    if result:
        print("Webhook установлен успешно")
    else:
        print("Ошибка установки webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
