from datetime import datetime
from typing import List, Dict
from templates.txt_templates import templ_footer_session
from database.model import Session

class SessionFormatter:

    def __init__(self):

        self.TYPE_RENAME = {
            "экзамен": "Экзамены",
            "дифф. зачет": "Дифф. зачёты",
            "зачет": "Зачёты",
            "Курсовая работа": "Курс. работа"
        }

        self.TYPE_PRIORITY = {
            "курс. работа": 0,
            "экзамен": 1,
            "дифф. зачет": 2,
            "зачет": 3,
            "другое": 4,
        }

    @staticmethod
    def _parse_date_sort_key(date_str: str):
        try:
            return datetime.strptime(date_str.strip(), "%d.%m.%Y")
        except:
            return datetime.max

    def _get_type_priority(self, type_name: str) -> int:
        k = type_name.lower().strip()
        for t, p in self.TYPE_PRIORITY.items():
            if t in k:
                return p
        return 999

    def _rename_type(self, type_name: str) -> str:
        if not type_name:
            return "Прочее"
        t = type_name.lower().strip()
        for key, val in self.TYPE_RENAME.items():
            if key in t:
                return val
        return type_name.capitalize()

    @staticmethod
    def _generate_title(user_data: Dict) -> str:

        choice = user_data.get('choice_type')

        if choice == 'group':
            grp = user_data.get('another_group')
            if grp:
                return f"📆 Расписание сессии для группы ***{grp}***\n"
            else: 
                return f"📆 Расписание сессии для ***вашей*** группы \n"
        else:
            teacher = user_data.get('another_teach')
            if teacher:
                return f"📆 Расписание сессии преподавателя ***{teacher}***\n"
            else:
                return f"***📆 Ваше*** расписание сессии\n"

    async def format_session(self, rows: List[Session], user_data: Dict) -> str:

        title = self._generate_title(user_data)

        if not rows:
            return title + "\nДанных пока нет."

        type_groups: Dict[str, List] = {}
        for r in rows:
            t = self._rename_type(r.ex_type)
            type_groups.setdefault(t, []).append(r)


        sorted_types = sorted(
            type_groups.keys(),
            key=lambda t: self._get_type_priority(t)
        )

        output = [title]

        choice = user_data.get('choice_type')


        for tp in sorted_types:

            output.append(f"\n├─<***{tp}***>─\n\n──────────")

            group_records = type_groups[tp]


            group_records.sort(
                key=lambda r: (
                    self._parse_date_sort_key(r.date),
                    r.time,
                )
            )


            packed = {}

            for r in group_records:

                key = (
                    
                    r.lesson,
                    r.time,
                    r.day_of_week,
                    r.date,
                    r.classroom,
                    r.group_name
                )

                teacher = r.teacher.strip()

                if key not in packed:
                    packed[key] = [teacher]
                else:
                    packed[key].append(teacher)


            for key, teachers in packed.items():

                lesson = key[0]
                time_str = key[1]
                day_week = key[2]
                date_str = key[3]
                classroom = key[4]

                if len(teachers) == 1:
                    t_block = teachers[0]
                else:
                    t_block = "Комиссия: " + ", ".join(teachers)

                if choice == 'teacher':
                    target = key[5]
                else:
                    target = t_block

                output.append(
                    f"{lesson}\n"
                    f"{time_str} — {day_week}: ___{date_str}___\n"
                    f"{target} — {classroom}\n"
                    f"──────────")

        output.append(f"\n{templ_footer_session}")

        return "\n".join(output)


session_formatter = SessionFormatter()