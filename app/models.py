from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db

class Book(db.Model):
    __tablename__ = 'books'
    __table_args__ = (
        db.Index('idx_book_title_author', 'title', 'author'),
        db.Index('idx_book_quantity', 'quantity'),  # Add index for quantity queries
    )
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    transactions = db.relationship('Transaction', backref='book', lazy=True)

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    debt = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='member', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    __table_args__ = (
        db.Index('idx_transaction_dates', 'issue_date', 'return_date'),
    )
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)  # Changed from 'book.id'
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)  # Changed from 'member.id'
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    rent_fee = db.Column(db.Float)
