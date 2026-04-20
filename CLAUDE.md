# Elitmedyaa - Proje Rehberi

## Site Hakkında
Türkçe haber aggregation sitesi. RSS kaynaklarından otomatik haber çekip Supabase'e kaydediyor, statik HTML frontend ile gösteriyor.

- **Canlı site:** https://elitmedyaa.com
- **Cloudflare Pages** üzerinde host ediliyor (GitHub push → otomatik deploy ~1 dk)
- **GitHub repo:** anbeanews-cloud/Anbeannews
- **GitHub hesabı:** anbeanews-cloud

## Teknoloji Stack
- **Frontend:** Tek dosya statik HTML (`index.html`) — tüm CSS ve JS içinde
- **Backend/DB:** Supabase (PostgreSQL)
- **Scraper:** Python (`scraper.py`) — 30 dakikada bir çalışır
- **Hosting:** Cloudflare Pages
- **Admin paneli:** `admin.html`

## Önemli Dosyalar
- `index.html` — Ana site (tüm CSS+JS tek dosyada)
- `admin.html` — Admin paneli (haber ekle/düzenle/sil)
- `scraper.py` — RSS haber çekici
- `.github/workflows/news-scraper.yml` — GitHub Actions workflow (30 dakikada bir)

## Supabase Bilgileri
- **URL:** https://qmgfqkmsjotzxnekgbey.supabase.co
- **Anon Key:** eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFtZ2Zxa21zam90enhuZWtnYmV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNjU5MzYsImV4cCI6MjA5MTc0MTkzNn0.Jjch1oLyhLVLCSRSNV6azA4zNF2-85e265pvPkLpcVw
- **Tablo:** `haberler` (id, baslik, ozet, icerik, kategori, kaynak, kaynak_url, resim_url, okunma, created_at)
- Haberler 7 günden eskiyse scraper otomatik siliyor

## Admin Paneli
- **URL:** https://elitmedyaa.com/admin.html
- **Kullanıcı adı:** admin
- **Şifre:** elitmedyaa2026
- Ana sitede footer sağ alt köşedeki ⚙ ikonu ile de girilir (çok soluk, gizli)
- Şifreyi değiştirmek için: `admin.html` ve `index.html` içindeki `ADMIN_PASS` değişkenlerini güncelle

## Scraper Zamanlama Sistemi
GitHub Actions tek başına güvenilmez (saatler atlayabiliyor). İki katmanlı sistem kuruldu:
1. **GitHub Actions:** `*/30 * * * *` — her 30 dakikada bir (kendi cron'u)
2. **cron-job.org:** Her 30 dakikada bir GitHub API'yi tetikliyor (kesin çözüm)
   - URL: `https://api.github.com/repos/anbeanews-cloud/Anbeannews/actions/workflows/news-scraper.yml/dispatches`
   - Method: POST, Body: `{"ref": "main"}`
   - Hesap: Anbeanews@gmail.com

## RSS Kaynakları (19 adet)
TRT Haber, AA, T24, BBC Türkçe, DW Türkçe, Euronews TR, Sputnik TR, Sözcü, Haberturk, Indigo Dergisi
Kategoriler: Gündem, Ekonomi, Dünya, Spor, Teknoloji, Sağlık, Magazin, Astroloji

## Sosyal Medya
- Twitter/X: https://x.com/elitmedyaa

## Marka / Logo
- Logo: **ELİT*MEDYAA*** — "ELİT" beyaz/koyu, "MEDYAA" mavi italik bold
- HTML: `ELİT<span>MEDYAA</span>`

## Sık Yapılan İşlemler

### Yeni RSS kaynağı eklemek
`scraper.py` içindeki `RSS_KAYNAKLARI` listesine tuple ekle:
```python
("https://kaynak.com/rss", "Kategori", "Kaynak Adı"),
```

### Manuel scraper tetiklemek
```bash
gh workflow run news-scraper.yml
```

### Scraper zamanlamasını değiştirmek
`.github/workflows/news-scraper.yml` içindeki cron ifadesini değiştir.
Şu an: `*/30 * * * *` (30 dakikada bir)

### Deploy
Her `git push` sonrası Cloudflare Pages otomatik deploy eder (~1 dk).
Remote URL: `https://anbeanews-cloud@github.com/anbeanews-cloud/Anbeannews.git`

## Dikkat Edilecekler
- URL'lerde angle bracket (`<` `>`) KULLANMA — JavaScript'i kırıyor (geçmişte büyük sorun yaşandı)
- `index.html` içindeki tüm JS ve CSS tek dosyada, ayrı dosya yok
- Supabase anon key frontend'de açık — bu normal, okuma/yazma için tasarlandı
- Git push için `anbeanews-cloud` GitHub hesabı kullanılmalı (`gh auth login`)
