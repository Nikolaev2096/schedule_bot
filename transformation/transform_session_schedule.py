import docx
import re

from typing import List, Tuple
from database.model import Session
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy import delete
HEADER_KEYWORDS = {
                    "экзамены": "Экзамен", "дифференцированные зачеты": "Дифф. зачет",
                    "зачеты": "Зачет", "консультации": "Консультация", "другие формы контроля": "Другое"
                }

DAYS = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")

CURRENT_YEAR = datetime.now().year

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def normalize_teacher(text: str) -> str:

    junk = ["аттестационная комиссия", "преподавателя", "преподаватель", ":", ","]
    clean = text
    for word in junk:
        clean = re.sub(word, ' ', clean, flags=re.IGNORECASE)

    pattern = r'([А-ЯЁ][а-яё]+)\s+([А-ЯЁ])\.\s*([А-ЯЁ])\.'
    matches = re.findall(pattern, clean)
    
    if matches:
        formatted_names = []
        for surname, i1, i2 in matches:
            formatted_names.append(f"{surname} {i1}.{i2}.")
        return ", ".join(formatted_names)
    
    cleaned_text = clean_text(clean)
    return cleaned_text if len(cleaned_text) > 2 else ""

def parse_date_and_day_full(date_text: str) -> Tuple[str, str]:

    text = date_text.lower()
    
    date_match = re.search(r'(\d{1,2})\.(\d{2})', text)
    formatted_date = ""
    
    if date_match:
        day_digit = date_match.group(1).zfill(2)
        month_digit = date_match.group(2)
        formatted_date = f"{day_digit}.{month_digit}.{CURRENT_YEAR}"
    

    day_name = "Не указан"
    for d in DAYS:
        if d in text:
            day_name = d.capitalize()
            break
            
    return formatted_date, day_name

def merge_date_and_day(raw_date_cell: str) -> List[str]:
    if not raw_date_cell:
        return []
    parts = [p.strip() for p in raw_date_cell.split('\n') if p.strip()]
    merged = []
    i = 0
    while i < len(parts):
        current = parts[i]
        if i + 1 < len(parts):
            next_part = parts[i+1].lower()
            is_date = re.search(r'\d', current)
            is_day_name = any(d in next_part for d in DAYS)
            
            if is_date and is_day_name:
                merged.append(f"{current} {parts[i+1]}")
                i += 2
                continue
        merged.append(current)
        i += 1
    return merged


def extract_session_data(docx_file: str) -> List[tuple]:
    doc = docx.Document(docx_file)
    processed_data = []
    
    current_group = None
    for block in doc.element.body:
        if block.tag.endswith('p'):
            text = block.text.strip()
            if "Группа" in text:
                parts = text.split("Группа")
                if len(parts) > 1:
                    current_group = parts[1].strip()

        elif block.tag.endswith('tbl'):
            if not current_group:
                continue

            table = docx.table.Table(block, doc) # pyright: ignore[reportAttributeAccessIssue]
            current_ex_type = "Прочее" 

            for row in table.rows:
                cells = row.cells
                row_text = [clean_text(c.text) for c in cells]
                
                if not any(row_text): continue

                full_row_str = " ".join(row_text).lower()
                first_cell_lower = row_text[0].lower() if row_text else ""

                
                is_header = False
                if len(row_text) > 0 and "наименование" in row_text[0].lower(): is_header = True
                elif len(row_text) > 1 and "фамилия" in row_text[1].lower(): is_header = True
                
                if not is_header:
                    for kw, val in HEADER_KEYWORDS.items():
                        if kw == first_cell_lower or (kw in full_row_str and len(full_row_str) < 60):
                            current_ex_type = val
                            is_header = True
                            break
                    if "дифференцированные" in first_cell_lower and "зачеты" in first_cell_lower:
                        current_ex_type = "Дифф. зачет"
                        is_header = True
                
                if is_header: continue

                try:
                    lesson_raw = cells[0].text
                    teacher_raw = cells[1].text
                    date_raw = cells[2].text
                    time_raw = cells[3].text
                    room_raw = cells[4].text
                except IndexError: continue


                if clean_text(lesson_raw).lower() in HEADER_KEYWORDS: continue

                lessons = [t for t in lesson_raw.split('\n') if t.strip()]
                dates_full = merge_date_and_day(date_raw)
                times = [t for t in time_raw.split('\n') if t.strip()]
                teachers_split = [t for t in teacher_raw.split('\n') if t.strip()]
                rooms = [t for t in room_raw.split('\n') if t.strip()]

                max_records = max(len(lessons), len(dates_full), len(times), len(teachers_split))
                if max_records == 0: continue

                for idx in range(max_records):
                    les = lessons[idx] if idx < len(lessons) else (lessons[-1] if lessons else "")
                    
                    t_raw = teachers_split[idx] if idx < len(teachers_split) else (teachers_split[-1] if teachers_split else "")
                    teach_clean = normalize_teacher(t_raw)
                    
                    d_raw = dates_full[idx] if idx < len(dates_full) else (dates_full[-1] if dates_full else "")
                    tm = times[idx] if idx < len(times) else (times[-1] if times else "")
                    rm = rooms[idx] if idx < len(rooms) else (rooms[-1] if rooms else "")

                    date_formatted, day_name = parse_date_and_day_full(d_raw)

                    if not les and not teach_clean: continue
                    if les.lower() == current_ex_type.lower(): continue

                    processed_data.append((
                        current_group,
                        day_name,       
                        date_formatted, 
                        tm,
                        les,
                        current_ex_type,
                        teach_clean,
                        rm
                    ))


    return processed_data

async def start_conversation_session(file_path: str, session: AsyncSession):
    if file_path.endswith(".docx"):
        data = extract_session_data(file_path)
        if data is None:
            return False
        elif data == []:
            return False
        elif data == ():
            return False
        await session.execute(delete(Session))

        session_obj = []
        for row in data:
            sch = Session(
                group_name=row[0],
                date = row[2],
                day_of_week = row[1],
                time = row[3],
                lesson = row[4],
                ex_type = row[5],
                teacher = row[6],
                classroom = row[7]
            )
            session_obj.append(sch)
        session.add_all(session_obj)

        await session.commit()
        return True
    else:
        return False
    
