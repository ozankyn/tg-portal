# -*- coding: utf-8 -*-
"""
TG Portal - Team Guerilla ERP Sistemi
Flask Application Factory
"""

from flask import Flask
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_mail import Mail
import os
import time

# Sunucu saat dilimi - Türkiye (Europe/Istanbul).
# datetime.now(), date.today(), time.localtime() ve loglar bu saat dilimini kullanır.
# Tüm zaman damgaları datetime.now() ile (yerel saat) saklanır; utcnow KULLANILMAZ.
os.environ['TZ'] = 'Europe/Istanbul'
try:
    time.tzset()  # Unix; Windows'ta mevcut değil
except AttributeError:
    pass

# Extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()


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

    # Saat dilimi (Türkiye)
    app.config['TIMEZONE'] = 'Europe/Istanbul'
    
    # Upload settings
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 110 * 1024 * 1024  # 110MB max (video uploads up to 100MB)
    # Flask-Login Remember Me
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    
    # NetGSM SMS
    app.config['NETGSM_USERCODE'] = os.environ.get('NETGSM_USERCODE', '')
    app.config['NETGSM_PASSWORD'] = os.environ.get('NETGSM_PASSWORD', '')
    app.config['NETGSM_HEADER'] = os.environ.get('NETGSM_HEADER', '')
    
    # Mail Settings
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', '')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # Anthropic AI
    app.config['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')
    
    # Şirket Ayarları
    app.config['COMPANY_NAME'] = os.environ.get('COMPANY_NAME', '')
    app.config['COMPANY_SUBTITLE'] = os.environ.get('COMPANY_SUBTITLE', 'ERP Sistemi')
    app.config['COMPANY_LOGO'] = os.environ.get('COMPANY_LOGO', 'logo.png')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    
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
    from app.modules.kariyer.routes import kariyer_bp
    from app.modules.masraf.routes import masraf_bp
    from app.modules.sozlesme.routes import sozlesme_bp
    from app.modules.satinalma.routes import satinalma_bp
    from app.modules.talep.routes import talep_bp
    from app.modules.rapor.routes import rapor_bp
    from app.modules.ayarlar.routes import ayarlar_bp
    from app.modules.sirket.routes import sirket_bp
    from app.modules.depo.routes import depo_bp
    
    app.register_blueprint(core_bp)
    app.register_blueprint(ik_bp, url_prefix='/ik')
    app.register_blueprint(filo_bp, url_prefix='/filo')
    app.register_blueprint(tedarikci_bp, url_prefix='/tedarikci')
    app.register_blueprint(proje_bp, url_prefix='/proje')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(basvuru_bp, url_prefix='/basvuru')
    app.register_blueprint(kariyer_bp, url_prefix='/kariyer')
    from app.modules.egitim.routes import egitim_bp
    app.register_blueprint(egitim_bp, url_prefix="/egitim")

    from app.modules.todo.routes import todo_bp
    app.register_blueprint(todo_bp, url_prefix="/todo")

    from app.modules.takvim.routes import takvim_bp
    from app.modules.mesaj.routes import mesaj_bp
    app.register_blueprint(takvim_bp, url_prefix="/takvim")
    csrf.exempt(takvim_bp)
    app.register_blueprint(mesaj_bp, url_prefix="/mesaj")
    csrf.exempt(mesaj_bp)
    app.register_blueprint(masraf_bp, url_prefix="/masraf")
    app.register_blueprint(sozlesme_bp, url_prefix="/sozlesme")
    app.register_blueprint(satinalma_bp, url_prefix="/satinalma")
    app.register_blueprint(talep_bp, url_prefix="/talep")
    app.register_blueprint(rapor_bp, url_prefix="/rapor")
    app.register_blueprint(ayarlar_bp, url_prefix="/ayarlar")
    app.register_blueprint(sirket_bp, url_prefix="/sirket")
    app.register_blueprint(depo_bp, url_prefix="/depo")

    from app.modules.onay.routes import onay_bp
    app.register_blueprint(onay_bp, url_prefix="/onay")
    
    # CSRF token süresi dolduğunda çirkin "Bad Request" yerine flash + geri yönlendir
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import flash, redirect, request, url_for
        flash('Oturum süreniz dolmuş, lütfen tekrar deneyin.', 'warning')
        return redirect(request.referrer or url_for('core.dashboard'))

    # Bozuk transaction temizleme
    @app.before_request
    def cleanup_db_session():
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception:
            db.session.rollback()

    @app.before_request
    def zorunlu_sifre_degistir():
        from flask import request, redirect, url_for
        from flask_login import current_user
        if not current_user.is_authenticated or current_user.sifre_degistirildi:
            return None
        if request.endpoint in (
            'core.sifre_degistir',
            'core.logout',
            'core.login',
            'static',
            'uploaded_file',
        ):
            return None
        return redirect(url_for('core.sifre_degistir'))

    # Jinja filters
    from markupsafe import Markup, escape

    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if not s:
            return ''
        return Markup('<br>'.join(escape(s).split('\n')))

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

    @app.cli.command('sozlesme-uyari')
    def sozlesme_uyari_cmd():
        """Sözleşmesi dolacak personel için uyarı maili gönder"""
        from app.services.notification import notify_sozlesme_dolacak
        count = notify_sozlesme_dolacak()
        print(f'{count} sözleşme uyarısı gönderildi.')
    

    # CLI komutlarını register et
    from app.scripts import import_calisanlar
    import_calisanlar.init_app(app)
    from app.scripts import import_araclar
    import_araclar.init_app(app)

    # Uploads klasörü için route
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Scheduler baslat
    from app.scheduler import init_scheduler
    init_scheduler(app)

    return app