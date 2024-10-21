#!/usr/bin/env python3

from aiogram import Bot, Dispatcher, F
from aiogram.typesmport import Message
from aiogram.filters import Command

from asyncio import run as async_run
from time import time as unixtime
from dotenv import dotenv_values
from applib import logf, with_db
from pathlib import Path
from typing import Dict
from uuid import uuid4
from json import loads

from os import environ
from dialogflow import SessionsClient
from google.api_core.exceptions import InvalidArgument


with open(Path(__file__).parent/'dialog_flow.json') as f:
    environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dialog_flow.json"

    DIALOGFLOW_PROJECT_ID = "project_id"
    DIALOGFLOW_LANGUAGE_CODE = '[LANGUAGE]'
    SESSION_ID = 'me'


session_client = SessionsClient()


secrets: Dict[str, str] = dotenv_values('.env')
TOKEN: str = secrets["BOT_TOKEN"]

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

admins_id = [1432248216,1300210900]
credentials = require('./key.json')

sessionClient = SessionsClient({ credentials })
projectId = 'small-talk-rwvf'

vid250 = './250videocards.png'

clan_type = (
	"Закрытый",
	"Открытый"
)
decor_clan_type = (
	"🔒",
	"🔓"
)

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
  "Обычный VIP",
  "MEGAVIP",
  "PREMIUM",
)

multiplies = (
  1,
  2,
  4,
)

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

clans = (
  "отсутствует",
)

lastToId = 0


botReady = false
startTime = unixtime()
cooldownPeriod = 5000




@dp.message_handler(Command('start'))
async def start(message: Message):
    await message.reply('Hello!')


@dp.message_handler(F.text.lower() == 'привет')
async def start(message: Message):
    await message.reply('Hello!')


async_run(dp.start_polling())
