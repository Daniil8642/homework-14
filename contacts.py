from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import ContactCreate, Contact
from utils import get_and_cache_contacts
from rq.decorators import job

router = APIRouter()


@router.post("/contacts/")
def create_contact(contact: ContactCreate, db: Session = Depends(get_db),
                   current_user: str = Depends(contacts.get_current_user)):
    """Кінцева точка для створення нового контакту."""
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.get("/contacts/")
def read_contacts(q: str = None, db: Session = Depends(get_db),
                  current_user: str = Depends(contacts.get_current_user)):
    """Кінцева точка для читання всіх контактів або пошуку за запитом."""
    contacts = db.query(Contact)
    if q:
        contacts = contacts.filter(
            Contact.first_name.contains(q) |
            Contact.last_name.contains(q) |
            Contact.email.contains(q)
        )
    return contacts.all()


@router.get("/contacts/{contact_id}")
def read_contact(contact_id: int, db: Session = Depends(get_db),
                 current_user: str = Depends(contacts.get_current_user)):
    """Кінцева точка для читання контакту за його ID."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return contact


@router.put("/contacts/{contact_id}")
def update_contact(contact_id: int, contact: ContactCreate, db: Session = Depends(get_db),
                   current_user: str = Depends(contacts.get_current_user)):
    """Кінцева точка для оновлення існуючого контакту."""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")

    for key, value in contact.dict().items():
        setattr(db_contact, key, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db),
                   current_user: str = Depends(contacts.get_current_user)):
    """Кінцева точка для видалення контакту."""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")

    db.delete(db_contact)
    db.commit()
    return {"message": "Контакт успішно видалено"}


@router.get("/contacts/birthday/")
def upcoming_birthdays(db: Session = Depends(get_db),
                      current_user: str = Depends(contacts.get_current_user)):
    """Кінцева точка для отримання контактів з майбутніми днями народження."""
    today = contacts.date.today()
    upcoming_birthdays = db.query(Contact).filter(
        (contacts.func.extract('month', Contact.birthday) == today.month) &
        (contacts.func.extract('day', Contact.birthday) >= today.day) &
        (contacts.func.extract('day', Contact.birthday) <= today.day + 7)
    ).all()
    return upcoming_birthdays


@router.get("/cache-contacts/")
def cache_contacts():
    """Кінцева точка для ініціювання кешування контактів."""
    contacts.worker_job.delay()
    return {"message": "Ініціювання кешування контактів"}


@router.post("/register/")
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    """Кінцева точка для реєстрації користувача."""
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Користувач вже зареєстрований")

    hashed_password = contacts.hash_password(password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = contacts.create_access_token(data={"sub": new_user.email})
    return {"message": "Користувач успішно зареєстрований", "access_token": access_token}
