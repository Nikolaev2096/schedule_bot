import os

from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.fsm.context import FSMContext


from sqlalchemy.ext.asyncio import AsyncSession
from config_bot import bot
from addons.notifications import (
    send_notification_to_all_users, 
    send_notification_to_group, 
    send_notification_to_group_of_users,
    send_notification_to_admins
)

from database.user_func import UserFunctions, Groups

from config_bot import OWNER_ID

from states import states as st
import keyboards.inline_keyboards as in_kb
import keyboards.reply_keyboards as re_kb
from templates.txt_templates import *

from addons.weeks import write_shift_week_and_year_half, get_half_year_num, get_inverse_week
from transformation.transform_education_schedule import start_conversation
from transformation.transform_session_schedule import start_conversation_session

router_admin = Router()

@router_admin.message(F.text == "🔐 Администрирование")
async def admin_menu(message: Message, session: AsyncSession):
    """
    Обработчик главного меню администрирования
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await message.answer(
            admin_menu_text,
            reply_markup=await re_kb.universal_reply_keyboard([
                "Статистика пользователей 🙍‍♂️",
                "Работа с расписанием 📆",
                "Рассылка уведомлений 📢",
                "Работа с администраторами 🤵",
                "🏠 Главное меню"

            ], 2, choose_action_ph)
        )
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())

@router_admin.message(F.text == "Работа с расписанием 📆")
async def work_with_schedule(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик меню работы с расписанием
    """
    await state.set_state(st.MenuState.schedule_menu)
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await message.answer(
            work_with_schedule_text,
            reply_markup=await re_kb.universal_reply_keyboard(admin_menu_list, 2, choose_action_ph)
        )
        await state.set_state(st.WorkWithSchedule.select_action)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())

@router_admin.message(F.text == "Работа с администраторами 🤵")
async def admin_management_menu(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик меню работы с администраторами
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await message.answer(
            admin_management_menu_text,
            reply_markup=await re_kb.universal_reply_keyboard(
                admin_management_list, 2, choose_action_ph
            )
        )
        await state.set_state(st.AdminManagement.menu)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())


@router_admin.message(F.text == "➕ Назначить администратора", st.AdminManagement.menu)
async def set_admin(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик начала процесса назначения администратора
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    if is_admin or user_id == OWNER_ID:
        await message.answer(input_admin_id_text, reply_markup=await in_kb.back_button_kb())
        await state.set_state(st.AdminManagement.input_admin_id)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())


@router_admin.message(F.text == "➖ Снять права администратора", st.AdminManagement.menu)
async def remove_admin(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик начала процесса удаления прав администратора
    """
    user_id = message.from_user.id   
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await message.answer(input_remove_admin_id_text, reply_markup=await in_kb.back_button_kb())
        await state.set_state(st.AdminManagement.input_remove_admin_id)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())


@router_admin.message(F.text == "ℹ️ Информация об администраторах", st.AdminManagement.menu)
async def get_admins_info(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик получения информации об администраторах
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        admins = await UserFunctions.get_all_admins_info(session)
        msg_text = '***Список администраторов:***\n\n' 
        for admin in admins: 
            info = ''
            if admin.role == 'user':
                info = f'***Роль: Студент ***\n Группа: {admin.group_name}'
            elif admin.role == 'teacher':
                info = f'***Роль: Преподаватель ***\n ФИО: {admin.full_name}\n'
            else: 
                info = '***Роль: Сотрудник***'
            admin_info = f'🤵‍♂️ Администратор: \n - id: {admin.id} \n {info}\n'
            msg_text = msg_text + admin_info
        await message.answer(msg_text, reply_markup= await in_kb.menu_inline_kb(), parse_mode = 'MarkDown')
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())


@router_admin.message(st.AdminManagement.input_admin_id)
async def process_set_admin(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик назначения прав администратора
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if not (is_admin or user_id == OWNER_ID):
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.clear()
        return
    
    try:
        target_user_id = int(message.text)
        
        user_info = await UserFunctions.get_user_info_by_id(session, target_user_id)
        if not user_info:
            await message.answer(
                "❌ Пользователь с таким ID не найден в системе.",
                reply_markup=await in_kb.back_button_kb()
            )
            return
        
        ability_to_set_admins = await UserFunctions.check_admin_exist_by_gr(target_user_id, session)
        if not ability_to_set_admins:
            await message.answer(
                admin_group_exists_error,
                reply_markup=await in_kb.back_button_kb()
            )
            return
        
        is_target_admin = await UserFunctions.check_admin_rights_by_id(session, target_user_id)
        if is_target_admin:
            await message.answer(
                f"⚠️ Пользователь {target_user_id} уже является администратором.",
                reply_markup=await in_kb.back_button_kb()
            )
            return
        
        await UserFunctions.set_admin_rights(session, target_user_id, True)
        
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=admin_rights_granted_notif,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
        
        await message.answer(
            admin_set_success.format(target_user_id),
            reply_markup=await re_kb.universal_reply_keyboard(
                admin_management_list, 2, choose_action_ph
            )
        )
        await state.set_state(st.AdminManagement.menu)
        
    except ValueError:
        await message.answer(
            invalid_id_format,
            reply_markup=await in_kb.back_button_kb()
        )


@router_admin.message(st.AdminManagement.input_remove_admin_id)
async def process_remove_admin(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик снятия прав администратора
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if not (is_admin or user_id == OWNER_ID):
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.clear()
        return
    
    try:
        target_user_id = int(message.text)
        
        if target_user_id == OWNER_ID:
            await message.answer(
                admin_cannot_remove_owner,
                reply_markup=await in_kb.back_button_kb()
            )
            return
        
        user_info = await UserFunctions.get_user_info_by_id(session, target_user_id)
        if not user_info:
            await message.answer(
                "❌ Пользователь с таким ID не найден в системе.",
                reply_markup=await in_kb.back_button_kb()
            )
            return
        
        is_target_admin = await UserFunctions.check_admin_rights_by_id(session, target_user_id)
        if not is_target_admin:
            await message.answer(
                f"⚠️ Пользователь {target_user_id} не является администратором.",
                reply_markup=await in_kb.back_button_kb()
            )
            return
        
        await UserFunctions.set_admin_rights(session, target_user_id, False)
        
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=admin_rights_revoked_notif,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка при отправке уведомления пользователю {target_user_id}: {e}")
        
        await message.answer(
            admin_remove_success.format(target_user_id),
            reply_markup=await re_kb.universal_reply_keyboard(
                admin_management_list, 2, choose_action_ph
            )
        )
        await state.set_state(st.AdminManagement.menu)
        
    except ValueError:
        await message.answer(
            invalid_id_format,
            reply_markup=await in_kb.back_button_kb()
        )


@router_admin.message(F.text.startswith("➡️ Включить сдвиг недели"))
async def enable_week_shift(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик включения сдвига недели
    """
    user_id = message.from_user.id   
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await write_shift_week_and_year_half(1, await get_half_year_num())
        await message.answer(week_shift_enabled, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.schedule_menu)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)


@router_admin.message(F.text.startswith("⬅️ Выключить сдвиг недели"))
async def disable_week_shift(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик выключения сдвига недели
    """
    user_id = message.from_user.id   
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await write_shift_week_and_year_half(0, await get_half_year_num())
        await message.answer(week_shift_disabled, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.schedule_menu)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)


@router_admin.message(F.text.startswith("📚 Установить первое полугодие (сен–дек)"))
async def shift_year_past_to_first(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик установки первого полугодия
    """
    user_id = message.from_user.id   
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await write_shift_week_and_year_half(await get_inverse_week(), 0)
        await message.answer(half_year_first_set, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.schedule_menu)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)


@router_admin.message(F.text.startswith("📚 Установить второе полугодие (янв–июл)"))
async def shift_year_past_to_second(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик установки второго полугодия
    """
    user_id = message.from_user.id   
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    if is_admin or user_id == OWNER_ID:
        await write_shift_week_and_year_half(await get_inverse_week(), 1)
        await message.answer(half_year_second_set, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.schedule_menu)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)


@router_admin.message(F.text == "Статистика пользователей 🙍‍♂️")
async def work_with_users(message: Message, session: AsyncSession):
    """
    Обработчик получения статистики пользователей
    """
    user_id = message.from_user.id   
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        total_users = await UserFunctions.get_all_users_count(session)
        groups_info = await UserFunctions.get_groups_members_count(session)
        
        msg_text = stats_text_start
        msg_text += stats_total_users.format(total_users)
        msg_text += stats_groups_header
        
        for group, count in groups_info.items():
            if group:  # Проверяем, что группа не None
                msg_text += stats_group_item.format(group, count)
        
        await message.answer(msg_text, reply_markup=await in_kb.menu_inline_kb())
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())


'''
                     !#################################################!
                    -####### Система рассылки уведомлений #######-
                     !#################################################!
'''

@router_admin.message(F.text == "Рассылка уведомлений 📢")
async def notifications_menu(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик меню рассылки уведомлений
    Переход в состояние выбора получателей уведомления
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await message.answer(
            notif_select_getter_text,
            reply_markup=await in_kb.notification_getter_kb()
        )
        await state.set_state(st.SendNotification.select_getter)
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())


@router_admin.callback_query(F.data.startswith("notif_getter:"), st.SendNotification.select_getter)
async def process_notification_getter(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик выбора получателей уведомления

    Обрабатывает выбор типа получателя: все, студенты, преподаватели, администраторы, группа
    """
    await callback.answer()
    getter_type = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if not (is_admin or user_id == OWNER_ID):
        await callback.message.edit_text(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.clear()
        return
    
    await state.update_data(getter_type=getter_type)
    
    if getter_type == "group":
        groups_list = await Groups.get_all_groups(session)
        await callback.message.edit_text(
            notif_select_group_text,
            reply_markup=await in_kb.notification_group_kb(groups_list)
        )
        await state.set_state(st.SendNotification.select_getter_group)
    elif getter_type == 'back_to_admin_menu':
         await callback.message.answer(
            admin_menu_text,
            reply_markup=await re_kb.universal_reply_keyboard([
                "Статистика пользователей 🙍‍♂️",
                "Работа с расписанием 📆",
                "Рассылка уведомлений 📢",
                "Работа с администраторами 🤵",
                "🏠 Главное меню"

            ], 2, choose_action_ph)
        )
    else:
        await callback.message.edit_text(
            notif_select_sound_text,
            reply_markup=await in_kb.notification_sound_kb()
        )
        await state.set_state(st.SendNotification.select_notification_sound)


@router_admin.callback_query(F.data.startswith("notif_group:"), st.SendNotification.select_getter_group)
async def process_notification_group(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора конкретной группы для уведомления

    Сохраняет выбранную группу и переходит к выбору типа уведомления (со звуком/без звука)
    """
    await callback.answer()
    group_name = callback.data.split(":", 1)[1]
    
    await state.update_data(group_name=group_name)
    
    await callback.message.edit_text(
        notif_select_sound_text,
        reply_markup=await in_kb.notification_sound_kb()
    )
    await state.set_state(st.SendNotification.select_notification_sound)


@router_admin.callback_query(F.data.startswith("notif_sound:"), st.SendNotification.select_notification_sound)
async def process_notification_sound(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора типа уведомления (со звуком/без звука)
    """
    await callback.answer()
    sound_param = callback.data.split(":", 1)[1]
    sound_bool = sound_param == "True"

    await state.update_data(sound=sound_bool)
    
    if sound_bool:
        text_prompt = notif_input_text_sound
    else:
        text_prompt = notif_input_text_silent
    
    await callback.message.edit_text(
        text_prompt,
        reply_markup=await in_kb.back_button_kb()
    )
    await state.set_state(st.SendNotification.input_text_notification)


@router_admin.message(st.SendNotification.input_text_notification)
async def process_notification_text(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик ввода текста уведомления пользователем

    Формирует текст подтверждения с информацией о получателях и типе уведомления
    """
    data = await state.get_data()
    notification_text = message.text
    getter_type = data.get("getter_type")
    sound = data.get("sound", True)
    

    if getter_type == "all":
        getter_display = notif_getter_all
    elif getter_type == "group":
        group_name = data.get("group_name")
        getter_display = notif_getter_group.format(group_name)
    elif getter_type == "students":
        getter_display = notif_getter_students
    elif getter_type == "teachers":
        getter_display = notif_getter_teachers
    elif getter_type == "admins":
        getter_display = notif_getter_admins
    else:
        getter_display = "Неизвестно"
    
    sound_display = notif_type_sound if sound else notif_type_silent
    

    confirm_text = notif_confirm_text.format(getter_display, sound_display, notification_text)
    

    await state.update_data(notification_text=notification_text)
    

    await message.answer(
        confirm_text,
        reply_markup=await in_kb.notification_confirm_kb(),
        parse_mode="Markdown"
    )

    await state.set_state(st.SendNotification.confirm_notification_send)


@router_admin.callback_query(F.data.startswith("notif_confirm:"), st.SendNotification.confirm_notification_send)
async def process_notification_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    '''
    Обработчик подтверждения отправки уведомления
    '''
    await callback.answer()
    confirm_action = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    
    if confirm_action == "yes":
        data = await state.get_data()
        getter_type = data.get("getter_type")
        notification_text = data.get("notification_text")
        sound = data.get("sound", True)
        
        try:

            if getter_type == "all":

                await send_notification_to_all_users(
                    notification_text, session, sound=sound, admin_id=user_id
                )
                success_text = notif_send_success_all
            elif getter_type == "group":

                group_name = data.get("group_name")
                await send_notification_to_group(
                    group_name, notification_text, session, sound=sound
                )
                success_text = notif_send_success_group.format(group_name)
            elif getter_type == "students":

                await send_notification_to_group_of_users(
                    "user", notification_text, session, sound=sound
                )
                success_text = notif_send_success_role.format("студенты")
            elif getter_type == "teachers":

                await send_notification_to_group_of_users(
                    "teacher", notification_text, session, sound=sound
                )
                success_text = notif_send_success_role.format("преподаватели")
            elif getter_type == "admins":

                await send_notification_to_admins(
                    notification_text, session, sound=sound, admin_id=user_id
                )
                success_text = notif_send_success_role.format("администраторы")
            else:
                raise ValueError(f"Неизвестный тип получателя: {getter_type}")
            
            await callback.message.edit_text(
                success_text,
                reply_markup=await in_kb.menu_inline_kb()
            )
        except Exception as e:

            await callback.message.edit_text(
                notif_send_error.format(str(e)),
                reply_markup=await in_kb.menu_inline_kb()
            )
    else:

        await callback.message.edit_text(
            notif_send_cancelled,
            reply_markup=await in_kb.menu_inline_kb()
        )

    await state.clear()


'''
                     !#################################################!
                    -####### Обработчики возврата назад #######-
                     !#################################################!
'''

@router_admin.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu_from_notifications(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    '''
    Обработчик возврата в админ-меню из системы уведомлений
    Очищает состояние и возвращает пользователя в главное меню администрирования
    '''
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await callback.message.edit_text(
            admin_menu_text,
            reply_markup=await re_kb.universal_reply_keyboard([
                "Статистика пользователей 🙍‍♂️",
                "Работа с расписанием 📆",
                "Рассылка уведомлений 📢",
                "Работа с администраторами 🤵",
                "🏠 Главное меню"
            ], 2, choose_action_ph)
        )
    else:
        await callback.message.edit_text(
            havent_rights,
            reply_markup=await in_kb.menu_inline_kb()
        )
    await state.clear()


@router_admin.callback_query(F.data == "back_to_menu", st.AdminManagement.input_admin_id or st.AdminManagement.input_remove_admin_id)
async def back_from_admin_input(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик возврата из состояния ввода ID администратора
    """
    await callback.answer()
    user_id = callback.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await callback.message.answer(
            admin_management_menu_text,
            reply_markup=await re_kb.universal_reply_keyboard(
                admin_management_list, 2, choose_action_ph
            )
        )
        await state.set_state(st.AdminManagement.menu)
    else:
        await callback.message.edit_text(
            havent_rights,
            reply_markup=await in_kb.menu_inline_kb()
        )
        await state.clear()


@router_admin.message(F.text == "🏠 Главное меню", st.AdminManagement.menu)
async def back_to_admin_main_menu(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик возврата в главное меню администрирования из меню работы с администраторами
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    
    if is_admin or user_id == OWNER_ID:
        await message.answer(
            admin_menu_text,
            reply_markup=await re_kb.universal_reply_keyboard([
                "Статистика пользователей 🙍‍♂️",
                "Работа с расписанием 📆",
                "Рассылка уведомлений 📢",
                "Работа с администраторами 🤵",
                "🏠 Главное меню"
            ], 2, choose_action_ph)
        )
        await state.clear()
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.clear()



@router_admin.callback_query(F.data == "notif_back_getter")
async def back_to_notification_getter(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик возврата к выбору получателей

    Возвращает пользователя к начальному этапу выбора получателей уведомления
    """
    await callback.answer()
    await callback.message.edit_text(
        notif_select_getter_text,
        reply_markup=await in_kb.notification_getter_kb()
    )

    await state.set_state(st.SendNotification.select_getter)


@router_admin.callback_query(F.data == "back_to_menu", st.SendNotification.input_text_notification)
async def back_from_input_text_notification(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик возврата из состояния ввода текста уведомления

    Возвращает пользователя к выбору типа уведомления (со звуком/без звука)
    """
    await callback.answer()
    data = await state.get_data()
    getter_type = data.get("getter_type")

    if getter_type == "group":
        await callback.message.edit_text(
            notif_select_sound_text,
            reply_markup=await in_kb.notification_sound_kb()
        )
        await state.set_state(st.SendNotification.select_notification_sound)
    else:

        await callback.message.edit_text(
            notif_select_getter_text,
            reply_markup=await in_kb.notification_getter_kb()
        )
        await state.set_state(st.SendNotification.select_getter)


""""

###### Обновление расписания (учебного и сессии)

"""

@router_admin.message(F.text=="📆 Обновить учебное расписание")
async def update_schedule(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик начала процесса обновления учебного расписания
    """
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    if is_admin or user_id == OWNER_ID:
        await state.set_state(st.UpdateSchedule.confirm_update)
        await message.answer(update_schedule_confirm_text, reply_markup=await in_kb.confirm_sch())
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)


@router_admin.callback_query(st.UpdateSchedule.confirm_update)
async def update_schedule_confirm(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик подтверждения обновления учебного расписания
    """
    data = callback.data
    if data == 'confirm':
        await callback.message.edit_text(send_file_text, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.UpdateSchedule.upload_schedule)
    else:
        await callback.message.edit_text(back_to_menu_btn_text, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)


@router_admin.message(st.UpdateSchedule.upload_schedule, F.document)
async def process_schedule_file(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик загрузки и обработки файла учебного расписания
    """
    destination_dir = "documents"
    os.makedirs(destination_dir, exist_ok=True)
    document = message.document
    file_id = document.file_id
    file_info = await bot.get_file(file_id)

    file_name = document.file_name
    if file_name.endswith('.docx'):
        file_path = os.path.join(destination_dir, file_name)
        await bot.download_file(file_info.file_path, file_path)
        await message.answer(file_received_text.format(file_name))
        success = await start_conversation(file_path, session)
        if success:
            await message.answer(schedule_updated_success, reply_markup=await in_kb.menu_inline_kb())
            await state.clear()
            os.remove(file_path)
            user_id = int(message.from_user.id)
            await send_notification_to_all_users(schedule_updated_notif, session, sound=False, admin_id=user_id)
        else:
            await message.answer(schedule_update_error, reply_markup=await in_kb.menu_inline_kb())
    else:
        await message.answer(wrong_file_format)
        await state.set_state(st.UpdateSchedule.upload_schedule)


@router_admin.message(F.text=="📆 Обновить расписание сессии")
async def update_session_schedule(message: Message, session: AsyncSession, state: FSMContext):
    '''
    Обработчик начала процесса обновления расписания сессии
    '''
    user_id = message.from_user.id
    is_admin = await UserFunctions.check_admin_rights_by_id(session, user_id)
    if is_admin or user_id == OWNER_ID:
        await state.set_state(st.UpdateSessionSchedule.confirm_update)
        await message.answer(update_session_confirm_text, reply_markup=await in_kb.confirm_sch())
    else:
        await message.answer(havent_rights, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.MenuState.menu)


@router_admin.callback_query(st.UpdateSessionSchedule.confirm_update)
async def update_session_schedule_confirm(callback: CallbackQuery, state: FSMContext):
    '''
    Обработчик подтверждения обновления расписания сессии
    '''
    data = callback.data
    if data == 'confirm':
        await callback.message.edit_text(send_file_text, reply_markup=await in_kb.menu_inline_kb())
        await state.set_state(st.UpdateSessionSchedule.upload_schedule)
    else:
        await state.set_state(st.MenuState.menu)
        await callback.message.edit_text(back_to_menu_btn_text, reply_markup=await in_kb.menu_inline_kb())


@router_admin.message(st.UpdateSessionSchedule.upload_schedule, F.document)
async def process_session_schedule_file(message: Message, state: FSMContext, session: AsyncSession):
    '''
    Обработчик загрузки и обработки файла расписания сессии
    '''
    destination_dir = "documents"
    os.makedirs(destination_dir, exist_ok=True)
    document = message.document
    file_id = document.file_id
    file_info = await bot.get_file(file_id)

    file_name = document.file_name
    if file_name.endswith('.docx'):
        file_path = os.path.join(destination_dir, file_name)
        await bot.download_file(file_info.file_path, file_path)
        await message.answer(file_received_text.format(file_name))
        success = await start_conversation_session(file_path, session)
        if success:
            await message.answer(schedule_updated_success, reply_markup=await in_kb.menu_inline_kb())
            await state.clear()
            os.remove(file_path)
            user_id = message.from_user.id
            await send_notification_to_all_users(session_updated_notif, session, sound=False, admin_id=user_id)
        else:
            await message.answer(schedule_update_error, reply_markup=await in_kb.menu_inline_kb())
    else:
        await message.answer(wrong_file_format)
        await state.set_state(st.UpdateSessionSchedule.upload_schedule)

