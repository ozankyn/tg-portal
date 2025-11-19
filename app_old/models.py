from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    aktif = db.Column(db.Boolean, default=True)
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    son_giris_tarihi = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Musteri(db.Model):
    __tablename__ = 'musteriler'
    
    id = db.Column(db.Integer, primary_key=True)
    musteri_adi = db.Column(db.String(100), unique=True, nullable=False)
    sektor = db.Column(db.String(100))
    yetkili_kisi = db.Column(db.String(100))
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    adres = db.Column(db.Text)
    logo_yolu = db.Column(db.String(255))
    aktif = db.Column(db.Boolean, default=True)
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    
    projeler = db.relationship('Proje', backref='musteri', lazy=True)

class Proje(db.Model):
    __tablename__ = 'projeler'
    
    id = db.Column(db.Integer, primary_key=True)
    proje_adi = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'))
    aktif = db.Column(db.Boolean, default=True)
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    
    kadrolar = db.relationship('HedefKadro', backref='proje', lazy=True)

class Mudurluk(db.Model):
    __tablename__ = 'mudurluker'
    
    id = db.Column(db.Integer, primary_key=True)
    mudurluk_adi = db.Column(db.String(100), unique=True, nullable=False)
    aktif = db.Column(db.Boolean, default=True)

class Direktorluk(db.Model):
    __tablename__ = 'direktorlukler'
    
    id = db.Column(db.Integer, primary_key=True)
    direktorluk_adi = db.Column(db.String(100), unique=True, nullable=False)
    aktif = db.Column(db.Boolean, default=True)

class Il(db.Model):
    __tablename__ = 'iller'
    
    id = db.Column(db.Integer, primary_key=True)
    il_adi = db.Column(db.String(50), unique=True, nullable=False)
    aktif = db.Column(db.Boolean, default=True)
    
    ilceler = db.relationship('Ilce', backref='il', lazy=True)

class Ilce(db.Model):
    __tablename__ = 'ilceler'
    
    id = db.Column(db.Integer, primary_key=True)
    il_id = db.Column(db.Integer, db.ForeignKey('iller.id'), nullable=False)
    ilce_adi = db.Column(db.String(50), nullable=False)
    aktif = db.Column(db.Boolean, default=True)

class HedefKadro(db.Model):
    __tablename__ = 'hedef_kadrolar'
    
    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'), nullable=False)
    pozisyon_adi = db.Column(db.String(100), nullable=False)
    calisma_sekli = db.Column(db.String(50))
    mudurluk_id = db.Column(db.Integer, db.ForeignKey('mudurluker.id'))
    direktorluk_id = db.Column(db.Integer, db.ForeignKey('direktorlukler.id'))
    il_id = db.Column(db.Integer, db.ForeignKey('iller.id'))
    ilce_id = db.Column(db.Integer, db.ForeignKey('ilceler.id'))
    magaza_adi = db.Column(db.String(100))
    hedef_kisi_sayisi = db.Column(db.Integer, default=1)
    dolu_kisi_sayisi = db.Column(db.Integer, default=0)
    aracli_durum = db.Column(db.String(20))
    durum = db.Column(db.String(20), default='Açık')
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    
    mudurluk = db.relationship('Mudurluk', backref='kadrolar')
    direktorluk = db.relationship('Direktorluk', backref='kadrolar')
    il = db.relationship('Il', backref='kadrolar')
    ilce = db.relationship('Ilce', backref='kadrolar')
    adaylar = db.relationship('Aday', backref='kadro', lazy=True)
    calisanlar = db.relationship('Calisan', backref='kadro', lazy=True)

class Aday(db.Model):
    __tablename__ = 'adaylar'
    
    id = db.Column(db.Integer, primary_key=True)
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'), nullable=False)
    ad_soyad = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    tc_kimlik = db.Column(db.String(11))
    dogum_tarihi = db.Column(db.Date)
    notlar = db.Column(db.Text)
    kaynak_id = db.Column(db.Integer, db.ForeignKey('kaynaklar.id'))
    kaynak_diger = db.Column(db.String(100))
    durum = db.Column(db.String(20), default='Aday')
    basvuru_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    ise_baslama_tarihi = db.Column(db.Date)

class Calisan(db.Model):
    __tablename__ = 'calisanlar'
    
    id = db.Column(db.Integer, primary_key=True)
    aday_id = db.Column(db.Integer, db.ForeignKey('adaylar.id'))
    kadro_id = db.Column(db.Integer, db.ForeignKey('hedef_kadrolar.id'), nullable=False)
    ad_soyad = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    tc_kimlik = db.Column(db.String(11))
    dogum_tarihi = db.Column(db.Date)
    adres = db.Column(db.Text)
    ise_baslama_tarihi = db.Column(db.Date, nullable=False)
    cikis_tarihi = db.Column(db.Date)
    cikis_nedeni = db.Column(db.String(100))
    liste_durumu = db.Column(db.String(20))
    aracli_durum = db.Column(db.String(20))
    aktif = db.Column(db.Boolean, default=True)
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)

class Kaynak(db.Model):
    __tablename__ = 'kaynaklar'
    
    id = db.Column(db.Integer, primary_key=True)
    kaynak_adi = db.Column(db.String(100), unique=True, nullable=False)
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Boolean, default=True)

class CikisTuru(db.Model):
    __tablename__ = 'cikis_nedenleri'
    
    id = db.Column(db.Integer, primary_key=True)
    neden = db.Column(db.String(100), unique=True, nullable=False)
    aktif = db.Column(db.Boolean, default=True)

class CikisKaydi(db.Model):
    __tablename__ = 'cikis_kayitlari'
    
    id = db.Column(db.Integer, primary_key=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    cikis_tarihi = db.Column(db.Date, nullable=False)
    cikis_nedeni = db.Column(db.String(100))
    liste_durumu = db.Column(db.String(20))
    tekrar_ise_alinabilir = db.Column(db.Boolean, default=True)
    zimmet_teslim = db.Column(db.Boolean, default=False)
    kiyafet_teslim = db.Column(db.Boolean, default=False)
    anahtar_teslim = db.Column(db.Boolean, default=False)
    kimlik_teslim = db.Column(db.Boolean, default=False)
    ihbar_tazminat_durumu = db.Column(db.String(100))
    kidem_tazminat_durumu = db.Column(db.String(100))
    yonetici_notu = db.Column(db.Text)
    ik_notu = db.Column(db.Text)
    genel_degerlendirme = db.Column(db.Text)
    islem_yapan = db.Column(db.String(100))
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    
    calisan = db.relationship('Calisan', backref='cikis_kayitlari')

class SurecLog(db.Model):
    __tablename__ = 'surec_loglari'
    
    id = db.Column(db.Integer, primary_key=True)
    islem_tipi = db.Column(db.String(50))
    tablo_adi = db.Column(db.String(50))
    kayit_id = db.Column(db.Integer)
    aciklama = db.Column(db.Text)
    kullanici = db.Column(db.String(100))
    islem_tarihi = db.Column(db.DateTime, default=datetime.utcnow)