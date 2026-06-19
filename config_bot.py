from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import dotenv_values

config = dotenv_values(".env")

TOKEN = config['token']
OWNER_ID = int(config['admin_id']) # type: ignore

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) # type: ignore

dp = Dispatcher()