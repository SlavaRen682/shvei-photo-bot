import telebot
from telebot import types
from flask import Flask, request
from io import BytesIO
import os

TOKEN = os.environ.get("TOKEN")  # Установи переменную TOKEN в Render
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Установи WEBHOOK_URL в Render
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

PHOTO_QUEUE = {}

# === Webhook route ===
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
    user_id = int(request.form['user_id'])
    username = request.form.get('username', '-')
    first_name = request.form.get('first_name', '-')
    phone = request.form.get('phone', '-')

    # 📌 Текст, который будет отображаться в группе (и у владельца)
    caption = (
        "✂️ НОВЫЙ ЗАКАЗ ✂️\n\n"
        "Если вы готовы взять пошив — ответьте на это сообщение со своей ценой и сроками.\n\n"
        "💬 Напишите цену пошива прямо здесь."
    )

    # ✅ Прочитать фото один раз
    raw_bytes = request.files['photo'].read()

    # ✅ Сделать копии файла
    owner_file = BytesIO(raw_bytes)
    group_file = BytesIO(raw_bytes)

    # 💾 Сохраняем в очередь для будущего отправления в группу
    PHOTO_QUEUE[user_id] = {'file': group_file, 'caption': caption}

    # 📥 Отправка владельцу с кнопками выбора категории
    markup = types.InlineKeyboardMarkup()
    for cat in CATEGORY_GROUPS:
        markup.add(types.InlineKeyboardButton(cat, callback_data=f"cat:{user_id}:{cat}"))

    bot.send_photo(OWNER_ID, owner_file, caption=caption, reply_markup=markup)

    return "ok", 200



@bot.message_handler(commands=['start'])
def bot_start(message):
    bot.send_message(message.chat.id, "👋 Отправьте фото изделия, чтобы выбрать категорию для размещения.")

@bot.message_handler(content_types=['photo'])
def handle_photo_from_user(message):
    user_id = message.chat.id
    file_id = message.photo[-1].file_id
    PHOTO_QUEUE[user_id] = {'file_id': file_id}

    markup = types.InlineKeyboardMarkup()
    for cat in CATEGORY_GROUPS:
        markup.add(types.InlineKeyboardButton(cat, callback_data=f"cat_user:{user_id}:{cat}"))

    bot.send_photo(user_id, file_id, caption="🧵 Выберите категорию пошива:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_user:"))
def handle_user_category(call):
    _, user_id_str, cat = call.data.split(":", 2)
    user_id = int(user_id_str)
    data = PHOTO_QUEUE.get(user_id)
    if not data:
        bot.answer_callback_query(call.id, "❌ Фото не найдено.")
        return

    file_id = data['file_id']
    group_id = CATEGORY_GROUPS.get(cat)

    try:
        bot.send_photo(group_id, file_id, caption="✂️ Новый заказ. Ответьте сообщением с ценой и сроками.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"✅ Фото успешно отправлено в категорию «{cat}».")
        del PHOTO_QUEUE[user_id]
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка отправки: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat:"))
def choose_category(call):
    _, user_id_str, cat = call.data.split(":", 2)
    user_id = int(user_id_str)
    data = PHOTO_QUEUE.get(user_id)
    if not data:
        bot.send_message(call.message.chat.id, "❌ Фото не найдено или уже отправлено.")
        return

    group_id = CATEGORY_GROUPS.get(cat)

    try:
        bot.send_photo(group_id, data['file'], caption=data['caption'])
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"✅ Фото успешно отправлено в категорию «{cat}».")
        del PHOTO_QUEUE[user_id]
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка отправки: {e}")

# === Webhook настройка ===
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
