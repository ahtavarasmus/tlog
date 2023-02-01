from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 
from os import path
from flask_mail import Mail
import os
import json
import time
from flask_crontab import Crontab

with open('/etc/config.json') as config_file:
    config = json.load(config_file)

crontab = Crontab()
db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.get('SECRET_KEY') 
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('SQLALCHEMY_DATABASE_URI')

    db.init_app(app)
    mail.init_app(app)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = config.get("GMAIL_USER")
    app.config['MAIL_PASSWORD'] = config.get("GMAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True

    mail.init_app(app)
    crontab.init_app(app)

    from .auth import auth
    from .routes import routes

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(routes, url_prefix='/')

    create_database(app) 
    
    from .models import User 

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @app.cli.command()
    def scheduled():
        """Run scheduled job."""
        print('Importing feeds...')
        time.sleep(5)
        print('Users:', str(User.query.all()))
        print('Done!')

    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    return app

def create_database(app):
    if not path.exists('emailapp/prod_db.db'):
        db.create_all(app=app)
        print('CREATED THE DATABASE.')
