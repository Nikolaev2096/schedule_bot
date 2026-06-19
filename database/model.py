from sqlalchemy import (BigInteger, String, Boolean,
                        SMALLINT, Integer)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine, AsyncSession)

engine = create_async_engine(url='sqlite+aiosqlite:///database/data_base.sqlite3', echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    group_name: Mapped[str] = mapped_column(String(10), nullable=True)
    admin_state: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(7), default='None')
    full_name: Mapped[str] = mapped_column(String(20), nullable=True)
    notification: Mapped[str] = mapped_column(String(6), nullable=True)
    notification_time: Mapped[str] = mapped_column(String(5), nullable = True)


class Schedule(Base):
    __tablename__ = 'schedule'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(10), nullable = False, index=True)
    day_of_week: Mapped[str] = mapped_column(String(13), nullable = False)
    time: Mapped[str] = mapped_column(String(40), nullable = False)
    lesson: Mapped[str] = mapped_column(String(90), nullable = False)
    lesson_type: Mapped[str] = mapped_column(String(80), nullable = False)
    week: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    teacher: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    classroom: Mapped[str] = mapped_column(String(15), nullable=False)
    dates: Mapped[str] = mapped_column(String(40), nullable=True)

class Session(Base):
    __tablename__ = 'session'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(10), nullable = False, index=True)
    day_of_week: Mapped[str] = mapped_column(String(15), nullable = False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    time: Mapped[str] = mapped_column(String(40), nullable=False)
    lesson: Mapped[str] = mapped_column(String(80), nullable = False)
    ex_type: Mapped[str] = mapped_column(String(20), nullable = False)
    teacher: Mapped[str] = mapped_column(String(30),nullable=False, index=True)
    classroom: Mapped[str] = mapped_column(String(15),nullable=False)

async def database_create():
    """
    Создает все таблицы в базе данных на основе моделей SQLAlchemy
    
    Выполняет создание всех таблиц, определенных в моделях, если они еще не существуют.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)