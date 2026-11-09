import telebot 
from telebot import types
import os
import time
import threading
from dotenv import load_dotenv

from database import (
    register_db,
    our_masters,
    check_id,
    my_booking,
    comments_author,
    yslygi,
    get_services,
    get_barbers,
    create_booking,
    add_service,
    add_barber,
    get_all_bookings,
    cancel_booking,
    add_review,
    get_clients_with_bookings,
    get_client_bookings,
    update_telegram_username,
    get_pending_bookings,
    confirm_booking,
    cleanup_old_bookings
)

from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

ADMIN_ID = int(os.getenv("ADMIN_ID"))

@bot.message_handler(commands = ['start'])
def start(m):
    update_telegram_username(m.from_user.id, m.from_user.username)
    keyboard = types.InlineKeyboardMarkup(row_width = 2)

    a1 = types.InlineKeyboardButton("📅 Записаться",callback_data = "a1")
    a2 = types.InlineKeyboardButton("📋 Мои записи",callback_data = "a2")
    a3 = types.InlineKeyboardButton("✂️ Услуги и цены",callback_data = "a3")
    a4 = types.InlineKeyboardButton("💈 Наши мастера",callback_data = "a4")
    a5 = types.InlineKeyboardButton("📍 Адрес и контакты",callback_data = "a5")
    a6 = types.InlineKeyboardButton("⭐ Отзывы",callback_data = "a6")
    a7 = types.InlineKeyboardButton("  Зарегистрироваться  ",callback_data = "a7")
    a8 = types.InlineKeyboardButton(
    "📩 Написать администратору",
    callback_data="contact_admin"
)

    keyboard.add(a1,a2,a3,a4,a5,a6,a7,a8)

    if m.from_user.id == ADMIN_ID:
        admin_button = types.InlineKeyboardButton(
        "⚙️ Админ-панель",
        callback_data="admin_panel"
        )
        keyboard.add(admin_button)

    bot.send_message(m.chat.id,'Добро пожаловать в Barbershop!',reply_markup = keyboard)

# ==============================
# СВЯЗЬ С АДМИНИСТРАТОРОМ
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "contact_admin")
def contact_admin(call):
    bot.answer_callback_query(call.id)

    user = call.from_user

    if user.id == ADMIN_ID:
        bot.send_message(
            call.message.chat.id,
            "Вы являетесь администратором."
        )
        return

    full_name = " ".join(filter(None, [
        user.first_name,
        user.last_name
    ])) or "Не указано"

    username = f"@{user.username}" if user.username else "Не указан"

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "💬 Связаться с клиентом",
            url=f"tg://user?id={user.id}"
        )
    )

    try:
        bot.send_message(
            ADMIN_ID,
            f"📩 <b>КЛИЕНТ ХОЧЕТ СВЯЗАТЬСЯ С ВАМИ!</b>\n\n"
            f"👤 Имя: {escape(full_name)}\n"
            f"🔗 Username: {escape(username)}\n"
            f"🆔 Telegram ID: <code>{user.id}</code>\n\n"
            f"Клиент нажал кнопку связи с администратором.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        bot.send_message(
            call.message.chat.id,
            "✅ Ваш запрос отправлен администратору!\n"
            "Ожидайте, с вами свяжутся."
        )

    except Exception as e:
        print("Ошибка отправки запроса администратору:", e)

        bot.send_message(
            call.message.chat.id,
            "❌ Не удалось отправить запрос. Попробуйте позже."
        )

# a7 button 
@bot.callback_query_handler(func = lambda call: call.data == "a7")
def a1(call):
    bot.answer_callback_query(call.id)

    tg_id = call.from_user.id
    rg_username = call.from_user.username

    a = check_id(tg_id)

    if a == True:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        yes = types.InlineKeyboardButton("yes",callback_data='y')
        no = types.InlineKeyboardButton("no",callback_data = 'n')
        keyboard.add(yes,no)
        bot.send_message(call.message.chat.id,"Вы уже зарегистрированы!\nХотите обновить свои данные?",reply_markup = keyboard)

    elif a==None:
        print("error with db !?")
    else:
        msg = bot.send_message(call.message.chat.id,'Введите ваше полное имя: ')
        bot.register_next_step_handler(msg,get_full_name,tg_id,rg_username)

@bot.callback_query_handler(func = lambda call: call.data == 'y')
def y(call):
    bot.answer_callback_query(call.id)

    tg_id = call.from_user.id
    rg_username = call.from_user.username

    msg = bot.send_message(call.message.chat.id,"Введите новое полное имя: ")
    bot.register_next_step_handler(msg, get_full_name, tg_id, rg_username)

@bot.callback_query_handler(func = lambda call : call.data == 'n')
def n(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("Хорошо! Ваши данные остались без изменений. ✅",call.message.chat.id,call.message.message_id)

def get_full_name(m,tg_id,rg_username):
    full_name = m.text.strip()

    msg = bot.send_message(m.chat.id,"Теперь отправьте номер телефона: ")
    bot.register_next_step_handler(msg,get_phone_name,tg_id,rg_username,full_name)

def get_phone_name(m,tg_id,rg_username,full_name,):
    if not m.text:
        msg = bot.send_message(m.chat.id,"Некорректный номер. Попробуйте ещё раз или напишите «Пропустить»:")
        bot.register_next_step_handler(msg,get_phone_name, tg_id, rg_username, full_name)
        return
    text = m.text.strip()

    if text.lower() == "пропустить":
        phone = None
    elif text.isdigit() and len(text) == 10:
        phone = text
    
    else:
        msg = bot.send_message(m.chat.id,"Некорректный номер. Введите 10 цифр или напишите «Пропустить»:")
        bot.register_next_step_handler(msg, get_phone_name, tg_id, rg_username, full_name)
        return 
              
    register_db(tg_id, rg_username, full_name, phone)

    bot.send_message(m.chat.id, "Вы успешно зарегистрированы! ✅")



# a4 Button
@bot.callback_query_handler(func = lambda call: call.data == "a4")
def a4(call):
    bot.answer_callback_query(call.id)
    masters = our_masters()
    if masters is None:
        bot.send_message(call.message.chat.id,"Не удалось загрузить список мастеров.")
        return
    bot.send_message(call.message.chat.id,masters,parse_mode="HTML")


# a2 Button
@bot.callback_query_handler(func=lambda call: call.data == "a2")
def a2(call):
    bot.answer_callback_query(call.id)

    result = my_booking(call.from_user.id)

    if not result:
        bot.send_message(call.message.chat.id, "📋 У вас пока нет записей.")
        return

    bot.send_message(call.message.chat.id, result)

        
#a5
@bot.callback_query_handler(func = lambda call : call.data == "a5")
def a5(call):
    bot.send_message(call.message.chat.id,'тел: <a href="https://wa.me/77777777777">+7 777 777 77 77</a>\nweb: <a href="https://google.com">Google</a>',parse_mode = "HTML")

#a6
@bot.callback_query_handler(func = lambda call : call.data == "a6")
def a6(call):
    a = comments_author()
    if not a:
        bot.send_message(call.message.chat.id, "💬 Пока отзывов нет.")
        return
    text = "⭐ <b>ОТЗЫВЫ НАШИХ КЛИЕНТОВ</b>\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"

    for master, comment in a:
        text += (
            f"💈 <b>Мастер: {master}</b>\n"
            f"💬 {comment}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )

    bot.send_message(
        call.message.chat.id,
        text,
        parse_mode="HTML"
    )

# a3
@bot.callback_query_handler(func = lambda call : call.data == "a3")
def a3(call):
    a = yslygi()
    if not a:
        bot.send_message(call.message.chat.id, "💈 Пока услуг нет.")
        return
    text = "💈 <b>НАШИ УСЛУГИ И ЦЕНЫ</b>\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    for name, description, price, duration in a:
        text += (
            f"✂️ <b>{name}</b>\n"
            f"📝 {description}\n"
            f"💰 <b>{price} ₸</b>\n"
            f"⏱ {duration} мин.\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )
    bot.send_message(
        call.message.chat.id,
        text,
        parse_mode="HTML"
    )

#a1
booking_data = {}
@bot.callback_query_handler(func=lambda call: call.data == "a1")
def booking_start(call):
    bot.answer_callback_query(call.id)

    services = get_services()

    if not services:
        bot.send_message(call.message.chat.id, "Услуг пока нет.")
        return

    keyboard = types.InlineKeyboardMarkup()

    for service_id, name, price, duration in services:
        keyboard.add(
            types.InlineKeyboardButton(
                f"{name} | {price} ₸",
                callback_data=f"book_service_{service_id}"
            )
        )

    bot.send_message(
        call.message.chat.id,
        "💈 <b>Выберите услугу:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("book_service_"))
def choose_service(call):
    bot.answer_callback_query(call.id)

    user_id = call.from_user.id
    service_id = int(call.data.replace("book_service_", ""))

    booking_data[user_id] = {"service_id": service_id}

    barbers = get_barbers()

    if not barbers:
        bot.send_message(call.message.chat.id, "Мастеров пока нет.")
        return

    keyboard = types.InlineKeyboardMarkup()

    for barber_id, name in barbers:
        keyboard.add(
            types.InlineKeyboardButton(
                name,
                callback_data=f"book_barber_{barber_id}"
            )
        )

    bot.send_message(
        call.message.chat.id,
        "💈 Выберите мастера:",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("book_barber_"))
def choose_barber(call):
    bot.answer_callback_query(call.id)

    user_id = call.from_user.id

    if user_id not in booking_data:
        bot.send_message(call.message.chat.id, "Начните запись заново.")
        return

    barber_id = int(call.data.replace("book_barber_", ""))

    booking_data[user_id]["barber_id"] = barber_id

    msg = bot.send_message(
        call.message.chat.id,
        "📅 Введите дату и время:\n\n"
        "Например: <code>05.11.2026 14:30</code>",
        parse_mode="HTML"
    )

    bot.register_next_step_handler(msg, finish_booking)


def finish_booking(message):
    user_id = message.from_user.id

    if user_id not in booking_data:
        bot.send_message(message.chat.id, "Начните запись заново.")
        return

    try:
        start_at = datetime.strptime(
            message.text,
            "%d.%m.%Y %H:%M"
        ).replace(tzinfo=ZoneInfo("Asia/Almaty"))

    except (ValueError, TypeError):
        msg = bot.send_message(
            message.chat.id,
            "❌ Неверный формат. Пример: 05.11.2026 14:30"
        )
        bot.register_next_step_handler(msg, finish_booking)
        return

    if start_at <= datetime.now(ZoneInfo("Asia/Almaty")):
        msg = bot.send_message(
            message.chat.id,
            "❌ Эта дата уже прошла. Введите другую дату."
        )
        bot.register_next_step_handler(msg, finish_booking)
        return

    full_name = " ".join(filter(None, [
        message.from_user.first_name,
        message.from_user.last_name
    ])) or "Клиент"

    data = booking_data[user_id]

    result = create_booking(
        message.from_user.id,
        message.from_user.username,
        full_name,
        data["barber_id"],
        data["service_id"],
        start_at
    )

    if result[0] == "occupied":
        msg = bot.send_message(
            message.chat.id,
            "❌ Это время занято! Измените дату или время."
        )
        bot.register_next_step_handler(msg, finish_booking)
        return

    if result[0] == "invalid":
        booking_data.pop(user_id, None)
        bot.send_message(message.chat.id, "Услуга или мастер недоступны.")
        return

    if result[0] != "ok":
        bot.send_message(message.chat.id, "Ошибка сохранения записи.")
        return

    booking_id, service_name, price, duration, barber_name, end_at = result[1:]

    booking_data.pop(user_id, None)

    bot.send_message(
        message.chat.id,
        f"✅ <b>Заявка отправлена!</b>\n\n"
        f"💈 Мастер: {escape(str(barber_name))}\n"
        f"✂️ Услуга: {escape(str(service_name))}\n"
        f"💰 Цена: {price} ₸\n"
        f"📅 Дата: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"⏱ Длительность: {duration} минут\n"
        f"📌 Ожидайте подтверждения.",
        parse_mode="HTML"
    )

    try:
        bot.send_message(
            ADMIN_ID,
            f"🔔 <b>НОВАЯ ЗАПИСЬ №{booking_id}</b>\n\n"
            f"👤 Клиент: {escape(full_name)}\n"
            f"🆔 Telegram ID: {user_id}\n"
            f"💈 Мастер: {escape(str(barber_name))}\n"
            f"✂️ Услуга: {escape(str(service_name))}\n"
            f"💰 Цена: {price} ₸\n"
            f"📅 Начало: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏱ Конец: {end_at.strftime('%H:%M')}\n"
            f"📌 Статус: Ожидает подтверждения",
            parse_mode="HTML"
        )
    except Exception as e:
        print("Ошибка отправки админу:", e)
    


# АДМИН-ПАНЕЛЬ

def is_admin(user_id):
    return user_id == ADMIN_ID


# ==============================
# АДМИН-ПАНЕЛЬ
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("➕ Добавить услугу", callback_data="admin_add_service"),
        types.InlineKeyboardButton("➕ Добавить барбера", callback_data="admin_add_barber"),
        types.InlineKeyboardButton("📋 Все активные записи", callback_data="admin_bookings"),
        types.InlineKeyboardButton("✅ Подтвердить запись", callback_data="admin_confirm_bookings"),
        types.InlineKeyboardButton("❌ Отменить запись", callback_data="admin_cancel_booking"),
        types.InlineKeyboardButton("✉️ Написать клиенту", callback_data="admin_message")
    )

    bot.send_message(
        call.message.chat.id,
        "⚙️ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ==============================
# ДОБАВЛЕНИЕ УСЛУГИ
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_service")
def admin_add_service_start(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "Введите название услуги:"
    )
    bot.register_next_step_handler(msg, admin_service_name)


def admin_service_name(message):
    if not is_admin(message.from_user.id):
        return

    name = message.text.strip()

    if not name:
        msg = bot.send_message(message.chat.id, "Название не может быть пустым.")
        bot.register_next_step_handler(msg, admin_service_name)
        return

    msg = bot.send_message(message.chat.id, "Введите описание услуги:")
    bot.register_next_step_handler(msg, admin_service_description, name)


def admin_service_description(message, name):
    if not is_admin(message.from_user.id):
        return

    description = message.text.strip()

    msg = bot.send_message(message.chat.id, "Введите стоимость услуги:")
    bot.register_next_step_handler(
        msg,
        admin_service_price,
        name,
        description
    )


def admin_service_price(message, name, description):
    if not is_admin(message.from_user.id):
        return

    try:
        price = float(message.text.replace(",", "."))

        if price < 0:
            raise ValueError

    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "Введите корректную стоимость (число не меньше 0):"
        )
        bot.register_next_step_handler(
            msg,
            admin_service_price,
            name,
            description
        )
        return

    msg = bot.send_message(
        message.chat.id,
        "Введите продолжительность услуги в минутах:"
    )

    bot.register_next_step_handler(
        msg,
        admin_service_duration,
        name,
        description,
        price
    )


def admin_service_duration(message, name, description, price):
    if not is_admin(message.from_user.id):
        return

    try:
        duration = int(message.text)

        if not 5 <= duration <= 480:
            raise ValueError

    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "Введите целое число от 5 до 480:"
        )
        bot.register_next_step_handler(
            msg,
            admin_service_duration,
            name,
            description,
            price
        )
        return

    result = add_service(name, description, price, duration)

    if result:
        bot.send_message(
            message.chat.id,
            "✅ Услуга успешно добавлена!"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось добавить услугу."
        )


# ==============================
# ДОБАВЛЕНИЕ БАРБЕРА
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_barber")
def admin_add_barber_start(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "Введите имя барбера:"
    )
    bot.register_next_step_handler(msg, admin_barber_name)


def admin_barber_name(message):
    if not is_admin(message.from_user.id):
        return

    name = message.text.strip()

    if not name:
        msg = bot.send_message(message.chat.id, "Имя не может быть пустым.")
        bot.register_next_step_handler(msg, admin_barber_name)
        return

    msg = bot.send_message(
        message.chat.id,
        "Введите описание барбера:"
    )
    bot.register_next_step_handler(
        msg,
        admin_barber_description,
        name
    )


def admin_barber_description(message, name):
    if not is_admin(message.from_user.id):
        return

    description = message.text.strip()

    result = add_barber(name, description)

    if result:
        bot.send_message(
            message.chat.id,
            "✅ Барбер успешно добавлен!"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось добавить барбера."
        )


# ==============================
# ПРОСМОТР ЗАПИСЕЙ
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "admin_bookings")
def admin_show_bookings(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)

    bookings = get_all_bookings()

    if not bookings:
        bot.send_message(
            call.message.chat.id,
            "📋 Активных записей нет."
        )
        return

    text = "📋 <b>АКТИВНЫЕ ЗАПИСИ</b>\n\n"

    for booking in bookings:
        booking_id, telegram_id, full_name, barber, service, start_at, status = booking

        text += (
            f"🔹 <b>Запись №{booking_id}</b>\n"
            f"👤 Клиент: {escape(str(full_name))}\n"
            f"🆔 Telegram ID: <code>{telegram_id}</code>\n"
            f"💈 Мастер: {escape(str(barber))}\n"
            f"✂️ Услуга: {escape(str(service))}\n"
            f"📅 Дата: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📌 Статус: {escape(str(status))}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    # Telegram ограничивает длину одного сообщения.
    # Разбиваем список на части.
    chunks = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > 3500:
            chunks.append(current)
            current = ""

        current += line + "\n"

    if current:
        chunks.append(current)

    for chunk in chunks:
        bot.send_message(
            call.message.chat.id,
            chunk,
            parse_mode="HTML"
        )


# ==============================
# ПОДТВЕРЖДЕНИЕ ЗАПИСЕЙ
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "admin_confirm_bookings")
def admin_confirm_bookings_list(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)
    bookings = get_pending_bookings()

    if bookings is None:
        bot.send_message(call.message.chat.id, "❌ Не удалось загрузить записи.")
        return
    if not bookings:
        bot.send_message(call.message.chat.id, "✅ Нет записей, ожидающих подтверждения.")
        return

    for booking_id, telegram_id, full_name, barber, service, start_at in bookings:
        text = (
            f"⏳ <b>Запись №{booking_id}</b>\n"
            f"👤 Клиент: {escape(str(full_name))}\n"
            f"🆔 Telegram ID: <code>{telegram_id}</code>\n"
            f"💈 Мастер: {escape(str(barber))}\n"
            f"✂️ Услуга: {escape(str(service))}\n"
            f"📅 Дата: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📌 Статус: ожидает подтверждения"
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "✅ Подтвердить эту запись",
            callback_data=f"admin_confirm_one_{booking_id}"
        ))
        bot.send_message(call.message.chat.id, text, reply_markup=keyboard, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_confirm_one_"))
def admin_confirm_one(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    booking_id = int(call.data.rsplit("_", 1)[1])
    result = confirm_booking(booking_id)
    bot.answer_callback_query(call.id)

    if not result:
        bot.send_message(call.message.chat.id, "❌ Не удалось подтвердить запись. Возможно, её уже подтвердили или отменили.")
        return

    telegram_id, confirmed_id, service_name, start_at = result
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, f"✅ Запись №{confirmed_id} подтверждена.")

    try:
        bot.send_message(
            telegram_id,
            "✅ <b>Ваша запись подтверждена!</b>\n\n"
            f"✂️ Услуга: {escape(str(service_name))}\n"
            f"📅 Дата: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
            "Ждём вас!",
            parse_mode="HTML"
        )
    except Exception as e:
        print("Не удалось уведомить клиента о подтверждении:", e)
        bot.send_message(call.message.chat.id, "⚠️ Запись подтверждена, но уведомление клиенту отправить не удалось.")


# ==============================
# ОТМЕНА ЗАПИСИ
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "admin_cancel_booking")
def admin_cancel_start(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)

    bookings = get_all_bookings()

    if not bookings:
        bot.send_message(
            call.message.chat.id,
            "Активных записей нет."
        )
        return

    text = "❌ <b>ВЫБЕРИТЕ ЗАПИСЬ ДЛЯ ОТМЕНЫ</b>\n\n"
    keyboard = types.InlineKeyboardMarkup()

    for booking in bookings:
        booking_id, telegram_id, full_name, barber, service, start_at, status = booking

        text += (
            f"🔹 <b>Запись №{booking_id}</b>\n"
            f"👤 Клиент: {escape(str(full_name))}\n"
            f"💈 Мастер: {escape(str(barber))}\n"
            f"✂️ Услуга: {escape(str(service))}\n"
            f"📅 Дата: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"━━━━━━━━━━━━━━\n"
        )

        keyboard.add(
            types.InlineKeyboardButton(
                f"Отменить запись №{booking_id}",
                callback_data=f"admin_cancel_select_{booking_id}"
            )
        )

    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("admin_cancel_select_")
)
def admin_cancel_select(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    booking_id = int(call.data.replace("admin_cancel_select_", ""))

    bot.answer_callback_query(call.id)

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Да, отменить",
            callback_data=f"admin_cancel_confirm_{booking_id}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ Нет",
            callback_data="admin_cancel_no"
        )
    )

    bot.send_message(
        call.message.chat.id,
        f"Вы действительно хотите отменить запись №{booking_id}?",
        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("admin_cancel_confirm_")
)
def admin_cancel_confirm(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    booking_id = int(call.data.replace("admin_cancel_confirm_", ""))

    result = cancel_booking(booking_id)

    bot.answer_callback_query(call.id)

    if not result:
        bot.send_message(
            call.message.chat.id,
            "❌ Не удалось отменить запись. Возможно, она уже отменена."
        )
        return

    telegram_id, booking_id, service_name, start_at = result

    bot.send_message(
        call.message.chat.id,
        f"✅ Запись №{booking_id} успешно отменена."
    )

    try:
        bot.send_message(
            telegram_id,
            f"❌ Ваша запись отменена администратором.\n\n"
            f"✂️ Услуга: {escape(str(service_name))}\n"
            f"📅 Дата: {start_at.strftime('%d.%m.%Y %H:%M')}"
        )
    except Exception as e:
        print("Не удалось уведомить клиента:", e)


@bot.callback_query_handler(func=lambda call: call.data == "admin_cancel_no")
def admin_cancel_no(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id, "Отмена отменена.")


# ==============================
# СПИСОК КЛИЕНТОВ И СООБЩЕНИЯ
# ==============================

CLIENTS_PAGE_SIZE = 10


def show_admin_clients(chat_id, page=0):
    offset = page * CLIENTS_PAGE_SIZE
    clients = get_clients_with_bookings(CLIENTS_PAGE_SIZE, offset)

    if clients is None:
        bot.send_message(chat_id, "❌ Не удалось загрузить клиентов из базы данных.")
        return

    if not clients and page == 0:
        bot.send_message(chat_id, "Пока нет клиентов с записями.")
        return

    if not clients:
        bot.send_message(chat_id, "Больше клиентов нет.")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    text = "👥 <b>КЛИЕНТЫ С ЗАПИСЯМИ</b>\n\nВыберите клиента, чтобы посмотреть его заказы:"

    for telegram_id, full_name, username, bookings_count, last_booking in clients:
        display_name = full_name or f"Клиент {telegram_id}"
        username_label = f" (@{username})" if username else ""
        keyboard.add(
            types.InlineKeyboardButton(
                f"{display_name}{username_label} · {bookings_count} записей",
                callback_data=f"admin_client_{telegram_id}"
            )
        )

    navigation = []
    if page > 0:
        navigation.append(
            types.InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_message_page_{page - 1}")
        )
    if len(clients) == CLIENTS_PAGE_SIZE:
        navigation.append(
            types.InlineKeyboardButton("Вперёд ➡️", callback_data=f"admin_message_page_{page + 1}")
        )
    if navigation:
        keyboard.row(*navigation)

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "admin_message")
def admin_message_start(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)
    show_admin_clients(call.message.chat.id, page=0)


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_message_page_"))
def admin_message_page(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)
    page = int(call.data.rsplit("_", 1)[1])
    show_admin_clients(call.message.chat.id, page)


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_client_"))
def admin_client_select(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа!")
        return

    bot.answer_callback_query(call.id)
    telegram_id = int(call.data.replace("admin_client_", "", 1))
    bookings = get_client_bookings(telegram_id)

    if bookings is None:
        bot.send_message(call.message.chat.id, "❌ Не удалось загрузить заказы клиента.")
        return

    if not bookings:
        bot.send_message(call.message.chat.id, "У этого клиента больше нет записей в базе.")
        return

    full_name = bookings[0][0]
    username = bookings[0][1]
    text = (
        f"👤 <b>{escape(str(full_name))}</b>\n"
        f"🆔 Telegram ID: <code>{telegram_id}</code>\n"
        f"👤 Username: @{escape(username) if username else 'не указан'}\n"
        f"📋 <b>ИСТОРИЯ ЗАПИСЕЙ</b>\n\n"
    )

    for _, _, booking_id, service, barber, start_at, end_at, status in bookings:
        text += (
            f"🔹 <b>Запись №{booking_id}</b>\n"
            f"✂️ Услуга: {escape(str(service))}\n"
            f"💈 Мастер: {escape(str(barber))}\n"
            f"📅 Начало: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏱ Окончание: {end_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📌 Статус: {escape(str(status))}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if username:
        keyboard.add(
            types.InlineKeyboardButton(
                "💬 Открыть личный чат в Telegram",
                url=f"https://t.me/{username.lstrip('@')}"
            )
        )
    else:
        text += (
            "\n⚠️ У клиента не указан Telegram username. "
            "Попросите его установить username в настройках Telegram, "
            "чтобы открыть личный чат по ссылке."
        )

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ К списку клиентов",
            callback_data="admin_message_page_0"
        )
    )

    # Делим длинную историю на сообщения, а кнопки прикрепляем к последнему.
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > 3500:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current:
        chunks.append(current)

    for chunk in chunks[:-1]:
        bot.send_message(call.message.chat.id, chunk, parse_mode="HTML")

    bot.send_message(
        call.message.chat.id,
        chunks[-1],
        reply_markup=keyboard,
        parse_mode="HTML"
    )




# ==============================
# АВТОМАТИЧЕСКАЯ ОЧИСТКА ЗАПИСЕЙ
# ==============================

def cleanup_worker():
    while True:
        try:
            cleanup_old_bookings()
        except Exception as e:
            print("Ошибка фоновой очистки записей:", e)

        time.sleep(3600)


# ==============================
# ЗАПУСК БОТА
# ==============================

if __name__ == "__main__":
    # Один раз запускаем очистку при старте, затем повторяем каждый час.
    cleanup_old_bookings()

    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

    bot.infinity_polling()








