from sqlalchemy import BigInteger, String, Integer, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(2), default="uz")
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

class Genre(Base):
    __tablename__ = "genres"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_uz: Mapped[str] = mapped_column(String(100))
    name_ru: Mapped[str] = mapped_column(String(100))

class Book(Base):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"))
    description_uz: Mapped[str] = mapped_column(String(1000))
    description_ru: Mapped[str] = mapped_column(String(1000))
    photo_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

class Library(Base):
    __tablename__ = "library"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Float)
    check_file_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
