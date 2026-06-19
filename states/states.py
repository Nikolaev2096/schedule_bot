from aiogram.fsm.state import State, StatesGroup 

'''
    ####    Регистрация    ####
'''

class Registration(StatesGroup):
    start = State()
    select_role = State()
    select_group = State()
    select_teacher = State()
    wait_for_check = State()
    confirm_base_reg_state = State()
    select_notif_type = State()
    insert_time = State()
    continue_reg = State()


'''
    ####    Для изменения группы | преподавателя    ####
'''

class ChangeOneParam(StatesGroup):
    change = State()

'''
    ####    Изменение прав доступа    ####
'''

class SetUserOrAdminRules(StatesGroup):
    input_used_id = State()
    select_state = State()

class AdminManagement(StatesGroup):
    menu = State()
    input_admin_id = State()
    input_remove_admin_id = State()


class ScheduleSelect(StatesGroup):
    select_slice = State()
    select_obj = State()
    select_week = State()
    select_owner = State()
    select_group = State()
    select_teacher = State()
    select_another_group = State()
    select_another_teach = State()
    input_room = State()
    input_day = State()
    error_state = State()
    confirm_state = State()

class MenuState(StatesGroup):
    menu = State()
    schedule_menu = State()
    settings_menu = State()
    improves_and_homework_menu = State()


class ChangeRole(StatesGroup):
    change_role = State()


class CalendarSchedule(StatesGroup):
    select_month = State()
    select_day = State()
    confirm_select = State()


class LessonDays(StatesGroup):
    select_lesson = State()

class SessionSchedule(StatesGroup):
    select_slice = State()
    select_owner = State()
    select_group = State()
    select_teacher = State()
    select_another_group = State()
    select_another_teach = State()
    error_state = State()
    confirm_state = State()
    state_for_get = State()

class GetInformation(StatesGroup):
    info_menu = State()
    Information = State()

class UpdateSchedule(StatesGroup):
    confirm_update = State()
    upload_schedule = State()

class UpdateSessionSchedule(StatesGroup):
    confirm_update = State()
    upload_schedule = State()

class WorkWithSchedule(StatesGroup):
    select_action = State()
    confirm = State()

class SendNotification(StatesGroup):
    select_getter = State()
    select_getter_group = State()
    select_notification_sound = State()
    input_text_notification = State()
    confirm_notification_send = State()

class ChangeNotification(StatesGroup):
    confirm = State()
    disable = State()

class DeleteAccount(StatesGroup):
    confirm = State()


