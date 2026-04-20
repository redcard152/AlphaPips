
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edgefx.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------- Models ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pair = db.Column(db.String(20), nullable=False)
    entry = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float, nullable=False)
    take_profit = db.Column(db.Float, nullable=False)
    result = db.Column(db.String(10))  # win/lose
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- Helpers ----------
def current_user():
    uid = session.get('user_id')
    if uid:
        return User.query.get(uid)
    return None

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password required', 'error')
            return redirect(url_for('signup'))
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    trades = Trade.query.filter_by(user_id=user.id).order_by(Trade.created_at.desc()).all()
    total = len(trades)
    wins = len([t for t in trades if t.result == 'win'])
    losses = len([t for t in trades if t.result == 'lose'])
    win_rate = round((wins / total) * 100, 2) if total > 0 else 0
    return render_template('dashboard.html', user=user, trades=trades, total=total, wins=wins, losses=losses, win_rate=win_rate)

@app.route('/add_trade', methods=['POST'])
def add_trade():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    pair = request.form.get('pair')
    entry = float(request.form.get('entry'))
    sl = float(request.form.get('sl'))
    tp = float(request.form.get('tp'))
    result = request.form.get('result')
    trade = Trade(user_id=user.id, pair=pair, entry=entry, stop_loss=sl, take_profit=tp, result=result)
    db.session.add(trade)
    db.session.commit()
    return redirect(url_for('dashboard'))

# ---------- Simulated M-Pesa ----------
@app.route('/pay', methods=['GET', 'POST'])
def pay():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # In production, integrate Safaricom Daraja API here
        flash('Payment simulated successfully. (Replace with real M-Pesa integration)', 'success')
        return redirect(url_for('dashboard'))
    return render_template('payment.html')

# ---------- CLI ----------
@app.cli.command('init-db')
def init_db():
    db.create_all()
    print('Database initialized')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
