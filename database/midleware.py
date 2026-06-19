from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

'''
                     !#####################################!
                    -####### Middleware для БД #######-
                     !#####################################!
'''

class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для автоматического управления сессиями БД в обработчиках aiogram
    
    Автоматически создает сессию БД для каждого обработчика и передает ее через data["session"]
    """
    def __init__(self, session_pool: async_sessionmaker):
        """
        Инициализация middleware с пулом сессий
        
        Args:
            session_pool: фабрика сессий БД (async_sessionmaker) для создания сессий
        """
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обработка события с автоматическим созданием сессии БД
        
        Args:
            handler: обработчик события от aiogram
            event: объект события Telegram (Message, CallbackQuery
            data: словарь с дополнительными данными для обработчика
            
        Returns:
            результат выполнения обработчика
        """
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)