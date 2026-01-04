# -*- coding: utf-8 -*-
"""
TG Portal - Quiz/Sınav Modelleri
Soru bankası, testler ve sonuçlar
"""

from datetime import datetime
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


class SoruKategorisi(db.Model, TimestampMixin):
    """Soru kategorileri - Konulara göre gruplandırma"""
    __tablename__ = 'soru_kategorileri'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text)
    ust_kategori_id = db.Column(db.Integer, db.ForeignKey('soru_kategorileri.id'))
    aktif = db.Column(db.Boolean, default=True)
    sira = db.Column(db.Integer, default=0)
    
    # İlişkiler
    ust_kategori = db.relationship('SoruKategorisi', remote_side=[id], backref='alt_kategoriler')
    sorular = db.relationship('Soru', backref='kategori', lazy='dynamic')
    
    def __repr__(self):
        return f'<SoruKategorisi {self.ad}>'


class Soru(db.Model, TimestampMixin, SoftDeleteMixin):
    """Soru bankası - Tüm sorular burada"""
    __tablename__ = 'sorular'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Soru içeriği
    soru_metni = db.Column(db.Text, nullable=False)
    soru_tipi = db.Column(db.String(20), default='coktan_secmeli')  # coktan_secmeli, dogru_yanlis, coklu_secim
    
    # Kategori ve zorluk
    kategori_id = db.Column(db.Integer, db.ForeignKey('soru_kategorileri.id'))
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'))  # Hangi eğitim tipine ait
    zorluk = db.Column(db.Integer, default=1)  # 1: Kolay, 2: Orta, 3: Zor
    
    # Puanlama
    puan = db.Column(db.Integer, default=10)
    
    # Açıklama (cevap sonrası gösterilecek)
    aciklama = db.Column(db.Text)  # Doğru cevabın açıklaması
    
    # Medya (opsiyonel)
    gorsel_url = db.Column(db.String(500))
    
    aktif = db.Column(db.Boolean, default=True)
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # İlişkiler
    secenekler = db.relationship('SoruSecenegi', backref='soru', lazy='dynamic',
                                  cascade='all, delete-orphan', order_by='SoruSecenegi.sira')
    egitim_tipi = db.relationship('EgitimTipi', backref='sorular')
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    
    @property
    def dogru_secenek(self):
        """Doğru seçeneği döndür"""
        return self.secenekler.filter_by(dogru=True).first()
    
    @property
    def dogru_secenekler(self):
        """Çoklu seçimde tüm doğru seçenekleri döndür"""
        return self.secenekler.filter_by(dogru=True).all()
    
    @property
    def secenek_sayisi(self):
        return self.secenekler.count()
    
    @property
    def zorluk_text(self):
        zorluk_map = {1: 'Kolay', 2: 'Orta', 3: 'Zor'}
        return zorluk_map.get(self.zorluk, 'Bilinmiyor')
    
    @property
    def zorluk_renk(self):
        renk_map = {1: 'success', 2: 'warning', 3: 'danger'}
        return renk_map.get(self.zorluk, 'secondary')
    
    def __repr__(self):
        return f'<Soru {self.id}: {self.soru_metni[:50]}>'


class SoruSecenegi(db.Model, TimestampMixin):
    """Soru seçenekleri"""
    __tablename__ = 'soru_secenekleri'
    
    id = db.Column(db.Integer, primary_key=True)
    soru_id = db.Column(db.Integer, db.ForeignKey('sorular.id'), nullable=False)
    
    secenek_metni = db.Column(db.Text, nullable=False)
    dogru = db.Column(db.Boolean, default=False)
    sira = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<SoruSecenegi {self.secenek_metni[:30]}>'


class Test(db.Model, TimestampMixin, SoftDeleteMixin):
    """Test/Sınav tanımı"""
    __tablename__ = 'testler'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Temel bilgiler
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    
    # Eğitim bağlantısı
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitimler.id'))
    egitim_tipi_id = db.Column(db.Integer, db.ForeignKey('egitim_tipleri.id'))  # Genel test için
    
    # Ayarlar
    sure_dakika = db.Column(db.Integer)  # Süre limiti, NULL = süresiz
    gecme_puani = db.Column(db.Integer, default=70)  # Yüzde olarak
    soru_karistir = db.Column(db.Boolean, default=True)  # Soruları karıştır
    secenek_karistir = db.Column(db.Boolean, default=True)  # Seçenekleri karıştır
    sonucu_goster = db.Column(db.Boolean, default=True)  # Bitince sonucu göster
    dogru_cevaplari_goster = db.Column(db.Boolean, default=False)  # Doğru cevapları göster
    tekrar_hak = db.Column(db.Integer, default=3)  # Kaç kez tekrar çözebilir, NULL = sınırsız
    
    # Durum
    aktif = db.Column(db.Boolean, default=True)
    baslangic_tarihi = db.Column(db.DateTime)  # Test açılış tarihi
    bitis_tarihi = db.Column(db.DateTime)  # Test kapanış tarihi
    
    olusturan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # İlişkiler
    egitim = db.relationship('Egitim', backref=db.backref('testler', lazy='dynamic'))
    egitim_tipi = db.relationship('EgitimTipi', backref='testler')
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    test_sorulari = db.relationship('TestSorusu', backref='test', lazy='dynamic',
                                     cascade='all, delete-orphan', order_by='TestSorusu.sira')
    sonuclar = db.relationship('TestSonuc', backref='test', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    @property
    def soru_sayisi(self):
        return self.test_sorulari.count()
    
    @property
    def toplam_puan(self):
        return sum(ts.soru.puan for ts in self.test_sorulari.all())
    
    @property
    def aktif_mi(self):
        """Test şu an çözülebilir mi?"""
        if not self.aktif:
            return False
        now = datetime.now()
        if self.baslangic_tarihi and now < self.baslangic_tarihi:
            return False
        if self.bitis_tarihi and now > self.bitis_tarihi:
            return False
        return True
    
    @property
    def durum_text(self):
        if not self.aktif:
            return 'Pasif'
        now = datetime.now()
        if self.baslangic_tarihi and now < self.baslangic_tarihi:
            return 'Bekliyor'
        if self.bitis_tarihi and now > self.bitis_tarihi:
            return 'Süresi Doldu'
        return 'Aktif'
    
    @property
    def durum_renk(self):
        durum = self.durum_text
        renk_map = {'Aktif': 'success', 'Pasif': 'secondary', 'Bekliyor': 'warning', 'Süresi Doldu': 'danger'}
        return renk_map.get(durum, 'secondary')
    
    def kullanici_cozebilir_mi(self, user_id):
        """Kullanıcı bu testi çözebilir mi?"""
        if not self.aktif_mi:
            return False, 'Test aktif değil'
        
        if self.tekrar_hak:
            cozum_sayisi = self.sonuclar.filter_by(calisan_id=user_id, tamamlandi=True).count()
            if cozum_sayisi >= self.tekrar_hak:
                return False, f'Tekrar hakkınız doldu ({self.tekrar_hak} hak)'
        
        return True, None
    
    def __repr__(self):
        return f'<Test {self.baslik}>'


class TestSorusu(db.Model, TimestampMixin):
    """Test-Soru ilişkisi"""
    __tablename__ = 'test_sorulari'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('testler.id'), nullable=False)
    soru_id = db.Column(db.Integer, db.ForeignKey('sorular.id'), nullable=False)
    sira = db.Column(db.Integer, default=0)
    
    # Puan override (opsiyonel)
    ozel_puan = db.Column(db.Integer)  # NULL ise sorunun default puanı kullanılır
    
    # İlişkiler
    soru = db.relationship('Soru')
    
    @property
    def puan(self):
        return self.ozel_puan if self.ozel_puan else self.soru.puan
    
    __table_args__ = (
        db.UniqueConstraint('test_id', 'soru_id', name='unique_test_soru'),
    )


class TestSonuc(db.Model, TimestampMixin):
    """Test sonuçları - Kullanıcının test çözümü"""
    __tablename__ = 'test_sonuclari'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('testler.id'), nullable=False)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=False)
    
    # Zamanlama
    baslangic_zamani = db.Column(db.DateTime, default=datetime.utcnow)
    bitis_zamani = db.Column(db.DateTime)
    gecen_sure_saniye = db.Column(db.Integer)  # Saniye cinsinden
    
    # Sonuç
    tamamlandi = db.Column(db.Boolean, default=False)
    toplam_puan = db.Column(db.Integer, default=0)
    alinan_puan = db.Column(db.Integer, default=0)
    dogru_sayisi = db.Column(db.Integer, default=0)
    yanlis_sayisi = db.Column(db.Integer, default=0)
    bos_sayisi = db.Column(db.Integer, default=0)
    yuzde = db.Column(db.Float, default=0)
    gecti = db.Column(db.Boolean, default=False)
    
    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('test_sonuclari', lazy='dynamic'))
    cevaplar = db.relationship('TestCevap', backref='sonuc', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    @property
    def sure_text(self):
        """Geçen süreyi formatla"""
        if not self.gecen_sure_saniye:
            return '-'
        dakika = self.gecen_sure_saniye // 60
        saniye = self.gecen_sure_saniye % 60
        return f'{dakika}:{saniye:02d}'
    
    @property
    def durum_text(self):
        if not self.tamamlandi:
            return 'Devam Ediyor'
        return 'Geçti' if self.gecti else 'Kaldı'
    
    @property
    def durum_renk(self):
        if not self.tamamlandi:
            return 'warning'
        return 'success' if self.gecti else 'danger'
    
    def __repr__(self):
        return f'<TestSonuc Test:{self.test_id} Calisan:{self.calisan_id}>'


class TestCevap(db.Model, TimestampMixin):
    """Test cevapları - Her soru için verilen cevap"""
    __tablename__ = 'test_cevaplari'
    
    id = db.Column(db.Integer, primary_key=True)
    sonuc_id = db.Column(db.Integer, db.ForeignKey('test_sonuclari.id'), nullable=False)
    soru_id = db.Column(db.Integer, db.ForeignKey('sorular.id'), nullable=False)
    
    # Cevap
    secilen_secenek_id = db.Column(db.Integer, db.ForeignKey('soru_secenekleri.id'))
    secilen_secenekler = db.Column(db.JSON)  # Çoklu seçim için: [secenek_id, secenek_id, ...]
    
    # Değerlendirme
    dogru = db.Column(db.Boolean)
    alinan_puan = db.Column(db.Integer, default=0)
    
    # İlişkiler
    soru = db.relationship('Soru')
    secilen_secenek = db.relationship('SoruSecenegi')
    
    __table_args__ = (
        db.UniqueConstraint('sonuc_id', 'soru_id', name='unique_sonuc_soru'),
    )
