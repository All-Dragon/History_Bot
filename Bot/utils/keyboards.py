from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from typing import Any
from math import ceil


def get_login_markup() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    bt1 = InlineKeyboardButton(text = 'Да', callback_data= 'login_yes')
    bt2 = InlineKeyboardButton(text = 'Нет', callback_data = 'login_no')
    markup = kb_builder.add(bt1, bt2).adjust(1, 1).as_markup()
    return markup


def get_change_username_markup() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    bt1 = InlineKeyboardButton(text = 'Да', callback_data= 'change_name_yes')
    bt2 = InlineKeyboardButton(text = 'Нет', callback_data= 'change_name_no')
    markup = kb_builder.add(bt1, bt2).adjust(1).as_markup()
    return markup

def get_progress_text(current_step: int, max_steps: int = 7) -> str:
    return f"📍 Шаг {current_step}/{max_steps}"

def get_step_emoji(step: int) -> str:
    emojis = {
        1: "📝",  # Тип вопроса
        2: "❓",  # Текст вопроса
        3: "🏷️",  # Тема
        4: "⚡",  # Сложность
        5: "🔤",  # Варианты/ответ
        6: "🖼️",  # Картинка
        7: "✅",  # Статус
    }
    return emojis.get(step, "")

def get_markup_registration_role() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    button1 = InlineKeyboardButton(text='Ученик', callback_data='Ученик')
    button2 = InlineKeyboardButton(text='Преподаватель', callback_data='Преподаватель')

    kb_builder.add(button1, button2)
    kb_builder.adjust(1, 1)
    markup = kb_builder.as_markup()
    return markup

def get_markup_question_type() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    bt1 = InlineKeyboardButton(text = 'С вариантами ответов', callback_data= 'multiple_choice')
    bt2 = InlineKeyboardButton(text = 'Свободный ответ', callback_data= 'free_text')
    bt3 = InlineKeyboardButton(text = '❌ Отмена', callback_data = 'cancel')
    markup = kb_builder.add(bt1, bt2, bt3).adjust(1, 1, 1).as_markup()
    return markup

def get_markup_difficulty() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    difficulties = [
        (1, "Легкий", "🟢"),
        (2, "Простой", "🟡"),
        (3, "Средний", "🟠"),
        (4, "Сложный", "🔴"),
        (5, "Эксперт", "⚫"),
    ]

    for level, name, emoji in difficulties:
        kb_builder.button(
            text=f"{emoji} {name} ({level})",
            callback_data=f"difficulty_{level}"
        )

    markup = kb_builder.adjust(1).as_markup()

    return markup

def get_markup_status() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    but1 = InlineKeyboardButton(text = 'Опубликовать сразу', callback_data= 'status_published')
    but2 = InlineKeyboardButton(text = 'Сохранить, как черновик', callback_data= 'status_draft')
    but3 = InlineKeyboardButton(text = 'В архив', callback_data= 'status_archived')
    but4 = InlineKeyboardButton(text = 'Отмена', callback_data = 'status_cancel')
    markup = kb_builder.add(but1, but2, but3, but4).adjust(1).as_markup()
    return markup

def get_markup_photo() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    bt1 = InlineKeyboardButton(text = '🖼️ Добавить фото', callback_data = 'add_image')
    bt2 = InlineKeyboardButton(text = '⏭️ Без фото (пропустить)', callback_data = 'skip_image')
    bt3 = InlineKeyboardButton(text = '◀️ Назад', callback_data='nav_back_6')
    markup = kb_builder.add(bt1, bt2, bt3).adjust(1).as_markup()
    return markup

def get_markup_back_cancel() -> InlineKeyboardMarkup:
    """Кнопки Назад и Отмена"""
    kb_builder = InlineKeyboardBuilder()
    back_btn = InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back")
    cancel_btn = InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_cancel")
    kb_builder.add(back_btn, cancel_btn)
    return kb_builder.as_markup()

def get_markup_back_cancel_difficulty() -> InlineKeyboardMarkup:
    """Кнопки Назад и Отмена для сложности"""
    kb_builder = InlineKeyboardBuilder()
    
    # Сначала все уровни сложности
    difficulties = [
        (1, "🟢 Легкий", "difficulty_1"),
        (2, "🟡 Простой", "difficulty_2"),
        (3, "🟠 Средний", "difficulty_3"),
        (4, "🔴 Сложный", "difficulty_4"),
        (5, "⚫ Эксперт", "difficulty_5"),
    ]
    
    for level, name, callback in difficulties:
        kb_builder.button(text=name, callback_data=callback)
    
    kb_builder.adjust(1)
    
    # Затем кнопки навигации
    back_btn = InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back_4")
    cancel_btn = InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_cancel")
    kb_builder.row(back_btn, cancel_btn)
    
    return kb_builder.as_markup()

def get_markup_navigation(current_step: int, max_step: int = 7, has_error: bool = False) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    

    if current_step > 1:
        buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"nav_back_{current_step}"))
    

    buttons.append(InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_cancel"))
    

    if current_step < max_step:
        buttons.append(InlineKeyboardButton(text="Далее ▶️", callback_data=f"nav_next_{current_step}"))
    

    if current_step == max_step:
        buttons.append(InlineKeyboardButton(text="✅ Создать", callback_data="confirm_create"))
    
    kb_builder.add(*buttons)
    kb_builder.adjust(2, 1) if current_step < max_step else kb_builder.adjust(2)
    
    return kb_builder.as_markup()

def get_markup_cancel_confirm() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    yes_btn = InlineKeyboardButton(text="✅ Да, отменить", callback_data="confirm_cancel_yes")
    no_btn = InlineKeyboardButton(text="❌ Нет, продолжить", callback_data="confirm_cancel_no")
    kb_builder.add(yes_btn, no_btn).adjust(1)
    return kb_builder.as_markup()


