import asyncio
import logging
import sys

from addons.notifications import send_notifications
from database.midleware import DbSessionMiddleware
from handlers.base_handlers import router_base
from handlers.abitur_handlers import router_abitur
from handlers.schedule_handlers import router_schedule
from handlers.admin_handlers import router_admin
from config_bot import bot, dp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo

from database.model import async_session
from database.model import database_create

scheduler = AsyncIOScheduler()

async def main() -> None:
    await database_create()
    
    scheduler.add_job(send_notifications, 'cron', second=0,  args=[bot, async_session], 
                      month="1,2,3,4,5,6,9,10,11,12",day_of_week="0-4,6",
                      timezone=ZoneInfo("Europe/Moscow"))
    scheduler.start()
    dp.update.middleware(DbSessionMiddleware(async_session))
    dp.include_routers(router_abitur, router_schedule,
                        router_admin, router_base)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except Exception as e:
        print("Exit", e)
    except KeyboardInterrupt:
        print("Exit")