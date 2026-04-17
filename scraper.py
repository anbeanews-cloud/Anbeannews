#!/usr/bin/env python3
"""
Anbeanews Haber Çekme Scripti
==============================
Üç kök sorunu çözer:
  1. ESKİ HABER  → pubDate ile kesin tarih filtresi, duplicate URL kontrolü
  2. GÖRSEL UYUMSUZLUĞU → Her haber sayfasından og:image/twitter:image çeker
  3. GÜNCELLİK  → GitHub Actions ile 15 dakikada bir otomatik çalışır
"""

import json
import re
import sys
import time
import ssl
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False
    print("[UYARI] beautifulsoup4 yüklü değil. pip install beautifulsoup4 lxml")

# ═══════════════════════════════════════════════════════════════════════════
# YAPILANDIRMA  (GitHub Actions'da bunları Secrets olarak saklayın)
# ═══════════════════════════════════════════════════════════════════════════
import os

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://qmgfqkmsjotzxnekgbey.supabase.co"
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFtZ2Zxa21zam90enhuZWtnYmV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNjU5MzYsImV4cCI6MjA5MTc0MTkzNn0.Jjch1oLyhLVLCSRSNV6azA4zNF2-85e265pvPkLpcVw"
)

# Kaç saatlik haber çekilsin (büyük değer = daha fazla eski haber riski)
MAX_YASH_SAAT = 6

# ═══════════════════════════════════════════════════════════════════════════
# RSS KAYNAKLARI
# (url, varsayılan_kategori, kaynak_adı)
# ═══════════════════════════════════════════════════════════════════════════
RSS_KAYNAKLARI = [
    # ── Gündem / Son Dakika ──────────────────────────────────────────────
    ("https://www.trthaber.com/sondakika.rss",           "Gündem",    "TRT Haber"),
    ("https://www.trthaber.com/gundem.rss",              "Gündem",    "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=guncel",  "Gündem",    "AA"),
    ("https://t24.com.tr/rss",                           "Gündem",    "T24"),
    ("https://feeds.bbci.co.uk/turkce/rss.xml",         "Gündem",    "BBC Türkçe"),
    ("https://rss.dw.com/rdf/rss-tur-all",              "Gündem",    "DW Türkçe"),
    ("https://tr.euronews.com/rss?format=mrss",         "Gündem",    "Euronews TR"),
    ("https://tr.sputniknews.com/export/rss2/archive/index.xml", "Gündem", "Sputnik TR"),
    # ── Ekonomi ──────────────────────────────────────────────────────────
    ("https://www.trthaber.com/ekonomi.rss",             "Ekonomi",   "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=ekonomi", "Ekonomi",   "AA"),
    # ── Dünya ────────────────────────────────────────────────────────────
    ("https://www.trthaber.com/dunya.rss",               "Dünya",     "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=dunya",   "Dünya",     "AA"),
    # ── Spor ─────────────────────────────────────────────────────────────
    ("https://www.trthaber.com/spor.rss",                "Spor",      "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=spor",    "Spor",      "AA"),
    # ── Teknoloji ────────────────────────────────────────────────────────
    ("https://www.trthaber.com/bilim-teknoloji.rss",     "Teknoloji", "TRT Haber"),
    # ── Sağlık ───────────────────────────────────────────────────────────
    ("https://www.trthaber.com/yasam.rss",               "Sağlık",    "TRT Haber"),
    # ── Magazin / Kültür ─────────────────────────────────────────────────
    ("https://www.trthaber.com/kultur-sanat.rss",        "Magazin",   "TRT Haber"),
]

# ═══════════════════════════════════════════════════════════════════════════
# KATEGORİ ANAHTAR KELİMELERİ
# Başlıkta bu kelimeler geçerse RSS'teki varsayılan kategorinin önüne geçer
# ═══════════════════════════════════════════════════════════════════════════
KATEGORI_ANAHTAR = {
    "Spor": [
        "maç", "gol", "futbol", "basketbol", "transfer", "şampiyon",
        "liga", "cup", "turnuva", "voleybol", "tenis", "olimpiyat",
        "milli takım", "beşiktaş", "galatasaray", "fenerbahçe", "trabzonspor",
    ],
    "Ekonomi": [
        "dolar", "euro", "borsa", "faiz", "enflasyon", "merkez bankası",
        "bütçe", "vergi", "ihracat", "ithalat", "ekonomi", "piyasa",
        "hisse", "altın", "döviz", "tcmb", "sgk", "emekli",
    ],
    "Teknoloji": [
        "yapay zeka", "yapay zekâ", "ai", "iphone", "android", "microsoft",
        "google", "apple", "yazılım", "uygulama", "teknoloji", "siber",
        "uzay", "nasa", "roket", "samsung", "tesla", "elektrikli",
    ],
    "Sağlık": [
        "sağlık", "hastane", "kanser", "aşı", "pandemi", "corona",
        "covid", "doktor", "ilaç", "tedavi", "obezite", "salgın",
        "diyet", "kalp", "ameliyat",
    ],
    "Dünya": [
        "abd", "rusya", "ukrayna", "çin", "avrupa", "nato", "bm", "trump",
        "putin", "savaş", "suriye", "iran", "irak", "yunanistan",
        "israil", "filistin", "biden", "macron", "erdoğan dış",
    ],
    "Magazin": [
        "oyuncu", "şarkıcı", "film", "dizi", "müzik", "magazin",
        "ünlü", "evlilik", "boşanma", "sinema", "tiyatro", "sanat",
        "moda", "oscar", "grammy",
    ],
    "Astroloji": [
        "astroloji", "burç", "yıldız falı", "ay falı", "kozmik",
        "enerji yüksel", "tarot",
    ],
}


def kategori_tahmin(baslik: str, varsayilan: str) -> str:
    baslik_lower = baslik.lower()
    for kat, kelimeler in KATEGORI_ANAHTAR.items():
        if any(k in baslik_lower for k in kelimeler):
            return kat
    return varsayilan


# ═══════════════════════════════════════════════════════════════════════════
# HTTP YARDIMCILAˆ
# ═══════════════════════════════════════════════════════════════════════════
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

# Birden fazla User-Agent dönüşümlü kullanılır
_UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Feedfetcher-Google; (+http://www.google.com/feedfetcher.html; 1 subscribers)",
    "Mozilla/5.0 (compatible; NewsBot/1.0; +https://anbeanews.com/bot)",
]
_ua_idx = 0


def _next_ua() -> str:
    global _ua_idx
    ua = _UA_LIST[_ua_idx % len(_UA_LIST)]
    _ua_idx += 1
    return ua


def http_get(url: str, timeout: int = 10) -> bytes | None:
    """Basit GET isteği; 2 kez dener, farklı UA kullanır."""
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": _next_ua(),
                    "Accept": "application/rss+xml,application/xml,text/xml,text/html,*/*",
                    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                    "Cache-Control": "no-cache",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                return resp.read()
        except Exception as e:
            if attempt == 0:
                time.sleep(1)
            else:
                print(f"    [!] {url[:55]}... → {e}")
    return None


# ═══════════════════════════════════════════════════════════════════════════
# OG:IMAGE ÇEKME  — Sorun 2'nin kök çözümü
# ═══════════════════════════════════════════════════════════════════════════
def og_image_cek(url: str) -> str:
    """
    Haber sayfasından DOĞRU görseli çeker.
    Öncelik sırası:
      1. og:image          (en güvenilir — editör tarafından atanmış)
      2. twitter:image
      3. <link rel="image_src">
      4. İlk makul büyüklükteki <img> (son çare)
    """
    if not BS4_OK:
        return ""
    data = http_get(url, timeout=8)
    if not data:
        return ""
    try:
        soup = BeautifulSoup(data, "lxml")
        # 1. og:image
        tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        if tag:
            src = tag.get("content", "")
            if src.startswith("http"):
                return src
        # 2. twitter:image
        tag = soup.find("meta", attrs={"name": "twitter:image"}) or \
              soup.find("meta", attrs={"name": "twitter:image:src"})
        if tag:
            src = tag.get("content", "")
            if src.startswith("http"):
                return src
        # 3. link rel=image_src
        tag = soup.find("link", rel="image_src")
        if tag:
            src = tag.get("href", "")
            if src.startswith("http"):
                return src
        # 4. İlk makul <img> (logo/ikon gibi küçükleri atla)
        for img in soup.find_all("img", src=True):
            src = img.get("src", "")
            # Mutlak URL ve tipik resim uzantısı olsun
            if src.startswith("http") and re.search(r"\.(jpe?g|png|webp)(\?|$)", src, re.I):
                # width/height attribute varsa çok küçük olanları atla
                w = img.get("width", "")
                h = img.get("height", "")
                if w and int(re.sub(r"\D", "", w) or 0) < 100:
                    continue
                if h and int(re.sub(r"\D", "", h) or 0) < 100:
                    continue
                return src
    except Exception:
        pass
    return ""


# ═══════════════════════════════════════════════════════════════════════════
# RSS AYRIŞT˙RMA
# ═══════════════════════════════════════════════════════════════════════════
_MEDIA_NS = "http://search.yahoo.com/mrss/"
_ATOM_NS  = "http://www.w3.org/2005/Atom"

ET.register_namespace("media", _MEDIA_NS)
ET.register_namespace("atom",  _ATOM_NS)


def _txt(el, tag: str, ns_map: dict | None = None) -> str:
    found = el.find(tag) if ns_map is None else el.find(tag, ns_map)
    return (found.text or "").strip() if found is not None else ""


def html_temizle(metin: str) -> str:
    """HTML etiketlerini ve gereksiz boşlukları temizler."""
    if not metin:
        return ""
    if BS4_OK:
        metin = BeautifulSoup(metin, "lxml").get_text(separator=" ")
    else:
        metin = re.sub(r"<[^>]+>", " ", metin)
    return re.sub(r"\s+", " ", metin).strip()


def rss_oku(url: str) -> list[dict]:
    """RSS/Atom feed'ini ayrıştırıp madde listesi döndürür."""
    data = http_get(url, timeout=12)
    if not data:
        return []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"    [!] XML hatası: {e}")
        return []

    ns = {"media": _MEDIA_NS, "atom": _ATOM_NS}
    items = root.findall(".//item") or root.findall(f".//{{{_ATOM_NS}}}entry")

    sonuclar = []
    for item in items:
        baslik = _txt(item, "title") or _txt(item, f"{{{_ATOM_NS}}}title")
        link   = _txt(item, "link")  or _txt(item, f"{{{_ATOM_NS}}}id")
        ozet   = _txt(item, "description") or _txt(item, "summary") or \
                 _txt(item, f"{{{_ATOM_NS}}}summary") or _txt(item, f"{{{_ATOM_NS}}}content")
        tarih  = _txt(item, "pubDate") or _txt(item, "published") or \
                 _txt(item, f"{{{_ATOM_NS}}}published") or _txt(item, "updated") or \
                 _txt(item, f"{{{_ATOM_NS}}}updated")

        # Atom: link href attribute
        if not link:
            link_el = item.find(f"{{{_ATOM_NS}}}link")
            if link_el is not None:
                link = link_el.get("href", "")

        # HTML temizle
        ozet = html_temizle(ozet)[:400]

        # Görsel: media:thumbnail > media:content > enclosure
        resim = ""
        for mtag in [f"{{{_MEDIA_NS}}}thumbnail", f"{{{_MEDIA_NS}}}content"]:
            el = item.find(mtag)
            if el is not None:
                resim = el.get("url", "")
                if resim:
                    break
        if not resim:
            enc = item.find("enclosure")
            if enc is not None and "image" in enc.get("type", ""):
                resim = enc.get("url", "")

        if baslik and link:
            sonuclar.append({
                "baslik":    baslik[:250],
                "link":      link,
                "ozet":      ozet,
                "tarih_str": tarih,
                "resim_rss": resim,
            })

    return sonuclar


# ═══════════════════════════════════════════════════════════════════════════
# TARİH AYRIŞTIRMA  — Sorun 1 ve 3'ün kök çözümü
# ═══════════════════════════════════════════════════════════════════════════
def tarih_ayristir(tarih_str: str) -> datetime | None:
    """
    pubDate (RFC 2822) veya ISO 8601 tarihini UTC-aware datetime'a çevirir.
    Timezone hatasını önlemek için her zaman UTC'ye normalize eder.
    """
    if not tarih_str:
        return None

    # RFC 2822 (RSS pubDate standardı): "Mon, 01 Jan 2024 12:00:00 +0300"
    try:
        return parsedate_to_datetime(tarih_str).astimezone(timezone.utc)
    except Exception:
        pass

    # ISO 8601 varyantları
    temiz = tarih_str.strip().replace("Z", "+00:00")
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            dt = datetime.strptime(temiz[:len(fmt) + 6], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue

    return None


# ═══════════════════════════════════════════════════════════════════════════
# SUPABASE İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════════════════
def _sb_headers() -> dict:
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
    }


def supabase_get(endpoint: str, params: dict | None = None):
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_sb_headers())
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [!] Supabase GET hatası: {e}")
        return None


def supabase_insert(kayit: dict) -> bool:
    url  = f"{SUPABASE_URL}/rest/v1/haberler"
    data = json.dumps(kayit).encode("utf-8")
    hdrs = {**_sb_headers(), "Prefer": "return=minimal"}
    req  = urllib.request.Request(url, data=data, method="POST", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
            return r.status in (200, 201)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        # 409 = zaten var (unique constraint) → başarı say
        if e.code == 409:
            return True
        print(f"  [!] Supabase INSERT {e.code}: {body[:120]}")
        return False
    except Exception as e:
        print(f"  [!] Supabase INSERT hatası: {e}")
        return False


def mevcut_url_seti() -> set[str]:
    """
    Duplicate kontrolü için Supabase'deki mevcut kaynak URL'lerini çeker.
    Son 1000 habere bakarak bellek kullanımını sınırlar.
    """
    sonuc = supabase_get(
        "haberler",
        {"select": "kaynak_url", "order": "created_at.desc", "limit": "1000"},
    )
    if not sonuc:
        return set()
    return {h["kaynak_url"] for h in sonuc if h.get("kaynak_url")}


# ═══════════════════════════════════════════════════════════════════════════
# ANA AKIŞ
# ═══════════════════════════════════════════════════════════════════════════
def main():
    baslangic = time.time()
    print("=" * 64)
    print(f"  Anbeanews Scraper  |  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 64)

    sinir = datetime.now(timezone.utc) - timedelta(hours=MAX_YASH_SAAT)
    print(f"\nYaş sınırı: son {MAX_YASH_SAAT} saat  (>= {sinir.strftime('%d.%m %H:%M')} UTC)\n")

    print("Supabase'den mevcut haber URL'leri alınıyor...")
    mevcut = mevcut_url_seti()
    print(f"  → {len(mevcut)} kayıt yüklendi\n")

    eklenen = 0
    atlanan_eski = 0
    atlanan_dup  = 0
    atlanan_hata = 0

    for rss_url, varsayilan_kat, kaynak_adi in RSS_KAYNAKLARI:
        print(f"[{kaynak_adi}] {rss_url[:56]}...")
        maddeler = rss_oku(rss_url)
        if not maddeler:
            print("  → erişilemedi / içerik yok, atlanıyor\n")
            continue
        print(f"  → {len(maddeler)} madde bulundu")

        for madde in maddeler:
            link = madde["link"]
            if not link:
                continue

            # ── 1. DUPLICATE KONTROLÜ ────────────────────────────────────
            if link in mevcut:
                atlanan_dup += 1
                continue

            # ── 2. TARİH KONTROLÜ ────────────────────────────────────────
            pub_dt = tarih_ayristir(madde["tarih_str"])
            if pub_dt is None:
                # pubDate yoksa şüpheli; 30 dakika öncesiyle etiketle ama ekle
                pub_dt = datetime.now(timezone.utc) - timedelta(minutes=30)
            elif pub_dt < sinir:
                atlanan_eski += 1
                continue

            # ── 3. GÖRSEL ÇEKME (og:image öncelikli) ─────────────────────
            resim_url = madde["resim_rss"]
            if not resim_url or not resim_url.startswith("http"):
                # RSS'te görsel yoksa makaleye gidip og:image al
                resim_url = og_image_cek(link)
                time.sleep(0.25)   # kaynak siteyi yormamak için

            # ── 4. KATEGORİ TAHMİNİ ─────────────────────────────────────
            kategori = kategori_tahmin(madde["baslik"], varsayilan_kat)

            # ── 5. SUPABASE'E EKLE ───────────────────────────────────────
            kayit = {
                "baslik":     madde["baslik"],
                "ozet":       madde["ozet"],
                "icerik":     madde["ozet"],  # RSS'te tam içerik yoktur
                "kategori":   kategori,
                "created_at": pub_dt.isoformat(),
                "okunma":     0,
                "kaynak":     kaynak_adi,
                "kaynak_url": link,
                "resim_url":  resim_url,
            }

            if supabase_insert(kayit):
                eklenen += 1
                mevcut.add(link)
                print(f"    ✓ [{kategori:10s}] {madde['baslik'][:52]}")
            else:
                atlanan_hata += 1

        time.sleep(0.4)  # feed'ler arası bekleme
        print()

    sure = round(time.time() - baslangic, 1)
    print("=" * 64)
    print(f"  ✓ Eklenen    : {eklenen}")
    print(f"  ↷ Duplikat   : {atlanan_dup}")
    print(f"  ⏰ Eski (>{MAX_YASH_SAAT}h) : {atlanan_eski}")
    print(f"  ✗ Hata       : {atlanan_hata}")
    print(f"  ⏱ Süre       : {sure}s")
    print("=" * 64)

    # Başarısız çıkış kodu döndür ki GitHub Actions logda görünür
    if eklenen == 0 and atlanan_hata > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
