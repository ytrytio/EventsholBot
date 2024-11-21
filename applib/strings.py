from .vars import vip_rangs, clan_types, indexes

__all__ = [
    "start_text", "balance_text", "farm_text_failure", "farm_text_success", "donate_text", "videocards_text_select",
    "profile_text", "clans_text",

    "start_keyboard", "donate_keyboard", "shop_keyboard", "videocards_keyboard", "clan_keyboard",
    "profile_clan_keyboard", "clans_keyboard", "clan_peoples_keyboard", "clan_owner_keyboard"
]


def start_keyboard(InlineKeyboardButton):
    keyboard = [
        [
            InlineKeyboardButton(
                text='📲 Команды',
                callback_data='commands'),
            InlineKeyboardButton(
                text='👾 РП-команды',
                url='https://t.me/eventshol_live/78'),
        ],
        [
            InlineKeyboardButton(
                text='➕ Добавить бота в группу',
                url='https://t.me/eventshol_bot?startgroup'),
        ],
        [
            InlineKeyboardButton(
                text='📣 Канал бота',
                url='https://t.me/eventshol_live'),
            InlineKeyboardButton(
                text='💬 Группа бота',
                url='https://t.me/eventshol_chat')
        ],
        [
            InlineKeyboardButton(
                text='👮 Политика конфиденциальности',
                url='https://teletype.in/@eventshol/privacy-policy')
        ]
    ]
    return keyboard


def shop_keyboard(InlineKeyboardButton, ecoin):
    keyboard = [
        [
            InlineKeyboardButton(
                text='🖥 Видеокарты',
                callback_data='buyvid')
        ],
        [
            InlineKeyboardButton(
                text='⭐️ VIP - 1М$',
                callback_data='pass_plus'),
            InlineKeyboardButton(
                text='➕ PLUS - 50М$',
                callback_data='pass_plus')
        ],
        [
            InlineKeyboardButton(
                text='🌟 ULTRA - 500M$',
                callback_data='pass_ultra'),
            InlineKeyboardButton(
                text='💠 QUANTUM - 10B$',
                callback_data='pass_quantum')
        ],
        [
            InlineKeyboardButton(
                text=f'💸 Купить макс. кол-во ECoin (1₠ ≈ {round(ecoin, 2)}$)',
                callback_data='buy_max_ecoins')
        ],
        [
            InlineKeyboardButton(
                text=f'🏷️ Продать макс. кол-во ECoin (1₠ ≈ {round(ecoin, 2)}$)',
                callback_data='sell_max_ecoins')
        ],
        [
            InlineKeyboardButton(
                text='Как продать/купить определенное число ECoin?',
                callback_data='crypto_guide')
        ]
    ]
    return keyboard


def donate_keyboard(InlineKeyboardButton, prices):
    keyboard = [
        [
            InlineKeyboardButton(
                text=f'🖥 {prices[i].label}',
                callback_data=f"donatevid{prices[i].label.split(' ')[0]}"
            )
        ] for i in range(len(prices))
    ]
    return keyboard


def videocards_keyboard(InlineKeyboardButton, factor: float, gpus: int, user_id: int):
    from .funcs import format_num
    base_cost = 50000
    quantities = [1, 10, 25, 50, 100, 250]
    helpers = ['а', '', '', '', '', '']

    keyboard = []

    for i in range(len(quantities)):
        total_cost = (base_cost * quantities[i]) + (gpus * factor)
        keyboard.append([
            InlineKeyboardButton(
                text=f'🖥 {quantities[i]} видеокарт{helpers[i]} - {format_num(total_cost)}$',
                callback_data=f'buyvid_{quantities[i]}_{user_id}'
            )
        ])

    return keyboard


def clan_keyboard(clan, InlineKeyboardButton):
    inline_keyboard = [
        [InlineKeyboardButton(text="💰 Пополнить бюджет", callback_data="clan_set_budget")],
        [
            InlineKeyboardButton(text="👥 Участники", callback_data=f"clan_show_peoples_{clan['owner']}"),
            InlineKeyboardButton(text="👑 Владелец", callback_data=f"clan_show_owner_{clan['owner']}")
        ],
        [
            InlineKeyboardButton(text="📇 Сменить название", callback_data="clan_set_name"),
            InlineKeyboardButton(text="🔐 Сменить тип", callback_data="clan_set_type")
        ],
        [InlineKeyboardButton(text="⚔️ Клановая война", callback_data="clan_war")]
    ]
    return inline_keyboard


def profile_clan_keyboard(clan_id, user_id, InlineKeyboardButton):
    inline_keyboard = [
        [InlineKeyboardButton(text="🚷 Выгнать", callback_data=f"clan_kick_{user_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"clan_show_peoples_{clan_id}")]
    ]
    return inline_keyboard


def clans_keyboard(clans_row, InlineKeyboardButton):
    from .funcs import format_num
    keyboard = []
    for index, clan_data in enumerate(clans_row, start=1):
        name = clan_data[0]
        money = clan_data[1]
        clan_type = clan_data[2]
        owner_id = clan_data[3]

        button_text = f"{indexes[index - 1]} | {clan_types[clan_type]} | {name} - {format_num(money)}$"
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"clan_show_info_{owner_id}"
        )])
    return keyboard


def clan_peoples_keyboard(clan_id, members, InlineKeyboardButton):
    keyboard = [
        [InlineKeyboardButton(text=member['name'], callback_data=f"clan_show_member_{member['id']}")]
        for member in members
    ] + [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"clan_show_info_{clan_id}")]
    ]

    return keyboard


def clan_owner_keyboard(owner, InlineKeyboardButton):
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"clan_show_info_{owner['id']}")]
    ]
    return keyboard


def start_text(user_name: str):
    """Форматирует стартовый текст."""
    return f"""
✨ *Привет, {user_name}!*

🚀 *Выберите действие:* 
"""


def balance_text(cash: str, ecoins: str):
    """Форматирует текст баланса."""
    return f"""
✨💰 *Ваш Баланс* 💰✨

💵 *Деньги:* {cash}
💎 *ECoins:* {ecoins}

🚀 *Заработайте больше* с помощью команды /farming!
"""


def farm_text_failure(time: int):
    """Форматирует текст для статуса майнинг фермы в случае неудачи."""
    from .funcs import format_time
    return f"""
💸 *Статус Майнинг Фермы* 💸

✅ *Вы уже собирали доход с майнинг фермы!*  
⏳ *Следующий приход:* {format_time(time)}  

🚀 **Возвращайтесь позже!**
"""


def farm_text_success(ecoins: int, vip: str, videocards: str, multiplier: int):
    """Форматирует текст для успешного получения дохода от майнинга."""
    from .funcs import format_num
    return f"""
💰 *Доход от Майнинга* 💰

✨ *Вы получили:* {format_num(ecoins)} ₠  
🌟 *Ваш пропуск:* {vip}  
🖥 *Видеокарты:* {videocards}  
✖️ *Множитель:* {multiplier}  

🚀 *Возвращайтесь за новыми достижениями!*
"""


def donate_text():
    """Форматирует стартовый текст."""
    return f"""
🏪 *Донат-магазин* 🏪

🚀 *Выберите товар для покупки:* 
"""


def videocards_text_select(user):
    """Форматирует текст выбора видеокарт."""
    return f"""
💻 Покупка видеокарт 💻

❗ <i>️Цены и кнопки ниже предназначены только для {user}!</i>
🛒 Выберите ниже количество видеокарт для покупки:
"""


def profile_text(link, hbold, user, clan):
    from .funcs import format_num
    information = f"""
👤 {link}
<b>Профиль</b> пользователя {hbold(user['name'])}:

🏰 Клан: {hbold(clan)}
🏷 Префикс: {hbold(user['tag'])}
📇 Псевдоним: {hbold(user['name'])}
🆔 ID: {user['id']}
💵 Баланс: {format_num(user['cash'])}$
💳 ECoins: {format_num(user['bitcoins'])}₠
🖥 Видеокарты: {user['videocards']} шт.
🪪 Пропуск: {vip_rangs[user['isvip']]}
    """
    return information


def clans_text():
    return """
🏰 ТОП-10 самых богатых кланов 🏰

🔽 Нажмите на клан для его просмотра:
    """

# def videocards_buying_text():
#     return f"""
#
# """
