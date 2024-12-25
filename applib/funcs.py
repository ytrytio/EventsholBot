from collections.abc import Awaitable, Callable
from aiogram import Bot
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hbold, hlink
from aiopg import create_pool, Cursor
from datetime import datetime, timedelta
from aiofiles import open as aiopen
from time import time as unixtime
from random import random, choice, sample, randint
from dotenv import dotenv_values
from psycopg2.extras import DictCursor
from re import sub, escape
from functools import wraps
from asyncio import sleep as asleep
from asyncio import CancelledError
from uuid import uuid4
import json

from .vars import (
    log_file, event_coin_file, slot_machine_multipliers, emoji_multipliers, MESSAGE_LIMIT, TIME_FRAME, global_quests
)

from .types import Any
from .strings import profile_text, clan_text, profile_clan_keyboard, clan_peoples_keyboard, clan_owner_keyboard

__all__ = [
    "logf", "with_db", "check_account", "format_num", "format_time", "filter_dict", "text2mdv2",
    "read_eventcoin", "parse_bid_and_dice", "validate_bid", "validate_dice_value", "send_error_reply",
    "check_flood_wait", "get_result", "get_emoji", "set_clan_budget", "set_clan_type", "set_clan_name",
    "handle_clan_set", "handle_clan_show", "get_clan_members", "write_eventcoin", "rate_update_loop",
    "ecoin_to_bucks", "bucks_to_ecoin", "sum_videocards", "generate_event_tokens", "is_admin",
    "generate_quests", "generate_quests_for_users", "update_quest", "get_quests"
]

secrets: dict[str, str | None] = dotenv_values('.env')

user_flood_data = {}


async def logf(err: str | Exception, warn: int = 0, prints: bool = True):
    """Log.
    `txt` - error text.
    `warn` - warning level (0 - info, 1 - warning, 2 - error).
    """

    warn_level = 'IWE'[warn]
    if prints:
        if isinstance(err, str):
            print(err)
        elif isinstance(err, Exception):
            raise err  # print(f"{err.args}\n\n{err}")
    async with aiopen(log_file, 'a') as f:
        await f.write(f'[{warn_level}]-{unixtime()}:\n{err!s}\n\n')


def with_db(send_load: bool | Callable[..., bool]):
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:

        @wraps(func)
        async def wrapped(*args: list[Any], **kwargs: dict[str, Any]) -> Any:
            message = None
            loading = None
            should_send_load = send_load
            if callable(send_load):
                should_send_load = send_load(*args, **kwargs)

            if should_send_load:
                for arg in args:
                    if isinstance(arg, Message):
                        message = arg
                        break
                    elif isinstance(arg, CallbackQuery):
                        message = arg.message
                        break

                if message:
                    loading = await message.reply(
                        '🔄 *Загрузка...*',
                        allow_sending_without_reply=True,
                        parse_mode='markdown'
                    )

            async with create_pool(
                    host=secrets["POSTGRES_HOST"],
                    port=secrets["POSTGRES_PORT"],
                    user=secrets["POSTGRES_USER"],
                    password=secrets["POSTGRES_PASSWORD"],
                    database=secrets["POSTGRES_DATABASE"]
            ) as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor(cursor_factory=DictCursor) as cursor:
                        try:
                            return await func(cursor, loading, *args, **kwargs)
                        except Exception as e:
                            await logf(
                                f"Error in {func.__name__}({', '.join((f'{i!r}' for i in args))}): {str(e)}",
                                2
                            )
                            raise e

        return wrapped

    return decorator


async def check_account(cur: Cursor, *args: Any) -> bool:
    message = None
    query = None
    user = None
    for arg in args:
        if isinstance(arg, Message):
            message = arg
            user = message.from_user
            break
        elif isinstance(arg, PreCheckoutQuery):
            query = arg
            user = query.from_user
            break
        elif isinstance(arg, CallbackQuery):
            query = arg
            user = query.from_user
            break

    assert user is not None

    await cur.execute("SELECT id FROM users WHERE id = %s", (user.id,))
    db_id = await cur.fetchone()

    if db_id is None:
        profile_link = f"<a href=\"tg://user?id={user.id}\">{user.first_name}</a>"

        await cur.execute("""
            INSERT INTO users 
            (id, mention, name, cash, last_farming_time, isvip, "farmLimit", videocards, viruses, "stopFarm", attacker,
            clan, event, posting, bitcoins, tag, password, registered, level) 
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user.id, "", user.first_name, 20000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1, "[ИГРОК]", 0, 0
        ))

    return True


async def is_admin(user_id: int) -> bool:
    admin_ids = [1432248216]
    return user_id in admin_ids


def sum_videocards(amount: int, gpus: int, factor: float):
    base_cost = 50000
    total_cost = (base_cost * amount) + (gpus * factor)
    return total_cost


def format_time(seconds: float):
    return datetime.fromtimestamp(seconds).time().isoformat('seconds')


def format_num(num: float):
    whole, fraction = f"{num:.1f}".split(".")
    whole_with_dots = f"{int(whole):,}".replace(",", ".")
    return f"{whole_with_dots},{fraction}"


def filter_dict(prices, prefix):
    for price in prices:
        if price.label.startswith(prefix):
            return price
    return None


def text2mdv2(text):
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return sub(f"([{escape(special_chars)}])", r"\\\1", text)


async def ecoin_to_bucks(value: int) -> float:
    rate, _ = await read_eventcoin()
    return value * rate


async def bucks_to_ecoin(value: int) -> float:
    rate, _ = await read_eventcoin()
    return value / rate


async def read_eventcoin() -> tuple[float, float]:
    """
    Считывает курс и количество произведённых монет из файла.
    Возвращает (курс, произведённые монеты).
    """
    try:
        async with aiopen(event_coin_file, 'r') as f:
            data = await f.read()
            rate, farmed_amount = map(float, data.split(':'))
        return rate, farmed_amount
    except FileNotFoundError:
        return 1000.0, 0.0
    except Exception as e:
        await logf(f'Ошибка при чтении файла {event_coin_file}:\n{e}')
        raise e


async def write_eventcoin(rate: float, farmed_amount: float):
    """
    Записывает курс и количество произведённых монет в файл.
    """
    async with aiopen(event_coin_file, 'w') as f:
        await f.write(f"{rate}:{farmed_amount}")


async def update_rate():
    """
    Обновляет курс на основе общего количества произведённых монет.
    Изменение курса ограничено, чтобы избежать сильных колебаний.
    """
    current_rate, farmed_amount = await read_eventcoin()
    print("1", current_rate, farmed_amount)

    course_change = farmed_amount * 0.0000001
    print("2", course_change)

    max_course_change = current_rate * 0.01
    print("3", max_course_change)

    course_change = min(course_change, max_course_change)
    course_change = max(course_change, -max_course_change)
    print("4", course_change)

    current_rate += course_change
    print("5", current_rate)

    current_rate = max(1.0, current_rate)
    print("6", current_rate)

    current_rate = round(current_rate, 2)

    print(f"Текущий курс: {current_rate}, Изменение: {course_change}")

    await write_eventcoin(current_rate, 0.0)

    return current_rate


async def rate_update_loop():
    try:
        while True:
            await asleep(3600)
            await update_rate()
    except CancelledError:
        raise


async def parse_bid_and_dice(message: Message) -> tuple[int, int] | None:
    try:
        bid = int(message.text.split(' ')[1])
        dice_value = int(message.text.split(' ')[2])
        return bid, dice_value
    except (IndexError, ValueError):
        return None


async def validate_bid(bid: int, balance: float) -> bool:
    return 10 <= bid <= balance


async def validate_dice_value(dice_value: int) -> bool:
    return 1 <= dice_value <= 6


async def send_error_reply(message: Message, error_text: str, usage_example: str):
    await message.reply(
        f"{error_text}\nИспользование: `{usage_example}`",
        allow_sending_without_reply=True,
        parse_mode="markdown"
    )


async def check_flood_wait(user_id):
    now = datetime.now()
    if user_id in user_flood_data:
        user_data = user_flood_data[user_id]
        user_data['count'] += 1
        if now - user_data['last_message'] <= timedelta(seconds=TIME_FRAME):
            if user_data['count'] > MESSAGE_LIMIT:
                return True
        else:
            user_flood_data[user_id] = {'count': 1, 'last_message': now}
    else:
        user_flood_data[user_id] = {'count': 1, 'last_message': now}
    return False


async def get_emoji(command):
    command = command.lower()
    emoji_map = {
        "/basketball": "🏀", "баскетбол": "🏀",
        "/darts": "🎯", "дартс": "🎯",
        "/football": "⚽", "футбол": "⚽",
        "/bowling": "🎳", "боулинг": "🎳",
        "/dice": "🎲", "кубик": "🎲", "кость": "🎲",
        "/spin": "🎰", "спин": "🎰", "казино": "🎰"
    }
    return emoji_map.get(command, "")


async def get_result(emoji, value, bid, balance, user_id):
    obt = ""
    nb = 0
    if emoji == "🎰":
        multiplier = slot_machine_multipliers[value]
    else:
        multiplier = emoji_multipliers[value]
    result = bid * multiplier
    match multiplier:
        case 0:
            nb = -bid
            obt = f"🎲 *Проигрыш!* 🔻\n\nВы потеряли: *-{format_num(bid)}* 💔\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 0.5:
            nb = -result
            obt = f"🎰 *Невезение!* 😔\n\nВы потеряли: *-{format_num(result)}* 💔\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 1:
            nb = 0
            obt = f"⚖️ *Нейтраль!* 🤷‍♂️\n\nВаша ставка осталась при вас.\n\n💰 Ваш баланс: {format_num(balance + nb)}💸"
        case 1.5:
            nb = result - bid
            obt = f"🍀 *Везение!* 🎉\n\nВы выиграли: *+{format_num(result)}* 💵\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 2.0:
            nb = result - bid
            obt = f"🤠 *Выигрыш!* 🎊\n\nВы получили: *+{format_num(result)}* 💸\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 3.5:
            nb = result - bid
            obt = f"🏆 *Крупный выигрыш!* 🎊\n\nВы получили: *+{format_num(result)}* 💸\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 10.0:
            nb = result - bid
            obt = f"🤑 *ДЖЕКПОТ!* 🚀\n\nВы выиграли: *+{format_num(result)}* 🤑\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
            await update_quest(user_id, "gambling", 1)

    await update_quest(user_id, "spent", bid)

    return obt, nb


@with_db(False)
async def handle_clan_set(cur, load: Message, callback: CallbackQuery, clan_row: dict, bot: Bot, owner: dict):
    """Функция для настройки клана (доступ только владельцу клана)"""
    if callback.from_user.id != clan_row["owner"]:
        await bot.answer_callback_query(
            callback.id,
            "⛔️ Только создатель клана может изменять настройки.",
            show_alert=True
        )
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📇 Изменить название", callback_data="clan_set_name")],
        [InlineKeyboardButton(text="🔒 Изменить тип", callback_data="clan_set_type")],
        [InlineKeyboardButton(text="💰 Пополнить бюджет", callback_data="clan_set_budget")]
    ])

    await bot.edit_message_text(
        f"⚙️ Настройки клана '{clan_row['name']}':",
        chat_id=load.chat.id,
        message_id=load.message_id,
        reply_markup=markup,
        parse_mode='HTML'
    )


@with_db(False)
async def get_clan_members(cur: Cursor, load: None, clan_id):
    """Получает список ID и имен участников клана по его ID."""
    await cur.execute("SELECT id, name FROM users WHERE clan = %s", (clan_id,))
    rows = await cur.fetchall()
    members = [{"id": row[0], "name": row[1]} for row in rows]
    return members


async def handle_clan_show(cur, load: Message, callback: CallbackQuery, bot: Bot, owner: dict):
    """Отображает информацию о клане или пользователе в зависимости от опции."""
    from .strings import clan_keyboard
    option, target_id = callback.data.split("_")[2], int(callback.data.split("_")[3])
    msg_text = None
    keyboard = None
    await cur.execute("SELECT * FROM clans WHERE owner = %s", (target_id,))
    clan_row = await cur.fetchone()
    if not clan_row:
        await bot.edit_message_text("❌ Клан не найден.", chat_id=load.chat.id, message_id=load.message_id)
        return

    if option in ["member", "owner"]:
        await cur.execute("SELECT name, id, cash, videocards, isvip, tag, bitcoins FROM users WHERE id = %s",
                          (target_id,))
        user_row = await cur.fetchone()

        if not user_row:
            await bot.edit_message_text(
                "❌ Не найдено данных для пользователя.",
                chat_id=load.chat.id,
                message_id=load.message_id
            )
            return

        link = hlink(user_row["name"], f'tg://user?id={user_row["id"]}')
        msg_text = profile_text(link, hbold, user_row, clan_row["name"])

        keyboard = profile_clan_keyboard(target_id, user_row['id'],
                                         InlineKeyboardButton) if option == "member" else clan_owner_keyboard(owner,
                                                                                                              InlineKeyboardButton)

    else:
        await cur.execute("SELECT name, id FROM users WHERE id = %s", (clan_row["owner"],))
        owner_row = await cur.fetchone()
        if not owner_row:
            await bot.edit_message_text(
                "❌ Не найдено данных для владельца.",
                chat_id=load.chat.id,
                message_id=load.message_id)
            return

        owner_link = hlink(owner_row["name"], f'tg://user?id={owner_row["id"]}')
        members = await get_clan_members(clan_id=clan_row['owner'])
        if option == "info":
            msg_text = clan_text(clan_row, owner_link, members)
            keyboard = clan_keyboard(clan_row, InlineKeyboardButton)

        elif option == "peoples":
            msg_text = f"👥 <b>Участники клана</b> {clan_row['name']}\n#️⃣ <b>Количество:</b> {len(members)}\n"
            keyboard = clan_peoples_keyboard(clan_row["owner"], members, InlineKeyboardButton)

    await bot.edit_message_text(
        text=msg_text,
        chat_id=load.chat.id,
        message_id=load.message_id,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


async def set_clan_name(cur, callback: CallbackQuery, new_name: str, bot: Bot):
    """Изменение названия клана"""
    await cur.execute("UPDATE clans SET name = %s WHERE owner = %s", (new_name, callback.from_user.id))
    await bot.send_message(callback.message.chat.id, f"✅ Название клана успешно изменено на {new_name}.")


async def set_clan_type(cur, callback: CallbackQuery, bot: Bot):
    """Переключает тип клана с закрытого на открытый и наоборот"""
    await cur.execute("SELECT type FROM clans WHERE owner = %s", (callback.from_user.id,))
    clan_row = await cur.fetchone()
    new_type = 0 if clan_row['type'] == 1 else 1

    await cur.execute("UPDATE clans SET type = %s WHERE owner = %s", (new_type, callback.from_user.id))
    await bot.answer_callback_query(
        callback.id,
        f"✅ Тип клана успешно изменен! {'Закрытый' if new_type == 0 else 'Открытый'}",
        show_alert=True
    )


async def set_clan_budget(cur, callback: CallbackQuery, amount: int, bot: Bot):
    """Пополнение бюджета клана"""
    await cur.execute("SELECT cash FROM users WHERE id = %s", (callback.from_user.id,))
    user = await cur.fetchone()

    if user["cash"] < amount:
        await bot.send_message(callback.message.chat.id, "❌ Недостаточно средств для пополнения бюджета.")
        return

    await cur.execute("UPDATE clans SET money = money + %s WHERE owner = %s", (amount, callback.from_user.id))
    await cur.execute("UPDATE users SET cash = cash - %s WHERE id = %s", (amount, callback.from_user.id))
    await bot.send_message(callback.message.chat.id, f"✅ Бюджет клана пополнен на {amount}$!")


def generate_event_tokens(user_level: int, boost: float) -> int:
    if user_level == 0:
        return 0

    min_tokens = 3 + user_level
    max_tokens = 6 + user_level * 2

    total = randint(min_tokens, max_tokens)
    total += total * boost

    return total


@with_db(False)
async def generate_quests(cur: Cursor, loading: None) -> None:
    await cur.execute("DELETE FROM quests")
    for quest in global_quests:
        name = quest["name"]
        description = quest["description"]
        action = quest["action"]
        difficulty = choice(quest["difficulty"])
        difficulty_index = quest["difficulty"].index(difficulty)
        reward = quest["reward"][difficulty_index]

        await cur.execute(
            """
            INSERT INTO quests
            (name, description, action, difficulty, reward)
            VALUES
            (%s, %s, %s, %s, %s)
            """,
            (name, description, action, difficulty, reward)
        )


@with_db(False)
async def generate_quests_for_users(cur: Cursor, loading: None) -> None:
    await cur.execute("DELETE FROM user_quests")

    await generate_quests()

    await cur.execute("SELECT id FROM users")
    all_users = await cur.fetchall()

    await cur.execute("SELECT id, name, description, action, difficulty, reward FROM quests")
    all_quests = await cur.fetchall()

    insert_values = []
    for user in all_users:
        user_id = user["id"]
        for quest in all_quests:
            quest_id = quest["id"]
            insert_values.append(f"({user_id}, {quest_id}, 0, FALSE)")

    if insert_values:
        insert_query = f"""
        INSERT INTO user_quests (user_id, quest_id, progress, is_completed)
        VALUES {','.join(insert_values)};
        """
        await cur.execute(insert_query)


@with_db(False)
async def update_quest(cur: Cursor, load: None, user_id: int, action: str, value: int):
    await cur.execute(
        """
        SELECT uq.progress, uq.is_completed, q.difficulty, q.id as quest_id
        FROM user_quests uq
        JOIN quests q ON uq.quest_id = q.id
        WHERE uq.user_id = %s AND q.action = %s
        """,
        (user_id, action)
    )
    user_quest = await cur.fetchone()

    if not user_quest:
        return

    progress = user_quest["progress"]
    completed = user_quest["is_completed"]
    difficulty = user_quest["difficulty"]
    quest_id = user_quest["quest_id"]

    if not completed and progress + value >= difficulty:
        progress = difficulty
        completed = True
    elif not completed and progress + value < difficulty:
        progress += value

    await cur.execute(
        "UPDATE user_quests SET progress=%s, is_completed=%s WHERE user_id=%s AND quest_id=%s",
        (progress, completed, user_id, quest_id)
    )


@with_db(False)
async def get_quests(cur: Cursor, load: None, user_id: int, link: str):
    await cur.execute("SELECT * FROM quests")
    all_quests = await cur.fetchall()

    quests_info = f"""
    📆 Доступные квесты для {link}:

    <blockquote expandable>🌍 <b>Ежедневные квесты:</b>

    Просмотреть / Скрыть
    """

    for quest in all_quests:
        quest_id = quest["id"]
        name = quest["name"]
        description = quest["description"]
        action = quest["action"]
        difficulty = quest["difficulty"]
        reward = quest["reward"]

        await cur.execute(
            "SELECT progress, is_completed FROM user_quests WHERE user_id=%s AND quest_id=%s",
            (user_id, quest_id)
        )
        user_quest = await cur.fetchone()

        if not user_quest:
            continue

        progress = user_quest["progress"]
        completed = user_quest["is_completed"]

        quests_info += f"""
    {name}
    ┣━ 🧾 {description.format(format_num(difficulty) if action == "spent" else difficulty)}
    ┣━ 🎁 Награда: {reward} ❄️
    ┣━ 📊 Прогресс: {format_num(progress) if action == "spent" else progress}/{format_num(difficulty) if action == "spent" else difficulty}
    ┗━ ✳️ Готовность: {"✅ Выполнен" if completed else "❌ Не выполнен"}\n
    """

    quests_info += "</blockquote>"

    return quests_info
