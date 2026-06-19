from typing import List
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Users
from config_bot import bot
from database.user_func import UserFunctions
from addons.weeks import get_current_week
from database.schedule_func import EduSchedule
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from templates.schedule_template import *
from templates.txt_templates import notif_admin_message_prefix
from zoneinfo import ZoneInfo

DAYS = {
            0: "понедельник",
            1: "вторник",
            2: "среда",
            3: "четверг",
            4: "пятница",
            5: "суббота",
            6: "воскресенье"
        }

async def send_notification_to_group(group_name: str, message_text: str, session: AsyncSession, sound: bool = True):
    """
    Отправка уведомления определенной группе студентов

    Args:
        group_name: название группы
        message_text: текст уведомления
        session: сессия БД
        sound: True - со звуком, False - беззвучное уведомление
    """
    req = select(Users.id).where(Users.group_name == group_name)
    res = await session.execute(req)
    users = res.scalars().all()
    
    if not users:
        return
    
    full_text = f"{notif_admin_message_prefix}\n\n{message_text}"

    for user_id in users:
        try:
            if user_id:
                await bot.send_message(
                    chat_id=user_id,
                    text=full_text,
                    disable_notification=not sound,  # True = со звуком, False = без звука
                    parse_mode="Markdown",
                )
        except Exception:
            continue


async def send_notification_to_group_of_users(users_role: str, message_text: str, session: AsyncSession, sound: bool = True):
    """
    Отправка уведомления пользователям с определенной ролью

    Args:
        users_role: роль пользователей ('user', 'teacher', 'abitur')
        message_text: текст уведомления
        session: сессия БД
        sound: True - со звуком, False - беззвучное уведомление
    """
   
    users = await UserFunctions.get_users_id_by_role(session, users_role)

    if not users:
        return

   
    full_text = f"{notif_admin_message_prefix}\n\n{message_text}"

    for user_id in users:
        try:
            if user_id:
                await bot.send_message(
                    chat_id=user_id,
                    text=full_text,
                    disable_notification=not sound,  # True = со звуком, False = без звука
                    parse_mode="Markdown",
                )
        except Exception:
            continue


async def send_notification_to_admins(message_text: str, session: AsyncSession, sound: bool = True, admin_id: int = None):
    '''
    Отправка уведомления всем администраторам бота

    Args:
        message_text: текст уведомления
        session: сессия БД
        sound: True - со звуком, False - беззвучное уведомление
        admin_id: ID администратора, который отправляет (исключается из рассылки)
    '''
    req = select(Users.id).where(Users.admin_state == True)
    res = await session.execute(req)
    users = res.scalars().all()
    
    if not users:
        return
    
    full_text = f"{notif_admin_message_prefix}\n\n{message_text}"
    
    for user_id in users:
        try:
            if user_id == admin_id:
                continue
            await bot.send_message(
                chat_id=user_id,
                text=full_text,
                disable_notification=not sound,  # True = со звуком, False = без звука
                parse_mode="Markdown",
            )
        except Exception:
            continue


async def send_notification_to_all_users(message_text: str, session: AsyncSession, sound: bool = True, admin_id: int = None):
    '''
    Отправка уведомления всем пользователям бота

    Args:
        message_text: текст уведомления
        session: сессия БД
        sound: True - со звуком, False - беззвучное уведомление
        admin_id: ID администратора, который отправляет (исключается из рассылки)
    '''
    users = await UserFunctions.get_all_users_id(session)
    
    for user_id in users:
        try:
            if user_id == admin_id:
                continue
            await bot.send_message(
                chat_id=user_id,
                text=message_text,
                disable_notification=not sound,  # Инвертируем логику: True = со звуком, False = без звука
                parse_mode="Markdown",
            )
        except Exception:
            continue



async def send_notifications(bot: Bot, session_maker: async_sessionmaker) -> None:
    """
    Автоматическая рассылка расписания на следующий день пользователям, настроившим уведомления

    Args:
        bot: экземпляр бота
        session_maker: фабрика сессий БД

    """
    async with session_maker() as session:
        current_time_str = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%H:%M")
        tomorrow_date = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(days=1)
        tomorrow_weekday_idx = tomorrow_date.weekday()
        cur_day = DAYS[tomorrow_weekday_idx]
        
     
        if cur_day.lower() == 'воскресенье':
            return None
            
        current_week = await get_current_week()
        
        if cur_day == 'понедельник':
            current_week += 1
            if current_week > 2:
                current_week = 1
                
        data = {"choice_type": "day", "week_number": current_week, 'day': 'Завтра', 'current': True}
        first_arr: List[Users] = await UserFunctions.get_users_for_send_notifications(session, current_time_str)

        if not first_arr:
            return None
        for row in first_arr:
            try:
                notification_type = row.notification
                role = row.role
                text_rows = None
                
                if role == 'user':
                    group = row.group_name
                    if group:
                        text_rows = await EduSchedule.get_for_group_by_day(session, group, current_week, cur_day.capitalize())
                elif role == 'teacher':
                    name = row.full_name
                    if name:
                        text_rows = await EduSchedule.get_for_teacher_by_day(session, name, current_week, cur_day.capitalize())
                
                if text_rows:
                    message_text = await formatter.format_schedule(text_rows, data, role)
            
                    disable_notif = (notification_type == 'silent') if notification_type else False
                    await bot.send_message(
                        chat_id=row.id,
                        text=message_text,
                        disable_notification=disable_notif,
                        parse_mode="Markdown",
                    )
                else:
                    continue
            except Exception:
                continue
        return None