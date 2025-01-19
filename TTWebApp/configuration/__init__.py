from flask import Flask
from flask_login import LoginManager
from .dbInitialization import db
from .blueprint import blp
from .apiRoutes import apiblp
from .models import User

DB_NAME = "appDatabase.db"


def create_application():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'TTapp'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    db.init_app(app)

    app.register_blueprint(blp, url_prefix='/')
    app.register_blueprint(apiblp)

    login_manager = LoginManager()
    login_manager.login_view = 'blp.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
