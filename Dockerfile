# Python 3.11 slim imajını kullan
FROM python:3.11-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem bağımlılıklarını kur
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# pip'i güncelle ve requirements dosyasını kopyala
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    --default-timeout=300 \
    --retries 5 \
    -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Port tanımla (bilgilendirme amaçlı)
EXPOSE 8005

# Uygulama çalıştırma komutu
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
