from aiogram.types import Message
from aiogram import F, Router
from aiogram.types import ReplyKeyboardRemove

import keyboards.inline_keyboards as in_kb
from templates.txt_templates import *

router_abitur = Router()

@router_abitur.message(F.text == "🌐 Сайт колледжа")
async def abitur_site(message: Message):
    await message.answer(kb_hide_text, reply_markup= ReplyKeyboardRemove())
    await message.answer(

        "***🌐 Сайт:***\n[Официальный сайт колледжа](https://rguts.ru)",
        parse_mode="Markdown",  
        disable_web_page_preview=True, 
        reply_markup= await in_kb.menu_inline_kb())
    
@router_abitur.message(F.text == "☎️ Контактный телефон")
async def abitur_phone(message: Message):
    await message.answer(kb_hide_text, reply_markup= ReplyKeyboardRemove())
    await message.answer(contact_phones,
                         parse_mode="Markdown", 
                         reply_markup= await in_kb.menu_inline_kb())

@router_abitur.message(F.text == "ℹ️ Соцсети колледжа")
async def abitur_social(message: Message):
    await message.answer(kb_hide_text, reply_markup= ReplyKeyboardRemove())
    await message.answer(social_networks,
    parse_mode="MarkdownV2",
    disable_web_page_preview=True,
    reply_markup=await in_kb.menu_inline_kb()
)
@router_abitur.message(F.text == "📍 Адрес колледжа")
async def abitur_address(message: Message):
    await message.answer(kb_hide_text, reply_markup= ReplyKeyboardRemove())
    await message.answer(college_address, 
                        disable_web_page_preview=True, 
                        parse_mode="Markdown", 
                        reply_markup= await in_kb.menu_inline_kb())
