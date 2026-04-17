#!/usr/bin/env python3

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

SUPABASE_URL = "https://qmgfqkmsjotzxnekgbey.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFtZ2Zxa21zam90enhuZWtnYmV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxNjU5MzYsImV4cCI6MjA5MTc0MTkzNn0.Jjch1oLyhLVLCSRSNV6azA4zNF2-85e265pvPkLpcVw"

MAX_YASH_SAAT = 24

# Kategori isimleri sitedeki nav linkleriyle birebir ayni olmali
RSS_KAYNAKLARI = [
    ("https://www.trthaber.com/sondakika.rss",            "ÇÜNDEM",    "TRT Haber"),
    ("https://www.trthaber.com/gundem.rss",               "ÇÜNDEM",    "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=guncel",   "ÇÜNDEM",    "AA"),
    ("https://t24.com.tr/rss",                            "ÇÜNDEM",    "T24"),
    ("https://feeds.bbci.co.uk/turkce/rss.xml",          "ÇÜNDEM",    "BBC Türkçe"),
    ("https://rss.dw.com/rdf/rss-tur-all",               "ÇÜNDEM",    "DW Türkçe"),
    ("https://tr.euronews.com/rss?format=mrss",          "ÇÜNDEM",    "Euronews TR"),
    ("https://tr.sputniknews.com/export/rss2/archive/index.xml", "ÇÜNDEM", "Sputnik TR"),
    ("https://www.trthaber.com/ekonomi.rss",              "Ekonomi",   "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=ekonomi",  "Ekonomi",   "AA"),
    ("https://www.trthaber.com/dunya.rss",                "Dünya",     "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=dunya",    "Dünya",     "AA"),
    ("https://www.trthaber.com/spor.rss",                 "Spor",      "TRT Haber"),
    ("https://www.aa.com.tr/tr/rss/default?cat=spor",     "Spor",      "AA"),
    ("https://www.trthaber.com/bilim-teknoloji.rss",      "Teknoloji", "TRT Haber"),
]

# Anahtarlar sitedeki kategori filtreleriyle birebir ayni
KATEGORI_ANAHTAR = {
    "Spor": [
        "maç", "gol", "futbol", "basketbol", "transfer", "şampiyon",
        "liga", "kupa", "turnuva", "voleybol", "tenis", "olimpiyat",
        "beşiktaş", "galatasaray", "fenerbahçe", "trabzonspor", "milli takım",
    ],
    "Ekonomi": [
        "dolar", "euro", "borsa", "faiz", "enflasyon", "merkez bankası",
        "bütçe", "vergi", "ihracat", "ithalat", "ekonomi", "piyasa",
        "hisse", "altın", "döviz", "tcmb", "sgk", "emekli",
    ],
    "Teknoloji": [
        "yapay zeka", "yapay zekâ", "iphone", "android", "microsoft",
        "google", "apple", "yazılım", "uygulama", "teknoloji", "siber",
        "uzay", "nasa", "roket", "samsung", "tesla", "elektrikli araç",
    ],
    "Sağlık": [
        "sağlık", "hastane", "kanser", "aşı", "pandemi", "corona",
        "covid", "doktor", "ilaç", "tedavi", "obezite", "salgın",
        "diyet", "kalp", "ameliyat",
    ],
    "Dünya": [
        "abd", "rusya", "ukrayna", "çin", "avrupa", "nato", "bm",
        "trump", "putin", "savaş", "suriye", "iran", "irak",
        "yunanistan", "israil", "filistin", "biden", "macron",
    ],
    "Magazin": [
        "oyuncu", "şarkıcı", "film", "dizi", "müzik", "magazin",
        "ünlü", "evlilik", "boşanma", "sinema", "tiyatro", "sanat",
        "moda", "oscar", "grammy",
    ],
    "Astroloji": [
        "astroloji", "burç", "yıldız falı", "ay falı", "kozmik", "tarot",
    ],
}

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Feedfetcher-Google; (+http://www.google.com/feedfetcher.html; 1 subscribers)",
]
_ua_idx = 0


def _next_ua():
    global _ua_idx
    ua = _UA_LIST[_ua_idx % len(_UA_LIST)]
    _ua_idx += 1
    return ua


def _hdrs(extra=None):
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def http_get(url, timeout=10):
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": _next_ua(),
                "Accept": "application/rss+xml,application/xml,text/xml,text/html,*/*",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            })
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                return resp.read()
        except Exception as e:
            if attempt == 0:
                time.sleep(1)
            else:
                print("    [!] " + url[:55] + " -> " + str(e))
    return None


def og_image_cek(url):
    if not BS4_OK:
        return ""
    data = http_get(url, timeout=8)
    if not data:
        return ""
    try:
        soup = BeautifulSoup(data, "lxml")
        tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        if tag:
            src = tag.get("content", "")
            if src.startswith("http"):
                return src
        for name in ["twitter:image", "twitter:image:src"]:
            tag = soup.find("meta", attrs={"name": name})
            if tag:
                src = tag.get("content", "")
                if src.startswith("http"):
                    return src
    except Exception:
        pass
    return ""


_MEDIA_NS = "http://search.yahoo.com/mrss/"
_ATOM_NS  = "http://www.w3.org/2005/Atom"


def _txt(el, tag):
    found = el.find(tag)
    return (found.text or "").strip() if found is not None else ""


def html_temizle(metin):
    if not metin:
        return ""
    if BS4_OK:
        metin = BeautifulSoup(metin, "lxml").get_text(separator=" ")
    else:
        metin = re.sub(r"<[^>]+>", " ", metin)
    return re.sub(r"\s+", " ", metin).strip()


def kategori_tahmin(baslik, varsayilan):
    bl = baslik.lower()
    for kat, kelimeler in KATEGORI_ANAHTAR.items():
        if any(k in bl for k in kelimeler):
            return kat
    return varsayilan


def rss_oku(url):
    data = http_get(url, timeout=12)
    if not data:
        return []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []

    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{" + _ATOM_NS + "}entry")

    sonuclar = []
    for item in items:
        baslik = _txt(item, "title") or _txt(item, "{" + _ATOM_NS + "}title")
        link   = _txt(item, "link")  or _txt(item, "{" + _ATOM_NS + "}id")
        ozet   = (_txt(item, "description") or _txt(item, "summary") or
                  _txt(item, "{" + _ATOM_NS + "}summary") or _txt(item, "{" + _ATOM_NS + "}content"))
        tarih  = (_txt(item, "pubDate") or _txt(item, "published") or
                  _txt(item, "{" + _ATOM_NS + "}published") or _txt(item, "updated"))

        if not link:
            link_el = item.find("{" + _ATOM_NS + "}link")
            if link_el is not None:
                link = link_el.get("href", "")

        ozet = html_temizle(ozet)[:400]

        resim = ""
        for mtag in ["{" + _MEDIA_NS + "}thumbnail", "{" + _MEDIA_NS + "}content"]:
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


def tarih_ayristir(tarih_str):
    if not tarih_str:
        return None
    try:
        return parsedate_to_datetime(tarih_str).astimezone(timezone.utc)
    except Exception:
        pass
    return None


def sb_req(method, path, data=None, params=None, extra_hdrs=None):
    url = SUPABASE_URL + "/rest/v1/" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method, headers=_hdrs(extra_hdrs))
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="ignore")
        return e.code, body_err
    except Exception as e:
        return 0, str(e)


def null_kayitlari_sil():
    status, data = sb_req("GET", "haberler", params={"select": "id", "baslik": "is.null"})
    if status != 200 or not data:
        return 0
    print("  " + str(len(data)) + " null kayit siliniyor...")
    sb_req("DELETE", "haberler", params={"baslik": "is.null"}, extra_hdrs={"Prefer": "return=minimal"})
    return len(data)


def sb_insert(kayit):
    status, resp = sb_req("POST", "haberler", data=kayit, extra_hdrs={"Prefer": "return=minimal"})
    if status in (200, 201, 204):
        return True
    if status == 409:
        return True
    print("  [!] INSERT " + str(status) + ": " + str(resp)[:200])
    return False


def mevcut_url_seti():
    status, data = sb_req("GET", "haberler", params={"select": "kaynak_url", "order": "created_at.desc", "limit": "1000"})
    if status != 200 or not data:
        return set()
    return {h["kaynak_url"] for h in data if h.get("kaynak_url")}


def main():
    t0 = time.time()
    print("=" * 60)
    print("  Anbeanews Scraper | " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    print("=" * 60)

    print("\nSupabase baglanti testi...")
    status, data = sb_req("GET", "haberler", params={"select": "*", "limit": "1"})
    print("  HTTP " + str(status))
    if status == 200 and data:
        print("  Sutunlar: " + str(list(data[0].keys())))
    elif status != 200:
        print("  HATA: " + str(data)[:200])
        sys.exit(1)

    print("\nBozuk kayitlar temizleniyor...")
    silinen = null_kayitlari_sil()
    print("  " + str(silinen) + " kayit silindi")

    print("\nMevcut URL'ler aliniyor...")
    mevcut = mevcut_url_seti()
    print("  -> " + str(len(mevcut)) + " kayit\n")

    sinir = datetime.now(timezone.utc) - timedelta(hours=MAX_YASH_SAAT)
    eklenen = atlanan_eski = atlanan_dup = atlanan_hata = 0

    for rss_url, varsayilan_kat, kaynak_adi in RSS_KAYNAKLARI:
        print("[" + kaynak_adi + "] " + rss_url[:55] + "...")
        maddeler = rss_oku(rss_url)
        if not maddeler:
            print("  -> erisilemedii / icerik yok\n")
            continue
        print("  -> " + str(len(maddeler)) + " madde")

        for madde in maddeler:
            link = madde["link"]
            if not link:
                continue
            if link in mevcut:
                atlanan_dup += 1
                continue

            pub_dt = tarih_ayristir(madde["tarih_str"])
            if pub_dt is not None and pub_dt < sinir:
                atlanan_eski += 1
                continue

            resim_url = madde["resim_rss"]
            if not resim_url or not resim_url.startswith("http"):
                resim_url = og_image_cek(link)
                time.sleep(0.2)

            kategori = kategori_tahmin(madde["baslik"], varsayilan_kat)

            kayit = {
                "baslik":     madde["baslik"],
                "ozet":       madde["ozet"],
                "kategori":   kategori,
                "okunma":     0,
                "kaynak":     kaynak_adi,
                "kaynak_url": link,
                "resim_url":  resim_url,
            }

            if sb_insert(kayit):
                eklenen += 1
                mevcut.add(link)
                print("    + [" + kategori + "] " + madde["baslik"][:55])
            else:
                atlanan_hata += 1

        time.sleep(0.3)
        print()

    sure = round(time.time() - t0, 1)
    print("=" * 60)
    print("  + Eklenen  : " + str(eklenen))
    print("  ~ Duplikat : " + str(atlanan_dup))
    print("  Eski       : " + str(atlanan_eski))
    print("  x Hata     : " + str(atlanan_hata))
    print("  Sure       : " + str(sure) + "s")
    print("=" * 60)

    if eklenen == 0 and atlanan_hata > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
