from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

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
    bt3 = InlineKeyboardButton(text = 'Отмена', callback_data = 'cancel')
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
    bt1 = InlineKeyboardButton(text = 'Добавить фото', callback_data = 'add_image')
    bt2 = InlineKeyboardButton(text = 'Без фото (пропустить)', callback_data = 'skip_image')
    bt3 = InlineKeyboardButton(text = 'Отмена', callback_data='photo_cancel')
    markup = kb_builder.add(bt1, bt2, bt3).adjust(1).as_markup()
    return markup