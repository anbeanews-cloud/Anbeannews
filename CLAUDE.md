# Elitmedyaa - Proje Rehberi

## Site Hakkında
Türkçe haber aggregation sitesi. RSS kaynaklarından otomatik haber çekip Supabase'e kaydediyor, statik HTML frontend ile gösteriyor.

- **Canlı site:** https://elitmedyaa.com
- **Cloudflare Pages** üzerinde host ediliyor
- **GitHub repo:** anbeanews-cloud/Anbeannews
- **GitHub hesabı:** anbeanews-cloud

## Teknoloji Stack
- **Frontend:** Tek dosya statik HTML (`index.html`)
- **Backend/DB:** Supabase (PostgreSQL)
- **Scraper:** Python (`scraper.py`) — GitHub Actions ile saatte 1 çalışır
- **Hosting:** Cloudflare Pages
- **Admin paneli:** `admin.html`

## Önemli Dosyalar
- `index.html` — Ana site (tüm CSS+JS tek dosyada)
- `admin.html` — Admin paneli (haber ekle/düzenle/sil)
- `scraper.py` — RSS haber çekici
- `.github/workflows/news-scraper.yml` — Saatte 1 otomatik scraper

## Supabase Bilgileri
- **URL:** https://qmgfqkmsjotzxnekgbey.supabase.co
- **Anon Key:** eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFtZ2Zxa21zam90enhuZWtnYmV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNjU5MzYsImV4cCI6MjA5MTc0MTkzNn0.Jjch1oLyhLVLCSRSNV6azA4zNF2-85e265pvPkLpcVw
- **Tablo:** `haberler` (id, baslik, ozet, icerik, kategori, kaynak, kaynak_url, resim_url, okunma, created_at)

## Admin Paneli
- **URL:** https://elitmedyaa.com/admin.html
- **Kullanıcı adı:** admin
- **Şifre:** anbeanews2026
- Ana sitede footer sağ alt köşedeki ⚙ ikonu ile de girilir (gizli)

## RSS Kaynakları (19 adet)
TRT Haber, AA, T24, BBC Türkçe, DW Türkçe, Euronews TR, Sputnik TR, Sözcü, Haberturk, Indigo Dergisi
Kategoriler: Gündem, Ekonomi, Dünya, Spor, Teknoloji, Sağlık, Magazin, Astroloji

## Sosyal Medya
- Twitter/X: https://x.com/elitmedyaa

## Sık Yapılan İşlemler

### Yeni RSS kaynağı eklemek
`scraper.py` içindeki `RSS_KAYNAKLARI` listesine tuple ekle:
```python
("https://kaynak.com/rss", "Kategori", "Kaynak Adı"),
```

### Scraper zamanlamasını değiştirmek
`.github/workflows/news-scraper.yml` içindeki cron ifadesini değiştir.
Şu an: `0 * * * *` (saatte bir)

### Admin şifresini değiştirmek
`admin.html` içindeki `ADMIN_PASS` ve `index.html` içindeki `ADMIN_PASS` değişkenlerini güncelle.

### Deploy
Her `git push` sonrası Cloudflare Pages otomatik deploy eder (~1 dk).

## Dikkat Edilecekler
- URL'lerde angle bracket (`<` `>`) kullanma — JavaScript'i kırıyor
- `index.html` içindeki tüm JS ve CSS tek dosyada, ayrı dosya yok
- Supabase anon key frontend'de açık — bu normal, okuma/yazma için tasarlandı
- Haberler 7 günden eskiyse scraper otomatik siliyor
