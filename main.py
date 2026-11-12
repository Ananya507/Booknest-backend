from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, Base, SessionLocal
from models import Book, User, SavedBook
import models
from fastapi import Depends
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException
import jwt
import secrets
from datetime import datetime, timedelta, timezone
import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()
def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = int(payload.get("sub"))

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return user

    finally:
        db.close()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://ananya507.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Create database tables
Base.metadata.create_all(bind=engine)
from sqlalchemy import text

from sqlalchemy import inspect, text

with engine.connect() as connection:
    columns = [
        column["name"]
        for column in inspect(engine).get_columns("books")
    ]

    if "image" not in columns:
        connection.execute(
            text("ALTER TABLE books ADD COLUMN image VARCHAR")
        )
        connection.commit()
    if "book_url" not in columns:
        connection.execute(
        text("ALTER TABLE books ADD COLUMN book_url VARCHAR")
    )
    connection.commit()

# Define the information needed to add a book
class BookCreate(BaseModel):
    title: str
    author: str
    category: str | None = None
    image: str | None = None
    book_url: str | None = None
class BookUpdate(BaseModel):
    title: str
    author: str
    category: str | None = None
    image: str | None = None
    book_url: str | None = None
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

@app.get("/")
def home():
    return {"message": "Welcome to BookNest API!"}


# Get all books (we'll implement this next)
@app.get("/books")
def get_books():
    db = SessionLocal()

    try:
        books = db.query(Book).all()
        return books
    finally:
        db.close()


# Add a new book to the database
@app.post("/books")
def create_book(book: BookCreate):
    db = SessionLocal()

    try:
        new_book = Book(
    title=book.title,
    author=book.author,
    category=book.category,
    image=book.image,
    book_url=book.book_url
)

        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        return {
            "id": new_book.id,
            "title": new_book.title,
            "author": new_book.author,
            "category": new_book.category,
            "image": new_book.image,
            "book_url": new_book.book_url
        }

    finally:
        db.close()
@app.get("/books/{book_id}")
def get_book(book_id: int):
    db = SessionLocal()

    try:
        book = db.query(Book).filter(Book.id == book_id).first()

        if book is None:
            return {"message": "Book not found"}

        return book

    finally:
        db.close()
@app.put("/books/{book_id}")
def update_book(book_id: int, updated_book: BookUpdate):
    db = SessionLocal()

    try:
        book = db.query(Book).filter(Book.id == book_id).first()

        if book is None:
            return {"message": "Book not found"}

        book.title = updated_book.title
        book.author = updated_book.author
        book.category = updated_book.category
        book.image = updated_book.image
        book.book_url = updated_book.book_url
        db.commit()
        db.refresh(book)

        return book

    finally:
        db.close()
@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    db = SessionLocal()

    try:
        book = db.query(Book).filter(Book.id == book_id).first()

        if book is None:
            return {"message": "Book not found"}

        db.delete(book)
        db.commit()

        return {"message": "Book deleted successfully"}

    finally:
        db.close()
@app.post("/register")
def register_user(user: UserCreate):
    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.email == user.email
        ).first()

        if existing_user:
            return {"message": "Email already registered"}

        hashed_password = pwd_context.hash(user.password)

        new_user = User(
            email=user.email,
            password_hash=hashed_password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User registered successfully",
            "user_id": new_user.id
        }

    finally:
        db.close()
@app.post("/login")
def login_user(user: UserLogin):
    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.email == user.email
        ).first()

        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        password_matches = pwd_context.verify(
            user.password,
            existing_user.password_hash
        )

        if not password_matches:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        access_token = create_access_token(existing_user.id)
        return {
    "message": "Login successful",
    "access_token": access_token,
    "token_type": "bearer",
    "user_id": existing_user.id
}

    finally:
        db.close()
@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "message": "Authentication successful",
        "user_id": current_user.id,
        "email": current_user.email
    }
@app.post("/my-library/{book_id}")
def save_book(
    book_id: int,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    try:
        book = db.query(Book).filter(Book.id == book_id).first()

        if book is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )

        existing = db.query(SavedBook).filter(
            SavedBook.user_id == current_user.id,
            SavedBook.book_id == book_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Book already saved"
            )

        saved_book = SavedBook(
            user_id=current_user.id,
            book_id=book_id
        )

        db.add(saved_book)
        db.commit()

        return {"message": "Book saved to your library"}

    finally:
        db.close()
@app.get("/my-library")
def get_my_library(
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    try:
        saved_books = db.query(Book).join(
            SavedBook,
            Book.id == SavedBook.book_id
        ).filter(
            SavedBook.user_id == current_user.id
        ).all()

        return saved_books

    finally:
        db.close()
@app.delete("/my-library/{book_id}")
def remove_saved_book(
    book_id: int,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    try:
        saved_book = db.query(SavedBook).filter(
            SavedBook.user_id == current_user.id,
            SavedBook.book_id == book_id
        ).first()

        if saved_book is None:
            raise HTTPException(
                status_code=404,
                detail="Book not found in your library"
            )

        db.delete(saved_book)
        db.commit()

        return {
            "message": "Book removed from your library"
        }

    finally:
        db.close()

@app.post("/books/bulk")
def create_books_bulk(books: list[BookCreate]):
    db = SessionLocal()

    try:
        added_books = []
        skipped_books = []

        for book in books:
            existing_book = db.query(Book).filter(
                Book.title == book.title,
                Book.author == book.author
            ).first()

            if existing_book:
                skipped_books.append(book.title)
                continue

            new_book = Book(
                title=book.title,
                author=book.author,
                category=book.category,
                image=book.image,
                book_url=book.book_url
            )

            db.add(new_book)
            db.flush()

            added_books.append({
                "id": new_book.id,
                "title": new_book.title,
                "author": new_book.author
            })

        db.commit()

        return {
            "message": "Bulk book addition completed",
            "added": added_books,
            "skipped": skipped_books
        }

    finally:
        db.close()
