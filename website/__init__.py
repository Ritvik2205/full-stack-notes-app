from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path, getenv, environ
from flask_login import LoginManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
import redis
from flask_session import Session
from flask_pymongo import PyMongo
# from .auth import get_current_user
import datetime
from dotenv import load_dotenv
# import mysql.connector

load_dotenv()


MYSQL_DB_NAME = getenv("MYSQL_DB_NAME")
MYSQL_USERNAME = getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = getenv("MYSQL_PASSWORD")
MYSQL_PORT = getenv("MYSQL_PORT")
MYSQL_HOST = getenv("MYSQL_HOST")

MONGO_DB_NAME = getenv("MONGO_DB_NAME")
MONGO_HOST = getenv("MONGO_HOST")

db = SQLAlchemy()
mail = Mail()
mongo = PyMongo()

def create_app():

    # connection = mysql.connector.connect(
    #     user='root', password='', host='mysql', port="3306", database='database')
    # print("DB connected")

    # cursor = connection.cursor()
    # cursor.execute('Select * FROM user')
    # users = cursor.fetchall()
    # connection.close()

    # print(users)

    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = getenv("SECRET_KEY")

    
    app.config['SQLALCHEMY_DATABASE_URI'] = \
                    f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}'

    app.config['MAIL_SERVER'] = getenv("MAIL_SERVER")
    app.config['MAIL_PORT'] = getenv("MAIL_PORT")
    app.config['MAIL_USERNAME'] = getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = getenv("MAIL_PASSWORD")
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_DEFAULT_SENDER'] = getenv("MAIL_DEFAULT_SENDER")

    #configuring redis
    app.config['SESSION_TYPE'] = getenv("SESSION_TYPE")
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_REDIS'] = redis.Redis(host=getenv("SESSION_REDIS_HOST"), port=getenv("SESSION_REDIS_PORT"))

    #configuring mongodb
    app.config['MONGO_URI'] = f'mongodb://{MONGO_HOST}:27017/{MONGO_DB_NAME}'

    db.init_app(app)
    mail.init_app(app)
    Session(app)
    mongo.init_app(app)

    s = URLSafeTimedSerializer('random-secret')

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    with app.app_context():
        db.create_all()

    


    return app



# def create_database(app):
#     if not path.exists('website/' + DB_NAME):
#         db.create_all(app=app)
#         print('Created Database!')
#
# <------- create_all() no longer supports arguments ------>