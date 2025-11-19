from app import app
from database import init_db, seed_sample_data
import os

if __name__ == '__main__':
    # Veritabanını başlat (tablolar yoksa oluştur)
    try:
        init_db()
        # İlk çalıştırmada örnek verileri ekle
        if os.environ.get('SEED_DATA', 'false').lower() == 'true':
            seed_sample_data()
    except Exception as e:
        print(f"Veritabanı başlatma hatası: {e}")
    
    # Uygulamayı başlat
    app.run(debug=True, host='0.0.0.0', port=5000)
