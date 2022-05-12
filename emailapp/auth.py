from flask import Blueprint, request, redirect, url_for, render_template
from flask_login import login_user, current_user
from flask_login.utils import logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User
from . import db
from flask import session
from datetime import datetime


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username:
            return 'email or username not found.'
        elif '@' in username:
            user = User.query.filter_by(email=username).first()
        else:
            user = User.query.filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                session['year'] = datetime.now().year
                session['month'] = datetime.now().month
                session['day'] = datetime.now().day
                return redirect(url_for('routes.home'))
            else:
                return 'wrong password'
        else:
            return 'User not registered'
    return render_template('login.html', user=current_user)


@auth.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            return 'email already in use, sorry.'
        else:
            user = User(username=username, email=email, password=generate_password_hash(password, method='sha256'))
            try:
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                session['year'] = datetime.now().year
                session['month'] = datetime.now().month
                session['day'] = datetime.now().day
                return redirect(url_for('routes.home'))
            except:
                return 'there was an error adding you to the database.'
    return render_template('register.html', user=current_user)

@auth.route('/logout')
def logout():
    logout_user()
    session.pop('year', None)
    session.pop('month', None)
    session.pop('day', None)
    return redirect(url_for('routes.home'))
        



