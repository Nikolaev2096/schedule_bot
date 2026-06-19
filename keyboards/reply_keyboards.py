from typing import List

from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import  KeyboardButton


async def universal_reply_keyboard(array : List, quantity: int, placeholder: str):
    """
    Создание reply клавиатуры с универсальными значениями

    Args:
        array: список значений, который будет использован в качестве клавиатуры
        quantity : количество рядов клавиатуры
        placeholder: текст, который заменит штатное "сообщение...."

    """

    keyboard = ReplyKeyboardBuilder()
    for i in array:
        keyboard.add(KeyboardButton(text = i))

    return keyboard.adjust(quantity).as_markup(
        input_field_placeholder=placeholder,
        one_time_keyboard=True)