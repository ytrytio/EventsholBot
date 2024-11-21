from pathlib import Path
from aiogram.types import LabeledPrice

__all__ = ["bot_path", "log_file", "event_coin_file", "dialog_flow_file", "slot_machine_multipliers",
           "emoji_multipliers", "MESSAGE_LIMIT", "TIME_FRAME", "max_videocards", "farming_timers",
           "vip_rangs", "prices", "factor", "commands", "multiplies", "clan_types", "indexes"]

bot_path: Path = Path(__file__).parent.parent
log_file: Path = bot_path / "log.txt"
event_coin_file: Path = bot_path / "rate"
dialog_flow_file: Path = bot_path / "dialog_flow.json"

MESSAGE_LIMIT = 1
TIME_FRAME = 5
slot_machine_multipliers = {
    1: 3.5,  # ("bar",   "bar",   "bar")
    2: 0.5,  # ("grape", "bar",   "bar")
    3: 0.5,  # ("lemon", "bar",   "bar")
    4: 1.0,  # ("seven", "bar",   "bar")
    5: 0.5,  # ("bar",   "grape", "bar")
    6: 1.0,  # ("grape", "grape", "bar")
    7: 0.5,  # ("lemon", "grape", "bar")
    8: 1.0,  # ("seven", "grape", "bar")
    9: 0.5,  # ("bar",   "lemon", "bar")
    10: 0.5,  # ("grape", "lemon", "bar")
    11: 0.5,  # ("lemon", "lemon", "bar")
    12: 0,  # ("seven", "lemon", "bar")
    13: 0.5,  # ("bar",   "seven", "bar")
    14: 0.5,  # ("grape", "seven", "bar")
    15: 0,  # ("lemon", "seven", "bar")
    16: 2.0,  # ("seven", "seven", "bar")
    17: 0.5,  # ("bar",   "bar",   "grape")
    18: 0,  # ("grape", "bar",   "grape")
    19: 0,  # ("lemon", "bar",   "grape")
    20: 1.0,  # ("seven", "bar",   "grape")
    21: 0.5,  # ("bar",   "grape", "grape")
    22: 2.0,  # ("grape", "grape", "grape")
    23: 0.5,  # ("lemon", "grape", "grape")
    24: 1.0,  # ("seven", "grape", "grape")
    25: 0,  # ("bar",   "lemon", "grape")
    26: 0.5,  # ("grape", "lemon", "grape")
    27: 1.5,  # ("lemon", "lemon", "grape")
    28: 0.5,  # ("seven", "lemon", "grape")
    29: 0,  # ("bar",   "seven", "grape")
    30: 0.5,  # ("grape", "seven", "grape")
    31: 0,  # ("lemon", "seven", "grape")
    32: 2.0,  # ("seven", "seven", "grape")
    33: 0.5,  # ("bar",   "bar",   "lemon")
    34: 0.5,  # ("grape", "bar",   "lemon")
    35: 0.5,  # ("lemon", "bar",   "lemon")
    36: 1.0,  # ("seven", "bar",   "lemon")
    37: 0,  # ("bar",   "grape", "lemon")
    38: 0.5,  # ("grape", "grape", "lemon")
    39: 0.5,  # ("lemon", "grape", "lemon")
    40: 0,  # ("seven", "grape", "lemon")
    41: 0,  # ("bar",   "lemon", "lemon")
    42: 0,  # ("grape", "lemon", "lemon")
    43: 1.5,  # ("lemon", "lemon", "lemon")
    44: 0.5,  # ("seven", "lemon", "lemon")
    45: 0.5,  # ("bar",   "seven", "lemon")
    46: 0,  # ("grape", "seven", "lemon")
    47: 0.5,  # ("lemon", "seven", "lemon")
    48: 2.0,  # ("seven", "seven", "lemon")
    49: 1.5,  # ("bar",   "bar",   "seven")
    50: 0,  # ("grape", "bar",   "seven")
    51: 0,  # ("lemon", "bar",   "seven")
    52: 2.0,  # ("seven", "bar",   "seven")
    53: 0,  # ("bar",   "grape", "seven")
    54: 0.5,  # ("grape", "grape", "seven")
    55: 0,  # ("lemon", "grape", "seven")
    56: 1.0,  # ("seven", "grape", "seven")
    57: 0,  # ("bar",   "lemon", "seven")
    58: 0.5,  # ("grape", "lemon", "seven")
    59: 1.5,  # ("lemon", "lemon", "seven")
    60: 0,  # ("seven", "lemon", "seven")
    61: 1.5,  # ("bar",   "seven", "seven")
    62: 0,  # ("grape", "seven", "seven")
    63: 0.5,  # ("lemon", "seven", "seven")
    64: 10.0  # ("seven", "seven", "seven")
}
emoji_multipliers = {
    1: 0,
    2: 0.5,
    3: 1.0,
    4: 1.0,
    5: 1.5,
    6: 2.0
}

clan_type = ("Закрытый", "Открытый")
decor_clan_type = ("🔒", "🔓")

factor = 10000

max_videocards = (
    250,
    500,
    750,
)

farming_timers = (
    7200,
    3600,
    1800,
)

vip_rangs = (
    "Отсутствует",
    "VIP",
    "PLUS",
    "ULTRA",
    "QUANTUM",
    "PREMIUM",
)

multiplies = (
    1,
    2,
    4,
    1.5
)

clan_types = ("🔒", "🔓")

indexes = (
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
    "🔟"
)

prices = [
    LabeledPrice(label='50 видеокарт', amount=100),
    LabeledPrice(label='100 видеокарт', amount=200),
    LabeledPrice(label='250 видеокарт', amount=500),
    LabeledPrice(label='500 видеокарт', amount=1000),
]

commands = (
    "/start - выводит меню бота.",
    "/cash - выводит состояние вашего счета.",
    "/farming - позволяет заработать деньги.",
    "/rich_top - выводит топ 10 самых богатых пользователей.",
    "/crypto_top - выводит топ 10 самых богатых криптомайнеров.",
    "/ping - выводит задержку бота.",
    "/shop - выводит магазин.",
    "/profile - показывает профиль (писать ответом).",
    "/my_clan - показать информацию о вашем клане.",
    "/clans - покажет топ богатых кланов.",
    "/give_c - передать деньги пользователю (писать ответом).",
    "/give_v - передать видеокарты пользователю (писать ответом).",
    "/post_sub - отписаться/подписаться на рассылку из канала.",
    "/code {код} - превратит кучку текста в красивый дизайн с кодом.",
    "/rate - вывести курс EventCoin.",
    "/buyCrypto {число} - купить EventCoin по курсу.",
    "/sellCrypto {число} - продать EventCoin по курсу.",
)
