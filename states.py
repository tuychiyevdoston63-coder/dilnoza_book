from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    first_name = State()
    last_name = State()
    phone_number = State()

class BalanceStates(StatesGroup):
    amount = State()
    check = State()

class SearchStates(StatesGroup):
    query = State()

class AdminStates(StatesGroup):
    add_genre_uz = State()
    add_genre_ru = State()
    
    # Kitob qo'shish bosqichlari
    add_book_title = State()
    add_book_author = State()
    add_book_genre = State()
    add_book_price = State()
    add_book_desc_uz = State()
    add_book_desc_ru = State()
    add_book_photo = State()
    add_book_file = State()
    add_book_audio = State()
    
    broadcast_msg = State()
