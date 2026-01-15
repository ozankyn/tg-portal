from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class Depo(db.Model, TimestampMixin, SoftDeleteMixin):
    """Depo tanımları"""
    __tablename__ = 'depolar'
    
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(20), unique=True, nullable=False)
    ad = db.Column(db.String(100), nullable=False)
    adres = db.Column(db.Text)
    sorumlu_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    aktif = db.Column(db.Boolean, default=True)
    notlar = db.Column(db.Text)
    
    # İlişkiler
    sorumlu = db.relationship('User', foreign_keys=[sorumlu_id])
    stok_kartlari = db.relationship('StokKarti', backref='depo', lazy='dynamic')


class UrunKategori(db.Model, TimestampMixin, SoftDeleteMixin):
    """Ürün kategorileri"""
    __tablename__ = 'urun_kategorileri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    ust_kategori_id = db.Column(db.Integer, db.ForeignKey('urun_kategorileri.id'))
    aktif = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    ust_kategori = db.relationship('UrunKategori', remote_side=[id], backref='alt_kategoriler')


class Urun(db.Model, TimestampMixin, SoftDeleteMixin):
    """Ürün/Malzeme tanımları"""
    __tablename__ = 'urunler'
    
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(50), unique=True, nullable=False)
    barkod = db.Column(db.String(50))
    ad = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    
    kategori_id = db.Column(db.Integer, db.ForeignKey('urun_kategorileri.id'))
    birim = db.Column(db.String(20), default='Adet')  # Adet, Kg, Lt, Kutu, Paket
    
    # Fiyatlar
    alis_fiyati = db.Column(db.Numeric(12, 2))
    satis_fiyati = db.Column(db.Numeric(12, 2))
    
    # Stok uyarı limitleri
    min_stok = db.Column(db.Integer, default=0)
    max_stok = db.Column(db.Integer)
    
    aktif = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    kategori = db.relationship('UrunKategori', backref='urunler')
    stok_kartlari = db.relationship('StokKarti', backref='urun', lazy='dynamic')
    
    @property
    def toplam_stok(self):
        """Tüm depolardaki toplam stok"""
        return sum(sk.miktar for sk in self.stok_kartlari.filter_by(is_deleted=False).all())


class StokKarti(db.Model, TimestampMixin, SoftDeleteMixin):
    """Depo bazlı stok kartları"""
    __tablename__ = 'stok_kartlari'
    
    id = db.Column(db.Integer, primary_key=True)
    depo_id = db.Column(db.Integer, db.ForeignKey('depolar.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urunler.id'), nullable=False)
    
    miktar = db.Column(db.Numeric(12, 2), default=0)
    rezerve_miktar = db.Column(db.Numeric(12, 2), default=0)  # Rezerve edilmiş miktar
    
    # Proje/Müşteri bazlı stok
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'))
    
    __table_args__ = (
        db.UniqueConstraint('depo_id', 'urun_id', 'proje_id', 'musteri_id', name='uq_stok_karti'),
    )
    
    @property
    def kullanilabilir_miktar(self):
        return float(self.miktar or 0) - float(self.rezerve_miktar or 0)


class StokHareketi(db.Model, TimestampMixin, SoftDeleteMixin):
    """Stok giriş/çıkış hareketleri"""
    __tablename__ = 'stok_hareketleri'
    
    id = db.Column(db.Integer, primary_key=True)
    hareket_no = db.Column(db.String(30), unique=True, nullable=False)
    tarih = db.Column(db.DateTime, nullable=False)
    
    # Hareket tipi
    tip = db.Column(db.String(20), nullable=False)  # giris, cikis, transfer, sayim, zimmet
    
    # Depo bilgileri
    depo_id = db.Column(db.Integer, db.ForeignKey('depolar.id'), nullable=False)
    hedef_depo_id = db.Column(db.Integer, db.ForeignKey('depolar.id'))  # Transfer için
    
    # İlişkili taraf (Tedarikçi, Müşteri, Personel, Şirket)
    taraf_tipi = db.Column(db.String(20))  # tedarikci, musteri, personel, sirket, diger
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'))
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'))
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'))  # Personele zimmet
    sirket_adi = db.Column(db.String(200))  # Dış şirket
    
    # Proje
    proje_id = db.Column(db.Integer, db.ForeignKey('projeler.id'))
    
    # Belge bilgileri
    belge_no = db.Column(db.String(50))  # Fatura/İrsaliye no
    belge_tarihi = db.Column(db.Date)
    
    # Durum
    durum = db.Column(db.String(20), default='taslak')  # taslak, onaylandi, iptal
    aciklama = db.Column(db.Text)
    
    # Onay bilgileri
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    onay_tarihi = db.Column(db.DateTime)
    
    # İmza
    imza_data = db.Column(db.Text)  # Base64 imza
    imzalayan_ad = db.Column(db.String(100))
    imza_tarihi = db.Column(db.DateTime)
    
    # İlişkiler
    depo = db.relationship('Depo', foreign_keys=[depo_id], backref='hareketler')
    hedef_depo = db.relationship('Depo', foreign_keys=[hedef_depo_id])
    tedarikci = db.relationship('Tedarikci', backref='stok_hareketleri')
    calisan = db.relationship('Calisan', backref='stok_hareketleri')
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    onaylayan = db.relationship('User', foreign_keys=[onaylayan_id])
    kalemler = db.relationship('StokHareketiKalem', backref='hareket', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def tip_text(self):
        tipler = {
            'giris': 'Mal Girişi',
            'cikis': 'Mal Çıkışı',
            'transfer': 'Depo Transferi',
            'sayim': 'Sayım Düzeltme',
            'zimmet': 'Personel Zimmet'
        }
        return tipler.get(self.tip, self.tip)
    
    @property
    def durum_text(self):
        durumlar = {
            'taslak': 'Taslak',
            'onaylandi': 'Onaylandı',
            'iptal': 'İptal'
        }
        return durumlar.get(self.durum, self.durum)
    
    @property
    def toplam_tutar(self):
        return sum(k.toplam for k in self.kalemler.filter_by(is_deleted=False).all())


class StokHareketiKalem(db.Model, TimestampMixin, SoftDeleteMixin):
    """Stok hareketi kalemleri"""
    __tablename__ = 'stok_hareketi_kalemleri'
    
    id = db.Column(db.Integer, primary_key=True)
    hareket_id = db.Column(db.Integer, db.ForeignKey('stok_hareketleri.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urunler.id'), nullable=False)
    
    miktar = db.Column(db.Numeric(12, 2), nullable=False)
    birim_fiyat = db.Column(db.Numeric(12, 2))
    
    seri_no = db.Column(db.String(100))
    lot_no = db.Column(db.String(100))
    son_kullanma = db.Column(db.Date)
    
    aciklama = db.Column(db.Text)
    
    # İlişkiler
    urun = db.relationship('Urun', backref='hareket_kalemleri')
    
    @property
    def toplam(self):
        return float(self.miktar or 0) * float(self.birim_fiyat or 0)
