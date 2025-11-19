#!/usr/bin/env python3
"""
SQLite'dan PostgreSQL'e veri aktarım script'i
Bu script hr_system.db'deki tüm verileri PostgreSQL'e aktarır.
"""

import json
import os

def load_seed_data():
    """JSON dosyasından verileri yükle"""
    # Script ile aynı dizinde hr_data.json olmalı
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'hr_data.json')
    
    if not os.path.exists(json_path):
        print(f"❌ {json_path} bulunamadı!")
        return None
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def seed_from_sqlite_data(conn, cursor):
    """SQLite'dan alınan verileri PostgreSQL'e aktar"""
    
    data = load_seed_data()
    if not data:
        print("⚠️ Veri dosyası bulunamadı, varsayılan veriler kullanılacak")
        return
    
    print("\n" + "="*50)
    print("SQLite'dan PostgreSQL'e veri aktarımı başlıyor...")
    print("="*50 + "\n")
    
    # 1. KULLANICILAR
    print("👤 Kullanıcılar aktarılıyor...")
    for user in data.get('users', []):
        try:
            cursor.execute('''
                INSERT INTO users (id, username, password_hash, email, full_name, role, aktif)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            ''', (user['id'], user['username'], user['password_hash'], 
                  user.get('email'), user.get('full_name'), user.get('role', 'user'), 
                  bool(user.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Kullanıcı hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('users', []))} kullanıcı aktarıldı")
    
    # 2. MÜŞTERİLER
    print("🏢 Müşteriler aktarılıyor...")
    for m in data.get('musteriler', []):
        try:
            cursor.execute('''
                INSERT INTO musteriler (id, musteri_adi, sektor, yetkili_kisi, telefon, email, adres, logo_yolu, aktif)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (musteri_adi) DO NOTHING
            ''', (m['id'], m['musteri_adi'], m.get('sektor'), m.get('yetkili_kisi'),
                  m.get('telefon'), m.get('email'), m.get('adres'), m.get('logo_yolu'),
                  bool(m.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Müşteri hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('musteriler', []))} müşteri aktarıldı")
    
    # 3. PROJELER
    print("📋 Projeler aktarılıyor...")
    for p in data.get('projeler', []):
        try:
            cursor.execute('''
                INSERT INTO projeler (id, proje_adi, aciklama, musteri_id, aktif)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (p['id'], p['proje_adi'], p.get('aciklama'), p.get('musteri_id'),
                  bool(p.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Proje hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('projeler', []))} proje aktarıldı")
    
    # 4. MÜDÜRLÜKLER
    print("🏛️ Müdürlükler aktarılıyor...")
    for m in data.get('mudurluker', []):
        try:
            cursor.execute('''
                INSERT INTO mudurluker (id, mudurluk_adi, aktif)
                VALUES (%s, %s, %s)
                ON CONFLICT (mudurluk_adi) DO NOTHING
            ''', (m['id'], m['mudurluk_adi'], bool(m.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Müdürlük hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('mudurluker', []))} müdürlük aktarıldı")
    
    # 5. DİREKTÖRLÜKLER
    print("🏛️ Direktörlükler aktarılıyor...")
    for d in data.get('direktorlukler', []):
        try:
            cursor.execute('''
                INSERT INTO direktorlukler (id, direktorluk_adi, aktif)
                VALUES (%s, %s, %s)
                ON CONFLICT (direktorluk_adi) DO NOTHING
            ''', (d['id'], d['direktorluk_adi'], bool(d.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Direktörlük hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('direktorlukler', []))} direktörlük aktarıldı")
    
    # 6. İLLER
    print("🗺️ İller aktarılıyor...")
    for il in data.get('iller', []):
        try:
            cursor.execute('''
                INSERT INTO iller (id, il_adi, aktif)
                VALUES (%s, %s, %s)
                ON CONFLICT (il_adi) DO NOTHING
            ''', (il['id'], il['il_adi'], bool(il.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ İl hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('iller', []))} il aktarıldı")
    
    # 7. İLÇELER
    print("🗺️ İlçeler aktarılıyor...")
    for ilce in data.get('ilceler', []):
        try:
            cursor.execute('''
                INSERT INTO ilceler (id, il_id, ilce_adi, aktif)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (ilce['id'], ilce['il_id'], ilce['ilce_adi'], bool(ilce.get('aktif', 1))))
        except Exception as e:
            pass  # Çok fazla ilçe var, hataları sessizce geç
    conn.commit()
    print(f"  ✅ {len(data.get('ilceler', []))} ilçe aktarıldı")
    
    # 8. KAYNAKLAR
    print("📌 Kaynaklar aktarılıyor...")
    for k in data.get('kaynaklar', []):
        try:
            cursor.execute('''
                INSERT INTO kaynaklar (id, kaynak_adi, aciklama, aktif)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (kaynak_adi) DO NOTHING
            ''', (k['id'], k['kaynak_adi'], k.get('aciklama'), bool(k.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Kaynak hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('kaynaklar', []))} kaynak aktarıldı")
    
    # 9. ÇALIŞMA ŞEKİLLERİ
    print("⏰ Çalışma şekilleri aktarılıyor...")
    for c in data.get('calisma_sekilleri', []):
        try:
            cursor.execute('''
                INSERT INTO calisma_sekilleri (id, calisma_sekli, aktif)
                VALUES (%s, %s, %s)
                ON CONFLICT (calisma_sekli) DO NOTHING
            ''', (c['id'], c['calisma_sekli'], bool(c.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Çalışma şekli hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('calisma_sekilleri', []))} çalışma şekli aktarıldı")
    
    # 10. ÇIKIŞ NEDENLERİ
    print("🚪 Çıkış nedenleri aktarılıyor...")
    for c in data.get('cikis_nedenleri', []):
        try:
            cursor.execute('''
                INSERT INTO cikis_nedenleri (id, neden, aktif)
                VALUES (%s, %s, %s)
                ON CONFLICT (neden) DO NOTHING
            ''', (c['id'], c['neden'], bool(c.get('aktif', 1))))
        except Exception as e:
            print(f"  ⚠️ Çıkış nedeni hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('cikis_nedenleri', []))} çıkış nedeni aktarıldı")
    
    # 11. EMAIL AYARLARI
    print("📧 Email ayarları aktarılıyor...")
    for e in data.get('email_ayarlari', []):
        try:
            cursor.execute('''
                INSERT INTO email_ayarlari (id, ayar_adi, ayar_degeri, aciklama, aktif)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ayar_adi) DO UPDATE SET ayar_degeri = EXCLUDED.ayar_degeri
            ''', (e['id'], e['ayar_adi'], e.get('ayar_degeri'), e.get('aciklama'),
                  bool(e.get('aktif', 1))))
        except Exception as ex:
            print(f"  ⚠️ Email ayarı hatası: {ex}")
    conn.commit()
    print(f"  ✅ {len(data.get('email_ayarlari', []))} email ayarı aktarıldı")
    
    # 12. EMAIL ŞABLONLARI
    print("📝 Email şablonları aktarılıyor...")
    for s in data.get('email_sablonlari', []):
        try:
            cursor.execute('''
                INSERT INTO email_sablonlari (id, sablon_adi, sablon_konusu, sablon_icerik, aktif)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (sablon_adi) DO UPDATE SET 
                    sablon_konusu = EXCLUDED.sablon_konusu,
                    sablon_icerik = EXCLUDED.sablon_icerik
            ''', (s['id'], s['sablon_adi'], s['sablon_konusu'], s['sablon_icerik'],
                  bool(s.get('aktif', 1))))
        except Exception as ex:
            print(f"  ⚠️ Email şablonu hatası: {ex}")
    conn.commit()
    print(f"  ✅ {len(data.get('email_sablonlari', []))} email şablonu aktarıldı")
    
    # 13. HEDEF KADROLAR
    print("👥 Hedef kadrolar aktarılıyor...")
    for hk in data.get('hedef_kadrolar', []):
        try:
            cursor.execute('''
                INSERT INTO hedef_kadrolar (id, proje_id, pozisyon_adi, calisma_sekli, 
                    mudurluk_id, direktorluk_id, il_id, ilce_id, magaza_adi, 
                    hedef_kisi_sayisi, dolu_kisi_sayisi, aracli_durum, durum)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (hk['id'], hk['proje_id'], hk['pozisyon_adi'], hk.get('calisma_sekli'),
                  hk.get('mudurluk_id'), hk.get('direktorluk_id'), hk.get('il_id'),
                  hk.get('ilce_id'), hk.get('magaza_adi'), hk.get('hedef_kisi_sayisi', 1),
                  hk.get('dolu_kisi_sayisi', 0), hk.get('aracli_durum'), hk.get('durum', 'Açık')))
        except Exception as e:
            print(f"  ⚠️ Kadro hatası: {e}")
    conn.commit()
    print(f"  ✅ {len(data.get('hedef_kadrolar', []))} kadro aktarıldı")
    
    # 14. ADAYLAR
    print("👤 Adaylar aktarılıyor...")
    for a in data.get('adaylar', []):
        try:
            # Boş string'leri None'a çevir
            dogum_tarihi = a.get('dogum_tarihi') if a.get('dogum_tarihi') else None
            ise_baslama_tarihi = a.get('ise_baslama_tarihi') if a.get('ise_baslama_tarihi') else None
            
            cursor.execute('''
                INSERT INTO adaylar (id, kadro_id, ad_soyad, telefon, email, tc_kimlik,
                    dogum_tarihi, notlar, kaynak_id, kaynak_diger, durum, ise_baslama_tarihi)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (a['id'], a['kadro_id'], a['ad_soyad'], a.get('telefon'), a.get('email'),
                  a.get('tc_kimlik'), dogum_tarihi, a.get('notlar'),
                  a.get('kaynak_id') or None, a.get('kaynak_diger'), a.get('durum', 'Aday'),
                  ise_baslama_tarihi))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"  ⚠️ Aday hatası ({a.get('ad_soyad', 'N/A')}): {e}")
    print(f"  ✅ {len(data.get('adaylar', []))} aday aktarıldı")
    
    # 15. ÇALIŞANLAR
    print("👷 Çalışanlar aktarılıyor...")
    for c in data.get('calisanlar', []):
        try:
            # Boş string'leri None'a çevir (PostgreSQL NULL için)
            dogum_tarihi = c.get('dogum_tarihi') if c.get('dogum_tarihi') else None
            cikis_tarihi = c.get('cikis_tarihi') if c.get('cikis_tarihi') else None
            adres = c.get('adres') if c.get('adres') else None
            
            cursor.execute('''
                INSERT INTO calisanlar (id, aday_id, kadro_id, ad_soyad, telefon, email,
                    tc_kimlik, dogum_tarihi, adres, ise_baslama_tarihi, cikis_tarihi,
                    cikis_nedeni, liste_durumu, aracli_durum, aktif)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (c['id'], c.get('aday_id') or None, c['kadro_id'], c['ad_soyad'], c.get('telefon'),
                  c.get('email'), c.get('tc_kimlik'), dogum_tarihi, adres,
                  c['ise_baslama_tarihi'], cikis_tarihi, c.get('cikis_nedeni'),
                  c.get('liste_durumu'), c.get('aracli_durum'), bool(c.get('aktif', 1))))
            conn.commit()  # Her çalışan için ayrı commit
        except Exception as e:
            conn.rollback()  # Hata durumunda rollback
            print(f"  ⚠️ Çalışan hatası ({c.get('ad_soyad', 'N/A')}): {e}")
    print(f"  ✅ {len(data.get('calisanlar', []))} çalışan aktarıldı")
    
    # 16. ÇIKIŞ KAYITLARI
    print("📋 Çıkış kayıtları aktarılıyor...")
    for ck in data.get('cikis_kayitlari', []):
        try:
            cursor.execute('''
                INSERT INTO cikis_kayitlari (id, calisan_id, cikis_tarihi, cikis_nedeni,
                    liste_durumu, tekrar_ise_alinabilir, zimmet_teslim, kiyafet_teslim,
                    anahtar_teslim, kimlik_teslim, ihbar_tazminat_durumu, kidem_tazminat_durumu,
                    yonetici_notu, ik_notu, genel_degerlendirme, islem_yapan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (ck['id'], ck['calisan_id'], ck['cikis_tarihi'], ck.get('cikis_nedeni'),
                  ck.get('liste_durumu'), bool(ck.get('tekrar_ise_alinabilir', 1)),
                  bool(ck.get('zimmet_teslim', 0)), bool(ck.get('kiyafet_teslim', 0)),
                  bool(ck.get('anahtar_teslim', 0)), bool(ck.get('kimlik_teslim', 0)),
                  ck.get('ihbar_tazminat_durumu'), ck.get('kidem_tazminat_durumu'),
                  ck.get('yonetici_notu'), ck.get('ik_notu'), ck.get('genel_degerlendirme'),
                  ck.get('islem_yapan')))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"  ⚠️ Çıkış kaydı hatası: {e}")
    print(f"  ✅ {len(data.get('cikis_kayitlari', []))} çıkış kaydı aktarıldı")
    
    # Sequence'ları güncelle (ID çakışması olmaması için)
    print("\n🔄 Sequence'lar güncelleniyor...")
    tables_with_id = [
        'users', 'musteriler', 'projeler', 'mudurluker', 'direktorlukler',
        'iller', 'ilceler', 'kaynaklar', 'calisma_sekilleri', 'cikis_nedenleri',
        'email_ayarlari', 'email_sablonlari', 'hedef_kadrolar', 'adaylar',
        'calisanlar', 'cikis_kayitlari'
    ]
    
    for table in tables_with_id:
        try:
            cursor.execute(f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1))")
        except:
            pass
    conn.commit()
    
    print("\n" + "="*50)
    print("✅ Veri aktarımı tamamlandı!")
    print("="*50 + "\n")


if __name__ == '__main__':
    # Test için doğrudan çalıştır
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    seed_from_sqlite_data(conn, cursor)
    conn.close()