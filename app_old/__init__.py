from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Konfigürasyon
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://tgportal:tgportal123@localhost:5432/tgportal')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Upload
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
    
    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    login_manager.login_view = 'login'
    login_manager.login_message = 'Bu sayfayı görüntülemek için giriş yapmalısınız.'
    
    # Models import (for migrations)
    from app import models
    
    # Ana sayfa route (geçici)
    @app.route('/')
    def index():
        return '<h1>TG Portal</h1><p>Sistem çalışıyor! PostgreSQL ve Redis hazır.</p>'
    
    return app