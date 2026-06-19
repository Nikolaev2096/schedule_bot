import re
from typing import List

from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.types import ReplyKeyboardRemove
from addons import weeks
from aiogram.fsm.context import FSMContext
from database.user_func import UserFunctions, Groups
from database.misc import GetDataFromSchedule 
from sqlalchemy.ext.asyncio import AsyncSession

from config_bot import OWNER_ID
from templates.txt_templates import *
from database.model import Users

from states import states as st
import keyboards.inline_keyboards as in_kb 
import keyboards.reply_keyboards as re_kb 

router_base = Router()

DAYS = ['Понедельник', 'Вторник', 'Среда','Четверг', 'Пятница', 'Суббота']

#---- Инициализация регистрации

@router_base.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start - начало регистрации пользователя
    """
    vis_name = message.from_user.first_name
    await state.set_state(st.Registration.start)
    await message.answer(
        reg_start_text.format(vis_name),
        reply_markup=await in_kb.init_reg()
    )

#---- Начало регистрации

@router_base.callback_query(F.data == 'start_setup', st.Registration.start)
async def start_setup(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(st.Registration.select_role)
    user_id = callback.from_user.id
   
    await UserFunctions.add_user(session, user_id)
    await callback.message.edit_text(reg_text,reply_markup=await in_kb.role_inline_kb())
    await callback.answer()

# ---- Выбор роли пользователя

@router_base.callback_query(F.data.startswith("set_role"), st.Registration.select_role)
async def process_set_role(callback: CallbackQuery, state:FSMContext, session: AsyncSession):
    user_id = callback.from_user.id
    await callback.answer()
    role = callback.data.split(":", 1)
    role = role[1]
    if role == "None":
        await state.clear()
        await UserFunctions.change_user_role(session, user_id, role)
        await callback.message.edit_text(reg_complete_without_role,
                                         reply_markup= await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)
    elif role == 'worker':
        await state.clear()
        await UserFunctions.change_user_role(session, user_id, role)
        await callback.message.edit_text(role_set_worker, reply_markup= await in_kb.menu_inline_kb())
    else:
        await callback.message.edit_text(
            role_set_user if role == 'user' else role_set_teacher)
        await UserFunctions.change_user_role(session, user_id, role)
        
        if role == 'user':
            await state.set_state(st.Registration.select_group)
            groups_list = await Groups.get_all_groups(session)
            await callback.message.answer(
                choose_group,
                reply_markup=await re_kb.universal_reply_keyboard(groups_list, 3, choose_group_ph)
            )
        elif role == 'teacher':
            await state.set_state(st.Registration.select_teacher)
            teachers_list = await GetDataFromSchedule.get_all_teachers(session)
            await callback.message.answer(
                choose_teach_name,
                reply_markup=await re_kb.universal_reply_keyboard(teachers_list, 2, choose_full_name_ph)
            )

#---- Проверка данных на валидность

@router_base.message(st.Registration.select_group)
async def done_student_reg(message, state: FSMContext, session: AsyncSession):
    '''
    Обработчик выбора группы студентом при регистрации
    '''
    cur_group = message.text
    user_id = message.from_user.id
    await state.set_state(st.Registration.wait_for_check)

    if await Groups.check_group(session, cur_group):
        await UserFunctions.change_user_group(session, user_id, cur_group)
        await message.answer(
            reg_complete_student.format(cur_group),
            reply_markup=await in_kb.base_reg_end()
        )
        await state.set_state(st.Registration.confirm_base_reg_state)
    else:
        await message.answer(group_select_error)
        await state.set_state(st.Registration.select_group)

@router_base.message(st.Registration.select_teacher)
async def done_teach_reg(message, state: FSMContext, session: AsyncSession):
    '''
    Обработчик выбора ФИО преподавателем при регистрации
    '''
    cur_teach = message.text
    await state.set_state(st.Registration.wait_for_check)

    user_id = message.from_user.id
    if await GetDataFromSchedule.check_teacher_exist(session, cur_teach):
        await UserFunctions.change_teacher_name(session, user_id, cur_teach)
        await message.answer(
            reg_complete_teacher.format(cur_teach),
            reply_markup=await in_kb.base_reg_end()
        )
        await state.set_state(st.Registration.confirm_base_reg_state)
    else:
        await message.answer(name_select_error)
        await state.set_state(st.Registration.select_teacher)

@router_base.callback_query(st.Registration.confirm_base_reg_state)
async def confirm_base_reg(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    '''
    Обработчик подтверждения базовой регистрации - переход к настройке уведомлений или меню
    '''
    data = callback.data
    await callback.answer()
    if data == 'time_set':
        await callback.message.answer(
            select_notif_type_text,
            reply_markup=await in_kb.select_sound()
        )
        await state.set_state(st.Registration.select_notif_type)
    else:
        await state.set_state(st.MenuState.menu)
        await show_menu(callback.from_user.id, callback.message, session)


@router_base.callback_query(st.Registration.select_notif_type)
async def time_input(callback: CallbackQuery, state: FSMContext):
    '''
    Обработчик выбора типа уведомления (со звуком/без звука) при регистрации
    '''
    data = callback.data
    await callback.answer()
    await state.set_state(st.Registration.insert_time)
    if data == 'sound':
        await state.update_data(notif_type=False)
        await callback.message.answer(input_notif_time_text)
    elif data == 'silent':
        await state.update_data(notif_type=True)
        await callback.message.answer(input_notif_time_text)
    else:
        await state.set_state(st.MenuState.menu)


@router_base.message(st.Registration.insert_time)
async def confirm_state(message: Message, state: FSMContext, session: AsyncSession):
    '''
    Обработчик ввода времени для уведомлений при регистрации
    '''
    time = message.text
    user_data = await state.get_data()
    sound = user_data['notif_type']
    valid = re.search(r"\d{2}:\d{2}", time)
    
    if valid:
        el1, el2 = time.split(':')
        if 0 <= int(el1) <= 23 and 0 <= int(el2) <= 59:
            notif_text = notif_silent_text if sound else notif_sound_text
            await message.answer(
                confirm_notif_settings.format(time, notif_text),
                reply_markup=await in_kb.confirm_sch()
            )
            await state.update_data(time=time)
            await state.set_state(st.Registration.continue_reg)
        else:
            await message.answer(invalid_time_format)
            await state.set_state(st.Registration.insert_time)
    else:
        await message.answer(invalid_time_format)
        await state.set_state(st.Registration.insert_time)

@router_base.callback_query(st.Registration.continue_reg)
async def end_of_reg(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    '''
    Обработчик завершения регистрации с сохранением настроек уведомлений
    '''
    data = callback.data
    user_data = await state.get_data()
    sound = bool(user_data['notif_type'])
    time = user_data['time']
    user_id = int(callback.from_user.id)
    await callback.answer()
    
    if data == 'confirm':
        await UserFunctions.insert_time_and_notification_type(session, user_id, time, sound)
        await callback.message.answer(notif_settings_saved)
        await state.clear()
        await show_menu(user_id, callback.message, session)
    else:
        await state.clear()
        await show_menu(user_id, callback.message, session)



#---- Обработка переходов в главное меню

@router_base.message(F.text == "🏠 Главное меню")
async def get_user_menu(message: Message, session: AsyncSession, state: FSMContext):
    '''
    Обработчик перехода в главное меню из текстового сообщения
    '''
    await state.set_state(st.MenuState.menu)
    await show_menu(message.from_user.id, message, session)


@router_base.callback_query(F.data == "menu")
async def callback_to_main_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Универсальный обработчик перехода в главное меню из inline-кнопки
    Работает из любого состояния FSM
    """
    await callback.answer()

    await state.clear()
  
    await state.set_state(st.MenuState.menu)
    await show_menu(callback.from_user.id, callback.message, session)


@router_base.callback_query(st.MenuState.menu)
async def user_menu(callback: CallbackQuery, session: AsyncSession):
    '''
    Обработчик перехода в главное меню из callback-кнопки в состоянии MenuState.menu
    '''
    await callback.answer()
    await show_menu(callback.from_user.id, callback.message, session)


async def show_menu(user_id: int, message: Message, session: AsyncSession):
    """
    Функция отображения главного меню в зависимости от роли пользователя

    Args:
        user_id: ID пользователя
        message: объект сообщения
        session: сессия БД
    """
    role = await UserFunctions.check_user_role(session, user_id)
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        keyboard = await re_kb.universal_reply_keyboard(menu_list_owner, 1, choose_menu_action_ph)
    elif role in ('user', 'teacher', 'worker'):
        keyboard = await re_kb.universal_reply_keyboard(teacher_and_student_menu, 1, choose_menu_action_ph)
    else:
        keyboard = await re_kb.universal_reply_keyboard(abitur_menu, 1, choose_menu_action_ph)
    
    await message.answer(menu_text, reply_markup=keyboard)


@router_base.message(F.text.startswith("🔄 Сменить группу") | F.text.startswith("🔄 Сменить фамилию"))
async def q_change_st_group_teacher_f(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик запроса на смену группы (для студента) или фамилии (для преподавателя)
    """
    user_id = message.from_user.id
    role = await UserFunctions.check_user_role(session, user_id)
    
    if role == 'teacher':
        await message.answer(q_change, reply_markup=await in_kb.choice_inline_kb())
        await state.set_state(st.ChangeOneParam.change)
        await state.update_data(us_role=role)
    elif role == 'user':
        await message.answer(q_change, reply_markup=await in_kb.choice_inline_kb())
        await state.set_state(st.ChangeOneParam.change)
        await state.update_data(us_role=role)
    else: 
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)

@router_base.callback_query(st.ChangeOneParam.change)
async def change_st_group_teacher_f(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик подтверждения смены группы/фамилии
    """
    callback_txt = callback.data
    await callback.answer()
    
    if callback_txt == 'Yes':
        data = await state.get_data()
        role = data.get('us_role')
        await state.clear()
        
        if role == 'teacher':
            teachers = await GetDataFromSchedule.get_all_teachers(session)
            await callback.message.answer(
                choose_teach_name,
                reply_markup=await re_kb.universal_reply_keyboard(teachers, 2, choose_full_name_ph)
            )
            await state.set_state(st.Registration.select_teacher)
        else:
            groups_list = await Groups.get_all_groups(session)
            await callback.message.answer(
                choose_group,
                reply_markup=await re_kb.universal_reply_keyboard(groups_list, 3, choose_group_ph)
            )
            await state.set_state(st.Registration.select_group)
    else:
        await callback.message.edit_text(
            back_to_menu_text,
            reply_markup=await in_kb.menu_inline_kb()
        )
        await state.set_state(st.MenuState.menu)

@router_base.message(F.text.startswith("🔄 Сменить роль"))
async def q_change_role(message: Message, state: FSMContext):
    '''
    Обработчик запроса на смену роли пользователя
    '''
    await message.answer(kb_hide_text, reply_markup=ReplyKeyboardRemove())  
    await message.answer(q_change, reply_markup=await in_kb.choice_inline_kb())
    await state.set_state(st.ChangeRole.change_role)


@router_base.callback_query(st.ChangeRole.change_role)
async def change_role(callback: CallbackQuery, state: FSMContext):
    '''
    Обработчик подтверждения смены роли
    '''
    data = callback.data
    await callback.answer()
    
    if data == 'Yes':
        await callback.message.edit_text(choose_role, reply_markup=await in_kb.role_inline_kb())  
        await state.set_state(st.Registration.select_role)
    else: 
        await callback.message.edit_text(back_to_menu_text, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)



@router_base.message(F.text.startswith("ℹ️ Показать информацию о профиле"))
async def get_info_about_me(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user_info: List[Users] = await UserFunctions.get_user_info_by_id(session, user_id)

    if len(user_info) == 0:
        await message.answer("❌ Информация о пользователе не найдена", reply_markup=await in_kb.menu_inline_kb())
        return

    us_group = None
    role = None
    name = None
    notification = None
    time = None
    for i in user_info:
        us_group = i.group_name
        role = i.role
        name = i.full_name
        notification = i.notification
        notification_bool = (
            True if notification == 'sound'
            else False if notification == 'silent'
            else None
        )
        time = i.notification_time

    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    admin_state_text = '❌ У вас нет прав администратора'
    if is_admin or user_id == OWNER_ID:
        admin_state_text = '✅ У вас есть права администратора'
    notification_text = '🕘 Вы не указали время для получения уведомлений c расписанием на следующий день'
    if notification_bool is None:
        notification_text = f'🕘 Рассылка уведомлений c расписанием на следующий день отключена'
    elif not notification_bool:
        notification_text = f'🕘 Вы получаете уведомление cо звуком в ***{time or "XX:XX"}*** c расписанием на следующий день'
    elif notification_bool:
        notification_text = f'🕘 Вы получаете беззвучное уведомление в ***{time or "XX:XX"}*** c расписанием на следующий день'
    else:
        notification_text = f'🕘 Рассылка уведомлений отключена'


    if role == 'teacher':
        msg_text = (f'***Информация о вас: ***\n──────────\n 👨‍🏫 Вы преподаватель \n\nВаше ФИО: {name or "Не указано"}\n──────────\n'
                    f'🆔 ID вашего телеграмм аккаунта: {user_id}\n──────────'
                    f'\n{notification_text}'
                    f'\n──────────\n{admin_state_text}'
                    )

    elif role == 'user':
        msg_text = (f'***Информация о вас: ***\n──────────\n 👨‍🎓 Вы студент \n\nВаша группа: {us_group}\n──────────\n'
                    f'🆔 ID вашего телеграмм аккаунта: {user_id}\n──────────'
                    f'\n{notification_text}'
                    f'\n──────────\n{admin_state_text}')
    else: 
        msg_text = (f'Информация о профиле:\nID: {user_id}\n'
                    f'\n\n{admin_state_text}')
    await message.answer(msg_text, parse_mode= "Markdown", reply_markup = await in_kb.menu_inline_kb())


@router_base.message(F.text.startswith("📅 Узнать номер недели"))
async def get_week_number(message: Message, state: FSMContext):
    await state.set_state(st.MenuState.menu)
    current_week = await weeks.get_current_week()
    week_num = weeks.get_week_num()
    inverse = await weeks.get_inverse_week()
    half_year = await weeks.get_half_year_num()
    inverse_text = "включен" if inverse == 1 else "выключен"
    half_text = "2 полугодие" if half_year == 1 else "1 полугодие"
    msg_text = (f"Информация о неделях: \n\n***📅 Текущая неделя: {current_week}***\n"
                f"📆 Номер недели в году: {week_num}\n"
                f"⏸️ Учебное полугодие: {half_text} \n"
                f"🔄 Сдвиг недели: {inverse_text}\n\n"
                f"***Для чего нужен сдвиг недели? 🤔 ***\n\n"
                f"Сдвиг необходим для корректного определения номера недели")
    await message.answer(msg_text, parse_mode="Markdown", reply_markup=await in_kb.menu_inline_kb())


@router_base.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message, state : FSMContext, session: AsyncSession):
    user_id = message.from_user.id
    role = await UserFunctions.check_user_role(session, user_id)
    if role == 'teacher':
        await message.answer("⚙️ Настройки:\n\nВыберите действие:",
                             reply_markup=await re_kb.universal_reply_keyboard(settings_menu_teacher, 2, choose_action_ph))
        
    elif role == 'worker':
        del settings_menu_teacher[0]
        del settings_menu_teacher[2]
        await message.answer("⚙️ Настройки:\n\nВыберите действие:",
                             reply_markup=await re_kb.universal_reply_keyboard(settings_menu_teacher, 2, choose_action_ph))
    else:
        await message.answer("⚙️ Настройки:\n\nВыберите действие:",
                             reply_markup=await re_kb.universal_reply_keyboard(settings_menu_user, 2, choose_action_ph))
    await state.set_state(st.MenuState.settings_menu)

@router_base.message(F.text == "📆 Расписание")
async def schedule_type_choice(message: Message, state: FSMContext):
    await message.answer(schedule_text, reply_markup= await re_kb.universal_reply_keyboard(schedule_menu, 1, choose_sch_slice_ph))
    await state.set_state(st.MenuState.schedule_menu)

@router_base.message(F.text == "ℹ️ Информация")
async def information(message: Message, state: FSMContext):
    await state.set_state(st.GetInformation.info_menu)
    await message.answer("Здесь вы можете получить информацию о боте и колледже",
                         reply_markup= await in_kb.info_inline_kb())

@router_base.callback_query(st.GetInformation.info_menu)
async def info_menu(callback: CallbackQuery, state: FSMContext):
    info_choice = callback.data
    if info_choice == 'bot':
        await callback.message.edit_text(bot_info, reply_markup= await in_kb.info_back_inline_kb())
        await state.set_state(st.GetInformation.Information)
    elif info_choice == "spravki":
        await state.set_state(st.GetInformation.Information)
        await callback.message.edit_text(info_about_docs, parse_mode="Markdown", reply_markup=await in_kb.info_back_inline_kb())
    elif info_choice == 'site':
        await state.set_state(st.GetInformation.Information)
        await callback.message.edit_text("***🌐 Сайт:***\n[Официальный сайт колледжа](https://rguts.ru)",
        parse_mode="Markdown",  reply_markup= await in_kb.info_back_inline_kb())
    elif info_choice == 'phones':
        await state.set_state(st.GetInformation.Information)
        await callback.message.edit_text(contact_phones, parse_mode="Markdown",  reply_markup= await in_kb.info_back_inline_kb())
    elif info_choice == 'address':
        await state.set_state(st.GetInformation.Information)
        await callback.message.edit_text(college_address, disable_web_page_preview=True, 
                        parse_mode="Markdown",  reply_markup= await in_kb.info_back_inline_kb())
    elif info_choice == 'socials':
        await state.set_state(st.GetInformation.Information)
        await callback.message.edit_text( social_networks ,parse_mode="MarkdownV2", reply_markup= await in_kb.info_back_inline_kb())


@router_base.callback_query(st.GetInformation.Information)
async def info_reading(callback: CallbackQuery, state: FSMContext):
    info_choice = callback.data
    if info_choice == 'back':
        await callback.message.edit_text("Здесь вы можете получить информацию о боте и колледже",
                                         reply_markup= await in_kb.info_inline_kb())
        await state.set_state(st.GetInformation.info_menu)
    else:
         await callback.message.edit_text(menu_text, reply_markup= await in_kb.menu_inline_kb())  

@router_base.message(F.text == '🕘 Настройки уведомлений')
async def change_notification_time_init(message: Message, state: FSMContext):
    await message.answer("Вы действительно хотите поменять время и тип уведомлений с расписанием или отключить их?", reply_markup= await in_kb.confirm_notifications())
    await state.set_state(st.ChangeNotification.confirm)

@router_base.callback_query(st.ChangeNotification.confirm)
async def change_notification_time(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = callback.data
    await callback.answer()
    if data == 'confirm':
        await callback.message.answer(select_notif_type_text, reply_markup=await in_kb.select_sound())
        await state.set_state(st.Registration.select_notif_type)
    elif data == 'mrnu':
        await state.set_state(st.MenuState.menu)
        await show_menu(callback.from_user.id, callback.message, session)
    else: 
        await state.set_state(st.ChangeNotification.disable)
        await callback.message.answer('Вы точно хотите отключить уведомления?', reply_markup= await in_kb.confirm_sch())

@router_base.callback_query(st.ChangeNotification.disable)
async def disable_notification(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = callback.data
    await callback.answer()
    if data == 'confirm':
        id = callback.from_user.id
        await UserFunctions.insert_time_and_notification_type(session, id, None, None)
        await state.set_state(st.MenuState.menu)
        await show_menu(callback.from_user.id, callback.message, session)
    else: 
        await state.set_state(st.MenuState.menu)
        await show_menu(callback.from_user.id, callback.message, session)



@router_base.message(F.text == '🗑️ Удалить учетную запись')
async def delete_account_init(message: Message, state: FSMContext):
    """
    Обработчик запроса на удаление учетной записи
    """
    
    await message.answer(delete_account_confirm_text, reply_markup=await in_kb.choice_inline_kb())
    await state.set_state(st.DeleteAccount.confirm)

@router_base.callback_query(st.DeleteAccount.confirm)
async def delete_account_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик подтверждения удаления учетной записи
    """
    user_id = callback.from_user.id
    data = callback.data
    await callback.answer()
    
    if user_id == OWNER_ID:
        await callback.message.edit_text(
            "❌ Владелец бота не может удалить свою учетную запись.",
            reply_markup=await in_kb.menu_inline_kb()
        )
        await state.clear()
        return
    else:  
        if data == 'Yes':
            try:
                await UserFunctions.delete_user(session, user_id)
                await callback.message.answer(
                    delete_account_success,
                    reply_markup=ReplyKeyboardRemove()
                )
                await state.clear()
            except Exception as e:
                print(f"Ошибка при удалении пользователя {user_id}: {e}")
                await callback.message.edit_text(
                    "❌ Произошла ошибка при удалении учетной записи. Попробуйте позже.",
                    reply_markup=await in_kb.menu_inline_kb()
                )
                await state.clear()
        else:
            await callback.message.edit_text(
                delete_account_cancelled,
                reply_markup=await in_kb.menu_inline_kb()
            )
            await state.set_state(st.MenuState.menu)

@router_base.message()
async def echo_handler(message: Message) -> None:
    try:
        await message.answer("Команда не распознана, выберите команду из списка.")
    except TypeError:
        await message.answer("Nice try!")

