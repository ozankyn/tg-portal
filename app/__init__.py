# -*- coding: utf-8 -*-
"""
TG Portal - Team Guerilla ERP Sistemi
Flask Application Factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os

# Extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'postgresql://tgportal:tgportal123@localhost:5432/tgportal'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Upload settings
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Login manager settings
    login_manager.login_view = 'core.login'
    login_manager.login_message = 'Bu sayfayı görüntülemek için giriş yapmalısınız.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.core import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.modules.core.routes import core_bp
    from app.modules.ik.routes import ik_bp
    from app.modules.filo.routes import filo_bp
    from app.modules.tedarikci.routes import tedarikci_bp
    from app.modules.proje.routes import proje_bp
    from app.modules.api.routes import api_bp
    from app.modules.basvuru.routes import basvuru_bp
    
    app.register_blueprint(core_bp)
    app.register_blueprint(ik_bp, url_prefix='/ik')
    app.register_blueprint(filo_bp, url_prefix='/filo')
    app.register_blueprint(tedarikci_bp, url_prefix='/tedarikci')
    app.register_blueprint(proje_bp, url_prefix='/proje')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(basvuru_bp, url_prefix='/basvuru')
    
    
    # Context processors
    @app.context_processor
    def inject_permissions():
        from flask_login import current_user
        return dict(
            has_permission=lambda p: current_user.is_authenticated and current_user.has_permission(p)
        )
    
    # CLI commands
    @app.cli.command('init-db')
    def init_db():
        """Veritabanını oluştur"""
        db.create_all()
        print('Veritabanı tabloları oluşturuldu.')
    
    @app.cli.command('seed')
    def seed_db():
        """Örnek verileri yükle"""
        from seed_data import seed_all
        seed_all()
        print('Örnek veriler yüklendi.')
    
    return app
