from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from lexicon import LEXICON

def get_lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
    ])

def get_phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=LEXICON[lang]["btn_send_phone"], request_contact=True)]
    ], resize_keyboard=True, one_time_keyboard=True)

def get_main_menu(lang: str, is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text=LEXICON[lang]["btn_catalog"]), KeyboardButton(text=LEXICON[lang]["btn_my_lib"])],
        [KeyboardButton(text=LEXICON[lang]["btn_balance"]), KeyboardButton(text=LEXICON[lang]["btn_profile"])],
        [KeyboardButton(text=LEXICON[lang]["btn_search"]), KeyboardButton(text=LEXICON[lang]["btn_settings"])]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_genres_keyboard(genres: list, lang: str) -> InlineKeyboardMarkup:
    keyboard = []
    for g in genres:
        name = g.name_uz if lang == "uz" else g.name_ru
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"genre_{g.id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_books_keyboard(books: list) -> InlineKeyboardMarkup:
    keyboard = []
    for b in books:
        keyboard.append([InlineKeyboardButton(text=b.title, callback_data=f"book_{b.id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_book_action_keyboard(lang: str, book_id: int, is_free: bool, has_access: bool) -> InlineKeyboardMarkup:
    keyboard = []
    if is_free or has_access:
        keyboard.append([InlineKeyboardButton(text=LEXICON[lang]["read"], callback_data=f"view_pdf_{book_id}")])
        keyboard.append([InlineKeyboardButton(text=LEXICON[lang]["listen"], callback_data=f"view_audio_{book_id}")])
    else:
        keyboard.append([InlineKeyboardButton(text=LEXICON[lang]["buy"], callback_data=f"buy_{book_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_balance_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON[lang]["fill_balance"], callback_data="deposit")]
    ])

def get_admin_panel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Janr qo'shish"), KeyboardButton(text="➕ Kitob qo'shish")],
        [KeyboardButton(text="💳 To'lovlarni ko'rish"), KeyboardButton(text="📢 Reklama yuborish")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🚪 Chiqish")]
    ], resize_keyboard=True)
