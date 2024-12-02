#!/usr/bin/env python3

from aiogram import Bot, Dispatcher, F
from aiogram.types import (Message, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery,
                           CallbackQuery)
from aiogram.utils.markdown import hbold, hlink

from babel.numbers import get_currency_symbol
from asyncio import run as async_run
from asyncio import sleep as asleep
from asyncio import gather, get_event_loop, create_task, CancelledError, all_tasks, current_task
from time import time as unixtime
from dotenv import dotenv_values
from applib.strings import *
from applib import *
from aiopg import Cursor
from random import randint
from typing import Dict
from signal import SIGINT, SIGTERM

from os import environ
from google.cloud import dialogflow
from google.api_core.exceptions import InvalidArgument
from google.oauth2 import service_account

with open(dialog_flow_file) as f:
    environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(dialog_flow_file)
    DIALOGFLOW_PROJECT_ID = "small-talk-rwvf"
    DIALOGFLOW_LANGUAGE_CODE = 'ru'
    SESSION_ID = 'me'
credentials = service_account.Credentials.from_service_account_file(dialog_flow_file)

sessionClient = dialogflow.SessionsClient(credentials=credentials)

secrets: Dict[str, str | None] = dotenv_values('.env')
TOKEN: str = secrets["BOT_TOKEN"]  # type: ignore

bot: Bot = Bot(TOKEN)
dp = Dispatcher(bot=bot)

# TelegramBot = require('node-telegram-bot-api');
# sqlite3 = require('sqlite3').verbose();
# dialogflow = require('@google-cloud/dialogflow').v2beta1;

# const sharp = require('sharp');
#  const fs = require('fs')

event_coin_path = './rate.txt'
# logf(chatCompletion.choices[0].message.content);

payment_token = "284685063:TEST:Y2YxMWE3NmJkODRh"

admins_id = [1432248216, 1300210900]
# credentials = require('./key.json')

projectId = 'small-talk-rwvf'

vid250 = './250videocards.png'

clans = ("отсутствует",)

lastToId = 0

startTime = unixtime()
cooldownPeriod = 5000


# region ----- Without using DB
@dp.message(F.text.regexp(r'^(\/start|меню)(\s|$)'))
async def start(message: Message):
    user_name = message.from_user.first_name

    try:
        await message.reply(
            start_text(user_name),
            allow_sending_without_reply=True,
            parse_mode="markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=start_keyboard(InlineKeyboardButton))
        )
    except Exception as e:
        await logf(e)
        await message.reply(f"❌ Произошла ошибка!\n <code>{e}</code>",
                            allow_sending_without_reply=True,
                            parse_mode='HTML')


@dp.message(F.text.regexp(r'^(\/ping|пинг)(\s|$)'))
async def ping(message: Message):
    start_time = unixtime()
    try:

        reply_message = await bot.send_message(message.chat.id, '🔄 *Пинг...*')
        end_time = unixtime()
        ping_time = round((end_time - start_time) * 1000, 2)
        await bot.edit_message_text(
            f"🚀 *Понг!*  \n💡 *Задержка:* {ping_time}ms",
            chat_id=message.chat.id,
            message_id=reply_message.message_id,
            parse_mode="markdown")
    except Exception as e:
        await bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")


@dp.message(F.text.startswith("/test") | F.text.lower().startswith('тест'))
async def test(message: Message):
    await bot.send_message(message.chat.id, f"Тест вывод: {1}")


@dp.message(F.text.regexp(r'^(\/donate|донат)(\s|$)'))
async def donate(message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if await check_flood_wait(user_id):
            warning = await message.reply(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(warning.chat.id, warning.message_id)
            return

        await message.reply(
            donate_text(),
            allow_sending_without_reply=True,
            parse_mode="markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=donate_keyboard(InlineKeyboardButton, prices)
            )
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'^(\/shop|магазин)(\s|$)'))
async def shop(message: Message):
    assert message.from_user is not None
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    ecoin = await ecoin_to_bucks(1)

    if await check_flood_wait(user_id):
        warning = await message.reply(
            f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, '
            f'Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
            parse_mode="HTML"
        )
        await asleep(3)
        await bot.delete_message(warning.chat.id, warning.message_id)
        return

    try:
        await message.reply(
            start_text(user_name),
            allow_sending_without_reply=True,
            parse_mode="markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=shop_keyboard(InlineKeyboardButton, ecoin)
            )
        )
    except Exception as e:
        await logf(e)
        await message.reply(f"❌ Произошла ошибка!\n <code>{e}</code>",
                            allow_sending_without_reply=True,
                            parse_mode='HTML')


@dp.message(F.text.regexp(r'(?i)^(\/rate|курс|екоин)(\s|$)'))
async def show_rate(message: Message):
    rate = await ecoin_to_bucks(1)
    await message.reply(
        rate_text(rate),
        allow_sending_without_reply=True,
        parse_mode='HTML'
    )
# endregion


# region ----- With using DB
@dp.message(F.text.regexp(r'^(\/cash|баланс)(\s|$)'))
@with_db(True)
async def get_cash(cur: Cursor, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if await check_flood_wait(user_id):
            await bot.edit_message_text(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(load.chat.id, load.message_id)
            return

        await cur.execute(
            "SELECT cash, goldfevervalue, bitcoins FROM users WHERE id=%s",
            (user_id,))

        row = await cur.fetchone()

        if row is None:
            await bot.edit_message_text(
                "❌ Не найдено данных для пользователя.",
                chat_id=load.chat.id,
                message_id=load.message_id)
            return

        if not await check_account(cur, message):
            return

        cash = format_num(row["cash"])
        ecoin = format_num(row["bitcoins"])

        cash_text = f"{cash} $"
        ecoins_text = f"{ecoin} ₠"

        await bot.edit_message_text(balance_text(cash_text, ecoins_text),
                                    chat_id=load.chat.id,
                                    message_id=load.message_id,
                                    parse_mode="markdown")

    except Exception as e:
        await bot.send_message(message.chat.id,
                               f"❌ Произошла ошибка!\n <code>{e}</code>",
                               parse_mode='HTML')
        raise e


@dp.message(F.text.regexp(r'^(\/farming|фарм)(\s|$)'))
@with_db(True)
async def farm(cur: Cursor, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        if await check_flood_wait(user_id):
            await bot.edit_message_text(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(load.chat.id, load.message_id)
            return

        await cur.execute(
            "SELECT isvip, videocards, last_farming_time FROM users WHERE id = %s",
            (message.from_user.id,))
        row = await cur.fetchone()

        if not await check_account(cur, message):
            return

        is_vip = vip_rangs[row['isvip']]
        videocards: int = row['videocards']

        last_farming_time = row['last_farming_time']
        time_now = unixtime()

        if time_now - last_farming_time < farming_timers[row['isvip']]:
            time_to_use = farming_timers[row['isvip']] - (time_now - last_farming_time)

            await bot.edit_message_text(farm_text_failure(time_to_use),
                                        chat_id=load.chat.id,
                                        message_id=load.message_id,
                                        parse_mode="markdown")
            return

        random_cash = int(randint(1000, 10000))
        random_cash *= multiplies[row['isvip']]
        random_cash *= videocards if videocards else 1

        multiply_text = multiplies[row['isvip']] * videocards
        text_video = videocards if videocards else 'Нет. \n💠Используется встроенное графическое ядро.'

        rate, farmed_amount = await read_eventcoin()
        cryptocoins = random_cash / rate

        farmed_amount += random_cash
        await write_eventcoin(rate, farmed_amount)

        # Ответ пользователю
        await bot.edit_message_text(farm_text_success(cryptocoins, is_vip,
                                                      str(text_video),
                                                      multiply_text),
                                    chat_id=load.chat.id,
                                    message_id=load.message_id,
                                    parse_mode="markdown")
        await logf(
            f"{message.from_user.first_name} - {format_time(int(time_now))}, Link - 'tg://user?id={message.from_user.id}"
        )
        await cur.execute(
            'UPDATE users SET last_farming_time = %s, bitcoins = bitcoins + %s WHERE id = %s',
            (time_now, cryptocoins, message.from_user.id))

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/rich_top|топ богачей|топ богатых|богатые)(\s|$)'))
@with_db(True)
async def rich_top(cur, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if await check_flood_wait(user_id):
            await bot.edit_message_text(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(load.chat.id, load.message_id)
            return

        await cur.execute("SELECT name, cash, id, tag FROM users ORDER BY cash DESC LIMIT 10")
        users_row = await cur.fetchall()
        keyboard = top_keyboard(users_row, InlineKeyboardButton, "$")

        await bot.edit_message_text(
            rich_text(),
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/crypto_top|топ крипта|топ майнеры|майнеры)(\s|$)'))
@with_db(True)
async def rich_top(cur, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if await check_flood_wait(user_id):
            await bot.edit_message_text(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(load.chat.id, load.message_id)
            return

        await cur.execute("SELECT name, bitcoins, id, tag FROM users ORDER BY bitcoins DESC LIMIT 10")
        users_row = await cur.fetchall()
        keyboard = top_keyboard(users_row, InlineKeyboardButton, "₠")

        await bot.edit_message_text(
            crypto_text(),
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/dice|кубик|кости)(\s|$)'))
@with_db(True)
async def dice(cur, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        first_name = message.from_user.first_name

        await cur.execute("SELECT cash FROM users WHERE id = %s", (user_id,))
        user = await cur.fetchone()

        if not await check_account(cur, message):
            return

        balance = user['cash']

        if await check_flood_wait(user_id):
            warning = await message.reply(
                f"🚫 <a href=tg://user?id={user_id}>{first_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.",
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(warning.chat.id, warning.message_id)
            return

        try:
            parts = message.text.split()
            bid = int(parts[1])
            dice_value = int(parts[2])

            if not await validate_bid(bid, balance):
                if bid < 10:
                    await send_error_reply(
                        message,
                        "⚠️ *Ошибка!* \nСтавка должна быть не меньше 10!",
                        f"{message.text.split(' ')[0]} [ставка] [1-6]"
                    )
                    await bot.delete_message(
                        chat_id=load.chat.id,
                        message_id=load.message_id,
                    )
                else:
                    await bot.edit_message_text(
                        "🚫 *Недостаточно денег!* 💸\nПожалуйста, внесите средства на свой счёт, чтобы продолжить игру.",
                        chat_id=load.chat.id,
                        message_id=load.message_id,
                        parse_mode="markdown"
                    )
                return

            if not await validate_dice_value(dice_value):
                await send_error_reply(
                    message,
                    "⚠️ *Ошибка!* \nЧисло должно быть от 1 до 6! 🎲",
                    f"{message.text.split(' ')[0]} [ставка] [1-6]"
                )
                await bot.delete_message(
                    chat_id=load.chat.id,
                    message_id=load.message_id,
                )
                return

        except (IndexError, ValueError):
            await message.reply(
                "⚠️ *Ошибка!* \n"
                "Введите ставку и число от 1 до 6! 🎯\n"
                f"Использование: `{message.text.split(' ')[0]} [ставка] [1-6]`",
                parse_mode="markdown"
            )
            return

        try:
            await bot.delete_message(
                load.chat.id,
                load.message_id
            )
            spin = await bot.send_dice(
                message.chat.id,
                emoji="🎲",
                allow_sending_without_reply=True,
                reply_to_message_id=message.message_id
            )
            value = spin.dice.value

            if value == dice_value:
                result_text = f"🎉 *Везение!* \n\nВы выиграли: +{bid}💸\n\n💰 Ваш баланс теперь: {format_num(balance + bid)}$"
                await cur.execute(
                    "UPDATE users SET cash = cash + %s WHERE id = %s",
                    (bid, user_id)
                )
            else:
                result_text = f"😞 *Мимо!* \n\nВы проиграли: -{bid}💸\n\n💰 Ваш баланс теперь: {format_num(balance - bid)}$"
                await cur.execute(
                    "UPDATE users SET cash = cash - %s WHERE id = %s",
                    (bid, user_id)
                )

            await asleep(4)

            await bot.send_message(
                message.chat.id,
                result_text,
                allow_sending_without_reply=True,
                reply_to_message_id=spin.message_id,
                parse_mode="markdown"
            )

        except Exception as e:
            await message.reply(
                f"❌ Произошла ошибка!\n<code>{e}</code>",
                parse_mode='HTML'
            )
    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/basketball|\/darts|\/football|\/bowling|баскетбол|дартс|футбол|боулинг)(\s|$)'))
@with_db(True)
async def game_handler(cur, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id

        await cur.execute("SELECT cash FROM users WHERE id = %s", (user_id,))
        user = await cur.fetchone()

        if not await check_account(cur, message):
            return

        balance = user['cash']

        if await check_flood_wait(user_id):
            warning = await message.reply(
                "🚫 Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.",
                parse_mode="markdown"
            )
            await asleep(3)
            await bot.delete_message(warning.chat.id, warning.message_id)
            return

        try:
            await bot.delete_message(
                load.chat.id,
                load.message_id
            )
            bid = int(message.text.split()[1])

            if bid < 10:
                await send_error_reply(
                    message,
                    "⚠️ *Ошибка!* \nСтавка должна быть не меньше 10!",
                    f"{message.text.split(' ')[0]} [ставка]"
                )
                return

            if bid > balance:
                await message.reply(
                    "🚫 *Недостаточно денег!* 💸\nПополните счёт, чтобы продолжить игру.",
                    parse_mode="markdown"
                )
                return

        except (IndexError, ValueError):
            await message.reply(
                "⚠️ *Ошибка!* \nВведите ставку как целое число!\n"
                f"Использование: `{message.text.split(' ')[0]} [ставка]`",
                parse_mode="markdown"
            )
            return

        try:
            emoji = await get_emoji(message.text.split(' ')[0])
            spin = await bot.send_dice(
                message.chat.id,
                emoji=emoji,
                allow_sending_without_reply=True,
                reply_to_message_id=message.message_id
            )
            value = spin.dice.value
            emoji = spin.dice.emoji

            obtaining, nb = await get_result(emoji, value, bid, balance)

            await asleep(4)
            await cur.execute(
                "UPDATE users SET cash = cash + %s WHERE id = %s",
                (bid, user_id)
            )
            await bot.send_message(
                message.chat.id,
                obtaining,
                reply_to_message_id=spin.message_id,
                parse_mode="markdown"
            )

        except Exception as e:
            await message.reply(f"❌ Произошла ошибка!\n <code>{e}</code>", parse_mode='HTML')

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/profile|профиль)(\s|$)'))
@with_db(True)
async def profile(cur: Cursor, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if await check_flood_wait(user_id):
            await bot.edit_message_text(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(load.chat.id, load.message_id)
            return

        if message.entities and len(message.entities) > 1 and message.entities[1].type == "mention":
            username = message.text[
                       message.entities[1].offset + 1:message.entities[1].offset + message.entities[1].length]
            user_query = "SELECT name, id, cash, isvip, videocards, clan, tag, bitcoins FROM users WHERE mention = %s"
            user_param = (username,)
        elif message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user_query = "SELECT name, id, cash, isvip, videocards, clan, tag, bitcoins FROM users WHERE id = %s"
            user_param = (user_id,)
        else:
            await bot.edit_message_text(
                "❗️ Команда должна писаться в ответ на сообщение или содержать упоминание пользователя!",
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            return

        await cur.execute(user_query, user_param)
        user = await cur.fetchone()

        if not user:
            await message.reply(
                "❌ У этого пользователя нет аккаунта!",
                allow_sending_without_reply=True
            )
            return

        if user["clan"] == 0:
            current_clan = "отсутствует"
        else:
            await cur.execute("SELECT name FROM clans WHERE owner=  %s", (user["clan"],))
            clan_data = await cur.fetchone()
            current_clan = clan_data["name"] if clan_data else "нет"

        user_name = message.reply_to_message.from_user.first_name if message.reply_to_message else f"@{username}"
        link = hlink(user_name, f'tg://user?id={user['id']}')
        """profile_result = (
            f"👤 {hlink(user_name, f'tg://user?id={user['id']}')}"
            f"\n<b>Профиль</b> пользователя {hbold(user['name'])}: \n"
            f"\n🏰 Клан: {hbold(current_clan)}"
            f"\n🏷 Префикс: {hbold(user['tag'])}"
            f"\n📇 Псевдоним: {hbold(user['name'])}"
            f"\n🆔 ID: {user['id']}"
            f"\n💵 Баланс: {format_num(user['cash'])}$"
            f"\n💳 ECoins: {format_num(user['bitcoins'])}₠"
            f"\n🖥 Видеокарты: {user['videocards']} шт."
            f"\n🪪 Пропуск: {vip_rangs[user['isvip']]}"
        )"""
        profile_result = profile_text(hlink(user_name, f'tg://user?id={user['id']}'), hbold, user, current_clan)

        invite_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✉️ Пригласить в клан", callback_data=f"clan_invite_{user['id']}")]
            ] if user["clan"] == 0 else [
                [InlineKeyboardButton(text=f"🏰 {current_clan}", callback_data=f"clan_show_info_{user["clan"]}")]
            ]
        )

        await bot.edit_message_text(
            profile_result,
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML",
            reply_markup=invite_keyboard
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/clans|кланы)(\s|$)'))
@with_db(True)
async def top_clans(cur: Cursor, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if await check_flood_wait(user_id):
            await bot.edit_message_text(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(load.chat.id, load.message_id)
            return

        await cur.execute("SELECT name, money, type, owner FROM clans ORDER BY money DESC LIMIT 10")
        clans_row = await cur.fetchall()
        keyboard = clans_keyboard(clans_row, InlineKeyboardButton)

        await bot.edit_message_text(
            clans_text(),
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/clan|клан|мой клан)(\s|$)'))
@with_db(True)
async def clan(cur: Cursor, load: Message, message: Message):
    try:
        assert message.from_user is not None
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        if await check_flood_wait(user_id):
            await bot.edit_message_text(
                f'🚫 <a href="tg://user?id={user_id}">{user_name}</a>, Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.',
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode="HTML"
            )
            await asleep(3)
            await bot.delete_message(load.chat.id, load.message_id)
            return

        if not await check_account(cur, message):
            return

        await cur.execute("SELECT clan FROM users WHERE id = %s", (message.from_user.id,))
        user = await cur.fetchone()
        await cur.execute("SELECT name, id FROM users WHERE id = %s", (user["clan"],))
        owner_row = await cur.fetchone()
        await cur.execute("SELECT * FROM clans WHERE owner = %s", (user["clan"],))
        clan_row = await cur.fetchone()

        owner_link = hlink(owner_row["name"], f'tg://user?id={owner_row["id"]}')
        members = await get_clan_members(clan_id=clan_row['owner'])
        keyboard = clan_keyboard(clan_row, InlineKeyboardButton)

        await bot.edit_message_text(
            clan_text(clan_row, owner_link, members),
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/buyCrypto|купить крипту|купить екоин)(\s|$)'))
@with_db(True)
async def buy_crypto(cur: Cursor, load: Message, message: Message):
    try:
        ecoins = int(message.text.split()[1])
    except (ValueError, IndexError):
        await bot.edit_message_text(
            text="❌ Введенное вами значение не является числом!",
            chat_id=load.chat.id,
            message_id=load.message_id
        )
        return
    try:
        if ecoins <= 0:
            await bot.edit_message_text(
                text="❌ Нельзя продать число меньше или равное нулю!",
                chat_id=load.chat.id,
                message_id=load.message_id
            )
            return

        bucks = await ecoin_to_bucks(ecoins)

        user_id = message.from_user.id
        await cur.execute("SELECT cash, bitcoins FROM users WHERE id=%s", (user_id,))
        row = await cur.fetchone()

        if not await check_account(cur, message):
            return

        cash, bitcoins = row
        if bucks > cash:
            await bot.edit_message_text(
                text="❌ У вас нет такого количества ECoin!",
                chat_id=load.chat.id,
                message_id=load.message_id
            )
            return

        await cur.execute(
            "UPDATE users SET cash = cash-%s, bitcoins = bitcoins+%s WHERE id=%s",
            (bucks, ecoins, user_id)
        )

        rate, farmed_amount = await read_eventcoin()
        farmed_amount += bucks
        await write_eventcoin(rate, farmed_amount)

        await bot.edit_message_text(
            text=f"✅ Успешно куплено {format_num(ecoins)}₠ за {format_num(int(bucks))}$!",
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML"
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.text.regexp(r'(?i)^(\/sellCrypto|продать крипту|продать екоин)(\s|$)'))
@with_db(True)
async def sell_crypto(cur: Cursor, load: Message, message: Message):
    try:
        ecoins = int(message.text.split()[1])
    except (ValueError, IndexError):
        await bot.edit_message_text(
            text="❌ Введенное вами значение не является числом!",
            chat_id=load.chat.id,
            message_id=load.message_id
        )
        return

    try:
        if ecoins <= 0:
            await bot.edit_message_text(
                text="❌ Нельзя продать число меньше или равное нулю!",
                chat_id=load.chat.id,
                message_id=load.message_id
            )
            return

        bucks = await ecoin_to_bucks(ecoins)

        user_id = message.from_user.id
        await cur.execute("SELECT cash, bitcoins FROM users WHERE id=%s", (user_id,))
        row = await cur.fetchone()

        if not await check_account(cur, message):
            return

        cash, bitcoins = row
        if ecoins > bitcoins:
            await bot.edit_message_text(
                text="❌ У вас нет такого количества ECoin!",
                chat_id=load.chat.id,
                message_id=load.message_id
            )
            return

        await cur.execute(
            "UPDATE users SET cash = cash+%s, bitcoins = bitcoins-%s WHERE id=%s",
            (bucks, ecoins, user_id)
        )

        rate, farmed_amount = await read_eventcoin()
        farmed_amount -= bucks
        await write_eventcoin(rate, farmed_amount)

        await bot.edit_message_text(
            text=f"✅ Успешно продано {format_num(ecoins)}₠ за {format_num(int(bucks))}$!",
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML"
        )

    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


@dp.message(F.successful_payment)
@with_db(True)
async def got_payment(cur: Cursor, load: Message, message: Message):
    try:
        payment = message.successful_payment
        currency = get_currency_symbol(payment.currency, locale="en")
        payload = payment.invoice_payload
        quantity = payload.split(' ')[0]

        await cur.execute(
            'UPDATE users SET videocards = videocards + %s WHERE id = %s',
            (int(quantity), message.from_user.id))

        await bot.edit_message_text(
            text=f'✅ Оплата прошла успешно, спасибо за покупку! \n\n'
                 f'🧾 *Детали заказа* \n'
                 f'📦 Товар: {payment.invoice_payload}\n'
                 f'💰 Цена: {payment.total_amount / 100}{currency}\n\n'
                 f'🔄 Ваш баланс обновлен.',
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode='Markdown'
        )
    except Exception as e:
        await bot.edit_message_text(
            f'❌ Произошла ошибка!\n{e}',
            chat_id=load.chat.id,
            message_id=load.message_id,
        )
        await logf(e)


# endregion


# region ----- Payments query
@dp.pre_checkout_query(lambda query: True)
@with_db(True)
async def checkout(cur: Cursor, loading: Message, pre_checkout_query: PreCheckoutQuery, *args: Any, **kwargs: Any):
    try:
        assert pre_checkout_query.from_user is not None
        await cur.execute(
            "SELECT cash, goldfevervalue, bitcoins FROM users WHERE id=%s",
            (pre_checkout_query.from_user.id,))

        row = await cur.fetchone()

        if row is None:
            await bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message=f'🚫 Вы не зарегистрированы! \nНапишите любую игровую команду для создания аккаунта.'
            )
            return

        if not await check_account(cur, pre_checkout_query):
            return

        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    except Exception as e:
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message=f"❌ Произошла ошибка!\n {e}"
        )
        raise e


# endregion


# region ----- Callback query
@dp.callback_query(lambda c: c.data.startswith('donatevid'))
async def donate_videocards(callback: CallbackQuery):
    vid_id = callback.data.split('donatevid')[1]
    price = filter_dict(prices, vid_id)
    await bot.answer_callback_query(callback.id)
    await bot.send_invoice(
        callback.message.chat.id, title=f"🖥 {price.label}",
        description='Купи больше видеокарт для своей майнинг фермы несмотря на лимит!',
        # provider_token='410694247:TEST:d26cecc4-1321-4cb9-b23f-b385f5d0594f',
        currency='XTR',
        prices=[price],
        start_parameter=f'vid{vid_id}',
        payload=price.label
    )


@dp.callback_query(lambda c: c.data == 'commands')
async def list_commands(callback: CallbackQuery):
    user = callback.from_user
    list_message = f'🚀 <a href="tg://user?id={user.id}">{user.first_name}</a> вызывает список команд.\n\n'
    for command in commands:
        head = command.split("-")[0]
        value = command.split("-")[1]
        list_message += f"‣ <b>{head}</b> - {value}\n"
    await callback.message.reply(
        list_message,
        allow_sending_without_reply=True,
        parse_mode='html'
    )


@dp.callback_query(lambda c: c.data.startswith('buyvid'))
@with_db(lambda c: len(c.data.split('_')) > 1)
async def buy_videocards(cur: Cursor, load: Message, callback: CallbackQuery, *args: Any, **kwargs: Any):
    try:
        assert callback.from_user is not None
        await cur.execute(
            "SELECT videocards FROM users WHERE id=%s",
            (callback.from_user.id,))

        row = await cur.fetchone()

        if row is None:
            await bot.edit_message_text(
                "❌ Не найдено данных для пользователя.",
                chat_id=load.chat.id,
                message_id=load.message_id)
            return

        if not await check_account(cur, callback):
            return

        link = f'<a href="tg://user?id={callback.from_user.id}">{callback.from_user.first_name}</a>'
        vid_value = None
        if len(callback.data.split('_')) > 1:
            vid_value = callback.data.split('_')[1]
            user_id = int(callback.data.split('_')[2])
            if callback.from_user.id != user_id:
                await bot.answer_callback_query(
                    callback.id,
                    "⛔️ Эта кнопка предназначена не для Вас!",
                    show_alert=True
                )
            else:
                await bot.edit_message_text(
                    text=f"Количество: {vid_value}",
                    chat_id=load.chat.id,
                    message_id=load.message_id,
                    parse_mode='html'
                )
        else:
            await bot.edit_message_text(
                text=videocards_text_select(link),
                chat_id=load.chat.id,
                message_id=load.message_id,
                parse_mode='html',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=videocards_keyboard(InlineKeyboardButton, factor, row["videocards"],
                                                        callback.from_user.id)
                )
            )

        await bot.answer_callback_query(callback.id)
    except Exception as e:
        await bot.send_message(
            callback.message.chat.id,
            f"❌ Произошла ошибка!\n <code>{e}</code>",
            parse_mode='HTML'
        )
        raise e


@dp.callback_query(lambda c: c.data == 'decor')
async def decoration(callback: CallbackQuery):
    await bot.answer_callback_query(callback.id)


@dp.callback_query(lambda c: c.data.startswith('clan'))
@with_db(lambda c: c.message.chat.type != "private")
async def clan_handler(cur, load: Message, callback: CallbackQuery):
    """Обрабатывает запросы для отображения информации о клане или пользователе."""
    try:
        assert callback.from_user is not None
        option = callback.data.split('_')[1]
        target_id = int(callback.data.split('_')[3]) if option == "show" else None
        load = callback.message if callback.message.chat.type == "private" else load
        if option == "show":
            await cur.execute("SELECT name, id FROM users WHERE id = %s", (target_id,))
            owner_row = await cur.fetchone()
            if not owner_row:
                await bot.edit_message_text(
                    "❌ Не найдено данных для создателя.",
                    chat_id=load.chat.id,
                    message_id=load.message_id
                )
                return
            await handle_clan_show(cur, load, callback, bot, owner_row)
        else:
            await bot.answer_callback_query(
                callback.id,
                "⛔️ Неверная опция!",
                show_alert=True
            )
            await bot.delete_message(
                chat_id=load.chat.id,
                message_id=load.message_id
            )

        await bot.answer_callback_query(callback.id)

    except Exception as e:
        await bot.send_message(
            callback.message.chat.id,
            f"❌ Произошла ошибка!\n<code>{e}</code>",
            parse_mode="HTML"
        )
        raise e


@dp.callback_query(lambda c: c.data.startswith('profile'))
@with_db(lambda c: c.message.chat.type != "private")
async def profile_handler(cur, load: Message, callback: CallbackQuery):
    try:
        assert callback.from_user is not None
        target_id = int(callback.data.split('_')[1])
        load = callback.message if callback.message.chat.type == "private" else load
        await cur.execute("SELECT name, id, cash, isvip, videocards, clan, tag, bitcoins FROM users WHERE id = %s",
                          (target_id,))
        user = await cur.fetchone()

        if not user:
            await load.reply(
                "❌ У этого пользователя нет аккаунта!",
                allow_sending_without_reply=True
            )
            return

        if user["clan"] == 0:
            current_clan = "отсутствует"
        else:
            await cur.execute("SELECT name FROM clans WHERE owner=  %s", (user["clan"],))
            clan_data = await cur.fetchone()
            current_clan = clan_data["name"] if clan_data else "нет"

        invite_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✉️ Пригласить в клан", callback_data=f"clan_invite_{user['id']}")]
            ] if user["clan"] == 0 else [
                [InlineKeyboardButton(text=f"🏰 {current_clan}", callback_data=f"clan_show_info_{user["clan"]}")]
            ]
        )

        link = hlink(user["name"], f'tg://user?id={user['id']}')

        await bot.edit_message_text(
            profile_text(link, hbold, user, current_clan),
            chat_id=load.chat.id,
            message_id=load.message_id,
            parse_mode="HTML",
            reply_markup=invite_keyboard
        )
        await bot.answer_callback_query(callback.id)

    except Exception as e:
        await bot.send_message(
            callback.message.chat.id,
            f"❌ Произошла ошибка!\n<code>{e}</code>",
            parse_mode="HTML"
        )
        raise e
# endregion


async def shutdown():
    await bot.session.close()
    tasks = [t for t in all_tasks() if t is not current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except CancelledError:
            pass


def signal_handler():
    loop = get_event_loop()
    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, lambda: create_task(shutdown()))


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    signal_handler()

    background_task = create_task(rate_update_loop())

    try:
        await dp.start_polling(bot)
    except CancelledError:
        pass
    finally:
        background_task.cancel()
        try:
            await background_task
        except CancelledError:
            pass
        await shutdown()


if __name__ == '__main__':
    try:
        async_run(main())
    except CancelledError:
        pass
