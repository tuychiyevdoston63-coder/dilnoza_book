from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from sqlalchemy import func, update, delete

from app.database import async_session
from app.models import User, Genre, Book, Library, Transaction
from app.lexicon import LEXICON
from app.states import RegistrationStates, BalanceStates, AdminStates
from app import keyboards as kb
from app.config import settings

router = Router()

async def get_user_lang(session, user_id: int) -> str:
    res = await session.execute(select(User.language).where(User.id == user_id))
    lang = res.scalar_one_or_none()
    return lang if lang else "uz"

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with async_session() as session:
        res = await session.execute(select(User).where(User.id == message.from_user.id))
        user = res.scalar_one_or_none()
        
        if not user:
            await message.answer(LEXICON["uz"]["select_lang"], reply_markup=kb.get_lang_keyboard())
        else:
            is_admin = message.from_user.id in settings.admin_list
            await message.answer(LEXICON[user.language]["main_menu"], reply_markup=kb.get_main_menu(user.language, is_admin))

@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(lang=lang)
    await callback.message.delete()
    await callback.message.answer(LEXICON[lang]["welcome_reg"])
    await state.set_state(RegistrationStates.first_name)

@router.message(RegistrationStates.first_name)
async def process_firstname(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    data = await state.get_data()
    await message.answer(LEXICON[data['lang']]["req_lastname"])
    await state.set_state(RegistrationStates.last_name)

@router.message(RegistrationStates.last_name)
async def process_lastname(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    data = await state.get_data()
    await message.answer(LEXICON[data['lang']]["req_phone"], reply_markup=kb.get_phone_keyboard(data['lang']))
    await state.set_state(RegistrationStates.phone_number)

@router.message(RegistrationStates.phone_number, F.contact)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    is_admin = message.from_user.id in settings.admin_list
    
    async with async_session() as session:
        new_user = User(
            id=message.from_user.id,
            first_name=data['first_name'],
            last_name=data['last_name'],
            username=message.from_user.username,
            phone_number=message.contact.phone_number,
            language=lang,
            is_admin=is_admin
        )
        session.add(new_user)
        await session.commit()
        
    await message.answer(LEXICON[lang]["main_menu"], reply_markup=kb.get_main_menu(lang, is_admin))
    await state.clear()

# --- KATALOG & XARID TIZIMI ---

@router.message(F.text.in_([LEXICON["uz"]["btn_catalog"], LEXICON["ru"]["btn_catalog"]]))
async def show_catalog(message: Message):
    async with async_session() as session:
        lang = await get_user_lang(session, message.from_user.id)
        res = await session.execute(select(Genre))
        genres = res.scalars().all()
        await message.answer("Janrlar:", reply_markup=kb.get_genres_keyboard(genres, lang))

@router.callback_query(F.data.startswith("genre_"))
async def show_books_by_genre(callback: CallbackQuery):
    genre_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        res = await session.execute(select(Book).where(Book.genre_id == genre_id, Book.is_available == True))
        books = res.scalars().all()
        if not books:
            lang = await get_user_lang(session, callback.from_user.id)
            await callback.answer(LEXICON[lang]["no_books"], show_alert=True)
            return
        await callback.message.edit_text("Kitobni tanlang:", reply_markup=kb.get_books_keyboard(books))

@router.callback_query(F.data.startswith("book_"))
async def show_book_details(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        book = await session.get(Book, book_id)
        
        lib_res = await session.execute(select(Library).where(Library.user_id == callback.from_user.id, Library.book_id == book_id))
        has_access = lib_res.scalar_one_or_none() is not None
        is_free = book.price == 0.0
        
        desc = book.description_uz if lang == "uz" else book.description_ru
        caption = f"📖 *{book.title}*\n✍️ Muallif: {book.author}\n💰 Narxi: {book.price} UZS\n\n📝 {desc}"
        
        await callback.message.delete()
        if book.photo_id:
            await callback.message.answer_photo(book.photo_id, caption=caption, parse_mode="Markdown", 
                                                reply_markup=kb.get_book_action_keyboard(lang, book_id, is_free, has_access))
        else:
            await callback.message.answer(caption, parse_mode="Markdown", 
                                          reply_markup=kb.get_book_action_keyboard(lang, book_id, is_free, has_access))

@router.callback_query(F.data.startswith("buy_"))
async def buy_book(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        user = await session.get(User, callback.from_user.id)
        book = await session.get(Book, book_id)
        
        if user.balance < book.price:
            await callback.answer(LEXICON[lang]["insufficient_funds"], show_alert=True)
            return
            
        user.balance -= book.price
        new_lib = Library(user_id=user.id, book_id=book.id)
        session.add(new_lib)
        await session.commit()
        
        await callback.answer(LEXICON[lang]["purchase_success"], show_alert=True)
        await show_book_details(callback)

@router.callback_query(F.data.startswith("view_"))
async def view_file(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    f_type, book_id = parts[1], int(parts[2])
    
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        book = await session.get(Book, book_id)
        
        lib_res = await session.execute(select(Library).where(Library.user_id == callback.from_user.id, Library.book_id == book_id))
        has_access = lib_res.scalar_one_or_none() is not None
        is_free = book.price == 0.0
        
        if not (is_free or has_access):
            await callback.answer("Xavfsizlik cheklovi: Avval sotib oling!", show_alert=True)
            return
            
        if f_type == "pdf" and book.file_id:
            await bot.send_document(callback.from_user.id, book.file_id)
        elif f_type == "audio" and book.audio_id:
            await bot.send_audio(callback.from_user.id, book.audio_id)
        else:
            await callback.answer("Fayl topilmadi yoki yuklanmagan.", show_alert=True)

# --- MENING KUTUBXONAM ---

@router.message(F.text.in_([LEXICON["uz"]["btn_my_lib"], LEXICON["ru"]["btn_my_lib"]]))
async def show_my_library(message: Message):
    async with async_session() as session:
        res = await session.execute(select(Book).join(Library).where(Library.user_id == message.from_user.id))
        books = res.scalars().all()
        if not books:
            lang = await get_user_lang(session, message.from_user.id)
            await message.answer(LEXICON[lang]["no_books"])
            return
        await message.answer("Sizning kitoblaringiz:", reply_markup=kb.get_books_keyboard(books))

# --- BALANS VA TO'LDIRISH TIZIMI ---

@router.message(F.text.in_([LEXICON["uz"]["btn_balance"], LEXICON["ru"]["btn_balance"]]))
async def show_balance(message: Message):
    async with async_session() as session:
        lang = await get_user_lang(session, message.from_user.id)
        user = await session.get(User, message.from_user.id)
        await message.answer(f"Hisobingiz: {user.balance} UZS", reply_markup=kb.get_balance_keyboard(lang))

@router.callback_query(F.data == "deposit")
async def start_deposit(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        await callback.message.answer(LEXICON[lang]["req_amount"])
        await state.set_state(BalanceStates.amount)

@router.message(BalanceStates.amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        await state.update_data(amount=amount)
        async with async_session() as session:
            lang = await get_user_lang(session, message.from_user.id)
            await message.answer(LEXICON[lang]["req_check"])
            await state.set_state(BalanceStates.check)
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting:")

@router.message(BalanceStates.check, F.photo)
async def process_deposit_check(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    
    async with async_session() as session:
        lang = await get_user_lang(session, message.from_user.id)
        tx = Transaction(user_id=message.from_user.id, amount=data['amount'], check_file_id=photo_id)
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        
    await message.answer(LEXICON[lang]["check_sent_admin"])
    
    # Adminlarni ogohlantirish
    for admin_id in settings.admin_list:
        try:
            admin_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tx_approve_{tx.id}"),
                 InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tx_reject_{tx.id}")]
            ])
            await bot.send_photo(admin_id, photo_id, caption=f"Yangi to'lov!\nID: {tx.id}\nFoydalanuvchi: {message.from_user.id}\nSumma: {data['amount']} UZS", reply_markup=admin_kb)
        except Exception:
            pass
    await state.clear()

# --- ADMIN PANEL & STATISTIKA ---

@router.message(F.text == "👑 Admin Panel")
async def cmd_admin_panel(message: Message):
    if message.from_user.id in settings.admin_list:
        await message.answer("Admin boshqaruv paneli:", reply_markup=kb.get_admin_panel())

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if message.from_user.id not in settings.admin_list: return
    async with async_session() as session:
        u_count = await session.scalar(select(func.count(User.id)))
        b_count = await session.scalar(select(func.count(Book.id)))
        g_count = await session.scalar(select(func.count(Genre.id)))
        t_count = await session.scalar(select(func.count(Transaction.id)))
        total_bal = await session.scalar(select(func.sum(User.balance))) or 0.0
        
        await message.answer(f"📊 Statistika:\n• Foydalanuvchilar: {u_count}\n• Kitoblar: {b_count}\n• Janrlar: {g_count}\n• To'lovlar soni: {t_count}\n• Jami joriy balanslar: {total_bal} UZS")

@router.callback_query(F.data.startswith("tx_"))
async def handle_transaction_status(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    action, tx_id = parts[1], int(parts[2])
    
    async with async_session() as session:
        tx = await session.get(Transaction, tx_id)
        if tx and tx.status == "pending":
            if action == "approve":
                tx.status = "approved"
                await session.execute(update(User).where(User.id == tx.user_id).values(balance=User.balance + tx.amount))
                await bot.send_message(tx.user_id, f"To'lovingiz tasdiqlandi! Hisobingizga {tx.amount} UZS qo'shildi.")
            else:
                tx.status = "rejected"
                await bot.send_message(tx.user_id, "To'lovingiz rad etildi. Muammo bo'lsa adminga yozing.")
            await session.commit()
            await callback.message.edit_caption(caption=callback.message.caption + f"\n\nStatus: {tx.status.upper()}")

@router.message(F.text == "📢 Reklama yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id in settings.admin_list:
        await message.answer("Reklama postini (matn, rasm yoki video) yuboring:")
        await state.set_state(AdminStates.broadcast_msg)

@router.message(AdminStates.broadcast_msg)
async def process_broadcast(message: Message, state: FSMContext):
    async with async_session() as session:
        res = await session.execute(select(User.id))
        users = res.scalars().all()
        
    count = 0
    for u_id in users:
        try:
            await message.copy_to(chat_id=u_id)
            count += 1
        except Exception:
            pass
    await message.answer(f"Reklama {count} ta foydalanuvchiga yuborildi.")
    await state.clear()

@router.message(F.text == "➕ Janr qo'shish")
async def add_genre_start(message: Message, state: FSMContext):
    if message.from_user.id in settings.admin_list:
        await message.answer("Yangi janr nomini O'zbek tilida kiriting:")
        await state.set_state(AdminStates.add_genre_uz)

@router.message(AdminStates.add_genre_uz)
async def add_genre_uz(message: Message, state: FSMContext):
    await state.update_data(name_uz=message.text)
    await message.answer("Janr nomini Rus tilida kiriting:")
    await state.set_state(AdminStates.add_genre_ru)

@router.message(AdminStates.add_genre_ru)
async def add_genre_ru(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        genre = Genre(name_uz=data['name_uz'], name_ru=message.text)
        session.add(genre)
        await session.commit()
    await message.answer("Janr muvaffaqiyatli qo'shildi!")
    await state.clear()

# Qo'shimcha profil va sozlamalar handlerlarini shu yerga ulash mumkin.
