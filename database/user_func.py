from sqlalchemy import select, update, delete, func, exists
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Users, Schedule
from config_bot import OWNER_ID


'''
                     !#####################################!
                    -####### Работа с пользователями #######-
                     !#####################################!
'''


class UserFunctions:

    @staticmethod
    async def add_user(session: AsyncSession, us_id:int):
        """
        Добавляет нового пользователя в базу данных
        
        Args:
            session: сессия БД для выполнения запросов
            us_id: ID пользователя в Telegram
            us_nm: имя пользователя в Telegram
        """
        is_admin = (us_id == OWNER_ID)

        user = Users(
            id=us_id,
            
            group_name=None,
            admin_state=is_admin,
            role="None",
            full_name=None,
            notification=None,
            notification_time = None

        )

        await session.merge(user)
        await session.commit()

    @staticmethod
    async def change_user_role(session: AsyncSession, us_id: int, role: str):
        """
        Изменяет роль пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            us_id: ID пользователя в Telegram
            role: новая роль пользователя ('user', 'teacher', 'abitur', 'None')
        """
        is_admin = (us_id == OWNER_ID)
        user = Users(
                id=us_id,
                role=role,
                admin_state=is_admin,
                group_name=None,
                full_name=None
            )
        await session.merge(user)
        await session.commit()

    @staticmethod
    async def check_user_role(session: AsyncSession, us_id:int):
        """
        Проверяет роль пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            us_id: ID пользователя в Telegram
            
        Returns:
            str или None: роль пользователя или None, если пользователь не найден
        """
        try:
            req = select(Users.role).where(Users.id == us_id)
            res = await session.execute(req)
            role =  res.scalar_one_or_none()
            return role
        except TypeError:
            return None

    @staticmethod
    async def check_user_group(session: AsyncSession,  us_id:int):
        """
        Проверяет группу пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            us_id: ID пользователя в Telegram
            
        Returns:
            str или None: название группы или None, если группа не установлена
        """
        try:
            req = select(Users.group_name).where(Users.id == us_id)
            res = await session.execute(req)
            group_name =  res.scalar_one_or_none()
            return group_name
        except TypeError:
            return None

    @staticmethod
    async def change_user_group(session: AsyncSession, user_id:int, group_name:str):
        """
        Изменяет группу пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram
            group_name: новое название группы
        """
        try:
            is_admin = (user_id == OWNER_ID)
            req = update(Users).where(Users.id == user_id).values(group_name = group_name, admin_state = is_admin)
            await session.execute(req)
            await session.commit()
        except TypeError:
            return None


    @staticmethod
    async def change_teacher_name(session: AsyncSession, user_id: int, full_name: str):
        """
        Изменяет ФИО преподавателя
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram
            full_name: новое ФИО преподавателя в формате 'Фамилия И.О.'
        """
        is_admin = (user_id == OWNER_ID)
        req = update(Users).where(Users.id == user_id).values(full_name = full_name, admin_state = is_admin)
        await session.execute(req)
        await session.commit()

    @staticmethod
    async def get_user_info_by_id(session: AsyncSession, user_id):
        """
        Получает полную информацию о пользователе по его ID
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram
            
        Returns:
            list: список объектов Users с информацией о пользователе
        """
        req = select(Users).where(Users.id == user_id)
        res = await session.execute(req)
        final_rows =  res.scalars().all()
        return final_rows

    @staticmethod
    async def delete_user(session: AsyncSession, user_id) -> None:
        """
        Удаляет пользователя из базы данных
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram для удаления
        """
        req = delete(Users).where(Users.id == user_id)
        await session.execute(req)
        await session.commit()

    @staticmethod
    async def get_only_one_group_users(session: AsyncSession, group_name) -> int:
        """
        Получает количество пользователей в указанной группе
        
        Args:
            session: сессия БД для выполнения запросов
            group_name: название группы
            
        Returns:
            list: список с количеством пользователей в группе
        """
        req = select(func.count(Users)).where(Users.group_name == group_name)
        res = await session.execute(req)
        return res.scalars().all()

    @staticmethod
    async def get_users_id_by_role(session: AsyncSession, role: str) -> int:
        """
        Получает список ID всех пользователей с указанной ролью
        
        Args:
            session: сессия БД для выполнения запросов
            role: роль пользователей ('user', 'teacher', 'abitur', 'None')
            
        Returns:
            list: список ID пользователей с указанной ролью
        """
        req = select(Users.id).where(Users.role == role)
        res = await session.execute(req)
        return res.scalars().all()

    @staticmethod
    async def get_all_admins_info(session: AsyncSession):
        """
        Получает список всех администраторов с их информацией
        
        Args:
            session: сессия БД для выполнения запросов
            
        Returns:
            list: список объектов Users с информацией об администраторах
        """
        req = select(Users).where(Users.admin_state == True)
        res = await session.execute(req)
        return res.scalars().all()
    
    @staticmethod
    async def set_admin_rights(session: AsyncSession, user_id:int, state: bool) -> None:
        """
        Устанавливает или снимает права администратора для пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram
            state: True - назначить права администратора, False - снять права
        """
        req = (update(Users).where(Users.id == user_id).values(admin_state=state))
        await session.execute(req)
        await session.commit()
    
    @staticmethod
    async def get_all_users_count(session: AsyncSession) -> int:
        """
        Получает общее количество пользователей в системе
        
        Args:
            session: сессия БД для выполнения запросов
            
        Returns:
            int: общее количество пользователей
        """
        req = select(func.count(Users.id))
        res = await session.execute(req)
        return  res.scalar()
    
    @staticmethod
    async def get_groups_members_count(session: AsyncSession):
        '''
        Получает статистику по группам (название группы и количество пользователей)
        
        Returns:
            dict: словарь с ключом - название группы, значением - количество пользователей
        '''
        req = select(Users.group_name, func.count(Users.id).label('count')).group_by(Users.group_name)
        res = await session.execute(req)
        rows = res.all()
        result = {}
        for row in rows:
            if row[0]: 
                result[row[0]] = row[1]
        return result


    @staticmethod
    async def get_all_users_id(session: AsyncSession):
        """
        Получает список ID всех пользователей системы
        
        Args:
            session: сессия БД для выполнения запросов
            
        Returns:
            list: список ID всех пользователей
        """
        req = select(Users.id)
        res = await session.execute(req)
        return res.scalars().all()

    @staticmethod
    async def check_admin_rights_by_id(session: AsyncSession,  user_id: int):
        """
        Проверяет наличие прав администратора у пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram
            
        Returns:
            bool или None: True если есть права администратора, False если нет, None если пользователь не найден
        """
        req = select(Users.admin_state).where(Users.id == user_id)
        res = await session.execute(req)
        return  res.scalar_one_or_none()

    @staticmethod
    async def check_teacher_name(session: AsyncSession, user_id):
        """
        Получает ФИО преподавателя по ID пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram
            
        Returns:
            str или None: ФИО преподавателя или None, если не установлено
        """
        req = select(Users.full_name).where(Users.id == user_id)
        res = await session.execute(req)
        return  res.scalar_one_or_none()
    
    @staticmethod
    async def check_admin_by_group(session: AsyncSession, group: str) -> bool:
        """
        Проверяет наличие администратора в указанной группе
        
        Args:
            session: сессия БД для выполнения запросов
            group: название группы для проверки
            
        Returns:
            bool: True если в группе есть администратор, False если нет
        """
        req = select(Users.group_name).where(Users.group_name == group, Users.admin_state == True).limit(1)
        res = await session.execute(req)
        return  res.scalar() is not None

    @staticmethod
    async def check_admin_exist_by_gr(user_id: int, session: AsyncSession) -> bool:
        role = await UserFunctions.check_user_role(session, user_id)

        if role != 'user':
            return True

        group = await UserFunctions.check_user_group(session, user_id)
        admin_exists = await UserFunctions.check_admin_by_group(session, group)

        # Можно назначить ТОЛЬКО если администратора нет
        return not admin_exists

    @staticmethod
    async def get_users_for_send_notifications(session: AsyncSession, time: str):
            """
            Получает список пользователей, настроивших уведомления на указанное время
            
            Args:
                session: сессия БД для выполнения запросов
                time: время уведомлений в формате 'ЧЧ:ММ' (например, '07:15')
                
            Returns:
                list: список объектов Users с пользователями, настроившими уведомления на указанное время
            """
            req = select(Users).where(
                Users.notification_time == time,
                Users.notification_time.isnot(None)
            )
            res = await session.execute(req)
            final_rows = res.scalars().all()
            return final_rows

    @staticmethod
    async def insert_time_and_notification_type(session: AsyncSession, user_id: int, time, type_notif):
        """
        Устанавливает время и тип уведомлений для пользователя
        
        Args:
            session: сессия БД для выполнения запросов
            user_id: ID пользователя в Telegram
            time: время уведомлений в формате 'ЧЧ:ММ' (например, '07:15')
            type_notif: тип уведомлений (True - беззвучные 'silent', False - со звуком 'sound')
        """
        if type_notif and time is None:
            req = update(Users).where(Users.id == user_id).values(notification=None, notification_time=None)
        else:
            
            notification_str = (
            'sound' if type_notif == True
            else 'silent' if type_notif == False
            else None
        )
            req = update(Users).where(Users.id == user_id).values(notification=notification_str, notification_time=time)
        await session.execute(req)
        await session.commit()

'''
                     !###############################!
                    -####### Работа с группами #######-
                     !###############################!
'''

class Groups:

    @staticmethod
    async def get_all_groups(session: AsyncSession):
        """
        Получает список всех групп из расписания
        
        Args:
            session: сессия БД для выполнения запросов
            
        Returns:
            list: список уникальных названий групп
        """
        req = select(Schedule.group_name).distinct()
        res = await session.execute(req)
        return res.scalars().all()

    @staticmethod
    async def check_group(session: AsyncSession, group_name : str) -> bool:
        """
        Проверяет существование группы в расписании
        
        Args:
            session: сессия БД для выполнения запросов
            group_name: название группы для проверки
            
        Returns:
            bool: True если группа существует в расписании, False если нет
        """
        group = group_name.strip()
        req = select(exists().where(Schedule.group_name == group))
        res = await session.execute(req)
        return res.scalar()

