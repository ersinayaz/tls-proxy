# TLS Proxy Service

Cloudflare bypass özellikli, session yönetimli proxy REST API servisi. `async-tls-client` kütüphanesi ve Chrome 133 TLS profili kullanarak harici API'lere güvenli istek atmanızı sağlar.

## Özellikler

- **Chrome 133 TLS Profili**: En güncel Chrome fingerprint ile Cloudflare bypass
- **Standart Browser Headers**: Otomatik Chrome 133 header'ları ve dinamik Origin/Referer
- **Session Yönetimi**: Cookie persistence ve state yönetimi
- **Proxy Desteği**: HTTP, HTTPS ve SOCKS5 proxy desteği
- **Async Mimari**: FastAPI + async-tls-client ile tam asenkron yapı
- **API Key Authentication**: Güvenli erişim kontrolü
- **REST API**: Basit ve anlaşılır endpoint yapısı
- **Otomatik Dokümantasyon**: Swagger UI ve ReDoc desteği

## Kurulum

### 1. Virtual Environment Oluşturun (Önerilen)

```bash
# Python 3.10+ gereklidir
python3 -m venv venv

# Virtual environment'ı aktif edin
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 2. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 3. Environment Ayarlarını Yapın

`.env.example` dosyasını `.env` olarak kopyalayın ve düzenleyin:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin:

```env
API_KEY=your-secret-api-key-here
SESSION_TTL=3600
MAX_SESSIONS=100
PORT=8000
REQUEST_TIMEOUT=30
```

### 4. Servisi Başlatın

```bash
# Geliştirme modu (auto-reload)
python main.py

# veya uvicorn ile
uvicorn main:app --reload --port 8000

# Production modu
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Hızlı Başlangıç

```bash
# Tek seferde tüm kurulum
cd /path/to/tls-proxy
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# .env dosyasını düzenle
python main.py
```

Servis `http://localhost:8000` adresinde çalışmaya başlayacak.

## Servisi Durdurma ve Yeniden Başlatma

```bash
# Servisi durdurmak için terminal'de CTRL+C

# Tekrar başlatmak için
cd /Users/ersinayaz/tls-proxy  # veya projenizin yolu
source venv/bin/activate        # Virtual environment'ı aktif et
python main.py                  # Servisi başlat
```

## Hızlı Başvuru

### Servis Bilgileri
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### API Key
`.env` dosyasındaki `API_KEY` değerini kullanın. Tüm isteklerde `X-API-Key` header'ı zorunludur.

### Örnek İstek
```bash
curl -X POST http://localhost:8000/proxy/request \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "https://httpbin.org/json"
  }'
```

## Kullanım

### API Dokümantasyonu

Servis başladıktan sonra otomatik dokümantasyon şu adreslerde görüntülenebilir:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoint'ler

#### 1. Health Check

```bash
GET /health
```

Servis sağlık durumunu ve aktif session sayısını kontrol eder.

**Örnek:**

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{
  "status": "healthy",
  "active_sessions": 5,
  "max_sessions": 100
}
```

#### 2. Proxy Request (Ana Endpoint)

```bash
POST /proxy/request
Headers: X-API-Key: your-api-key
```

Target URL'e proxy üzerinden istek atar.

**Request Body:**

```json
{
  "method": "GET",
  "url": "https://api.example.com/data",
  "headers": {
    "User-Agent": "Custom Agent"
  },
  "body": null,
  "session_id": "optional-session-id",
  "proxy": "http://user:pass@proxy.example.com:8080"
}
```

**Proxy Desteği:**
- HTTP Proxy: `http://user:pass@host:port` veya `http://host:port`
- HTTPS Proxy: `https://user:pass@host:port`
- SOCKS5 Proxy: `socks5://user:pass@host:port` veya `socks5://host:port`

**Örnek - Session'sız İstek:**

```bash
curl -X POST http://localhost:8000/proxy/request \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "https://httpbin.org/json"
  }'
```

**Örnek - Session'lı İstek (Cookie Persistence):**

```bash
curl -X POST http://localhost:8000/proxy/request \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "https://example.com/api/login",
    "session_id": "my-session-1"
  }'
```

**Örnek - POST Request:**

```bash
curl -X POST http://localhost:8000/proxy/request \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "url": "https://api.example.com/data",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "key": "value"
    },
    "session_id": "my-session-1"
  }'
```

**Response:**

```json
{
  "status_code": 200,
  "headers": {
    "content-type": "application/json",
    "content-length": "256"
  },
  "body": {
    "data": "response data"
  },
  "session_id": "my-session-1",
  "elapsed_ms": 234.56
}
```

#### 3. Session Oluşturma

```bash
POST /proxy/session/create
Headers: X-API-Key: your-api-key
```

Yeni bir session oluşturur ve unique ID döner.

**Örnek:**

```bash
curl -X POST http://localhost:8000/proxy/session/create \
  -H "X-API-Key: your-api-key"
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session created successfully"
}
```

#### 4. Session Silme

```bash
DELETE /proxy/session/{session_id}
Headers: X-API-Key: your-api-key
```

Mevcut bir session'ı siler.

**Örnek:**

```bash
curl -X DELETE http://localhost:8000/proxy/session/my-session-1 \
  -H "X-API-Key: your-api-key"
```

**Response:**

```json
{
  "session_id": "my-session-1",
  "message": "Session deleted successfully"
}
```

#### 5. Session Cookie'lerini Görüntüleme

```bash
GET /proxy/session/{session_id}/cookies
Headers: X-API-Key: your-api-key
```

Bir session'da saklanan tüm cookie'leri görüntüler.

**Örnek:**

```bash
curl http://localhost:8000/proxy/session/my-session-1/cookies \
  -H "X-API-Key: your-api-key"
```

**Response:**

```json
{
  "session_id": "my-session-1",
  "cookies": {
    "session_token": "abc123",
    "user_id": "12345"
  }
}
```

## Python İstemci Örneği

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Session oluştur
response = requests.post(
    f"{API_URL}/proxy/session/create",
    headers=headers
)
session_id = response.json()["session_id"]
print(f"Session ID: {session_id}")

# İlk istek - Login
response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "POST",
        "url": "https://example.com/api/login",
        "body": {
            "username": "user",
            "password": "pass"
        },
        "session_id": session_id
    }
)
print(f"Login Response: {response.json()}")

# İkinci istek - Aynı session ile (cookies persist eder)
response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "GET",
        "url": "https://example.com/api/protected-data",
        "session_id": session_id
    }
)
print(f"Protected Data: {response.json()}")

# Cookie'leri görüntüle
response = requests.get(
    f"{API_URL}/proxy/session/{session_id}/cookies",
    headers=headers
)
print(f"Cookies: {response.json()}")

# Session'ı sil
response = requests.delete(
    f"{API_URL}/proxy/session/{session_id}",
    headers=headers
)
print(f"Session Deleted: {response.json()}")
```

## Kullanım Senaryoları

### 1. Cloudflare Korumalı API'lere Erişim

```python
# Cloudflare korumalı siteye istek
response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "GET",
        "url": "https://protected-site.com/api/data",
        "session_id": "my-session"
    }
)
```

### 2. Proxy Üzerinden İstek Atma

```python
# HTTP Proxy ile istek
response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "GET",
        "url": "https://api.example.com/data",
        "proxy": "http://username:password@proxy.example.com:8080"
    }
)

# SOCKS5 Proxy ile istek
response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "GET",
        "url": "https://api.example.com/data",
        "proxy": "socks5://127.0.0.1:1080",
        "session_id": "proxy-session"
    }
)
```

### 3. Multi-Step Authentication

```python
# 1. Login
login_response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "POST",
        "url": "https://api.example.com/login",
        "body": {"user": "test", "pass": "123"},
        "session_id": "auth-session"
    }
)

# 2. 2FA Token
token_response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "POST",
        "url": "https://api.example.com/verify-2fa",
        "body": {"token": "123456"},
        "session_id": "auth-session"
    }
)

# 3. Protected endpoint'e erişim
data_response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "GET",
        "url": "https://api.example.com/protected/data",
        "session_id": "auth-session"
    }
)
```

### 4. Web Scraping

```python
# Session oluştur
session_response = requests.post(
    f"{API_URL}/proxy/session/create",
    headers=headers
)
session_id = session_response.json()["session_id"]

# Birden fazla sayfayı scrape et
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

for url in urls:
    response = requests.post(
        f"{API_URL}/proxy/request",
        headers=headers,
        json={
            "method": "GET",
            "url": url,
            "session_id": session_id
        }
    )
    data = response.json()["body"]
    print(f"Scraped {url}: {len(str(data))} bytes")
```

## Redirect Yönetimi

Servis 30x redirect response'larını otomatik olarak takip eder ve redirect history'sini saklar.

### Özellikler

- **Otomatik Redirect Takibi**: 301, 302, 303, 307, 308 status kodları otomatik takip edilir
- **Maksimum 5 Redirect Limiti**: Sonsuz loop koruması
- **Redirect Chain History**: Hangi URL'lerden geçildiği kaydedilir
- **303 Redirect Özel Davranışı**: POST/PUT/PATCH istekleri GET'e dönüştürülür
- **Cookie Persistence**: Redirect'ler arasında cookie'ler korunur
- **Header Güncelleme**: Her redirect'te Origin/Referer otomatik güncellenir

### Response Fields

```json
{
  "status_code": 200,
  "final_url": "https://final-destination.com/page",
  "redirect_count": 2,
  "redirect_chain": [
    "https://original-url.com",
    "https://intermediate-url.com"
  ],
  "body": {...},
  "elapsed_ms": 1234.56
}
```

### Redirect Status Kodları

| Kod | Açıklama | Method Davranışı |
|-----|----------|------------------|
| **301** | Moved Permanently | Method korunur |
| **302** | Found | Method korunur |
| **303** | See Other | GET'e dönüştürülür |
| **307** | Temporary Redirect | Method korunur |
| **308** | Permanent Redirect | Method korunur |

### Kullanım Örnekleri

```bash
# Kısa URL'leri takip etme
curl -X POST http://localhost:8000/proxy/request \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "https://bit.ly/3xyz123"
  }'

# Response:
{
  "status_code": 200,
  "final_url": "https://long-url.com/actual/page",
  "redirect_count": 1,
  "redirect_chain": ["https://bit.ly/3xyz123"],
  "body": {...}
}
```

### Python Örneği

```python
response = requests.post(
    f"{API_URL}/proxy/request",
    headers=headers,
    json={
        "method": "GET",
        "url": "https://short-url.com/abc",
        "session_id": "my-session"
    }
)

data = response.json()
print(f"Final URL: {data['final_url']}")
print(f"Redirects: {data['redirect_count']}")
if data['redirect_chain']:
    print(f"Path: {' -> '.join(data['redirect_chain'])} -> {data['final_url']}")
```

### Güvenlik ve Limitler

- **Max Redirect**: 5 redirect (daha fazlası error döner)
- **URL Validation**: Relative URL'ler absolute'a çevrilir
- **Timeout**: Her redirect REQUEST_TIMEOUT'a tabidir
- **Loop Protection**: Sonsuz redirect loop'larına karşı korumalı

## Konfigürasyon

### Environment Variables

| Variable | Açıklama | Default |
|----------|----------|---------|
| `API_KEY` | API erişim anahtarı | `change-me-in-production` |
| `SESSION_TTL` | Session timeout (saniye) | `3600` |
| `MAX_SESSIONS` | Maksimum aktif session sayısı | `100` |
| `PORT` | Servis portu | `8000` |
| `REQUEST_TIMEOUT` | İstek timeout (saniye) | `30` |

### TLS Client Ayarları

Servis otomatik olarak aşağıdaki ayarları kullanır:

- **Client Profile**: `chrome_133` (en güncel Chrome profili)
- **Random TLS Extension Order**: `True` (fingerprint randomization)
- **HTTP/2 Support**: Otomatik
- **Cookie Management**: Otomatik

### Standart Browser Headers

Her istek otomatik olarak gerçek Chrome 133 browser header'larıyla gönderilir:

```
Accept: application/json, text/plain, */*
Accept-Language: tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7
Accept-Encoding: gzip, deflate, br, zstd
Cache-Control: no-cache
Pragma: no-cache
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36
Sec-Ch-Ua: "Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "macOS"
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-site
Origin: <dinamik - request URL'den otomatik>
Referer: <dinamik - request URL'den otomatik>
```

**Önemli Notlar:**
- `Origin` ve `Referer` header'ları istek URL'inden otomatik olarak belirlenir
- Kullanıcı tarafından gönderilen header'lar default header'ları override eder
- Örneğin, kendi `User-Agent` header'ınızı gönderirseniz default User-Agent yerine sizinki kullanılır

## Güvenlik

- **API Key**: Tüm endpoint'ler `X-API-Key` header ile korunur
- **HTTPS**: Production'da HTTPS kullanın (nginx/reverse proxy ile)
- **Rate Limiting**: Production'da rate limiting ekleyin
- **Firewall**: Sadece güvenilir IP'lere izin verin

## Hata Yönetimi

Servis standart HTTP status kodları kullanır:

- `200`: İstek başarılı
- `400`: Geçersiz istek (max session limiti, geçersiz URL vb.)
- `401`: Unauthorized - Geçersiz API Key
- `404`: Session bulunamadı
- `500`: Sunucu hatası

**Hata Response Örneği:**

```json
{
  "error": "Invalid API Key",
  "detail": "The provided API key is invalid or missing"
}
```

## Performans

- **Async İşlemler**: Tüm network işlemleri async
- **Session Pooling**: Yeniden kullanılabilir TLS bağlantıları
- **Otomatik Cleanup**: Süresi dolan session'lar otomatik temizlenir
- **Memory Efficient**: Session-based cookie storage

## Geliştirme

### Debug Modu

```bash
# Detaylı log ile çalıştır
export LOG_LEVEL=DEBUG
python main.py
```

### Test

```bash
# Health check
curl http://localhost:8000/health

# Test request
curl -X POST http://localhost:8000/proxy/request \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"method": "GET", "url": "https://httpbin.org/json"}'
```

## Sorun Giderme

### "Invalid API Key" Hatası

`.env` dosyasında `API_KEY` değerini kontrol edin ve istek header'ında doğru kullanın.

### "Maximum sessions reached" Hatası

`MAX_SESSIONS` değerini artırın veya kullanılmayan session'ları silin.

### Connection Timeout

`REQUEST_TIMEOUT` değerini artırın veya hedef URL'i kontrol edin.

### TLS Fingerprint Tespit Edildi

Chrome 133 profili güncel tutulmuş olsa da bazı gelişmiş sistemler tespit edebilir. Bu durumda:

- Farklı `client_identifier` deneyin (config.py)
- Request header'larını özelleştirin
- Request timing'i randomize edin

## Lisans

MIT License

## Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır!

## Destek

Sorunlar için GitHub Issues kullanın.
