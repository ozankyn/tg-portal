FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV TZ=Europe/Istanbul

# Install system dependencies
# - gcc/libpq-dev: psycopg2 build
# - libpango/libcairo/libgdk-pixbuf/libffi/shared-mime-info: WeasyPrint PDF rendering
# - fonts-dejavu: Türkçe karakter desteği
# - ffmpeg: aday tanıtım videolarının otomatik sıkıştırılması
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    pkg-config \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo2-dev \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Saat dilimini Türkiye'ye ayarla (Europe/Istanbul)
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create upload directory and symlink for static serving
RUN mkdir -p uploads && ln -sf /app/uploads /app/app/static/uploads

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "wsgi:app"]
