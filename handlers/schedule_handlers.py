from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.types import ReplyKeyboardRemove

from datetime import date
from addons import weeks
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.user_func import UserFunctions, Groups
from database.misc import GetDataFromSchedule
from database.schedule_func import EduSchedule, SessionSchedule
from addons.weeks import get_half_year_num, get_current_week

from templates.schedule_template import *
from templates.session_template import *
from templates.txt_templates import *

from states import states as st
import keyboards.inline_keyboards as in_kb 
import keyboards.reply_keyboards as re_kb 


router_schedule = Router()

##########################################
#------------- Глобальные переменные ----


DAYS_list = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

DAYS = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье"
}

MONTHS = {
        "Январь": 1,
        "Февраль": 2,
        "Март": 3,
        "Апрель": 4,
        "Май": 5,
        "Июнь": 6,
        "Сентябрь": 9,
        "Октябрь": 10,
        "Ноябрь": 11,
        "Декабрь": 12
}

##########################################
#---------------- Учебное расписание ----
 


@router_schedule.message(F.text == "📆 Свое расписание на текущую неделю")
async def get_my_schedule_current_week(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик выдачи своего расписания на текущую неделю
    Выдает расписание пользователя без дополнительных выборов
    """
    user_id = message.from_user.id
    role = await UserFunctions.check_user_role(session, user_id)
    current_week = await get_current_week()
    
    try:
        raw_rows = []
        user_data = {
            'choice_type': 'group' if role == 'user' else 'teacher',
            'week_number': current_week, 
            'current': True 
        }
        
        if role == 'user':

            group_name = await UserFunctions.check_user_group(session, user_id)
            if group_name:
                raw_rows = await EduSchedule.get_for_group(session, group_name, current_week)
            else:
                await message.answer(
                    "❌ Ваша группа не указана в профиле. Пожалуйста, укажите группу в настройках.",
                    reply_markup=await in_kb.menu_inline_kb()
                )
                await state.set_state(st.MenuState.menu)
                return
        elif role == 'teacher':
       
            teacher_name = await UserFunctions.check_teacher_name(session, user_id)
            if teacher_name:
                raw_rows = await EduSchedule.get_for_teacher(session, teacher_name, current_week)
            else:
                await message.answer(
                    "❌ Ваше ФИО не указано в профиле. Пожалуйста, укажите ФИО в настройках.",
                    reply_markup=await in_kb.menu_inline_kb()
                )
                await state.set_state(st.MenuState.menu)
                return
        else:
            await message.answer(
                "❌ Для получения расписания необходимо указать роль в профиле.",
                reply_markup=await in_kb.menu_inline_kb()
            )
            await state.set_state(st.MenuState.menu)
            return
        
        if not raw_rows:
            await message.answer(
                info_not_found,
                reply_markup=await in_kb.menu_inline_kb()
            )
            await state.set_state(st.MenuState.menu)
            return
        
        schedule_msg_text = await formatter.format_schedule(raw_rows, user_data, role)
        await message.answer(
            schedule_msg_text,
            parse_mode="Markdown",
            reply_markup=await in_kb.menu_inline_kb()
        )
        await state.set_state(st.MenuState.menu)
        
    except Exception as e:
        await message.answer(
            f"Произошла ошибка при получении расписания: {e}",
            reply_markup=await in_kb.menu_inline_kb()
        )
        await state.set_state(st.MenuState.menu)

@router_schedule.message(F.text.startswith("📆 Учебное расписание"))
async def get_schedule(message: Message, state: FSMContext,):
    """
    Обработчик выдачи inline клавиатуры для выбора среза учебного расписания
    """
    await state.set_state(st.ScheduleSelect.select_slice)
    await message.answer(schedule_text, reply_markup= await in_kb.schedule_inline_kb())


@router_schedule.callback_query(F.data.startswith("sch"), st.ScheduleSelect.select_slice)
async def process_select_sch(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик выдачи inline клавиатуры для получения данных о желаемом расписании
    """
    user_id = callback.from_user.id
    role = await UserFunctions.check_user_role(session, user_id)
    await callback.answer()
    _, schedule_type = callback.data.split(":", 1)
    await state.update_data(choice_type=schedule_type)
    if schedule_type == 'teacher':
        await callback.message.edit_text(get_text, reply_markup=await in_kb.schedule_teach_inline_kb(role))
        await state.set_state(st.ScheduleSelect.select_teacher)
    elif schedule_type == 'group':
        await callback.message.edit_text(get_text, reply_markup=await in_kb.schedule_group_inline_kb(role))
        await state.set_state(st.ScheduleSelect.select_group)
    elif schedule_type == 'day':
        await callback.message.answer(get_text_by_day, reply_markup=await re_kb.universal_reply_keyboard(DAYS_list, 2, choose_day_ph))
        await state.set_state(st.ScheduleSelect.input_day)
    elif schedule_type == 'room':
        rooms_all = await GetDataFromSchedule.get_all_rooms(session)
        await callback.message.answer(get_text_room, reply_markup=await re_kb.universal_reply_keyboard(rooms_all, 3, choose_room_ph))
        await state.set_state(st.ScheduleSelect.input_room)
    elif schedule_type == 'calendar':
        if await get_half_year_num() == 0:
            months = ['Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        else:
            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь']
        await callback.message.answer("Выберите месяц:", reply_markup=await re_kb.universal_reply_keyboard(months, 3, choose_month_ph))
        await state.set_state(st.CalendarSchedule.select_month)
    elif schedule_type == 'schedule_menu':
        await callback.message.answer(
            schedule_text,
            reply_markup=await re_kb.universal_reply_keyboard(schedule_menu, 1, choose_sch_slice_ph)
        )
        await state.set_state(st.MenuState.schedule_menu)
    else:
        await callback.message.answer(
            schedule_text,
            reply_markup=await re_kb.universal_reply_keyboard(schedule_menu, 1, choose_sch_slice_ph)
        )
        await state.set_state(st.MenuState.schedule_menu)

@router_schedule.message(st.CalendarSchedule.select_month)
async def select_month(message: Message, state: FSMContext):
    month = message.text
    await state.update_data(month=month) 
    days = []
    for i in range(32):
        if i == 0:
            continue
        days.append(str(i))
    await message.answer("Выберите день: ", reply_markup = await re_kb.universal_reply_keyboard(days, 7, choose_day_ph))
    await state.set_state(st.CalendarSchedule.confirm_select)


@router_schedule.message(st.CalendarSchedule.confirm_select)
async def confirm_calendar_sch(message: Message, state: FSMContext):
    day = message.text
    await state.update_data(day=day) 
    user_choice = await state.get_data()
    month = user_choice.get("month")
    await message.answer(kb_hide_text, reply_markup= ReplyKeyboardRemove())
    try:
        month_s = MONTHS[month]  # Номер месяца
        year = datetime.now().year # Год
        day = int(day) # Число
        cur_date = date(year, month_s, day)
        week_current = cur_date.isocalendar().week
        day_current = cur_date.weekday()
        week_number = 1
        if await weeks.get_inverse_week() == 1:
            week_current += 1
        if week_current % 2 == 0:
            week_number = 2

        num_day = day
        day = DAYS[day_current]
        await state.update_data(day=day)
        await state.update_data(week_number = week_number)
        await message.answer(f'Вы хотите получить свое расписание на ***{num_day}.{month_s}.{year}*** (___{day}___)?', parse_mode="Markdown", reply_markup= await in_kb.confirm_sch())
        await state.set_state(st.ScheduleSelect.confirm_state)
    except ValueError:
        await message.answer('Проверьте корректность введенного дня. Введите валидное число')
        await state.set_state(st.CalendarSchedule.confirm_select)
    except KeyError:
        await message.answer('Выберите месяц из списка')
        await state.set_state(st.CalendarSchedule.select_month)
        if get_half_year_num() == 0:
            months = ['Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        else:
            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь']
        await message.answer("Выберите месяц:", reply_markup=await re_kb.universal_reply_keyboard(months, 3, choose_month_ph))
        

@router_schedule.callback_query(st.ScheduleSelect.select_group)
async def select_group(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик выбора группы для учебного расписания

    Обрабатывает выбор своей группы, другой группы или возврат назад
    """
    await callback.answer()
    if callback.data == 'my_group':
    
        await callback.message.edit_text(week_select_text, reply_markup=await in_kb.schedule_week_inline_kb())  
        await state.set_state(st.ScheduleSelect.select_week)
    elif callback.data == 'back_to_schedule_type' or callback.data == 'menu':
        await callback.message.edit_text(schedule_text, reply_markup=await in_kb.schedule_inline_kb())
        await state.set_state(st.ScheduleSelect.select_slice)
    else:
        groups_list = await Groups.get_all_groups(session)
        await callback.message.answer(group_select, reply_markup=await re_kb.universal_reply_keyboard(groups_list, 3, choose_group_ph))
        await state.set_state(st.ScheduleSelect.select_another_group)


@router_schedule.message(st.ScheduleSelect.select_another_group)
async def select_another_group(message: Message, state: FSMContext, session: AsyncSession):
    group_name = message.text.strip()
    group_exists = await Groups.check_group(session, group_name)
    if not group_exists:
        await message.answer(invalid_group, reply_markup=await in_kb.menu_inline_kb())
        return
    
    await state.update_data(another_group=group_name) 
    await message.answer(week_select_text, reply_markup=await in_kb.schedule_week_inline_kb())
    await state.set_state(st.ScheduleSelect.select_week)
    

@router_schedule.callback_query(st.ScheduleSelect.select_teacher)
async def select_teach(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик выбора преподавателя для учебного расписания

    Обрабатывает выбор своего расписания, другого преподавателя или возврат назад
    """
    await callback.answer()
    if callback.data == 'my_sch':
        await callback.message.edit_text(week_select_text,  reply_markup=await in_kb.schedule_week_inline_kb())  
        await state.set_state(st.ScheduleSelect.select_week)
    elif callback.data == 'back_to_schedule_type' or callback.data == 'menu':
        await callback.message.edit_text(schedule_text, reply_markup=await in_kb.schedule_inline_kb())
        await state.set_state(st.ScheduleSelect.select_slice)
    else:
        teachers_list = await GetDataFromSchedule.get_all_teachers(session)
        await callback.message.answer(choose_teach_name, reply_markup=await re_kb.universal_reply_keyboard(teachers_list, 2, choose_full_name_ph))
        await state.set_state(st.ScheduleSelect.select_another_teach)

@router_schedule.message(st.ScheduleSelect.select_another_teach)
async def select_another_teach(message: Message, state: FSMContext, session: AsyncSession):
    teacher_name = message.text.strip()
    teacher_exists = await GetDataFromSchedule.check_teacher_exist(session, teacher_name)
    if not teacher_exists:
        await message.answer(invalid_teacher, reply_markup=await in_kb.menu_inline_kb())
        return
    
    await state.update_data(another_teach=teacher_name) 
    await message.answer(week_select_text, reply_markup=await in_kb.schedule_week_inline_kb())
    await state.set_state(st.ScheduleSelect.select_week)
    
@router_schedule.message(st.ScheduleSelect.input_room)
async def process_room_input(message: Message, state: FSMContext):
    unified_data = message.text  
    await state.update_data(room=unified_data) 

    await message.answer(select_day_from_list, reply_markup=await re_kb.universal_reply_keyboard(DAYS_list, 2, choose_day_ph))
    await state.set_state(st.ScheduleSelect.input_day)

@router_schedule.message(st.ScheduleSelect.input_day)
async def process_day_input(message: Message, state: FSMContext):
    unified_data = message.text  
    await state.update_data(day=unified_data)
    await message.answer(week_select_text, reply_markup=await in_kb.schedule_week_inline_kb())
    await state.set_state(st.ScheduleSelect.select_week)

@router_schedule.callback_query(st.ScheduleSelect.select_week)
async def process_week_selection(callback: CallbackQuery, state: FSMContext):
    week_cb = callback.data 
    await callback.answer()
    if week_cb in ('one', 'two', 'all'):
        await state.update_data(current=False)
    else: 
        await state.update_data(current=True)

    if week_cb == 'one':
        week = 1
        week_str = 'На первую неделю'
    elif week_cb == 'two':
        week = 2
        week_str = 'На вторую неделю'
    elif week_cb == 'all':
        week = 0
        week_str = 'На все недели'
    else: 
        week = await get_current_week()
        week_str = 'На текущую неделю'

    await state.update_data(week_number=week)

    user_data = await state.get_data()
    choice = user_data.get('choice_type')
    tick = False
    # Нужно для определения текущего сообщения,
    # если сообщение с inline клавиатурой - сообщение будет отредактировано,
    # если нет - отправлено новое
    choice_txt = ''
    if choice == 'group':
        type_choice = user_data.get('another_group')
        if type_choice:
            tick = True
            choice_txt = f"Расписание группы: ***{type_choice}***"
        else:
            choice_txt = 'Вашей группы'
    elif choice == 'teacher':
        teacher = user_data.get('another_teach')
        if teacher:
            tick = True
            choice_txt = f"Расписание преподавателя: {teacher}"
        else: 
            choice_txt = "Ваше расписание"
    elif choice == "day":
        day = user_data.get('day') 
        choice_txt = f'Вы получите свое расписание на: ***{day}***'
    elif choice == 'room':
        data = user_data.get('room') 
        day_str = user_data.get('day') 
        choice_txt = f'Вы получите расписание кабинета: {data} на {day_str}'
    if tick:
        await callback.message.answer(f"Вы хотите получить это расписание:\n{choice_txt} \n{week_str}", reply_markup= await in_kb.confirm_sch(), parse_mode="Markdown")
    else:
        await callback.message.edit_text(f"Вы хотите получить это расписание:\n{choice_txt} \n{week_str}", reply_markup= await in_kb.confirm_sch(), parse_mode="Markdown")
    await state.set_state(st.ScheduleSelect.confirm_state)

'''
                     !#################################################!
                    -####### Обработчики навигации "Назад" #######-
                     !#################################################!
'''

@router_schedule.callback_query(F.data == "schedule_menu")
async def back_to_schedule_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик возврата к меню расписания

    Возвращает пользователя к выбору типа расписания (учебное/сессии)
    """
    await callback.answer()
    await callback.message.answer(
        schedule_text,
        reply_markup=await re_kb.universal_reply_keyboard(schedule_menu, 1, choose_sch_slice_ph)
    )
    await state.set_state(st.MenuState.schedule_menu)


@router_schedule.callback_query(F.data == "back_to_schedule_type")
async def back_to_schedule_type(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик возврата к выбору типа среза расписания

    Возвращает из выбора группы/преподавателя к выбору типа (по группе, по преподавателю и т.д.)
    """
    await callback.answer()
    await callback.message.edit_text(
        schedule_text,
        reply_markup=await in_kb.schedule_inline_kb()
    )
    await state.set_state(st.ScheduleSelect.select_slice)


@router_schedule.callback_query(F.data == "back_to_schedule_prev", st.ScheduleSelect.select_week)
async def back_from_week_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик возврата из выбора недели к предыдущему этапу

    Возвращает к выбору группы/преподавателя в зависимости от типа выбранного расписания
    """
    await callback.answer()
    user_id = callback.from_user.id
    user_data = await state.get_data()
    choice_type = user_data.get('choice_type')
    role = await UserFunctions.check_user_role(session, user_id)
    
    if choice_type == 'group':
        await callback.message.edit_text(
            get_text,
            reply_markup=await in_kb.schedule_group_inline_kb(role)
        )
        await state.set_state(st.ScheduleSelect.select_group)
    elif choice_type == 'teacher':
        await callback.message.edit_text(
            get_text,
            reply_markup=await in_kb.schedule_teach_inline_kb(role)
        )
        await state.set_state(st.ScheduleSelect.select_teacher)
    elif choice_type == 'day':
        await callback.message.answer(
            get_text_by_day,
            reply_markup=await re_kb.universal_reply_keyboard(DAYS_list, 2, choose_day_ph)
        )
        await state.set_state(st.ScheduleSelect.input_day)
    elif choice_type == 'room':
        rooms_all = await GetDataFromSchedule.get_all_rooms(session)
        rooms = [i[0] for i in rooms_all]
        await callback.message.answer(
            get_text_room,
            reply_markup=await re_kb.universal_reply_keyboard(rooms, 3, choose_room_ph)
        )
        await state.set_state(st.ScheduleSelect.input_room)
    elif choice_type == 'calendar':
        if get_half_year_num() == 0:
            months = ['Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        else:
            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь']
        await callback.message.answer(
            "Выберите месяц:",
            reply_markup=await re_kb.universal_reply_keyboard(months, 3, choose_month_ph)
        )
        await state.set_state(st.CalendarSchedule.select_month)
    else:
        await callback.message.edit_text(
            schedule_text,
            reply_markup=await in_kb.schedule_inline_kb()
        )
        await state.set_state(st.ScheduleSelect.select_slice)


@router_schedule.callback_query(st.ScheduleSelect.confirm_state)
async def get_done_schedule(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик подтверждения выбора расписания

    Обрабатывает подтверждение, отмену и возврат в главное меню
    """
    user_id = callback.from_user.id
    us_c = callback.data

    if us_c == 'confirm':
        await callback.answer()
        role = await UserFunctions.check_user_role(session, user_id)
        user_data = await state.get_data()
        await state.clear()
        choice = user_data.get('choice_type')
        week = user_data.get('week_number')
        raw_rows = [] 
        try:
            if choice == 'group':
                type_choice = user_data.get('another_group')
                if type_choice:
                    raw_rows = await EduSchedule.get_for_group(session, type_choice, week)
                else:
                    group_name= await UserFunctions.check_user_group(session, user_id)
                    if group_name:
                        raw_rows = await EduSchedule.get_for_group(session, group_name, week)
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  
            elif choice == 'teacher':
                teacher = user_data.get('another_teach')
                if teacher:
                    raw_rows = await EduSchedule.get_for_teacher(session, teacher, week)
                else: 
                    teacher_name = await UserFunctions.check_teacher_name(session, user_id)
                    if teacher_name:
                        raw_rows = await EduSchedule.get_for_teacher(session, teacher_name, week)
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  
            elif choice == 'day':
                day = user_data.get('day')
                if role == 'teacher':
                    teacher_row = await UserFunctions.check_teacher_name(session, user_id)
                    if teacher_row:
                        raw_rows = await EduSchedule.get_for_teacher_by_day(session, teacher_row, week, day)
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  
                else:
                    group_name = await UserFunctions.check_user_group(session, user_id)
                    if group_name:
                        raw_rows = await EduSchedule.get_for_group_by_day(session, group_name, week, day)
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  
            elif choice == 'room':
                room = user_data.get('room')
                current_day_str = user_data.get('day') 
                raw_rows = await EduSchedule.get_by_room(session, room, week, current_day_str)
            elif choice == 'calendar':
                data = user_data.get('day') 
                if role == 'teacher':
                    teacher_row = await UserFunctions.check_teacher_name(session, user_id)
                    if teacher_row:
                        raw_rows = await EduSchedule.get_for_teacher_by_day(session, teacher_row, week, data)
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  
                else:
                    group_name = await UserFunctions.check_user_group(session, user_id)
                    if group_name:
                        raw_rows = await EduSchedule.get_for_group_by_day(session, group_name, week, data)
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  
            schedule_msg_text = await formatter.format_schedule(raw_rows, user_data, role) 
            if len(schedule_msg_text) > 4096:
                schedule_msg_text = schedule_msg_text[:4090] + "\n\n... (сообщение обрезано, слишком длинное для отправки)"
            await callback.message.answer(
                schedule_msg_text, 
                parse_mode="Markdown", 
                reply_markup=await in_kb.menu_inline_kb() 
            )
            await state.set_state(st.MenuState.menu)
        except Exception as e:
            await callback.message.answer(f"Произошла ошибка при получении расписания: {e}",reply_markup= await in_kb.menu_inline_kb() )
            await state.set_state(st.MenuState.menu)
    elif us_c == 'menu':
        await callback.answer()
        await state.clear()
        await state.set_state(st.MenuState.menu)
        try:
            await callback.message.edit_text(menu_text, reply_markup=await in_kb.menu_inline_kb())
        except:
            await callback.message.answer(menu_text, reply_markup=await in_kb.menu_inline_kb())
    else:
        await callback.answer()
        await state.set_state(st.ScheduleSelect.select_slice)
        await callback.message.edit_text(schedule_text, reply_markup=await in_kb.schedule_inline_kb())   


##########################################
# ---------------- Расписание сессии -----


@router_schedule.message(F.text == '📆 Расписание сессии')
async def session_schedule(message: Message, state: FSMContext):
    await message.answer(kb_hide_text, reply_markup=ReplyKeyboardRemove())  
    await message.answer(get_text, reply_markup= await in_kb.session_inline_kb())
    await state.set_state(st.SessionSchedule.select_owner)

@router_schedule.callback_query(st.SessionSchedule.select_owner)
async def session_owner(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
   
    _, type_val = callback.data.split(":", 1)  
    await state.update_data(choice_type=type_val) 
    us_id = callback.from_user.id
    us_role = await UserFunctions.check_user_role(session, us_id)
    
    if type_val == 'teacher':
        await callback.message.edit_text(get_text, reply_markup=await in_kb.schedule_teach_inline_kb(us_role))   
        await state.set_state(st.SessionSchedule.select_teacher)
    elif type_val == 'group':
        await callback.message.edit_text(get_text, reply_markup=await in_kb.schedule_group_inline_kb(us_role))   
        await state.set_state(st.SessionSchedule.select_group)
    else: 
        await callback.message.answer(
            schedule_text,
            reply_markup=await re_kb.universal_reply_keyboard(schedule_menu, 1, choose_sch_slice_ph)
        )
        await state.set_state(st.MenuState.schedule_menu)


@router_schedule.callback_query(st.SessionSchedule.select_group)
async def select_session_sch_for_group(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик выбора группы для расписания сессии

    Обрабатывает выбор своей группы, другой группы или возврат назад
    """
    await callback.answer()
    if callback.data == 'my_group':
        await state.set_state(st.SessionSchedule.confirm_state)
        await process_session_selection(callback, state)
    elif callback.data == 'back_to_schedule_type' or callback.data == 'menu':
        await callback.message.edit_text(get_text, reply_markup=await in_kb.session_inline_kb())
        await state.set_state(st.SessionSchedule.select_owner)
    else:
        groups_list = await Groups.get_all_groups(session)
        await callback.message.answer(group_select, reply_markup=await re_kb.universal_reply_keyboard(groups_list, 3, choose_group_ph))
        await state.set_state(st.SessionSchedule.select_another_group)

@router_schedule.message(st.SessionSchedule.select_another_group)
async def select_another_session_sch_for_group(message: Message, state: FSMContext, session: AsyncSession):
    group_name = message.text.strip()
    group_exists = await GetDataFromSchedule.check_group_in_session(session, group_name)
    if not group_exists:
        await message.answer(invalid_group_session, reply_markup=await in_kb.menu_inline_kb())
        return
    
    await state.update_data(another_group=group_name) 
    await state.set_state(st.SessionSchedule.confirm_state)
    await message.answer(kb_hide_text, reply_markup=ReplyKeyboardRemove())  
    await process_session_selection(message, state)

@router_schedule.callback_query(st.SessionSchedule.select_teacher)
async def select_session_sch_for_teach(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик выбора преподавателя для расписания сессии

    Обрабатывает выбор своего расписания, другого преподавателя или возврат назад
    """
    await callback.answer()
    if callback.data == 'my_sch':
        await state.set_state(st.SessionSchedule.confirm_state)
        await process_session_selection(callback, state)
    elif callback.data == 'back_to_schedule_type' or callback.data == 'menu':
        await callback.message.edit_text(get_text, reply_markup=await in_kb.session_inline_kb())
        await state.set_state(st.SessionSchedule.select_owner)
    else:
        teachers_list = await GetDataFromSchedule.get_all_teachers(session)
        await callback.message.answer(choose_teach_name, reply_markup=await re_kb.universal_reply_keyboard(teachers_list, 2, choose_full_name_ph))
        await state.set_state(st.SessionSchedule.select_another_teach)

@router_schedule.message(st.SessionSchedule.select_another_teach)
async def select_session_sch_for_another_teach(message: Message, state: FSMContext, session: AsyncSession):
    teacher_name = message.text.strip()
    teacher_exists = await GetDataFromSchedule.check_teacher_in_session(session, teacher_name)
    if not teacher_exists:
        await message.answer(invalid_teacher_session, reply_markup=await in_kb.menu_inline_kb())
        return
    
    await state.update_data(another_teach=teacher_name)
    await state.set_state(st.SessionSchedule.confirm_state)
    await message.answer(kb_hide_text, reply_markup=ReplyKeyboardRemove())  
    await process_session_selection(message, state)

@router_schedule.callback_query(st.SessionSchedule.confirm_state)
async def process_session_selection(callback: CallbackQuery , state: FSMContext):

    user_data = await state.get_data()
    choice = user_data.get('choice_type')
    choice_txt = ""
    if choice == 'group':
        type_choice = user_data.get('another_group')
        choice_txt = f"Расписание группы: ***{type_choice}***" if type_choice else 'Вашей группы'
    elif choice == 'teacher':
        teacher = user_data.get('another_teach')
        choice_txt = f"Расписание преподавателя: {teacher}" if teacher else "Ваше расписание"
    else:
        await callback.message.answer("Ошибка: тип не выбран.")
        return

    text_to_send = f"Вы хотите получить это расписание:\n{choice_txt}"
    kb = await in_kb.confirm_sch()

    await callback.message.edit_text(text_to_send, reply_markup=kb, parse_mode="Markdown")
    
    await state.set_state(st.SessionSchedule.state_for_get)


@router_schedule.callback_query(st.SessionSchedule.state_for_get)
async def get_done_session_schedule(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик подтверждения выбора расписания сессии

    Обрабатывает подтверждение, отмену и возврат в главное меню
    """
    user_id = callback.from_user.id
    us_c = callback.data
    if us_c == 'confirm':
        await callback.answer()
        user_data = await state.get_data()
        await state.clear()
        choice = user_data.get('choice_type')
        raw_rows = [] 
        try:
            if choice == 'group':
                type_choice = user_data.get('another_group')
                if type_choice:
                    raw_rows = await SessionSchedule.get_for_group(session, type_choice)
                else:
                    group_name = await UserFunctions.check_user_group(session, user_id)
                    if group_name:
                        raw_rows = await SessionSchedule.get_for_group(session, group_name)
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  
            elif choice == 'teacher':

                teacher = user_data.get('another_teach')
                if teacher:
                    raw_rows = await SessionSchedule.get_for_teacher(session,teacher, )
                else: 
                    teacher_row = await UserFunctions.check_teacher_name(session,user_id)
                    if teacher_row:
                        raw_rows = await SessionSchedule.get_for_teacher(session,teacher_row, )
                    else:
                        await callback.message.answer(info_not_found, reply_markup= await in_kb.menu_inline_kb())  

            session_msg_text = await session_formatter.format_session(raw_rows, user_data) 

            #if len(schedule_msg_text) > 4096:
            await callback.message.answer(
                session_msg_text, 
                parse_mode="Markdown", 
                reply_markup=await in_kb.menu_inline_kb() 
            )
            await state.set_state(st.MenuState.menu)
        except Exception as e:
            await callback.message.answer(f"Произошла ошибка при получении расписания: {e}",reply_markup= await in_kb.menu_inline_kb() )
            await state.set_state(st.MenuState.menu)
    elif us_c == 'menu':
        await callback.answer()
        await state.clear()
        await state.set_state(st.MenuState.menu)
        try:
            await callback.message.edit_text(menu_text, reply_markup=await in_kb.menu_inline_kb())
        except:
            await callback.message.answer(menu_text, reply_markup=await in_kb.menu_inline_kb())
    else:
        await callback.answer()
        await state.set_state(st.SessionSchedule.select_owner)
        await callback.message.edit_text(get_text, reply_markup=await in_kb.session_inline_kb())   

'''
                     !###############################!
                    -####### Начало работы с КТП #####-
                     !###############################!
'''

@router_schedule.message(F.text.startswith("📚 Найти дни с предметом") | F.text.startswith("Дни с предметом"))
async def get_days_by_lesson(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id
    role = await UserFunctions.check_user_role(session,user_id)
    if role == 'teacher':
        teacher_name = await UserFunctions.check_teacher_name(session, user_id)
        if teacher_name:
            schedule_rows = await EduSchedule.get_for_teacher(session, teacher_name, 0)
            lessons = list(r for r in schedule_rows.lessons)
        else:
            await message.answer("❌ Не найдено ваше ФИО в базе данных", reply_markup=await in_kb.menu_inline_kb())
            return
    else:
        group_row = await UserFunctions.check_user_group(session, user_id)
        if group_row != 'no_group':
            lessons = await GetDataFromSchedule.get_all_lessons_by_group(session, group_row)
        else:
            lessons = await GetDataFromSchedule.get_all_lessons(session,)

    if not lessons:
        await message.answer("❌ Не найдено предметов", reply_markup=await in_kb.menu_inline_kb())
        return

    await message.answer("Выберите предмет:", reply_markup=await re_kb.universal_reply_keyboard(lessons, 2, choose_lesson_ph))
    await state.set_state(st.LessonDays.select_lesson)


@router_schedule.message(st.LessonDays.select_lesson)
async def process_lesson_days(message: Message, state: FSMContext, session: AsyncSession):
    lesson = message.text
    days_info = await GetDataFromSchedule.get_days_by_lesson(session, lesson)

    if not days_info:
        await message.answer(f"❌ Предмет '{lesson}' не найден в расписании", reply_markup=await in_kb.menu_inline_kb())
        await state.clear()
        return

    days_dict = {}
    for day, week, group in days_info:
        if day not in days_dict:
            days_dict[day] = []
        week_text = f"{week} неделя" if week != 0 else "Обе недели"
        days_dict[day].append(f"{week_text} ({group})")

    msg_text = f"📚 Дни с предметом '{lesson}':\n\n"
    for day, weeks_info in days_dict.items():
        msg_text += f"📅 {day}:\n"
        for week_info in weeks_info:
            msg_text += f"  • {week_info}\n"
        msg_text += "\n"

    await message.answer(msg_text, reply_markup=await in_kb.menu_inline_kb())
    await state.set_state(st.MenuState.menu)


