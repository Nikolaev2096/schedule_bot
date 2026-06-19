import re
import docx
from typing import List, Optional, Tuple 
from dataclasses import dataclass

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Schedule

@dataclass
class ScheduleRow:
    group_name: str
    day_of_week: str
    time: str
    lesson: str
    lesson_type: str
    week: int
    teacher: str
    classroom: str
    dates: str = ""  

def clean_text(text: str) -> str:
    """Базовая очистка: удаление лишних пробелов и невидимых символов"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def smart_split_classroom(text: str) -> List[str]:
    """
    Разделение строки с кабинетами
    """
    text = clean_text(text)
    if not text:
        return []

    
    parts = re.split(r'[;\n/,]+', text)
    
    final_parts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
       
        match_complex = re.match(r'^([А-Яа-яЁёA-Za-z]{3,})\s+(\d{1,4}[а-я]?)$', part)
        
        exceptions = ['ауд', 'каб']
        
        if match_complex:
            word, number = match_complex.groups()
            if word.lower() not in exceptions:
                final_parts.append(word)
                final_parts.append(number)
                continue

        final_parts.append(part)

    return final_parts


def extract_dates_from_text(text: str) -> Tuple[str, str]:
    """
    Поиск даты в тексте.
    Поддерживает форматы: (12.09), 12.09, до 12.09, 12.09, 13.09
    """
    if not text:
        return "", ""

    dates_pattern = re.compile(
        r'(?:^|\s|\(|до|с)\s*(\d{1,2}\.\d{1,2}(?:[;,\s]+\d{1,2}\.\d{1,2})*)(?:\)|$|\s)', 
        re.IGNORECASE
    )
    
    match = dates_pattern.search(text)
    dates = ""
    clean_text_str = text

    if match:
        candidate = match.group(1)
        
        if '.' in candidate and any(c.isdigit() for c in candidate):
            dates = candidate.strip(' .,;')
            
            clean_text_str = text.replace(match.group(0).strip(), " ").strip()
            
            clean_text_str = re.sub(r'\(\s*\)', '', clean_text_str)
            clean_text_str = clean_text_str.strip(' ,;')
            
            clean_text_str = re.sub(r'\s+', ' ', clean_text_str)

    return clean_text(clean_text_str), dates


def split_lesson_names(text: str) -> List[str]:

    """
    Разрезает строку, если в ней несколько названий предметов.
    Пример: 'Основы безопасности Индивидуальный проект' 
    Полагаемся на то, что новое название начинается с Заглавной буквы.
    """

    exceptions = ('Родина', "Родины", 'ИКТ', "Исполнитель", "ИС", 
                  "России", "Фонда", "Российской", "Российской Федерации", "Федерации", 
                  "Адаптивные", "Адаптивная")
    words = text.split()
    result = []
    buffer = words[0]

    for prev, current in zip(words, words[1:]):
        if current in exceptions:
            buffer += " " + current
       
        elif re.search(r'[а-яё]$', prev) and re.match(r'[А-ЯЁ]', current):
            result.append(clean_text(buffer))
            buffer = current
        else:
            buffer += " " + current
    return [clean_text(buffer)]
 

def extract_week_and_clean_type(text: str) -> Tuple[int, str]:
    """
    Попытка достать неделю и очистить тип занятия 
    """
    if not text:
        return 0, ""

    week = 0
    if re.search(r'\b1\s*н(ед|\.)?', text):
        week = 1
    elif re.search(r'\b2\s*н(ед|\.)?', text):
        week = 2

    clean_type = re.sub(
        r'\b[12]\s*н(ед|\.)?[.,]?\s*',
        '',
        text
    ).strip()

    return week, clean_type

def split_cell_text(text: str) -> List[str]:
    """Разбивка содержимого ячейки по строкам """
    if not text:
        return []
    return [clean_text(t) for t in text.split('\n') if clean_text(t)]

def extract_data_from_docx(docx_file: str) -> List[ScheduleRow]:
    doc = docx.Document(docx_file)
    processed_data = []
    current_group = None

    for block in doc.element.body:
        if block.tag.endswith('p'):
            text = block.text.strip() if block.text else ""
            if text.startswith("Группа"):
                try:
                    current_group = text.split(" ", 1)[1].strip().upper()
                except IndexError:
                    pass

        elif block.tag.endswith('tbl'):
            if not current_group:
                continue
            table = docx.table.Table(block, doc) # pyright: ignore[reportAttributeAccessIssue]
            processed_data.extend(_process_schedule_table(table, current_group))

    return processed_data

def _process_schedule_table(table, group_name: str) -> List[ScheduleRow]:
    rows_data = []
    current_day = None

    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        if len(cells) < 6: continue
        if not any(cells) or any("Время занятий" in c for c in cells): continue

        if cells[0]:
            current_day = cells[0].strip().capitalize()
        if not current_day: continue

        time_db = re.sub(r'\s*\n\s*', ' / ', cells[1]).strip()

        raw_lessons_lines = split_cell_text(cells[2])
        final_lessons = []
        for line in raw_lessons_lines:
            final_lessons.extend(split_lesson_names(line))

        raw_types_lines = split_cell_text(cells[3])
        processed_types = []
        processed_dates = []

        for line in raw_types_lines:
            sub_types = split_lesson_types(line)
            
            for st in sub_types:
                t_clean, d_extracted = extract_dates_from_text(st)
                
                is_just_date = len(re.sub(r'[^а-яА-Яa-zA-Z]', '', t_clean)) < 2
                
                if is_just_date and len(processed_types) > 0:
                    if d_extracted:
                        idx = len(processed_types) - 1
                        processed_dates[idx] = (processed_dates[idx] + ", " + d_extracted).strip(", ")
                else:
                    processed_types.append(t_clean)
                    processed_dates.append(d_extracted)

        raw_teachers = split_cell_text(cells[4])
        raw_classrooms = split_cell_text(cells[5]) if '\n' in cells[5] else smart_split_classroom(cells[5])

        max_len = max(len(final_lessons), len(processed_types), len(raw_teachers))

        for i in range(max_len):
            def get_val(lst: List[str], idx: int, broadcast_single: bool = False) -> str:
                if not lst: return ""
                if idx < len(lst): return lst[idx]
                if broadcast_single and len(lst) == 1: return lst[0]
                return ""

            lesson = get_val(final_lessons, i, broadcast_single=True)
            curr_type_full = get_val(processed_types, i)
            curr_dates = get_val(processed_dates, i)
            teacher = get_val(raw_teachers, i, broadcast_single=True)
            classroom = get_val(raw_classrooms, i, broadcast_single=True)

            week, clean_type_str = extract_week_and_clean_type(curr_type_full)

            if not lesson and not teacher:
                continue

            record = ScheduleRow(
                group_name=group_name,
                day_of_week=current_day,
                time=time_db,
                lesson=lesson,
                lesson_type=clean_type_str if clean_type_str else "None",
                week=week,
                teacher=teacher if teacher else "None",
                classroom=classroom if classroom else "None",
                dates=curr_dates
            )
            rows_data.append(record)

    return rows_data


def split_lesson_types(text: str) -> List[str]:
    """
    Разбивает слипшиеся типы занятий.
    Примеры: 
    'Лекция1нед. Практические занятия' -> ['Лекция 1нед.', 'Практические занятия']
    'Практические занятия Практические занятия' -> ['Практические занятия', 'Практические занятия']
    """
    if not text:
        return []


    text = re.sub(r'(\d)\s*(нед)', r' \1 \2', text)
    keywords = ['Лекция', 'Практические занятия', 'Лабораторные занятия', 'Семинар', 'Консультация']
    pattern = '|'.join(keywords)
    parts = re.findall(r'(?:' + pattern + r').*?(?=(?:' + pattern + r')|$)', text, re.IGNORECASE)

    if parts:
        return [clean_text(p) for p in parts]

    return [clean_text(text)]

async def post_process_schedule_data(session: AsyncSession):
    """
    Финальная зачистка:
    1. Убирает дубликаты 
    2. Заполняет пропуски, которые не смог решить парсер 
    """
    stmt = select(Schedule).order_by(Schedule.id)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    
 
    records = []
    for r in rows:
        records.append({"obj": r, "vals": {
            "lesson": r.lesson, "type": r.lesson_type, 
            "teacher": r.teacher, "room": r.classroom
        }})

    ids_to_delete = set()

    for i in range(1, len(records)):
        prev = records[i-1]
        curr = records[i]
        
        if (prev["obj"].group_name == curr["obj"].group_name and 
            prev["obj"].day_of_week == curr["obj"].day_of_week and 
            prev["obj"].time == curr["obj"].time):
            
            if (curr["vals"] == prev["vals"]):
                ids_to_delete.add(curr["obj"].id)
                continue

            
            if curr["vals"]["room"] in ("None", "") and prev["vals"]["room"] not in ("None", ""):
                curr["vals"]["room"] = prev["vals"]["room"]
                await session.execute(
                    update(Schedule).where(Schedule.id == curr["obj"].id).values(classroom=prev["vals"]["room"])
                )

    if ids_to_delete:
        await session.execute(delete(Schedule).where(Schedule.id.in_(ids_to_delete)))
    
    await session.commit()


def extract_surname_and_initials(name: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Извлекает фамилию и инициалы из строки
    
    Args:
        name (str): Строка с именем 
        
    Returns:
        Tuple: (Фамилия, Инициал1, Инициал2) или (name, None, None), если не удалось распарсить
    """
    name = name.strip().replace(",", ".").replace("  ", " ")

    match = re.match(r'^([А-ЯЁа-яё]+)(?:\s+([А-ЯЁ])\.?\s*([А-ЯЁ])\.?)?$', name)
    
    if not match:
        return name, None, None

    return match.groups() # pyright: ignore[reportReturnType]

async def restore_teacher_initials(session: AsyncSession):
    """
    Проходит по БД и приводит имена преподавателей к единому формату
    Восстанавливает инициалы, если где-то записана только фамилия, но в других строках есть полные данные
    
    Args:
        session (AsyncSession): Сессия БД
        
    Returns:
        None
    """
   
    stmt = select(Schedule.teacher).distinct()
    result = await session.execute(stmt)
    teachers_db = [t for t in result.scalars().all() if t]

    initials_index = {}
    for t in teachers_db:
        surname, i1, i2 = extract_surname_and_initials(t)
        if surname and i1 and i2:
            initials_index[surname] = (i1.upper(), i2.upper())

    for original in teachers_db:
        surname, i1, i2 = extract_surname_and_initials(original)
        
        if not i1 or not i2:
            found = initials_index.get(surname)
            if found:
                i1, i2 = found
        
        if i1 and i2:
            normalized = f"{surname} {i1}.{i2}."
            if normalized != original:
                await session.execute(
                    update(Schedule).where(Schedule.teacher == original).values(teacher=normalized)
                )
    
    await session.commit()


async def distribute_teachers_by_week(session: AsyncSession):
    """
    Разносит сдвоенных преподавателей по неделям.
    Логика: Первое имя - 1 неделя, Второе имя - 2 неделя
    """
  
    stmt = select(Schedule).where(Schedule.teacher.is_not(None))
    result = await session.execute(stmt)
    rows = result.scalars().all()


    pattern = re.compile(
        r'^([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.?\s*[А-ЯЁ]\.?)\s+([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.?\s*[А-ЯЁ]\.?)$'
    )

    for row in rows:
        teacher_text = clean_text(row.teacher) 
        match = pattern.match(teacher_text)

        if not match:
            continue

        teacher_1, teacher_2 = match.groups()

        if row.week == 1:
            row.teacher = teacher_1
            session.add(row)
        elif row.week == 2:
            row.teacher = teacher_2
            session.add(row)
        else:
            row.teacher = teacher_1
            session.add(row)

    await session.commit()

async def split_sport_rooms(session: AsyncSession):
    req = select(Schedule).where(Schedule.classroom.startswith('Спорт'))
    res = await session.execute(req)
    rows = res.scalars().all()
    pattern = re.compile(r'Иванов[а-я]*\s+[А-ЯЁ]\.?\s*[А-ЯЁ]\.?')
    for row in rows:
        teacher_text = clean_text(row.teacher) 
        match = pattern.match(teacher_text)
        if not match:
            continue
        else: 
            row.classroom = 'Спортзал (модуль)'
            session.add(row)
    await session.commit()

async def start_conversation(file_path: str, session: AsyncSession) -> bool:
    
    """
    Точка входа 

    Args:
        file_path (str): Путь к файлу 
        session (AsyncSession): Сессия БД
    """

    try:
        if not file_path.endswith(".docx"):
            return False

        raw_data = extract_data_from_docx(file_path)
        
        if not raw_data:
            return False

        await session.execute(delete(Schedule))
        
        schedule_objects = [
            Schedule(
                group_name=row.group_name,
                day_of_week=row.day_of_week,
                time=row.time,
                lesson=row.lesson,
                lesson_type=row.lesson_type,
                week=row.week,
                teacher=row.teacher,
                classroom=row.classroom,
                dates=row.dates
            ) for row in raw_data
        ]
        
        session.add_all(schedule_objects)
        await session.commit()

        await post_process_schedule_data(session)
        await restore_teacher_initials(session)
        await distribute_teachers_by_week(session)
        await split_sport_rooms(session)
        return True
    except:  
        return False