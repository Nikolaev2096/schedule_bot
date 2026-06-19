from database.model import Schedule, Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

'''
                     !##################################!
                    -####### Работа с расписанием #######-
                     !##################################!
'''


class EduSchedule:

    @staticmethod
    def get_week_params(week: int) -> tuple:
        """
        Получает параметры недель для запроса расписания
        
        Args:
            week: номер недели (0 - обе недели, 1 - первая неделя, 2 - вторая неделя)
            
        Returns:
            tuple: кортеж с номерами недель для фильтрации
        """
        if week == 1:
            return (0, 1)
        elif week == 2:
            return (0, 2)
        elif week == 0:
            return (0, 1, 2)
        else:
            return (0, week)


    @staticmethod
    async def get_for_group(session: AsyncSession, group_name: str, week: int):
        """
        Получает расписание для указанной группы
        
        Args:
            session: сессия БД для выполнения запросов
            group_name: название группы
            week: номер недели (0 - обе недели, 1 - первая неделя, 2 - вторая неделя)
            
        Returns:
            list: список объектов Schedule с расписанием группы
        """
        weeks_to_fetch = EduSchedule.get_week_params(week)
        req = select(Schedule).where(Schedule.group_name ==group_name.strip(), Schedule.week.in_(weeks_to_fetch))
        res = await session.execute(req)
        final_rows = res.scalars().all()
        return final_rows

    @staticmethod
    async def get_for_teacher(session: AsyncSession, teacher: str, week: int):
        """
        Получает расписание для указанного преподавателя
        
        Args:
            session: сессия БД для выполнения запросов
            teacher: ФИО преподавателя в формате 'Фамилия И. О.'
            week: номер недели (0 - обе недели, 1 - первая неделя, 2 - вторая неделя)
            
        Returns:
            list: список объектов Schedule с расписанием преподавателя
        """
        weeks_to_fetch = EduSchedule.get_week_params(week)
        req = select(Schedule).where(Schedule.teacher == teacher, Schedule.week.in_(weeks_to_fetch))
        res = await session.execute(req)
        final_rows = res.scalars().all()
        return final_rows

    @staticmethod
    async def get_for_group_by_day(session: AsyncSession, group_name: str, week: int, day: str):
        """
        Получает расписание для указанной группы на конкретный день недели
        
        Args:
            session: сессия БД для выполнения запросов
            group_name: название группы
            week: номер недели (0 - обе недели, 1 - первая неделя, 2 - вторая неделя)
            day: день недели в нижнем регистре (например, 'понедельник', 'вторник')
            
        Returns:
            list: список объектов Schedule с расписанием группы на указанный день
        """
        weeks_to_fetch = EduSchedule.get_week_params(week)
        req = select(Schedule).where(Schedule.group_name == group_name).where(Schedule.week.in_(weeks_to_fetch), Schedule.day_of_week == day)
        res = await session.execute(req)
        final_rows = res.scalars().all()
        return final_rows

    @staticmethod
    async def get_for_teacher_by_day(session: AsyncSession, teacher_name: str, week: int, day: str):
        """
        Получает расписание для указанного преподавателя на конкретный день недели
        
        Args:
            session: сессия БД для выполнения запросов
            teacher_name: ФИО преподавателя в формате 'Фамилия И.О.'
            week: номер недели (0 - обе недели, 1 - первая неделя, 2 - вторая неделя)
            day: день недели в нижнем регистре (например, 'понедельник', 'вторник')
            
        Returns:
            list: список объектов Schedule с расписанием преподавателя на указанный день
        """
        weeks_to_fetch = EduSchedule.get_week_params(week)
        req = select(Schedule).where(Schedule.teacher == teacher_name).where(Schedule.week.in_(weeks_to_fetch), Schedule.day_of_week == day)
        res = await session.execute(req)
        final_rows = res.scalars().all()
        return final_rows

    @staticmethod
    async def get_by_room(session: AsyncSession, room: str, week: int, day: str):
        """
        Получает расписание для указанного кабинета на конкретный день недели
        
        Args:
            session: сессия БД для выполнения запросов
            room: номер кабинета/аудитории
            week: номер недели (0 - обе недели, 1 - первая неделя, 2 - вторая неделя)
            day: день недели в нижнем регистре (например, 'понедельник', 'вторник')
            
        Returns:
            list: список объектов Schedule с расписанием кабинета на указанный день
        """
        weeks_to_fetch = EduSchedule.get_week_params(week)
        req = select(Schedule).where(Schedule.classroom == room).where(Schedule.week.in_(weeks_to_fetch), Schedule.day_of_week == day)
        res = await session.execute(req)
        final_rows = res.scalars().all()
        return final_rows


class SessionSchedule:

    @staticmethod
    async def get_for_group(session:AsyncSession, group_name: str):
        """
        Получает расписание сессии для указанной группы
        
        Args:
            session: сессия БД для выполнения запросов
            group_name: название группы
            
        Returns:
            list: список объектов Session с расписанием сессии группы
        """
        req = select(Session).where(Session.group_name == group_name)
        res = await session.execute(req)
        final_rows = res.scalars().all()
        for row in final_rows:
            print(row)
        return final_rows
    
    @staticmethod
    async def get_for_teacher(session:AsyncSession, teacher: str):
        """
        Получает расписание сессии для указанного преподавателя
        
        Args:
            session: сессия БД для выполнения запросов
            teacher: ФИО преподавателя в формате 'Фамилия И.О.'
            
        Returns:
            list: список объектов Session с расписанием сессии преподавателя
        """
        req = select(Session).where(Session.teacher == teacher)
        res = await session.execute(req)
        final_rows = res.scalars().all()
        return final_rows

