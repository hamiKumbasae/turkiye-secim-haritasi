"""
Açık veri: sitenin veri.html sayfası ve indirilebilir dosyaları (site/build.py çağırır).

Üretilenler (site/dist/ altına):
  veri/<seçim>.csv                 il + ilçe sonuçları; sitedeki "CSV indir" ile aynı sütunlar
  veri/meclis/<seçim>_<bm|igm>.csv yerel seçim belediye meclisi / il genel meclisi
  veri/mahalle/<seçim>.csv         mahalle (muhtarlık) sonuçları, 15 seçim
  veri/tum-secimler-csv.zip        il/ilçe ve meclis CSV'lerinin hepsi (mahalle hariç, büyük)
  veri/SHA256SUMS.txt              veri/ altındaki her dosyanın özeti
  veri.html                        seçim başına bir indirme satırı, lisans, atıf, sütun sözlüğü

JSON dosyaları zaten yayında (data/elections/<seçim>.json, data/mahalle_votes/<yıl>.json);
sayfa onlara bağlanır. CSV'ler sitedeki tarayıcı doğrulamasının (data-loader.js prepareElection)
aynısından geçer: parti oyları toplamı geçerli oyla tutmayan satırda yüzde boş bırakılır ve
nedeni "not" sütununa yazılır; hiçbir değer düzeltilmez ya da tahmin edilmez.
Çıktı deterministiktir (zip zaman damgası sabit): aynı veriden aynı baytlar.
"""
import csv
import hashlib
import html
import io
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
KAPSAM = ROOT / "docs" / "rapor" / "kapsam_tablosu.csv"
YAYIN = "https://hamikumbasae.github.io/turkiye-secim-haritasi/"

TURLER = [("genel", "Genel seçimler"), ("yerel", "Yerel seçimler"),
          ("referandum", "Referandumlar"), ("cumhurbaskanligi", "Cumhurbaşkanlığı seçimleri")]
OYLAMA_ADI = {"bm": "Belediye meclisi", "igm": "İl genel meclisi"}
KALITE = {"COMPLETE": "tam", "MOSTLY_COMPLETE": "büyük ölçüde tam", "PARTIAL": "kısmi",
          "VERY_PARTIAL": "çok kısmi", "NONE": "yok", "UNKNOWN": "araştırılmadı"}
ZIP_TARIH = (2026, 1, 1, 0, 0, 0)


def _sayi_metni(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _fmt(n):
    return f"{n:,}".replace(",", ".")


def _koltuk_bazli(o):
    return bool(o) and (o.get("oy") in (None, 0)) and o.get("sandalye") is not None


def _dogrula(kayit):
    """data-loader.js prepareElection'ın Python karşılığı: (notlar, yüzde gizli mi, katılım gizli mi)."""
    geom_say = {}
    for r in kayit.get("ilceler") or []:
        if r.get("geomId"):
            geom_say[r["geomId"]] = geom_say.get(r["geomId"], 0) + 1
    sonuc = {}
    for r in (kayit.get("iller") or []) + (kayit.get("ilceler") or []):
        degerler = list((r.get("oy") or {}).values())
        toplam = sum((v.get("oy") or 0) for v in degerler)
        gecerli = r.get("gecerliOy")
        notlar, gizli, katilim_yok = [], False, False
        hepsi_oy = bool(degerler) and all(v.get("oy") is not None for v in degerler)
        if gecerli and hepsi_oy and abs(toplam - gecerli) > max(1, gecerli * 0.0001):
            notlar.append(f"Parti oyları toplamı ({_fmt(toplam)}) ile geçerli oy ({_fmt(gecerli)}) uyuşmuyor. "
                          "Yüzdeler ve değişim karşılaştırması doğrulanana kadar gösterilmiyor.")
            gizli = True
        if (gecerli and hepsi_oy and abs(toplam - gecerli) <= max(1, gecerli * 0.0001) and
                any(v.get("oran") is not None and abs(v["oran"] - v["oy"] / gecerli * 100) > 0.11 for v in degerler)):
            notlar.append("Kaynak yüzdeleri oy sayımlarına uymuyor; yüzdeler doğrulama bekliyor.")
            gizli = True
        if r.get("geomId") and geom_say.get(r["geomId"], 0) > 1:
            notlar.append("Aynı harita bölgesine birden fazla kayıt eşleşiyor; yüzdeler doğrulama bekliyor.")
            gizli = True
        if r.get("ilceGeneliSonuc"):
            notlar.append("Belediye kapsamı doğrulanmadı: " + r["ilceGeneliSonuc"])
        if r.get("secmen") and gecerli and gecerli > r["secmen"]:
            notlar.append("Geçerli oy seçmen sayısını aşıyor; sayımlar kaynak doğrulaması bekliyor. Katılım gösterilmiyor.")
            katilim_yok = True
        sonuc[id(r)] = (notlar, gizli, katilim_yok)
    return sonuc


def _yuzde(o, gizli):
    if not o or gizli or _koltuk_bazli(o):
        return None
    v = o.get("oran")
    return v if isinstance(v, (int, float)) and 0 <= v <= 100 else None


def _csv_baytlari(satirlar):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    for s in satirlar:
        w.writerow([_sayi_metni(v) for v in s])
    return ("﻿" + buf.getvalue()).encode("utf-8")


def secim_csv(anahtar, kayit):
    """Sitedeki table.js csvMetni ile aynı sütunlar ve sıra."""
    dogrulama = _dogrula(kayit)
    il_ad = {p["plaka"]: p["ad"] for p in kayit["iller"]}
    satirlar = [("il", r) for r in kayit["iller"]]
    satirlar += [("ilçe", r) for r in kayit.get("ilceler") or [] if (r.get("oy") and len(r["oy"])) or r.get("not")]
    yd = kayit.get("yurtdisi")
    if yd and yd.get("oy"):
        satirlar.append(("yurt dışı", dict(yd, ad="Yurt dışı")))
    partiler = list(kayit.get("majorPartiler") or [])
    for _, r in satirlar:
        for p in (r.get("oy") or {}):
            if p not in partiler:
                partiler.append(p)
    vekil_var = any(r.get("vekil") for _, r in satirlar)
    sandalye_var = any(_koltuk_bazli(o) for _, r in satirlar for o in (r.get("oy") or {}).values())
    bas = ["seçim", "düzey", "plaka", "il", "ilçe", "seçmen", "sandık", "geçerli oy", "katılım %", "kazanan"]
    if vekil_var:
        bas.append("toplam vekil")
    for p in partiler:
        bas += [p + " oy", p + " %"]
        if vekil_var:
            bas.append(p + " vekil")
        if sandalye_var:
            bas.append(p + " sandalye")
    bas.append("not")
    out = [bas]
    for duzey, r in satirlar:
        notlar, gizli, katilim_yok = dogrulama.get(id(r), ([], False, False))
        il = r["ad"] if duzey == "il" else (il_ad.get(r.get("plaka"), "") if duzey == "ilçe" else "")
        satir = [anahtar, duzey, "" if duzey == "yurt dışı" else r.get("plaka"), il, r["ad"] if duzey == "ilçe" else "",
                 r.get("secmen"), r.get("sandik"), r.get("gecerliOy"), None if katilim_yok else r.get("katilim"), r.get("kazanan")]
        if vekil_var:
            satir.append(r.get("toplamVekil"))
        for p in partiler:
            o = (r.get("oy") or {}).get(p)
            satir += [o.get("oy") if o else None, _yuzde(o, gizli)]
            if vekil_var:
                satir.append((r.get("vekil") or {}).get(p))
            if sandalye_var:
                satir.append(o.get("sandalye") if o else None)
        satir.append(" ".join(x for x in [r.get("not"), r.get("veriNotu"), *notlar] if x))
        out.append(satir)
    return _csv_baytlari(out)


def mahalle_csv(anahtar, kayit, oylar, mahalle_geo):
    ilce = {d["geomId"]: d for d in kayit.get("ilceler") or [] if d.get("geomId")}
    il_ad = {p["plaka"]: p["ad"] for p in kayit["iller"]}
    toplam = {}
    for satirlar in oylar.values():
        for v in satirlar.values():
            for p, o in (v.get("oy") or {}).items():
                toplam[p] = toplam.get(p, 0) + (o.get("oy") or 0)
    partiler = sorted(toplam, key=lambda p: (-toplam[p], p))
    bas = ["seçim", "plaka", "il", "ilçe", "ilçe geomId", "mahalle osm id", "mahalle", "seçmen", "sandık",
           "katılım %", "kazanan"]
    for p in partiler:
        bas += [p + " oy", p + " %"]
    out = [bas]
    for g in sorted(oylar):
        d = ilce.get(g, {})
        adlar = mahalle_geo.get(g, {})
        for osm in sorted(oylar[g]):
            v = oylar[g][osm]
            satir = [anahtar, d.get("plaka"), il_ad.get(d.get("plaka"), ""), d.get("ad", ""), g, osm,
                     (adlar.get(osm) or {}).get("ad", ""), v.get("secmen"), v.get("sandik"), v.get("katilim"), v.get("kazanan")]
            for p in partiler:
                o = (v.get("oy") or {}).get(p)
                satir += [o.get("oy") if o else None, o.get("oran") if o else None]
            out.append(satir)
    return _csv_baytlari(out)


def _boyut(n):
    if n >= 1e6:
        return f"{n / 1e6:.1f} MB".replace(".", ",")
    return f"{max(1, round(n / 1e3))} KB"


def _kapsam():
    with KAPSAM.open(encoding="utf-8") as f:
        return {r["secim"]: r for r in csv.DictReader(f)}


def _secim_adi(anahtar, kayit):
    ad = kayit["ad"]
    if anahtar.endswith("cb1tur"):
        return ad + " · 1. tur"
    if anahtar.endswith("cb2tur"):
        return ad + " · 2. tur"
    return ad


def uret(files, out):
    """files: export_static.public_files(public=True); out: site/dist yolu. {göreli yol: bayt} döndürür."""
    yazilan = {}
    kapsam = _kapsam()
    secimler = {rel.split("/")[-1][:-5]: obj for rel, obj in files.items() if rel.startswith("data/elections/")}
    meclis = {rel.split("/")[-1][:-5]: obj for rel, obj in files.items() if rel.startswith("data/meclis_harita/")}
    mahalle_yillari = {rel.split("/")[-1][:-5] for rel in files if rel.startswith("data/mahalle_votes/")}
    mahalle_geo = None

    satirlar = {t: [] for t, _ in TURLER}
    for anahtar, kayit in secimler.items():
        yazilan[f"veri/{anahtar}.csv"] = secim_csv(anahtar, kayit)
        ekler = []
        for kisa in ("bm", "igm"):
            m = meclis.get(f"{anahtar}_{kisa}")
            if m:
                yazilan[f"veri/meclis/{anahtar}_{kisa}.csv"] = secim_csv(f"{anahtar}_{kisa}", m)
                ekler.append((OYLAMA_ADI[kisa], f"veri/meclis/{anahtar}_{kisa}.csv", f"data/meclis_harita/{anahtar}_{kisa}.json"))
        if anahtar in mahalle_yillari:
            if mahalle_geo is None:
                mahalle_geo = {rel.split("/")[-1][:-5]: obj for rel, obj in files.items() if rel.startswith("geo/mahalle/")}
            yazilan[f"veri/mahalle/{anahtar}.csv"] = mahalle_csv(anahtar, kayit, files[f"data/mahalle_votes/{anahtar}.json"], mahalle_geo)
        satirlar[kayit["tur"]].append((anahtar, kayit, ekler))

    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in sorted(r for r in yazilan if not r.startswith("veri/mahalle/")):
            info = zipfile.ZipInfo(rel[len("veri/"):], ZIP_TARIH)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, yazilan[rel])
        lisans = ("Türkiye Seçim Tarihi Atlası — açık veri\n" + YAYIN + "veri.html\n\n"
                  "Lisans: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/deed.tr)\n"
                  "Kaynaklar: YSK, TÜİK/DİE ve belgelenmiş diğer kaynaklar; ayrıntı: " + YAYIN + "yontem.html\n").encode("utf-8")
        info = zipfile.ZipInfo("OKUBENI.txt", ZIP_TARIH)
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, lisans)
    yazilan["veri/tum-secimler-csv.zip"] = zbuf.getvalue()
    yazilan["veri/SHA256SUMS.txt"] = "".join(
        f"{hashlib.sha256(b).hexdigest()}  {rel[len('veri/'):]}\n" for rel, b in sorted(yazilan.items())).encode("utf-8")

    yazilan["veri.html"] = _sayfa(satirlar, kapsam, yazilan, files).encode("utf-8")
    for rel, b in yazilan.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
    return yazilan


def _sayfa(satirlar, kapsam, yazilan, files):
    e = html.escape

    def bag(rel, etiket, boyut_bayt):
        return f'<a href="{e(rel)}" download>{e(etiket)}</a> <span class="boyut">{_boyut(boyut_bayt)}</span>'

    def json_boyut(rel):
        return len(json.dumps(files[rel], ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    bolumler = []
    toplam_secim = 0
    for tur, baslik in TURLER:
        liste = sorted(satirlar[tur], key=lambda x: x[0][:4] + x[0], reverse=True)
        toplam_secim += len(liste)
        tr = []
        for anahtar, kayit, ekler in liste:
            k = kapsam.get(anahtar, {})
            ilce_sayi = sum(1 for d in kayit.get("ilceler") or [] if d.get("oy"))
            duzey = [f"{len(kayit['iller'])} il"]
            if ilce_sayi:
                duzey.append(f"{ilce_sayi} ilçe")
            if f"veri/mahalle/{anahtar}.csv" in yazilan:
                duzey.append("mahalle")
            kalite = KALITE.get(k.get("kalite"), "")
            kaynak = k.get("kaynak", "")
            indir = [bag(f"veri/{anahtar}.csv", "CSV", len(yazilan[f"veri/{anahtar}.csv"])),
                     bag(f"data/elections/{anahtar}.json", "JSON", json_boyut(f"data/elections/{anahtar}.json"))]
            if f"veri/mahalle/{anahtar}.csv" in yazilan:
                indir.append(bag(f"veri/mahalle/{anahtar}.csv", "Mahalle CSV", len(yazilan[f"veri/mahalle/{anahtar}.csv"])))
                indir.append(bag(f"data/mahalle_votes/{anahtar}.json", "Mahalle JSON", json_boyut(f"data/mahalle_votes/{anahtar}.json")))
            for etiket, csv_rel, json_rel in ekler:
                indir.append(bag(csv_rel, etiket + " CSV", len(yazilan[csv_rel])))
            tr.append(
                f'<tr id="{e(anahtar)}"><th scope="row">{e(_secim_adi(anahtar, kayit))}'
                f'<span class="anahtar">{e(anahtar)}</span></th>'
                f'<td>{e(" · ".join(duzey))}</td>'
                f'<td>{e(kaynak)}{(" · ilçe verisi " + e(kalite)) if kalite and ilce_sayi else ""}</td>'
                f'<td class="indir">{" · ".join(indir)}</td></tr>')
        bolumler.append(
            f'<h2 id="{tur}">{e(baslik)} <span class="sayi">{len(liste)}</span></h2>\n<div class="tablo-wrap"><table class="tablo">'
            '<thead><tr><th scope="col">Seçim</th><th scope="col">Düzey</th><th scope="col">Kaynak</th><th scope="col">İndir</th></tr></thead>'
            f'<tbody>{"".join(tr)}</tbody></table></div>')

    zip_boyut = _boyut(len(yazilan["veri/tum-secimler-csv.zip"]))
    return SAYFA.replace("__TOPLAM__", str(toplam_secim)).replace("__ZIP_BOYUT__", zip_boyut).replace(
        "__BOLUMLER__", "\n".join(bolumler))


SAYFA = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Açık Veri · Türkiye Seçim Tarihi Atlası</title>
<meta name="description" content="1950–2024 Türkiye genel, yerel, referandum ve cumhurbaşkanlığı seçim sonuçları: il, ilçe ve mahalle düzeyinde CSV ve JSON, CC BY-SA 4.0.">
<link rel="canonical" href="https://hamikumbasae.github.io/turkiye-secim-haritasi/veri.html">
<meta name="theme-color" content="#f6f4ef">
<!-- paylasim onizlemesi (WhatsApp, X, Facebook, LinkedIn...): gorsel site/onizleme.png, site/build.py kopyalar -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="Türkiye Seçim Tarihi Atlası">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="Açık veri · Türkiye Seçim Tarihi Atlası">
<meta property="og:description" content="1950–2024 Türkiye genel, yerel, referandum ve cumhurbaşkanlığı seçim sonuçları: il, ilçe ve mahalle düzeyinde CSV ve JSON, CC BY-SA 4.0.">
<meta property="og:url" content="https://hamikumbasae.github.io/turkiye-secim-haritasi/veri.html">
<meta property="og:image" content="https://hamikumbasae.github.io/turkiye-secim-haritasi/onizleme.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Türkiye haritası: 2023 genel seçiminde illere göre birinci parti; yanında Türkiye Seçim Tarihi Atlası yazısı">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Açık veri · Türkiye Seçim Tarihi Atlası">
<meta name="twitter:description" content="1950–2024 Türkiye genel, yerel, referandum ve cumhurbaşkanlığı seçim sonuçları: il, ilçe ve mahalle düzeyinde CSV ve JSON, CC BY-SA 4.0.">
<meta name="twitter:image" content="https://hamikumbasae.github.io/turkiye-secim-haritasi/onizleme.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --surface-0:#f6f4ef; --surface-1:#fcfbf8; --line:#ddd8cb;
    --ink-1:#211f1a; --ink-2:#5a564a; --ink-3:#8a8574; --link:#2b5f8a;
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){
      --surface-0:#161512; --surface-1:#1d1c18; --line:#38352b;
      --ink-1:#f1efe6; --ink-2:#c7c2b2; --ink-3:#8f8a78; --link:#8cbfe8;
      color-scheme: dark;
    }
  }
  *{box-sizing:border-box;}
  body{margin:0; background:var(--surface-0); color:var(--ink-1);
    font-family:'Inter',system-ui,-apple-system,sans-serif; line-height:1.6; -webkit-font-smoothing:antialiased;}
  .wrap{max-width:1040px; margin:0 auto; padding:28px 16px 64px;}
  .back{font-size:14px; color:var(--link); text-decoration:none;}
  .back:hover{text-decoration:underline;}
  h1{font-family:'Newsreader',Georgia,serif; font-weight:600; font-size:clamp(28px,5vw,38px); line-height:1.2; margin:18px 0 6px;}
  .lead{color:var(--ink-2); font-size:17px; margin:0 0 22px; max-width:760px;}
  h2{font-family:'Newsreader',Georgia,serif; font-weight:600; font-size:23px; margin:36px 0 8px; padding-top:14px; border-top:1px solid var(--line);}
  h2 .sayi{font-family:'Inter',sans-serif; font-size:13px; font-weight:600; color:var(--ink-3); margin-left:6px;}
  p, li{font-size:15px;}
  a{color:var(--link);}
  .ust{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; margin:0 0 8px;}
  .kutu{background:var(--surface-1); border:1px solid var(--line); border-radius:10px; padding:14px 16px; font-size:14px;}
  .kutu h3{font-size:14px; margin:0 0 6px;}
  .kutu p{font-size:14px; margin:6px 0;}
  .kutu code{font-size:12.5px;}
  .buyuk-indir{display:inline-block; font-weight:600; padding:7px 12px; border-radius:8px; background:var(--ink-1); color:var(--surface-0); text-decoration:none; margin:4px 8px 4px 0;}
  .tablo-wrap{overflow-x:auto;}
  .tablo{width:100%; border-collapse:collapse; font-size:14px;}
  .tablo th, .tablo td{text-align:left; vertical-align:top; padding:9px 10px; border-bottom:1px solid var(--line);}
  .tablo thead th{font-weight:600; color:var(--ink-2); font-size:12.5px;}
  .tablo tbody th{font-weight:600; white-space:nowrap;}
  .anahtar{display:block; font-weight:400; font-size:12px; color:var(--ink-3); font-family:ui-monospace,Menlo,monospace;}
  .indir a{font-weight:600; white-space:nowrap;}
  .boyut{font-size:12px; color:var(--ink-3); white-space:nowrap;}
  .sozluk td:first-child{font-family:ui-monospace,Menlo,monospace; font-size:13px; white-space:nowrap;}
  footer{margin-top:48px; font-size:13px; color:var(--ink-3);}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="index.html">← Haritaya dön</a>
  <h1>Açık veri</h1>
  <p class="lead">Atlastaki __TOPLAM__ seçimin il ve ilçe sonuçları, 15 seçimin mahalle sonuçları ve yerel seçimlerin
  meclis sonuçları, haritada gördüğünüz verinin aynısı olarak indirilebilir. Her seçim için bir satır var.</p>

  <div class="ust">
    <div class="kutu">
      <h3>Lisans</h3>
      <p>Veri <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.tr" rel="license">CC BY-SA 4.0</a> ile
      açıktır: kaynak gösterilerek ve aynı lisansla paylaşılarak her amaçla kullanılabilir. Mahalle sınırları
      OpenStreetMap'ten türetilmiştir (ODbL, © OpenStreetMap katkıcıları). Kod MIT lisanslıdır.</p>
      <p><b>Atıf:</b> Türkiye Seçim Tarihi Atlası, <a href="https://hamikumbasae.github.io/turkiye-secim-haritasi/">hamikumbasae.github.io/turkiye-secim-haritasi</a> (YSK, TÜİK/DİE ve diğer kaynaklardan derlenmiştir).</p>
    </div>
    <div class="kutu">
      <h3>Toplu indirme</h3>
      <a class="buyuk-indir" href="veri/tum-secimler-csv.zip" download>Tüm seçimler, CSV (zip)</a> <span class="boyut">__ZIP_BOYUT__</span>
      <p>İl, ilçe ve meclis CSV'lerinin hepsi; mahalle dosyaları büyük olduğu için ayrı. Dosya özetleri:
      <a href="veri/SHA256SUMS.txt">SHA256SUMS.txt</a>. Ham kaynaklar, işleme betikleri ve her verinin kökeni
      <a href="https://github.com/hamiKumbasae/turkiye-secim-haritasi">GitHub deposunda</a>.</p>
    </div>
  </div>
  <div class="kutu">
    <h3>Bilmeniz gerekenler</h3>
    <p>Kaynak sütunu verinin birincil kaynağını ve güvenilirlik sınıfını gösterir: A birincil/resmî (YSK, TÜİK/DİE),
    D zayıf (Vikipedi). Kaynakla tutmayan satırlarda hiçbir değer düzeltilmez: yüzde boş bırakılır, nedeni
    <code>not</code> sütunundadır. Eski seçimlerin ilçe sınırları ve kapsam sınırları için
    <a href="yontem.html">Kaynaklar ve yöntem</a> sayfasına bakın.</p>
  </div>

__BOLUMLER__

  <h2 id="sutunlar">Sütunlar</h2>
  <p>CSV'ler UTF-8 (Excel'de Türkçe karakterler bozulmasın diye BOM'lu), virgülle ayrılmıştır; ondalık ayırıcı noktadır.
  Her satır bir il, ilçe ya da (varsa) yurt dışı toplamıdır.</p>
  <div class="tablo-wrap"><table class="tablo sozluk"><tbody>
    <tr><td>seçim</td><td>Seçim anahtarı (ör. <code>2023</code>, <code>2019yerel</code>, <code>2019yerel_bm</code>); JSON dosyasının adıyla aynı.</td></tr>
    <tr><td>düzey</td><td><code>il</code>, <code>ilçe</code> ya da <code>yurt dışı</code>.</td></tr>
    <tr><td>plaka, il, ilçe</td><td>O seçim tarihindeki il ve ilçe; sonradan kurulan ilçeler eski seçimlerde ayrı satır değildir.</td></tr>
    <tr><td>seçmen, sandık, geçerli oy</td><td>Kayıtlı seçmen, sandık sayısı ve geçerli oy; kaynakta yoksa boş.</td></tr>
    <tr><td>katılım %</td><td>Kaynaktaki katılım oranı.</td></tr>
    <tr><td>kazanan</td><td>En çok oy (1950–1957 genel seçimlerinde ilde en çok vekil) alan parti.</td></tr>
    <tr><td>toplam vekil, &lt;parti&gt; vekil</td><td>Yalnız genel seçimlerde: ilin çıkardığı milletvekili.</td></tr>
    <tr><td>&lt;parti&gt; oy, &lt;parti&gt; %</td><td>Partinin oyu ve geçerli oya oranı. Parti adları sitedeki kısaltmalardır.</td></tr>
    <tr><td>&lt;parti&gt; sandalye</td><td>Yalnız 1950 ve 1955 yerel seçimlerinde: belediye meclisi sandalyesi (başkanı meclis seçiyordu).</td></tr>
    <tr><td>not</td><td>Kaynağa ya da doğrulamaya dair not; boş değilse satırı kullanmadan önce okuyun.</td></tr>
    <tr><td>ilçe geomId, mahalle osm id</td><td>Mahalle dosyalarında: haritadaki ilçe kimliği ve OpenStreetMap mahalle kimliği.</td></tr>
  </tbody></table></div>

  <footer>Türkiye Seçim Tarihi Atlası · Veriler YSK, TÜİK, TBMM ve belgelenmiş diğer kaynaklardan derlenmiştir. Resmî YSK yayını değildir.</footer>
</div>
</body>
</html>
"""
