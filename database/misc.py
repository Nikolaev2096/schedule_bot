from database.model import  Schedule, Session
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession


class GetDataFromSchedule:

    @staticmethod
    async def get_all_teachers(session: AsyncSession):
        """
        Получает список всех уникальных преподавателей из расписания
        
        Args:
            session: сессия БД для выполнения запросов
            
        Returns:
            list: список уникальных ФИО преподавателей
        """
        req = select(Schedule.teacher).where(Schedule.teacher.is_not("None")).distinct()
        res = await session.execute(req)
        return res.scalars().all()


    @staticmethod
    async def get_all_rooms(session: AsyncSession):
        """
        Получает список всех уникальных кабинетов/аудиторий из расписания
        
        Args:
            session: сессия БД для выполнения запросов
            
        Returns:
            list: список уникальных номеров кабинетов/аудиторий
        """
        req = select(Schedule.classroom).distinct()
        res = await session.execute(req)
        return res.scalars().all()

    @staticmethod
    async def get_all_lessons_by_group(session: AsyncSession, group):
        """
        Получает список всех предметов для указанной группы
        
        Args:
            session: сессия БД для выполнения запросов
            group: название группы
            
        Returns:
            list: список всех предметов группы (с возможными дубликатами)
        """
        req = select(Schedule.lesson).where(Schedule.group_name == group)
        res = await session.execute(req)
        final_rows = res.scalars().all()
        return final_rows

    @staticmethod
    async def get_days_by_lesson(session: AsyncSession, lesson):
        """
        Получает информацию о днях недели, когда проходит указанный предмет
        
        Args:
            session: сессия БД для выполнения запросов
            lesson: название предмета
            
        Returns:
            list: список кортежей (день недели, номер недели, название группы) для указанного предмета
        """
        req = select(Schedule.day_of_week, Schedule.week, Schedule.group_name).where(Schedule.lesson == lesson)
        res = await session.execute(req)
        return res.all()
    
    @staticmethod
    async def get_all_lessons(session: AsyncSession):
        """
        Получает список всех уникальных предметов из расписания
        
        Args:
            session: сессия БД для выполнения запросов
            
        Returns:
            list: список всех уникальных названий предметов
        """
        req = select(Schedule.lesson).distinct()
        res = await session.execute(req)
        return res.all()

    @staticmethod
    async def check_teacher_exist(session: AsyncSession, teacher : str) -> bool:
        """
        Проверяет наличие учителя в расписании

        Args:
            session: сессия БД для выполнения запросов
            teacher: ФИО преподавателя
        Returns:
            bool: True если преподаватель существует в расписании, False если нет
        """
        teacher_name = teacher.strip()
        req = select(exists().where(Schedule.teacher == teacher_name))
        res = await session.execute(req)
        return res.scalar()
    
    @staticmethod
    async def check_group_in_session(session: AsyncSession, group_name: str) -> bool:
        """
        Проверяет существование группы в расписании сессии
        
        Args:
            session: сессия БД для выполнения запросов
            group_name: название группы для проверки
            
        Returns:
            bool: True если группа существует в расписании сессии, False если нет
        """
        group = group_name.strip()
        req = select(exists().where(Session.group_name == group))
        res = await session.execute(req)
        return res.scalar()
    
    @staticmethod
    async def check_teacher_in_session(session: AsyncSession, teacher: str) -> bool:
        """
        Проверяет наличие преподавателя в расписании сессии
        
        Args:
            session: сессия БД для выполнения запросов
            teacher: ФИО преподавателя
            
        Returns:
            bool: True если преподаватель существует в расписании сессии, False если нет
        """
        teacher_name = teacher.strip()
        req = select(exists().where(Session.teacher == teacher_name))
        res = await session.execute(req)
        return res.scalar()