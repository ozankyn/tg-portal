# =============================================================================
# FİLO YÖNETİMİ MODÜLÜ - FLASK ROUTES
# =============================================================================
# Bu dosya app.py'ye eklenecek

# =============================================================================
# ARAÇLAR - TEMEL İŞLEMLER
# =============================================================================

@app.route('/filo/araclar')
@login_required
def filo_araclar():
    """Araç listesi"""
    conn = get_db()
    
    # Filtreler
    durum_filtre = request.args.get('durum', '')
    zimmet_filtre = request.args.get('zimmet', '')  # 'zimmetli', 'bosta'
    
    # Temel sorgu
    query = '''
        SELECT 
            a.*,
            z.calisan_id,
            c.ad_soyad as zimmetli_calisan,
            z.teslim_tarihi as zimmet_tarihi
        FROM araclar a
        LEFT JOIN (
            SELECT * FROM arac_zimmet WHERE aktif = TRUE
        ) z ON a.id = z.arac_id
        LEFT JOIN calisanlar c ON z.calisan_id = c.id
        WHERE 1=1
    '''
    
    params = []
    
    if durum_filtre:
        query += ' AND a.durum = %s'
        params.append(durum_filtre)
    
    if zimmet_filtre == 'zimmetli':
        query += ' AND z.id IS NOT NULL'
    elif zimmet_filtre == 'bosta':
        query += ' AND z.id IS NULL'
    
    query += ' ORDER BY a.plaka'
    
    araclar = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('filo/araclar.html', araclar=araclar)


@app.route('/filo/arac/ekle', methods=['GET', 'POST'])
@login_required
def filo_arac_ekle():
    """Yeni araç ekle"""
    if request.method == 'POST':
        # Form verilerini al
        plaka = request.form['plaka'].upper().strip()
        marka = request.form['marka']
        model = request.form['model']
        yil = request.form.get('yil')
        renk = request.form.get('renk')
        
        # Teknik bilgiler
        sasi_no = request.form.get('sasi_no')
        motor_no = request.form.get('motor_no')
        yakit_tipi = request.form.get('yakit_tipi')
        
        # Sigorta bilgileri
        sigorta_sirket = request.form.get('sigorta_sirket')
        sigorta_police_no = request.form.get('sigorta_police_no')
        sigorta_bitis_tarihi = request.form.get('sigorta_bitis_tarihi') or None
        
        # Muayene
        muayene_tarihi = request.form.get('muayene_tarihi') or None
        sonraki_muayene_tarihi = request.form.get('sonraki_muayene_tarihi') or None
        
        # Kilometre
        baslangic_km = request.form.get('baslangic_km', 0)
        guncel_km = request.form.get('guncel_km', baslangic_km)
        
        # Notlar
        notlar = request.form.get('notlar')
        
        conn = get_db()
        
        # Plaka kontrolü
        mevcut = conn.execute('SELECT id FROM araclar WHERE plaka = %s', (plaka,)).fetchone()
        if mevcut:
            flash('Bu plaka ile kayıtlı bir araç zaten mevcut!', 'danger')
            conn.close()
            return redirect(url_for('filo_arac_ekle'))
        
        # Araç ekle
        conn.execute('''
            INSERT INTO araclar (
                plaka, marka, model, yil, renk,
                sasi_no, motor_no, yakit_tipi,
                sigorta_sirket, sigorta_police_no, sigorta_bitis_tarihi,
                muayene_tarihi, sonraki_muayene_tarihi,
                baslangic_km, guncel_km, notlar
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s
            )
        ''', (plaka, marka, model, yil, renk,
              sasi_no, motor_no, yakit_tipi,
              sigorta_sirket, sigorta_police_no, sigorta_bitis_tarihi,
              muayene_tarihi, sonraki_muayene_tarihi,
              baslangic_km, guncel_km, notlar))
        
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'araclar', None, f'{plaka} plakalı araç eklendi', session.get('username'))
        flash(f'{plaka} plakalı araç başarıyla eklendi!', 'success')
        return redirect(url_for('filo_araclar'))
    
    return render_template('filo/arac_ekle.html')


@app.route('/filo/arac/<int:arac_id>')
@login_required
def filo_arac_detay(arac_id):
    """Araç detay sayfası"""
    conn = get_db()
    
    # Araç bilgileri
    arac = conn.execute('SELECT * FROM araclar WHERE id = %s', (arac_id,)).fetchone()
    
    if not arac:
        flash('Araç bulunamadı!', 'danger')
        return redirect(url_for('filo_araclar'))
    
    # Mevcut zimmet durumu
    zimmet = conn.execute('''
        SELECT z.*, c.ad_soyad, c.telefon
        FROM arac_zimmet z
        JOIN calisanlar c ON z.calisan_id = c.id
        WHERE z.arac_id = %s AND z.aktif = TRUE
    ''', (arac_id,)).fetchone()
    
    # Teslim/İade geçmişi
    teslim_iade_gecmis = conn.execute('''
        SELECT ti.*, c.ad_soyad, u.username as teslim_eden
        FROM arac_teslim_iade ti
        JOIN calisanlar c ON ti.calisan_id = c.id
        LEFT JOIN users u ON ti.teslim_eden_user_id = u.id
        WHERE ti.arac_id = %s
        ORDER BY ti.islem_tarihi DESC
        LIMIT 20
    ''', (arac_id,)).fetchall()
    
    # Bakım kayıtları
    bakim_kayitlari = conn.execute('''
        SELECT * FROM arac_bakim
        WHERE arac_id = %s
        ORDER BY bakim_tarihi DESC
        LIMIT 10
    ''', (arac_id,)).fetchall()
    
    # Yakıt kayıtları
    yakit_kayitlari = conn.execute('''
        SELECT y.*, c.ad_soyad
        FROM arac_yakit y
        LEFT JOIN calisanlar c ON y.calisan_id = c.id
        WHERE y.arac_id = %s
        ORDER BY y.yakit_tarihi DESC
        LIMIT 10
    ''', (arac_id,)).fetchall()
    
    # Sigorta/Kaza kayıtları
    sigorta_kaza = conn.execute('''
        SELECT * FROM arac_sigorta_kaza
        WHERE arac_id = %s
        ORDER BY kayit_tarihi DESC
        LIMIT 10
    ''', (arac_id,)).fetchall()
    
    conn.close()
    
    return render_template('filo/arac_detay.html',
                         arac=dict(arac),
                         zimmet=dict(zimmet) if zimmet else None,
                         teslim_iade_gecmis=teslim_iade_gecmis,
                         bakim_kayitlari=bakim_kayitlari,
                         yakit_kayitlari=yakit_kayitlari,
                         sigorta_kaza=sigorta_kaza)


@app.route('/filo/arac/<int:arac_id>/duzenle', methods=['GET', 'POST'])
@login_required
def filo_arac_duzenle(arac_id):
    """Araç bilgilerini düzenle"""
    conn = get_db()
    arac = conn.execute('SELECT * FROM araclar WHERE id = %s', (arac_id,)).fetchone()
    
    if not arac:
        flash('Araç bulunamadı!', 'danger')
        return redirect(url_for('filo_araclar'))
    
    if request.method == 'POST':
        # Form verilerini al (arac_ekle ile benzer)
        plaka = request.form['plaka'].upper().strip()
        marka = request.form['marka']
        model = request.form['model']
        yil = request.form.get('yil')
        renk = request.form.get('renk')
        sasi_no = request.form.get('sasi_no')
        motor_no = request.form.get('motor_no')
        yakit_tipi = request.form.get('yakit_tipi')
        sigorta_sirket = request.form.get('sigorta_sirket')
        sigorta_police_no = request.form.get('sigorta_police_no')
        sigorta_bitis_tarihi = request.form.get('sigorta_bitis_tarihi') or None
        muayene_tarihi = request.form.get('muayene_tarihi') or None
        sonraki_muayene_tarihi = request.form.get('sonraki_muayene_tarihi') or None
        guncel_km = request.form.get('guncel_km')
        durum = request.form.get('durum')
        notlar = request.form.get('notlar')
        
        # Plaka kontrolü (kendi plakas hariç)
        mevcut = conn.execute('SELECT id FROM araclar WHERE plaka = %s AND id != %s', 
                            (plaka, arac_id)).fetchone()
        if mevcut:
            flash('Bu plaka ile kayıtlı başka bir araç mevcut!', 'danger')
            conn.close()
            return redirect(url_for('filo_arac_duzenle', arac_id=arac_id))
        
        # Güncelle
        conn.execute('''
            UPDATE araclar SET
                plaka = %s, marka = %s, model = %s, yil = %s, renk = %s,
                sasi_no = %s, motor_no = %s, yakit_tipi = %s,
                sigorta_sirket = %s, sigorta_police_no = %s, sigorta_bitis_tarihi = %s,
                muayene_tarihi = %s, sonraki_muayene_tarihi = %s,
                guncel_km = %s, durum = %s, notlar = %s,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (plaka, marka, model, yil, renk,
              sasi_no, motor_no, yakit_tipi,
              sigorta_sirket, sigorta_police_no, sigorta_bitis_tarihi,
              muayene_tarihi, sonraki_muayene_tarihi,
              guncel_km, durum, notlar, arac_id))
        
        conn.commit()
        conn.close()
        
        log_islem('GÜNCELLEME', 'araclar', arac_id, f'{plaka} plakalı araç güncellendi', 
                 session.get('username'))
        flash('Araç bilgileri güncellendi!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=arac_id))
    
    conn.close()
    return render_template('filo/arac_duzenle.html', arac=dict(arac))


# =============================================================================
# TESLİM / İADE İŞLEMLERİ
# =============================================================================

@app.route('/filo/teslim-iade', methods=['GET', 'POST'])
@login_required
def filo_teslim_iade():
    """Araç teslim/iade işlemi"""
    conn = get_db()
    
    if request.method == 'POST':
        islem_tipi = request.form['islem_tipi']  # Teslim veya İade
        arac_id = request.form['arac_id']
        calisan_id = request.form['calisan_id']
        islem_tarihi = request.form.get('islem_tarihi', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        kilometre = request.form['kilometre']
        yakit_durumu = request.form.get('yakit_durumu')
        hasar_var = request.form.get('hasar_var') == 'on'
        hasar_aciklama = request.form.get('hasar_aciklama')
        temizlik_durumu = request.form.get('temizlik_durumu')
        ic_durum_aciklama = request.form.get('ic_durum_aciklama')
        dis_durum_aciklama = request.form.get('dis_durum_aciklama')
        eksikler = request.form.get('eksikler')
        notlar = request.form.get('notlar')
        
        # Teslim/İade kaydını oluştur
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO arac_teslim_iade (
                arac_id, calisan_id, islem_tipi, islem_tarihi,
                kilometre, yakit_durumu, hasar_var, hasar_aciklama,
                temizlik_durumu, ic_durum_aciklama, dis_durum_aciklama,
                eksikler, teslim_eden_user_id, notlar
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            ) RETURNING id
        ''', (arac_id, calisan_id, islem_tipi, islem_tarihi,
              kilometre, yakit_durumu, hasar_var, hasar_aciklama,
              temizlik_durumu, ic_durum_aciklama, dis_durum_aciklama,
              eksikler, session['user_id'], notlar))
        
        teslim_iade_id = cursor.fetchone()[0]
        
        # Araç km güncelle
        conn.execute('UPDATE araclar SET guncel_km = %s WHERE id = %s', (kilometre, arac_id))
        
        if islem_tipi == 'Teslim':
            # Zimmet kaydı oluştur
            conn.execute('''
                INSERT INTO arac_zimmet (
                    arac_id, calisan_id, teslim_tarihi, teslim_km, teslim_kayit_id
                ) VALUES (%s, %s, %s, %s, %s)
            ''', (arac_id, calisan_id, islem_tarihi.split()[0], kilometre, teslim_iade_id))
            
            mesaj = 'Araç teslim edildi'
            
        else:  # İade
            # Mevcut zimmet kaydını kapat
            conn.execute('''
                UPDATE arac_zimmet SET
                    iade_tarihi = %s,
                    iade_km = %s,
                    iade_kayit_id = %s,
                    aktif = FALSE,
                    guncelleme_tarihi = CURRENT_TIMESTAMP
                WHERE arac_id = %s AND aktif = TRUE
            ''', (islem_tarihi.split()[0], kilometre, teslim_iade_id, arac_id))
            
            mesaj = 'Araç iade edildi'
        
        conn.commit()
        conn.close()
        
        log_islem(islem_tipi.upper(), 'arac_teslim_iade', teslim_iade_id, mesaj, session.get('username'))
        flash(f'{mesaj}!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=arac_id))
    
    # GET request - Form göster
    # Boşta olan araçlar (teslim için)
    bosta_araclar = conn.execute('''
        SELECT a.id, a.plaka, a.marka, a.model
        FROM araclar a
        LEFT JOIN arac_zimmet z ON a.id = z.arac_id AND z.aktif = TRUE
        WHERE a.aktif = TRUE AND a.durum = 'Aktif' AND z.id IS NULL
        ORDER BY a.plaka
    ''').fetchall()
    
    # Zimmetli araçlar (iade için)
    zimmetli_araclar = conn.execute('''
        SELECT a.id, a.plaka, a.marka, a.model, c.id as calisan_id, c.ad_soyad
        FROM araclar a
        JOIN arac_zimmet z ON a.id = z.arac_id AND z.aktif = TRUE
        JOIN calisanlar c ON z.calisan_id = c.id
        WHERE a.aktif = TRUE
        ORDER BY a.plaka
    ''').fetchall()
    
    # Aktif çalışanlar
    calisanlar = conn.execute('''
        SELECT id, ad_soyad, telefon
        FROM calisanlar
        WHERE aktif = TRUE
        ORDER BY ad_soyad
    ''').fetchall()
    
    conn.close()
    
    return render_template('filo/teslim_iade.html',
                         bosta_araclar=bosta_araclar,
                         zimmetli_araclar=zimmetli_araclar,
                         calisanlar=calisanlar)


# =============================================================================
# BAKIM YÖNETİMİ
# =============================================================================

@app.route('/filo/arac/<int:arac_id>/bakim/ekle', methods=['GET', 'POST'])
@login_required
def filo_bakim_ekle(arac_id):
    """Araç bakım kaydı ekle"""
    conn = get_db()
    arac = conn.execute('SELECT * FROM araclar WHERE id = %s', (arac_id,)).fetchone()
    
    if not arac:
        flash('Araç bulunamadı!', 'danger')
        return redirect(url_for('filo_araclar'))
    
    if request.method == 'POST':
        bakim_tipi = request.form['bakim_tipi']
        bakim_tarihi = request.form['bakim_tarihi']
        bakim_km = request.form.get('bakim_km')
        aciklama = request.form['aciklama']
        yapilan_islemler = request.form.get('yapilan_islemler')
        tutar = request.form.get('tutar')
        servis_adi = request.form.get('servis_adi')
        servis_telefon = request.form.get('servis_telefon')
        sonraki_bakim_km = request.form.get('sonraki_bakim_km')
        sonraki_bakim_tarihi = request.form.get('sonraki_bakim_tarihi') or None
        
        conn.execute('''
            INSERT INTO arac_bakim (
                arac_id, bakim_tipi, bakim_tarihi, bakim_km,
                aciklama, yapilan_islemler, tutar,
                servis_adi, servis_telefon,
                sonraki_bakim_km, sonraki_bakim_tarihi
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (arac_id, bakim_tipi, bakim_tarihi, bakim_km,
              aciklama, yapilan_islemler, tutar,
              servis_adi, servis_telefon,
              sonraki_bakim_km, sonraki_bakim_tarihi))
        
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'arac_bakim', arac_id, f'{bakim_tipi} bakımı eklendi', session.get('username'))
        flash('Bakım kaydı eklendi!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=arac_id))
    
    conn.close()
    return render_template('filo/bakim_ekle.html', arac=dict(arac))


# =============================================================================
# YAKIT YÖNETİMİ
# =============================================================================

@app.route('/filo/arac/<int:arac_id>/yakit/ekle', methods=['GET', 'POST'])
@login_required
def filo_yakit_ekle(arac_id):
    """Yakıt kaydı ekle"""
    conn = get_db()
    arac = conn.execute('SELECT * FROM araclar WHERE id = %s', (arac_id,)).fetchone()
    
    if not arac:
        flash('Araç bulunamadı!', 'danger')
        return redirect(url_for('filo_araclar'))
    
    # Araç zimmetli mi kontrol et
    zimmet = conn.execute('''
        SELECT calisan_id FROM arac_zimmet
        WHERE arac_id = %s AND aktif = TRUE
    ''', (arac_id,)).fetchone()
    
    if request.method == 'POST':
        calisan_id = zimmet['calisan_id'] if zimmet else None
        yakit_tarihi = request.form['yakit_tarihi']
        kilometre = request.form['kilometre']
        litre = request.form['litre']
        birim_fiyat = request.form.get('birim_fiyat')
        toplam_tutar = request.form.get('toplam_tutar')
        yakit_tipi = request.form.get('yakit_tipi')
        fatura_no = request.form.get('fatura_no')
        istasyon = request.form.get('istasyon')
        notlar = request.form.get('notlar')
        
        conn.execute('''
            INSERT INTO arac_yakit (
                arac_id, calisan_id, yakit_tarihi, kilometre,
                litre, birim_fiyat, toplam_tutar, yakit_tipi,
                fatura_no, istasyon, notlar
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (arac_id, calisan_id, yakit_tarihi, kilometre,
              litre, birim_fiyat, toplam_tutar, yakit_tipi,
              fatura_no, istasyon, notlar))
        
        # Araç km güncelle
        conn.execute('UPDATE araclar SET guncel_km = %s WHERE id = %s', (kilometre, arac_id))
        
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'arac_yakit', arac_id, f'Yakıt kaydı eklendi: {litre} lt', session.get('username'))
        flash('Yakıt kaydı eklendi!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=arac_id))
    
    conn.close()
    return render_template('filo/yakit_ekle.html', arac=dict(arac), zimmet=zimmet)


# =============================================================================
# SİGORTA/KAZA YÖNETİMİ
# =============================================================================

@app.route('/filo/arac/<int:arac_id>/sigorta-kaza/ekle', methods=['GET', 'POST'])
@login_required
def filo_sigorta_kaza_ekle(arac_id):
    """Sigorta/kaza kaydı ekle"""
    conn = get_db()
    arac = conn.execute('SELECT * FROM araclar WHERE id = %s', (arac_id,)).fetchone()
    
    if not arac:
        flash('Araç bulunamadı!', 'danger')
        return redirect(url_for('filo_araclar'))
    
    if request.method == 'POST':
        kayit_tipi = request.form['kayit_tipi']
        kayit_tarihi = request.form['kayit_tarihi']
        notlar = request.form.get('notlar')
        
        if kayit_tipi == 'Kaza':
            kaza_aciklama = request.form.get('kaza_aciklama')
            kusur_durumu = request.form.get('kusur_durumu')
            hasar_tutari = request.form.get('hasar_tutari')
            
            conn.execute('''
                INSERT INTO arac_sigorta_kaza (
                    arac_id, kayit_tipi, kayit_tarihi,
                    kaza_aciklama, kusur_durumu, hasar_tutari, notlar
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (arac_id, kayit_tipi, kayit_tarihi,
                  kaza_aciklama, kusur_durumu, hasar_tutari, notlar))
        else:  # Sigorta
            sigorta_sirket = request.form.get('sigorta_sirket')
            police_no = request.form.get('police_no')
            baslangic_tarihi = request.form.get('baslangic_tarihi')
            bitis_tarihi = request.form.get('bitis_tarihi')
            prim_tutari = request.form.get('prim_tutari')
            
            conn.execute('''
                INSERT INTO arac_sigorta_kaza (
                    arac_id, kayit_tipi, kayit_tarihi,
                    sigorta_sirket, police_no, baslangic_tarihi,
                    bitis_tarihi, prim_tutari, notlar
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (arac_id, kayit_tipi, kayit_tarihi,
                  sigorta_sirket, police_no, baslangic_tarihi,
                  bitis_tarihi, prim_tutari, notlar))
            
            # Araç sigorta bilgilerini güncelle
            conn.execute('''
                UPDATE araclar SET
                    sigorta_sirket = %s,
                    sigorta_police_no = %s,
                    sigorta_bitis_tarihi = %s
                WHERE id = %s
            ''', (sigorta_sirket, police_no, bitis_tarihi, arac_id))
        
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'arac_sigorta_kaza', arac_id, f'{kayit_tipi} kaydı eklendi', session.get('username'))
        flash(f'{kayit_tipi} kaydı eklendi!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=arac_id))
    
    conn.close()
    return render_template('filo/sigorta_kaza_ekle.html', arac=dict(arac))


# =============================================================================
# RAPORLAR
# =============================================================================

@app.route('/filo/raporlar')
@login_required
def filo_raporlar():
    """Filo raporları"""
    conn = get_db()
    
    # Genel özet
    ozet = conn.execute('''
        SELECT 
            COUNT(*) as toplam_arac,
            COUNT(CASE WHEN durum = 'Aktif' THEN 1 END) as aktif_arac,
            COUNT(CASE WHEN durum = 'Bakımda' THEN 1 END) as bakimda_arac,
            COUNT(CASE WHEN durum = 'Hasarlı' THEN 1 END) as hasarli_arac
        FROM araclar
        WHERE aktif = TRUE
    ''').fetchone()
    
    # Zimmet durumu
    zimmet_durum = conn.execute('''
        SELECT 
            COUNT(DISTINCT a.id) as toplam_arac,
            COUNT(DISTINCT z.arac_id) as zimmetli_arac,
            COUNT(DISTINCT a.id) - COUNT(DISTINCT z.arac_id) as bosta_arac
        FROM araclar a
        LEFT JOIN arac_zimmet z ON a.id = z.arac_id AND z.aktif = TRUE
        WHERE a.aktif = TRUE AND a.durum = 'Aktif'
    ''').fetchone()
    
    # Yakında dolacak sigortalar (30 gün içinde)
    yakin_sigortalar = conn.execute('''
        SELECT plaka, marka, model, sigorta_bitis_tarihi
        FROM araclar
        WHERE sigorta_bitis_tarihi IS NOT NULL
          AND sigorta_bitis_tarihi <= CURRENT_DATE + INTERVAL '30 days'
          AND sigorta_bitis_tarihi >= CURRENT_DATE
          AND aktif = TRUE
        ORDER BY sigorta_bitis_tarihi
    ''').fetchall()
    
    # Yakında gelecek muayeneler (30 gün içinde)
    yakin_muayeneler = conn.execute('''
        SELECT plaka, marka, model, sonraki_muayene_tarihi
        FROM araclar
        WHERE sonraki_muayene_tarihi IS NOT NULL
          AND sonraki_muayene_tarihi <= CURRENT_DATE + INTERVAL '30 days'
          AND sonraki_muayene_tarihi >= CURRENT_DATE
          AND aktif = TRUE
        ORDER BY sonraki_muayene_tarihi
    ''').fetchall()
    
    # Aylık yakıt tüketimi (son 6 ay)
    aylik_yakit = conn.execute('''
        SELECT 
            TO_CHAR(yakit_tarihi, 'YYYY-MM') as ay,
            SUM(litre) as toplam_litre,
            SUM(toplam_tutar) as toplam_tutar,
            COUNT(*) as islem_sayisi
        FROM arac_yakit
        WHERE yakit_tarihi >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY TO_CHAR(yakit_tarihi, 'YYYY-MM')
        ORDER BY ay DESC
    ''').fetchall()
    
    # Aylık bakım maliyeti (son 6 ay)
    aylik_bakim = conn.execute('''
        SELECT 
            TO_CHAR(bakim_tarihi, 'YYYY-MM') as ay,
            SUM(tutar) as toplam_tutar,
            COUNT(*) as islem_sayisi
        FROM arac_bakim
        WHERE bakim_tarihi >= CURRENT_DATE - INTERVAL '6 months'
          AND tutar IS NOT NULL
        GROUP BY TO_CHAR(bakim_tarihi, 'YYYY-MM')
        ORDER BY ay DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('filo/raporlar.html',
                         ozet=ozet,
                         zimmet_durum=zimmet_durum,
                         yakin_sigortalar=yakin_sigortalar,
                         yakin_muayeneler=yakin_muayeneler,
                         aylik_yakit=aylik_yakit,
                         aylik_bakim=aylik_bakim)

# =============================================================================
# FİLO YÖNETİMİ - KİRALAMA ÖZELLİKLERİ
# =============================================================================
# Bu route'lar mevcut filo_routes.py dosyasına eklenecek

# =============================================================================
# KİRALAMA YÖNETİMİ
# =============================================================================

@app.route('/filo/kiralamalar')
@login_required
def filo_kiralamalar():
    """Kiralık araçlar listesi"""
    conn = get_db()
    
    # Kiralık araçlar ve sözleşme bilgileri
    kiralamalar = conn.execute('''
        SELECT 
            a.id as arac_id,
            a.plaka,
            a.marka,
            a.model,
            k.*,
            CASE 
                WHEN k.sozlesme_bitis < CURRENT_DATE THEN 'Süresi Dolmuş'
                WHEN k.sozlesme_bitis <= CURRENT_DATE + INTERVAL '30 days' THEN 'Yakında Bitiyor'
                ELSE 'Aktif'
            END as sozlesme_durumu,
            (k.sozlesme_bitis - CURRENT_DATE) as kalan_gun
        FROM araclar a
        JOIN arac_kira_bilgileri k ON a.id = k.arac_id
        WHERE a.mulkiyet_tipi = 'Kiralık' AND k.aktif = TRUE
        ORDER BY k.sozlesme_bitis
    ''').fetchall()
    
    # Rol kontrolü - Finans bilgilerini gösterebilir mi?
    user_role = session.get('role', '')
    can_view_finance = user_role in ['admin', 'finans']
    
    conn.close()
    
    return render_template('filo/kiralamalar.html', 
                         kiralamalar=kiralamalar,
                         can_view_finance=can_view_finance)


@app.route('/filo/arac/<int:arac_id>/kiralama/ekle', methods=['GET', 'POST'])
@login_required
def filo_kiralama_ekle(arac_id):
    """Araç kiralama bilgisi ekle"""
    conn = get_db()
    arac = conn.execute('SELECT * FROM araclar WHERE id = %s', (arac_id,)).fetchone()
    
    if not arac:
        flash('Araç bulunamadı!', 'danger')
        return redirect(url_for('filo_araclar'))
    
    if request.method == 'POST':
        # Form verilerini al
        kiralama_sirket = request.form['kiralama_sirket']
        sirket_telefon = request.form.get('sirket_telefon')
        sirket_email = request.form.get('sirket_email')
        yetkili_kisi = request.form.get('yetkili_kisi')
        sozlesme_no = request.form.get('sozlesme_no')
        sozlesme_baslangic = request.form['sozlesme_baslangic']
        sozlesme_bitis = request.form['sozlesme_bitis']
        aylik_kira_bedeli = request.form.get('aylik_kira_bedeli')
        para_birimi = request.form.get('para_birimi', 'TRY')
        odeme_donemi = request.form.get('odeme_donemi')
        odeme_gunu = request.form.get('odeme_gunu')
        km_limiti = request.form.get('km_limiti')
        km_asim_ucreti = request.form.get('km_asim_ucreti')
        sigorta_dahil = request.form.get('sigorta_dahil') == 'on'
        bakim_dahil = request.form.get('bakim_dahil') == 'on'
        notlar = request.form.get('notlar')
        
        # Sözleşme dosyası upload (şimdilik yol sakla)
        sozlesme_dosya_yolu = None
        if 'sozlesme_dosya' in request.files:
            file = request.files['sozlesme_dosya']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                filename = secure_filename(file.filename)
                # Dosyayı uploads/sozlesmeler/ klasörüne kaydet
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sozlesmeler')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, f"{arac_id}_{filename}")
                file.save(file_path)
                sozlesme_dosya_yolu = file_path
        
        # Kiralama kaydı oluştur
        conn.execute('''
            INSERT INTO arac_kira_bilgileri (
                arac_id, kiralama_sirket, sirket_telefon, sirket_email,
                yetkili_kisi, sozlesme_no, sozlesme_baslangic, sozlesme_bitis,
                aylik_kira_bedeli, para_birimi, odeme_donemi, odeme_gunu,
                sozlesme_dosya_yolu, km_limiti, km_asim_ucreti,
                sigorta_dahil, bakim_dahil, notlar
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        ''', (arac_id, kiralama_sirket, sirket_telefon, sirket_email,
              yetkili_kisi, sozlesme_no, sozlesme_baslangic, sozlesme_bitis,
              aylik_kira_bedeli, para_birimi, odeme_donemi, odeme_gunu,
              sozlesme_dosya_yolu, km_limiti, km_asim_ucreti,
              sigorta_dahil, bakim_dahil, notlar))
        
        # Aracın mülkiyet tipini "Kiralık" yap
        conn.execute('UPDATE araclar SET mulkiyet_tipi = %s WHERE id = %s', ('Kiralık', arac_id))
        
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'arac_kira_bilgileri', arac_id, 
                 f'{arac["plaka"]} kiralama bilgisi eklendi', session.get('username'))
        flash('Kiralama bilgisi eklendi!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=arac_id))
    
    conn.close()
    return render_template('filo/kiralama_ekle.html', arac=dict(arac))


@app.route('/filo/kiralama/<int:kiralama_id>/duzenle', methods=['GET', 'POST'])
@login_required
def filo_kiralama_duzenle(kiralama_id):
    """Kiralama bilgisini düzenle"""
    conn = get_db()
    
    kiralama = conn.execute('''
        SELECT k.*, a.plaka, a.marka, a.model
        FROM arac_kira_bilgileri k
        JOIN araclar a ON k.arac_id = a.id
        WHERE k.id = %s
    ''', (kiralama_id,)).fetchone()
    
    if not kiralama:
        flash('Kiralama bilgisi bulunamadı!', 'danger')
        return redirect(url_for('filo_kiralamalar'))
    
    if request.method == 'POST':
        # Form verilerini al (kiralama_ekle ile aynı)
        kiralama_sirket = request.form['kiralama_sirket']
        sirket_telefon = request.form.get('sirket_telefon')
        sirket_email = request.form.get('sirket_email')
        yetkili_kisi = request.form.get('yetkili_kisi')
        sozlesme_no = request.form.get('sozlesme_no')
        sozlesme_baslangic = request.form['sozlesme_baslangic']
        sozlesme_bitis = request.form['sozlesme_bitis']
        aylik_kira_bedeli = request.form.get('aylik_kira_bedeli')
        para_birimi = request.form.get('para_birimi', 'TRY')
        odeme_donemi = request.form.get('odeme_donemi')
        odeme_gunu = request.form.get('odeme_gunu')
        km_limiti = request.form.get('km_limiti')
        km_asim_ucreti = request.form.get('km_asim_ucreti')
        sigorta_dahil = request.form.get('sigorta_dahil') == 'on'
        bakim_dahil = request.form.get('bakim_dahil') == 'on'
        notlar = request.form.get('notlar')
        
        # Dosya upload varsa güncelle
        sozlesme_dosya_yolu = kiralama['sozlesme_dosya_yolu']
        if 'sozlesme_dosya' in request.files:
            file = request.files['sozlesme_dosya']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sozlesmeler')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, f"{kiralama['arac_id']}_{filename}")
                file.save(file_path)
                sozlesme_dosya_yolu = file_path
        
        # Güncelle
        conn.execute('''
            UPDATE arac_kira_bilgileri SET
                kiralama_sirket = %s,
                sirket_telefon = %s,
                sirket_email = %s,
                yetkili_kisi = %s,
                sozlesme_no = %s,
                sozlesme_baslangic = %s,
                sozlesme_bitis = %s,
                aylik_kira_bedeli = %s,
                para_birimi = %s,
                odeme_donemi = %s,
                odeme_gunu = %s,
                sozlesme_dosya_yolu = %s,
                km_limiti = %s,
                km_asim_ucreti = %s,
                sigorta_dahil = %s,
                bakim_dahil = %s,
                notlar = %s,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (kiralama_sirket, sirket_telefon, sirket_email,
              yetkili_kisi, sozlesme_no, sozlesme_baslangic, sozlesme_bitis,
              aylik_kira_bedeli, para_birimi, odeme_donemi, odeme_gunu,
              sozlesme_dosya_yolu, km_limiti, km_asim_ucreti,
              sigorta_dahil, bakim_dahil, notlar, kiralama_id))
        
        conn.commit()
        conn.close()
        
        log_islem('GÜNCELLEME', 'arac_kira_bilgileri', kiralama_id, 
                 'Kiralama bilgisi güncellendi', session.get('username'))
        flash('Kiralama bilgisi güncellendi!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=kiralama['arac_id']))
    
    conn.close()
    return render_template('filo/kiralama_duzenle.html', kiralama=dict(kiralama))


@app.route('/filo/kiralama/<int:kiralama_id>/odeme/ekle', methods=['GET', 'POST'])
@login_required
def filo_kiralama_odeme_ekle(kiralama_id):
    """Kiralama ödeme kaydı ekle"""
    conn = get_db()
    
    kiralama = conn.execute('''
        SELECT k.*, a.plaka, a.marka, a.model
        FROM arac_kira_bilgileri k
        JOIN araclar a ON k.arac_id = a.id
        WHERE k.id = %s
    ''', (kiralama_id,)).fetchone()
    
    if not kiralama:
        flash('Kiralama bilgisi bulunamadı!', 'danger')
        return redirect(url_for('filo_kiralamalar'))
    
    if request.method == 'POST':
        odeme_donemi = request.form['odeme_donemi']
        tutar = request.form['tutar']
        para_birimi = request.form.get('para_birimi', 'TRY')
        km_asim_tutari = request.form.get('km_asim_tutari', 0)
        toplam_tutar = float(tutar) + float(km_asim_tutari or 0)
        odeme_durumu = request.form.get('odeme_durumu', 'Bekliyor')
        planlanan_odeme_tarihi = request.form.get('planlanan_odeme_tarihi')
        gerceklesen_odeme_tarihi = request.form.get('gerceklesen_odeme_tarihi')
        fatura_no = request.form.get('fatura_no')
        notlar = request.form.get('notlar')
        
        conn.execute('''
            INSERT INTO arac_kira_odemeler (
                kira_bilgi_id, arac_id, odeme_donemi, tutar, para_birimi,
                km_asim_tutari, toplam_tutar, odeme_durumu,
                planlanan_odeme_tarihi, gerceklesen_odeme_tarihi,
                fatura_no, notlar
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (kiralama_id, kiralama['arac_id'], odeme_donemi, tutar, para_birimi,
              km_asim_tutari, toplam_tutar, odeme_durumu,
              planlanan_odeme_tarihi, gerceklesen_odeme_tarihi,
              fatura_no, notlar))
        
        conn.commit()
        conn.close()
        
        log_islem('EKLEME', 'arac_kira_odemeler', kiralama_id, 
                 f'{odeme_donemi} dönemi ödeme kaydı', session.get('username'))
        flash('Ödeme kaydı eklendi!', 'success')
        return redirect(url_for('filo_arac_detay', arac_id=kiralama['arac_id']))
    
    conn.close()
    return render_template('filo/odeme_ekle.html', kiralama=dict(kiralama))


@app.route('/filo/kiralama/odemeler')
@login_required
def filo_kiralama_odemeler():
    """Tüm kiralama ödemeleri listesi"""
    # Sadece admin ve finans görebilir
    if session.get('role') not in ['admin', 'finans']:
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('filo_kiralamalar'))
    
    conn = get_db()
    
    # Ödeme listesi
    odemeler = conn.execute('''
        SELECT 
            o.*,
            a.plaka,
            a.marka,
            a.model,
            k.kiralama_sirket
        FROM arac_kira_odemeler o
        JOIN araclar a ON o.arac_id = a.id
        JOIN arac_kira_bilgileri k ON o.kira_bilgi_id = k.id
        ORDER BY o.odeme_donemi DESC, o.planlanan_odeme_tarihi DESC
    ''').fetchall()
    
    # Özet istatistikler
    ozet = conn.execute('''
        SELECT 
            COUNT(*) as toplam_odeme,
            COUNT(CASE WHEN odeme_durumu = 'Bekliyor' THEN 1 END) as bekleyen,
            COUNT(CASE WHEN odeme_durumu = 'Ödendi' THEN 1 END) as odenen,
            COUNT(CASE WHEN odeme_durumu = 'Gecikti' THEN 1 END) as geciken,
            SUM(CASE WHEN odeme_durumu = 'Bekliyor' THEN toplam_tutar ELSE 0 END) as bekleyen_tutar,
            SUM(CASE WHEN odeme_durumu = 'Ödendi' THEN toplam_tutar ELSE 0 END) as odenen_tutar
        FROM arac_kira_odemeler
    ''').fetchone()
    
    conn.close()
    
    return render_template('filo/kiralama_odemeler.html', 
                         odemeler=odemeler,
                         ozet=ozet)


# ARAÇ EKLE/DÜZENLE route'larını güncelle - mulkiyet_tipi ekle
# Bu kısım mevcut arac_ekle ve arac_duzenle fonksiyonlarına eklenecek

# Araç ekle formunda:
# mulkiyet_tipi = request.form.get('mulkiyet_tipi', 'Özmal')
# INSERT sorgusuna ekle

# Araç düzenle formunda:
# mulkiyet_tipi = request.form.get('mulkiyet_tipi')
# UPDATE sorgusuna ekle