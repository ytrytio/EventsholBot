from collections.abc import Awaitable, Callable
from aiogram import Bot
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hbold, hlink
from aiopg import create_pool, Cursor
from datetime import datetime, timedelta
from aiofiles import open as aiopen
from time import time as unixtime
from dotenv import dotenv_values
from psycopg2.extras import DictCursor
from re import sub, escape
from functools import wraps
from asyncio import sleep as asleep
from asyncio import CancelledError

from .vars import log_file, event_coin_file, slot_machine_multipliers, emoji_multipliers, MESSAGE_LIMIT, TIME_FRAME
from .types import Any
from .strings import profile_text, clan_text, profile_clan_keyboard, clan_peoples_keyboard, clan_owner_keyboard

__all__ = ["logf", "with_db", "check_account", "format_num", "format_time", "filter_dict", "text2mdv2",
           "read_eventcoin", "parse_bid_and_dice", "validate_bid", "validate_dice_value", "send_error_reply",
           "check_flood_wait", "get_result", "get_emoji", "set_clan_budget", "set_clan_type", "set_clan_name",
           "handle_clan_set", "handle_clan_show", "get_clan_members", "write_eventcoin", "rate_update_loop",
           "ecoin_to_bucks", "bucks_to_ecoin"]

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
            (id, mention, name, cash, last_farming_time, isvip, farmLimit, videocards, viruses, stopFarm, attacker, clan, goldfevervalue, posting, bitcoins, tag) 
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user.id, "", user.first_name, 20000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            1, "[ИГРОК]"
        ))

    return True


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
        "/spin": "🎰", "спин": "🎰"
    }
    return emoji_map.get(command, "")


async def get_result(emoji, value, bid, balance):
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
            nb = result
            obt = f"🍀 *Везение!* 🎉\n\nВы выиграли: *+{format_num(result)}* 💵\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 2.0:
            nb = result
            obt = f"🤠 *Выигрыш!* 🎊\n\nВы получили: *+{format_num(result)}* 💸\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 3.5:
            nb = result
            obt = f"🏆 *Крупный выигрыш!* 🎊\n\nВы получили: *+{format_num(result)}* 💸\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"
        case 10.0:
            nb = result
            obt = f"🤑 *ДЖЕКПОТ!* 🚀\n\nВы выиграли: *+{format_num(result)}* 🤑\n\n💰 Ваш баланс теперь: {format_num(balance + nb)}💸"

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
