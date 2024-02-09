from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ContactCreate(BaseModel):
    """Модель для створення нового контакту."""
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: contacts.date
    additional_data: str = None


class Contact(Base):
    """Модель контакту в базі даних."""
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True)
    birthday = Column(contacts.Date)
    additional_data = Column(String, nullable=True)


class User(Base):
    """Модель користувача в базі даних."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    avatar_url = Column(String, nullable=True)
