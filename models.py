from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    category = Column(String, nullable=True)
    image = Column(String, nullable=True)
    book_url = Column(String, nullable=True)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
class SavedBook(Base):
    __tablename__ = "saved_books"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    __table_args__ = (
    UniqueConstraint("user_id", "book_id", name="unique_user_book"),
)