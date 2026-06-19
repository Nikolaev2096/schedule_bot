from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



'''
                     !##########################!
                    -####### Регистрация  #######-
                     !##########################!
'''


async def init_reg():
     return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👉 Приступить к регистрации", callback_data="start_setup"),
            ]
        ]
     )

async def role_inline_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍🎓 Студент", callback_data="set_role:user"),
                InlineKeyboardButton(text="👨‍🏫 Преподаватель", callback_data="set_role:teacher"),
            ], 
            [
                InlineKeyboardButton(text="🤵‍♂️ Сотрудник", callback_data="set_role:worker")
            ],
            [
                InlineKeyboardButton(text="❌ Пропустить", callback_data="set_role:None")
            ]
        ]
    )
    

async def menu_inline_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Главное меню ", callback_data="menu")
            ]
        ]
    )

async def base_reg_end():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Главное меню ", callback_data="menu")
            ],
            [
                InlineKeyboardButton(text="🕘 Настроить уведомления с расписанием", callback_data="time_set")
            ],
        ]
    )

async def select_sound():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔔 Со звуком  ", callback_data="sound")
            ],
            [
                InlineKeyboardButton(text="🔕 Без звука ", callback_data="silent")
            ],
           
        ]
    )



'''
                     !#################################!
                    -####### Расписание (учебное)#######-
                     !#################################!
'''


async def schedule_inline_kb():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="По преподавателю", callback_data="sch:teacher")
                ], 
                [
                    InlineKeyboardButton(text="По группе", callback_data="sch:group")
                ], 
                [
                    InlineKeyboardButton(text="По кабинету", callback_data="sch:room")
                ], 
                [
                    InlineKeyboardButton(text="По дню недели", callback_data="sch:day")
                ],
                [
                    InlineKeyboardButton(text="По календарному дню", callback_data="sch:calendar")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="sch:schedule_menu")
                ]
            ]
        )

async def schedule_group_inline_kb(role):
    if role == 'user':
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Получить свое расписание ", callback_data="my_group")
                ], 
                [
                    InlineKeyboardButton(text="Получить расписание другой группы ", callback_data="other_group")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_schedule_type")
                ]
            ]
        )
    else: 
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Получить расписание другой группы ", callback_data="other_group")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_schedule_type")
                ]
            ]
        )



async def schedule_teach_inline_kb(role):
    '''
    Клавиатура для выбора расписания преподавателя
    '''
    if role == 'teacher':
        return InlineKeyboardMarkup(
            inline_keyboard=[
                
                [
                    InlineKeyboardButton(text="Получить свое расписание ", callback_data="my_sch")
                ], 
                [
                    InlineKeyboardButton(text="Получить расписание другого преподавателя ", callback_data="other_sch")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_schedule_type")
                ]
    
            ]
        )
    else: 
        return InlineKeyboardMarkup(
            inline_keyboard=[

                [
                    InlineKeyboardButton(text="Получить расписание другого преподавателя ", callback_data="other_teach")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_schedule_type")
                ]
            ]
        )

async def teacher_chart():
    return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Получить расписание на месяц", callback_data="month_teach")
                ],
                [
                    InlineKeyboardButton(text="Получить расписание на семестр", callback_data="semester_teach")
                ],
                [
                    InlineKeyboardButton(text="Получить расписание без привязки к датам", callback_data="without_dates_teach")
                ],
            ]
        )


async def schedule_week_inline_kb():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Получить расписание по 1 неделе ", callback_data="one")
            ], 
            [
                InlineKeyboardButton(text="Получить расписание по 2 неделе  ", callback_data="two")
            ], 
            [
                InlineKeyboardButton(text="Получить расписание по 1 и 2 неделе  ", callback_data="all")
            ], 
            [
                InlineKeyboardButton(text="Получить расписание на текущую неделю  ", callback_data="current")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_schedule_prev")
            ]
        ]
    )

async def choice_inline_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="Yes")
            ], 
            [
                InlineKeyboardButton(text="Нет", callback_data="No")
            ],
        ]
    )

async def back_button_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")
            ]
        ]
    )

async def confirm_sch():
    return InlineKeyboardMarkup(
        inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить ", callback_data="confirm")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")
        ]
        ]
    )

async def confirm_notifications():
    return InlineKeyboardMarkup(
        inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить ", callback_data="confirm")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")
        ],
        [
            InlineKeyboardButton(text="📵 Отключить уведомления", callback_data="disable")
        ],
        ]
    )

async def session_inline_kb():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="По преподавателю", callback_data="sch:teacher")
                ], 
                [
                    InlineKeyboardButton(text="По группе", callback_data="sch:group")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="sch:schedule_menu")
                ]
        ]
    )


async def info_inline_kb():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="ℹ️ О боте", callback_data="bot")
                ], [
                    InlineKeyboardButton(text="📋 Получение справок", callback_data="spravki")
                ],[
                    InlineKeyboardButton(text="🌐 Сайт колледжа", callback_data="site")
                ],[
                    InlineKeyboardButton(text= "☎️ Контактный телефон", callback_data="phones")
                ], [
                    InlineKeyboardButton(text="📍 Адрес колледжа", callback_data="address")
                ], [
                    InlineKeyboardButton(text="ℹ️ Соцсети колледжа", callback_data="socials")
                ], [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")
                ]
        ]
    )

async def info_back_inline_kb():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
                ],
                [
                    InlineKeyboardButton(text="🏠 Главное меню ", callback_data="menu")
                ],
        ]
    )

async def getter_inline_kb():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Студентам", callback_data="users")
                ],
                [
                    InlineKeyboardButton(text="Студентам определенной группы ", callback_data="users_from_one_group")
                ],
                [
                    InlineKeyboardButton(text="Преподавателям ", callback_data="teachers")
                ],
                [
                    InlineKeyboardButton(text="Администраторам", callback_data="users")
                ],
                [
                    InlineKeyboardButton(text="Назад", callback_data="back ")
                ],
            ]
        )

async def sound_inline_kb():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Со звуком ", callback_data="users")
                ],
                [
                    InlineKeyboardButton(text="Без звука", callback_data="users")
                ],
            ]
        )

'''
                     !#################################################!
                    -####### Система рассылки уведомлений #######-
                     !#################################################!
'''

async def notification_getter_kb():
    '''
    Клавиатура для выбора получателей уведомления
    '''
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Всем пользователям", callback_data="notif_getter:all")
            ],
            [
                InlineKeyboardButton(text="👨‍🎓 Студентам", callback_data="notif_getter:students")
            ],
            [
                InlineKeyboardButton(text="👨‍🏫 Преподавателям", callback_data="notif_getter:teachers")
            ],
            [
                InlineKeyboardButton(text="👨‍💼 Администраторам", callback_data="notif_getter:admins")
            ],
            [
                InlineKeyboardButton(text="📘 Конкретной группе студентов", callback_data="notif_getter:group")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="notif_getter:back_to_admin_menu")
            ]
        ]
    )

async def notification_sound_kb():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔔 Со звуком", callback_data="notif_sound:True")
            ],
            [
                InlineKeyboardButton(text="🔕 Без звука", callback_data="notif_sound:False")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="notif_back_getter")
            ]
        ]
    )

async def notification_group_kb(groups: list):
    buttons = []
    for group in groups:
        if group:
            buttons.append([InlineKeyboardButton(text=f"{group}", callback_data=f"notif_group:{group}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="notif_back_getter")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def notification_confirm_kb():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="notif_confirm:yes")
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="notif_confirm:no")
            ]
        ]
    )
