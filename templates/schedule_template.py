import re
from typing import List, Dict
from templates.txt_templates import templ_footer
from database.model import Schedule


class ScheduleFormatter:

    def __init__(self):
        self.DAYS_ORDER = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]

        self.TIME_MAP = {
            "09-00": 1,
            "10-50": 2,
            "13-00": 3,
            "15-00": 4,
            "16-50": 5,
        }
        self.tomorrow = False

    def _get_pair_number(self, time_str: str) -> int:
        """Получает номер пары из строки времени (например, '9-00 ...' -> 1)"""
        if not time_str:
            return 99

        start_time = time_str.split(' ')[0].strip()
        return self.TIME_MAP.get(start_time, 99)

    @staticmethod
    def _get_week_str(week_num: int, is_cur: bool) -> str:
        if is_cur: return "на текущую неделю "
        if week_num == 1: return "на 1 неделю"
        if week_num == 2: return "на 2 неделю"
        if week_num == 0: return "на 1 и 2 неделю"
        return "на текущую неделю"

    @staticmethod
    def _clean_type_name(type_str: str) -> str:
        """Убирает лишние пометки вроде (1 нед.) из типа занятия"""
        if not type_str: return ""
        return re.sub(r'\s*\(?\d+\s*нед\.?\)?', '', type_str, flags=re.IGNORECASE).strip()

    def _generate_title(self, user_data: Dict) -> str:
        choice = user_data.get('choice_type')
        week = user_data.get('week_number')
        current = user_data.get('current')
        week_str = self._get_week_str(week, current)
        
        title = f"***📆 Расписание {week_str}***\n\n"

        if choice == 'group':
            group = user_data.get('another_group') or "вашей группы"
            if group == "вашей группы":
                title = f"***📆 Расписание {group} {week_str}***\n"
            else:
                title = f"***📆 Расписание для группы {group} {week_str}***\n"

        elif choice == 'teacher':
            teacher = user_data.get('another_teach') or ""
            if not teacher:
                title = f"***📆 Ваше расписание {week_str}***\n"
            else:
                title = f"***📆 Расписание для преподавателя {teacher} {week_str}***\n"

        elif choice == 'day':
            day = user_data.get('day')
            title = f"***📆 Ваше расписание на {day} {week_str}***\n"
            if day == 'Завтра':
                title = f"***🕘 Запланированное уведомление:*** \n\n***📆 Ваше расписание на завтра***\n"
                self.tomorrow = True

        elif choice == 'room':
            room = user_data.get('room')
            title = f"***📆 Расписание кабинета {room} {week_str}***\n"

        return title

    @staticmethod
    def _format_lesson_week(week_num: int) -> str:
        if week_num == 1: return "***- 1 неделя***"
        if week_num == 2: return "***- 2 неделя***"
        return ""

    async def format_schedule(self, rows: List[Schedule], user_data: Dict, user_role: str) -> str:

        title = self._generate_title(user_data)

        if not rows:
            return title + "Пар нет. "


        lessons_by_day: Dict[str, List[Schedule]] = {}
        for row in rows:
            day = row.day_of_week.lower()
            if day not in lessons_by_day:
                lessons_by_day[day] = []
            lessons_by_day[day].append(row)

        output_parts = [title]


        sorted_days = sorted(
            lessons_by_day.keys(),
            key=lambda d: self.DAYS_ORDER.index(d) if d in self.DAYS_ORDER else 99
        )

        for day in sorted_days:
            output_parts.append(f"├──<***{day.capitalize()}***>—\n\n──────────")


            sorted_lessons = sorted(
                lessons_by_day[day],
                key=lambda r: self._get_pair_number(r.time)
            )

            merged_lessons = []

            for row in sorted_lessons:
                current_time_num = self._get_pair_number(row.time)
                current_clean_type = self._clean_type_name(row.lesson_type)

                unique_key = (
                    current_time_num,
                    row.lesson,
                    current_clean_type,
                    row.classroom,
                    row.week
                )

                lesson_data = {
                    'original_obj': row,
                    'groups': [row.group_name],
                    'clean_type': current_clean_type,
                    'key': unique_key
                }

                should_try_merge = (user_data.get('choice_type') == 'teacher') or \
                                   (user_data.get('choice_type') == 'day' and user_role == 'teacher' ) or \
                                    (user_data.get('choice_type') == 'room') or \
                                      (user_role == 'teacher')

                is_merged = False

                if should_try_merge and merged_lessons:

                    for lesson_to_maerge in merged_lessons:
                        if lesson_to_maerge['key'] == unique_key:
                            lesson_to_maerge['groups'].append(row.group_name)
                            is_merged = True
                if not is_merged:
                    merged_lessons.append(lesson_data)

        
            for item in merged_lessons:
                lesson: Schedule = item['original_obj']  

             
                time_str = lesson.time
                pair_num = self._get_pair_number(time_str)
                pair_display = str(pair_num) if pair_num != 99 else time_str

               
                subject = lesson.lesson
                classroom = lesson.classroom
                week_val = lesson.week
                l_type = item['clean_type']
                date = lesson.dates

                
                teacher_str = lesson.teacher if lesson.teacher else "преподавателя нет"

                choice = user_data.get('choice_type')

               
                group_info = ", ".join(item['groups'])

               
                if choice == 'teacher':
                    target_info = group_info
                elif choice == 'day' and user_role == 'teacher':
                    target_info = group_info
                elif choice == 'room':
                    target_info = f'{group_info} - {teacher_str}'
                else:
                    target_info = teacher_str

                week_note = self._format_lesson_week(week_val)
                
                date_note = ''
                if date:
                    date_note = f'***- Дата проведения занятия(до)***: {date}'

                line = f"***{pair_display} пара*** - {subject} - {target_info} - {l_type} - {classroom} {week_note} {date_note} \n───────────"
                output_parts.append(line)

            output_parts.append('')

       
        output_parts.append(templ_footer)

        return "\n".join(output_parts)



formatter = ScheduleFormatter()