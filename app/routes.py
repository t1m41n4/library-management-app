from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.models import db, Book, Member, Transaction
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    stats = {
        'total_books': Book.query.count(),
        'available_books': Book.query.filter(Book.quantity > 0).count(),
        'total_members': Member.query.count(),
        'active_loans': Transaction.query.filter_by(return_date=None).count(),
        'total_revenue': db.session.query(db.func.sum(Transaction.rent_fee)).scalar() or 0,
        'total_debt': db.session.query(db.func.sum(Member.debt)).scalar() or 0
    }
    return render_template('index.html', stats=stats)

@bp.route('/books', methods=['GET', 'POST'])
def books():
    if request.method == 'POST':
        book = Book(
            title=request.form['title'],
            author=request.form['author'],
            quantity=int(request.form['quantity'])
        )
        db.session.add(book)
        db.session.commit()
        return redirect(url_for('main.books'))

    books = Book.query.all()
    return render_template('books.html', books=books)

@bp.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        member = Member(
            name=request.form['name'],
            email=request.form['email']
        )
        db.session.add(member)
        db.session.commit()
        return redirect(url_for('main.members'))

    members = Member.query.all()
    return render_template('members.html', members=members)

@bp.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    member = Member.query.get_or_404(member_id)
    data = request.get_json()

    member.name = data.get('name', member.name)
    member.email = data.get('email', member.email)

    db.session.commit()
    return jsonify({'message': 'Member updated successfully'})

@bp.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()

    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.quantity = data.get('quantity', book.quantity)

    db.session.commit()
    return jsonify({'message': 'Book updated successfully'})

@bp.route('/issue-book', methods=['POST'])
def issue_book():
    book_id = request.form['book_id']
    member_id = request.form['member_id']

    member = Member.query.get_or_404(member_id)
    if member.debt > 500:
        return jsonify({'error': 'Member has too much debt'}), 400

    book = Book.query.get_or_404(book_id)
    if book.quantity < 1:
        return jsonify({'error': 'Book out of stock'}), 400

    transaction = Transaction(book_id=book_id, member_id=member_id)
    book.quantity -= 1

    db.session.add(transaction)
    db.session.commit()
    flash('Book issued successfully', 'success')
    return redirect(url_for('main.transactions'))

@bp.route('/return-book', methods=['POST'])
def return_book():
    transaction_id = request.form['transaction_id']
    transaction = Transaction.query.get_or_404(transaction_id)

    if not transaction.return_date:
        days = (datetime.utcnow() - transaction.issue_date).days
        rent_fee = days * 10  # KES 10 per day

        transaction.return_date = datetime.utcnow()
        transaction.rent_fee = rent_fee
        transaction.member.debt += rent_fee
        transaction.book.quantity += 1

        db.session.commit()
        flash(f'Book returned. Rent fee: KES {rent_fee}', 'info')

    return redirect(url_for('main.transactions'))

@bp.route('/transactions')
def transactions():
    books = Book.query.all()
    members = Member.query.all()
    active_transactions = Transaction.query.filter_by(return_date=None).all()
    return render_template('transactions.html',
                         books=books,
                         members=members,
                         active_transactions=active_transactions)

@bp.route('/transactions/history/<int:member_id>')
def transaction_history(member_id):
    member = Member.query.get_or_404(member_id)
    transactions = Transaction.query.filter_by(member_id=member_id).all()
    return jsonify([{
        'book_title': t.book.title,
        'issue_date': t.issue_date.strftime('%Y-%m-%d'),
        'return_date': t.return_date.strftime('%Y-%m-%d') if t.return_date else None,
        'rent_fee': t.rent_fee
    } for t in transactions])

@bp.route('/search/books')
def search_books():
    query = request.args.get('q', '')
    books = Book.query.filter(
        db.or_(
            Book.title.ilike(f'%{query}%'),
            Book.author.ilike(f'%{query}%')
        )
    ).all()
    return jsonify([{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'quantity': book.quantity
    } for book in books])

@bp.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.transactions:
        return jsonify({'error': 'Cannot delete book with transactions'}), 400
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully'})
