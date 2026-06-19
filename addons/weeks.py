import json
import datetime as dt
import aiofiles
import os

path = 'config.json'
default_data = {"week_inverse": 0, "half_year_num": 0}

async def get_current_week():
    """
    Получение номера текущей недели (1 или 2)
    Returns:
        Номер недели в расписании (1\2)
    """
    inverse = await get_inverse_week()
    day = dt.date.today()
    week = day.isocalendar()[1]
    if inverse == 1:
        week +=1
    if week % 2 == 0:
        return 2
    else:
        return 1
    
def get_week_num():
    """
    Получение номера текущей недели от начала года
    Returns:
        Номер недели в году
    """
    day = dt.date.today()
    week = day.isocalendar()[1]
    return week


async def get_inverse_week():
    """
    Получение информации о сдвиге недель
    Returns:
        Состояние сдвига недели
    """
    if not os.path.exists(path):
        async with aiofiles.open(path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(default_data, ensure_ascii=False, indent=4))
        return default_data["week_inverse"]
    async with aiofiles.open(path, 'r', encoding='utf-8') as file:
        text = await file.read()
    if not text.strip():
        async with aiofiles.open(path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(default_data, ensure_ascii=False, indent=4))
        return default_data["week_inverse"]
    try:
        data = json.loads(text)
        return data["week_inverse"]
    except json.JSONDecodeError:
        async with aiofiles.open(path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(default_data, ensure_ascii=False, indent=4))
        return default_data["week_inverse"]
    
async def get_half_year_num():
    """
    Получение информации о текущем полугодии
    Returns:
        Номер полугодия
    """
    if not os.path.exists(path):
        async with aiofiles.open(path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(default_data, ensure_ascii=False, indent=4))
        return default_data["half_year_num"]
    async with aiofiles.open(path, 'r', encoding='utf-8') as file:
        text = await file.read()
    if not text.strip():
        async with aiofiles.open(path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(default_data, ensure_ascii=False, indent=4))
        return default_data["week_inverse"]
    try:
        data = json.loads(text)
        return data["week_inverse"]
    except json.JSONDecodeError:
        async with aiofiles.open(path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(default_data, ensure_ascii=False, indent=4))
        return default_data["week_inverse"]
    
async def write_shift_week_and_year_half(shift, half):
    """
    Обновление данных о сдвиге и номере полугодия
    Args:
        shift: Состояние сдвига (0 (выкл) или 1 (вкл))
        half: Номер полугодия (0 (первое) или 1 (второе))
    """
    data = {"week_inverse": 1 if shift == 1 else 0,
                "half_year_num": 1 if half == 1 else 0}
    async with aiofiles.open(path, 'w') as file:
        await file.write(json.dumps(data, ensure_ascii=False, indent=4))
        await file.close()

