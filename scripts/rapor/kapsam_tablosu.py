"""
Kapsam tablosu: her secim (ve yerel secimde her oylama turu) icin il/ilce verisinin ne kadar
tam oldugunu, en iyi kaynagi ve yeni arastirma gerekip gerekmedigini tek tabloda verir.
YAPILACAKLAR.md 9. (ana tablo), 10. (arastirma onceligi), 2. (referandum alanlari) ve
3. (yerel secim A/B/C/D) maddelerinin ciktisi. Yalniz depodaki veriden uretilir, web'e cikmaz.

Ciktilar (docs/rapor/):
  KAPSAM_TABLOSU.md      okunabilir tablolar
  kapsam_tablosu.csv     ana tablo (makine-okunur)
  kapsam_il_bazinda.csv  tam olmayan secimlerde il il ilce kapsami

Sayim yontemi:
  birim      kaynaktaki ilce/belediye satiri. Secimden SONRA kurulan ilcelerin bos "iskelet"
             satirlari (district_lineage.json kurulus tarihi > secim tarihi) sayilmaz.
  sonuclu    en az bir partide/secenekte 0'dan buyuk oy olan satir.
  yalniz kazanan  oy yok, yalniz kazanan parti bilinen satir (1950/1955 yerel).
  eksik      birim - sonuclu (yalniz kazanan satirlar da eksik sayilir).
  donemdeki ilce  election_admin_snapshots.json (Icisleri kurulus tarihleri + secim kaniti);
             yerel secimde birim belediye oldugu icin satir sayisi bundan farkli olabilir.

Veri kalitesi (YAPILACAKLAR.md 9. madde):
  COMPLETE >= %99,5 · MOSTLY_COMPLETE >= %90 · PARTIAL >= %50 · VERY_PARTIAL > 0
  NONE: arastirildi, kaynak yok (ARASTIRMA_KAYDI.md) · UNKNOWN: henuz arastirilmadi

Kullanim:
  python3 scripts/rapor/kapsam_tablosu.py
"""
import collections
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "rapor"
EL = ROOT / "data" / "normalized" / "elections"
MECLIS = ROOT / "data" / "normalized" / "meclis_harita"
IDARI = ROOT / "geo" / "historical" / "idari"

TUR_ADI = {"genel": "Genel seçim", "referandum": "Referandum", "yerel": "Yerel seçim",
           "cumhurbaskanligi": "Cumhurbaşkanlığı"}
OYLAMA_ADI = {"baskan": "Belediye başkanlığı", "bm": "Belediye meclisi", "igm": "İl genel meclisi",
              "-": "-"}

# Arastirmasi kapanmis, ilce kaynagi olmadigi bilinen secimler (ARASTIRMA_KAYDI.md)
ILCE_KAYNAGI_YOK = {"1950", "1954", "1957"}

# Projede hic kaydi olmayan yerel meclis secimleri (1984 oncesi). Belediye meclisi ve il genel
# meclisi bu yillarda da secildi; sonuc kaynagi henuz aranmadi.
KAYITSIZ_MECLIS = ["1950yerel", "1955yerel", "1963yerel", "1968yerel", "1973yerel", "1977yerel"]

KAYNAK_ADI = {
    "ysk": ("YSK", "A"), "tuik": ("TÜİK/DİE", "A"), "wikipedia": ("Türkçe Wikipedia", "D"),
    "mertnuhoglu": ("mertnuhoglu tabanı, TÜİK ile karşılaştırılmış", "A"),
}


def oku(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def oylu(r):
    oy = r.get("oy") or {}
    return any(isinstance(v, dict) and (v.get("oy") or 0) > 0 for v in oy.values())


def yalniz_kazanan(r):
    return not oylu(r) and bool(r.get("sadeceKazanan") or r.get("kazanan"))


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def kalite(oran, kazanan_payi):
    if oran is None:
        return "UNKNOWN"
    if kazanan_payi and kazanan_payi > 50:
        return "VERY_PARTIAL"
    if oran >= 99.5:
        return "COMPLETE"
    if oran >= 90:
        return "MOSTLY_COMPLETE"
    if oran >= 50:
        return "PARTIAL"
    if oran > 0:
        return "VERY_PARTIAL"
    return "NONE"


def kurulus_tarihleri():
    out = {}
    for d in oku(IDARI / "district_lineage.json")["districts"]:
        t = (d.get("kurulus") or {}).get("tarih")
        if t:
            out[d["geomId"]] = t
    return out


def kaynak_ozeti(key, sonuclu_satirlar, src, ust_kaynak):
    """Sonuclu ilce satirlarinin kaynak dagilimi; satirda kaynak yoksa sources.yml."""
    c = collections.Counter()
    teyit = 0
    for r in sonuclu_satirlar:
        k = r.get("kaynak") if isinstance(r.get("kaynak"), dict) else {}
        ana = k.get("ana")
        if ana in (None, "il satırı"):
            continue
        c[ana] += 1
        if ana == "wikipedia" and "tuik" in k:
            teyit += 1
    if ust_kaynak:
        ad, guv = KAYNAK_ADI.get(ust_kaynak, (ust_kaynak, "?"))
        return f"{ad} ({guv})", guv
    if c:
        top = sum(c.values())
        parcalar = []
        guvler = []
        for ana, n in c.most_common():
            if n / top < 0.01:
                continue
            ad, guv = KAYNAK_ADI.get(ana, (ana, "?"))
            if ana == "wikipedia" and teyit:
                ad, guv = "Wikipedia satırları, sayılar DİE kitabıyla teyitli", "A"
                if teyit < n:
                    ad += f" ({teyit}/{n})"
            parcalar.append(f"{ad} %{round(100 * n / top)}" if n < top * 0.99 else ad)
            guvler.append(guv)
        guv = "A" if all(g == "A" for g in guvler) else ("A/D" if "A" in guvler else guvler[0])
        return f"{'; '.join(parcalar)} ({guv})", guv
    e = (src or {}).get(key.split("_")[0]) or {}
    ilce = e.get("ilce_source") or e.get("ilce_base") or {}
    prim = e.get("primary") or {}
    ad = ilce.get("authority") or ilce.get("source") or prim.get("authority") or "?"
    guv = "D" if "Wikipedia" in ad else "A"
    if "Wikipedia" in ad:
        ad = "Türkçe Wikipedia"
    return f"{ad} ({guv})", guv


def secimler():
    for tur in ("genel", "referandum", "yerel", "cumhurbaskanligi"):
        for p in sorted((EL / tur).glob("*.json")):
            yield p.stem, tur, "baskan" if tur == "yerel" else "-", p
    for p in sorted(MECLIS.glob("*.json")):
        k, oyl = p.stem.split("_")
        yield p.stem, "yerel", oyl, p


def yil(key):
    return int(key[:4])


def main():
    import yaml  # requirements.txt

    src = yaml.safe_load((ROOT / "sources.yml").read_text(encoding="utf-8"))["elections"]
    snaps = oku(IDARI / "election_admin_snapshots.json")["elections"]
    kurulus = kurulus_tarihleri()

    satirlar, il_satirlari, ref_alanlari = [], [], []
    for key, tur, oyl, path in secimler():
        d = oku(path)
        snap = snaps.get(key.split("_")[0], {})
        tarih = snap.get("tarih") or ""
        ilceler = d.get("ilceler") or []
        iller = d.get("iller") or []

        def iskelet(r):
            t = kurulus.get(r.get("geomId") or "")
            return not oylu(r) and not r.get("not") and not yalniz_kazanan(r) and t and t > tarih

        birimler = [r for r in ilceler if not iskelet(r)]
        sonuclu = [r for r in birimler if oylu(r)]
        kazanan = [r for r in birimler if yalniz_kazanan(r)]
        n_birim, n_son = len(birimler), len(sonuclu)

        # il duzeyi: buyuksehirlerde il genel meclisi secimi yok (6360) -> paydadan cikar
        il_payda = [r for r in iller if "6360" not in (r.get("not") or "")]
        il_son = sum(1 for r in il_payda if oylu(r))
        il_kaz = sum(1 for r in il_payda if yalniz_kazanan(r))

        notlar = []
        if not ilceler:
            oran = 0.0
            kal = "NONE" if key in ILCE_KAYNAGI_YOK else "UNKNOWN"
            ilce_durum = "Yok"
        else:
            oran = pct(n_son, n_birim)
            kal = kalite(oran, pct(len(kazanan), n_birim))
            ilce_durum = {"COMPLETE": "Tam", "MOSTLY_COMPLETE": "Neredeyse tam", "PARTIAL": "Kısmi",
                          "VERY_PARTIAL": "Çok kısmi", "NONE": "Yok"}.get(kal, "?")
        if kazanan:
            notlar.append(f"{len(kazanan)} satırda yalnız kazanan parti (oy yok)")
        vekalet = sum(1 for r in sonuclu if r.get("buyuksehirSonucu") or r.get("ilceGeneliSonuc"))
        if vekalet:
            notlar.append(f"{vekalet} satırda ilçe belediyesi yerine büyükşehir/ilçe geneli toplamı")
        if sonuclu:
            alan_eksik = [ad for ad, f in (("seçmen", "secmen"), ("katılım", "katilim"),
                                           ("geçerli oy", "gecerliOy"))
                          if sum(1 for r in sonuclu if r.get(f)) < 0.95 * len(sonuclu)]
            if alan_eksik:
                notlar.append("bazı satırlarda " + ", ".join(alan_eksik) + " yok")
        if len(il_payda) < len(iller):
            notlar.append(f"yalnız büyükşehir olmayan {len(il_payda)} ilde seçilir (6360 sayılı Kanun)")
        if il_kaz:
            notlar.append(f"{il_kaz} ilde yalnız kazanan / sandalye dağılımı")

        ust = d.get("kaynak", {}).get("ana") if isinstance(d.get("kaynak"), dict) else None
        kaynak, guv = kaynak_ozeti(key, sonuclu, src, ust)

        if kal in ("NONE",):
            arastir = "Hayır (kaynak araması kapandı)"
        elif kal == "UNKNOWN":
            arastir = "Evet (araştırılmadı)"
        elif kal == "COMPLETE" and guv.startswith("A") and guv != "A/D":
            arastir = "Hayır"
        elif kal == "COMPLETE":
            arastir = "Doğrulama (D kaynaklı satırlar A kaynağıyla)"
        else:
            arastir = "Evet"

        satirlar.append({
            "secim": key, "tur": TUR_ADI[tur], "yil": yil(key), "oylama": OYLAMA_ADI[oyl],
            "il_verisi": f"{il_son}/{len(il_payda)}" + (f" (+{il_kaz} yalnız kazanan)" if il_kaz else ""),
            "ilce_verisi": ilce_durum,
            "donemdeki_ilce": None if len(il_payda) < len(iller) else snap.get("ilceSayisi"),
            "birim": n_birim if ilceler else None,
            "sonuclu": n_son, "eksik": (n_birim - n_son) if ilceler else snap.get("ilceSayisi"),
            "eksik_yuzde": (round(100 - oran, 1) if oran is not None else None) if ilceler else 100.0,
            "kalite": kal, "kaynak": kaynak, "guvenilirlik": guv,
            "arastirma": arastir, "not": "; ".join(notlar),
        })

        # il il kirilim (tam olmayan secimler)
        if ilceler and kal != "COMPLETE":
            by = collections.defaultdict(lambda: [0, 0, None])
            ad_by = {r.get("plaka"): r.get("ad") for r in iller}
            for r in birimler:
                b = by[r.get("plaka")]
                b[0] += 1
                b[1] += oylu(r)
            for pl, (n, s, _) in sorted(by.items(), key=lambda x: (x[0] is None, x[0] or 0)):
                il_satirlari.append({"secim": key, "oylama": OYLAMA_ADI[oyl], "plaka": pl,
                                     "il": ad_by.get(pl, ""), "birim": n, "sonuclu": s,
                                     "eksik": n - s, "durum": "tam" if s == n else
                                     ("hiç yok" if s == 0 else "kısmi")})

        if tur == "referandum":
            def alanlar(rows):
                rows = [r for r in rows if oylu(r)]
                n = len(rows) or 1
                def var(f):
                    k = sum(1 for r in rows if r.get(f))
                    return "var" if k >= 0.95 * n else ("kısmi" if k else "yok")
                def sec(s):
                    k = sum(1 for r in rows if ((r.get("oy") or {}).get(s) or {}).get("oy"))
                    return "var" if k >= 0.95 * n else ("kısmi" if k else "yok")
                return {"EVET": sec("Evet"), "HAYIR": sec("Hayır"), "geçerli": var("gecerliOy"),
                        "geçersiz": var("gecersizOy"), "katılım": var("katilim"),
                        "kayıtlı seçmen": var("secmen"), "sandık": var("sandik")}
            ref_alanlari.append((key, d.get("ad"), alanlar(iller), alanlar(birimler), satirlar[-1]))

    # 1984 oncesi yerel meclisler: projede kayit yok
    for key in KAYITSIZ_MECLIS:
        for oyl in ("bm", "igm"):
            satirlar.append({
                "secim": f"{key}_{oyl}", "tur": TUR_ADI["yerel"], "yil": yil(key),
                "oylama": OYLAMA_ADI[oyl], "il_verisi": "0", "ilce_verisi": "Yok",
                "donemdeki_ilce": snaps.get(key, {}).get("ilceSayisi"), "birim": None,
                "sonuclu": 0, "eksik": snaps.get(key, {}).get("ilceSayisi"), "eksik_yuzde": 100.0,
                "kalite": "UNKNOWN", "kaynak": "-", "guvenilirlik": "-",
                "arastirma": "Evet (araştırılmadı)",
                "not": "projede kayıt yok; 1950/1955'te başkanlık satırları zaten meclis sandalyesi"
                       if key in ("1950yerel", "1955yerel") else "projede kayıt yok",
            })

    sira = {"Genel seçim": 0, "Referandum": 1, "Yerel seçim": 2, "Cumhurbaşkanlığı": 3}
    osira = {"-": 0, "Belediye başkanlığı": 0, "Belediye meclisi": 1, "İl genel meclisi": 2}
    satirlar.sort(key=lambda s: (sira[s["tur"]], s["yil"], s["secim"].split("_")[0], osira[s["oylama"]]))

    OUT.mkdir(parents=True, exist_ok=True)
    alanlar = list(satirlar[0].keys())
    with open(OUT / "kapsam_tablosu.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=alanlar)
        w.writeheader()
        w.writerows(satirlar)
    with open(OUT / "kapsam_il_bazinda.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(il_satirlari[0].keys()))
        w.writeheader()
        w.writerows(il_satirlari)

    (OUT / "KAPSAM_TABLOSU.md").write_text(markdown(satirlar, il_satirlari, ref_alanlari),
                                          encoding="utf-8")
    print(f"yazildi: {len(satirlar)} satir -> docs/rapor/KAPSAM_TABLOSU.md, kapsam_tablosu.csv, "
          f"kapsam_il_bazinda.csv")


def fmt(v):
    if v is None:
        return "–"
    if isinstance(v, float):
        return f"{v:.1f}".replace(".", ",")
    return str(v)


def secim_adi(s):
    k = s["secim"].split("_")[0]
    ad = k.replace("referandum", "").replace("yerel", "").replace("cb", " CB ").replace("1tur", "1. tur") \
        .replace("2tur", "2. tur").replace("Haziran", " Haziran").replace("Kasim", " Kasım").strip()
    return ad


def kucuk(t):
    return t.replace("İ", "i").replace("I", "ı").lower()


def oncelik(s):
    k = s["kalite"]
    if k == "MOSTLY_COMPLETE":
        return 1, "Tamamlanmaya çok yakın"
    if k == "PARTIAL":
        return 2, "Kısmi veri mevcut"
    if k == "VERY_PARTIAL" or (k == "NONE" and s["secim"] in ILCE_KAYNAGI_YOK):
        return 3, "Dağınık veri mevcut"
    return 4, "Neredeyse hiç veri yok"


ARASTIRILACAK = {
    "Belediye meclisi": "Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları",
    "İl genel meclisi": "Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları",
}


def markdown(satirlar, il_satirlari, ref_alanlari):
    L = []
    a = L.append
    a("# Seçim verisi kapsam tablosu")
    a("")
    a("> `scripts/rapor/kapsam_tablosu.py` üretir, elle düzenlemeyin. Yalnız depodaki veriye dayanır.")
    a("> Görev tanımı: `YAPILACAKLAR.md` (2., 3., 9. ve 10. maddeler). Kaynak günlüğü:")
    a("> `data/kaynaklar/ARASTIRMA_KAYDI.md`. İl il kırılım: `kapsam_il_bazinda.csv`.")
    a("")
    a("**Sayım:** *Birim* kaynaktaki ilçe/belediye satırıdır; seçimden sonra kurulan ilçelerin boş satırları")
    a("sayılmaz. *Sonuçlu* en az bir oyu olan satırdır; yalnız kazananı bilinen satır eksik sayılır.")
    a("*Dönemdeki ilçe* İçişleri kuruluş tarihlerinden; yerel seçimde birim belediye olduğu için satır")
    a("sayısı bundan farklı olabilir. Kalite: COMPLETE ≥ %99,5 · MOSTLY_COMPLETE ≥ %90 · PARTIAL ≥ %50 ·")
    a("VERY_PARTIAL > 0 · NONE araştırıldı, kaynak yok · UNKNOWN henüz araştırılmadı.")
    a("Güvenilirlik: A birincil/resmî · D zayıf/keşif (Wikipedia).")
    a("")

    # Genel durum ozeti
    say = collections.Counter(s["kalite"] for s in satirlar)
    a("## Genel durum özeti")
    a("")
    a(f"{len(satirlar)} satır (46 seçim; yerel seçimlerde başkanlık, belediye meclisi ve il genel meclisi ayrı): "
      + ", ".join(f"{k} {say[k]}" for k in ("COMPLETE", "MOSTLY_COMPLETE", "PARTIAL", "VERY_PARTIAL",
                                             "NONE", "UNKNOWN") if say[k]) + ".")
    a("")
    eksik = [s for s in satirlar if s["kalite"] != "COMPLETE"]
    for tur in ("Genel seçim", "Referandum", "Yerel seçim", "Cumhurbaşkanlığı"):
        ts = [s for s in satirlar if s["tur"] == tur]
        te = [s for s in ts if s["kalite"] != "COMPLETE"]
        if not te:
            a(f"- **{tur}:** {len(ts)} satırın hepsi ilçe düzeyinde tam.")
        else:
            a(f"- **{tur}:** {len(ts)} satırdan {len(ts) - len(te)} tam; eksik olanlar: "
              + ", ".join(f"{secim_adi(s)}{'' if s['oylama'] in ('-', 'Belediye başkanlığı') else ' ' + {'Belediye meclisi': 'BM', 'İl genel meclisi': 'İGM'}[s['oylama']]} ({s['kalite']})"
                          for s in te) + ".")
    dsatir = [s for s in satirlar if s["kalite"] == "COMPLETE" and s["guvenilirlik"] in ("D", "A/D")]
    if dsatir:
        a(f"- **Tam ama zayıf kaynaklı:** " + ", ".join(f"{secim_adi(s)} {s['tur'].split()[0].lower()}"
                                                       for s in dsatir)
          + " — sayılar tam, ancak satırların bir kısmı ya da tamamı yalnız Wikipedia'dan; A kaynağıyla doğrulanmadı.")
    a("")

    # Ana tablo
    a("## Ana tablo")
    a("")
    a("| Seçim türü | Yıl | Oylama | İl verisi | İlçe verisi | Dönemdeki ilçe | Birim | Sonuçlu | Eksik | Eksik % | Kalite | En iyi mevcut kaynak | Yeni araştırma? |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in satirlar:
        a(f"| {s['tur']} | {secim_adi(s)} | {s['oylama']} | {s['il_verisi']} | {s['ilce_verisi']} | "
          f"{fmt(s['donemdeki_ilce'])} | {fmt(s['birim'])} | {fmt(s['sonuclu'])} | {fmt(s['eksik'])} | "
          f"{fmt(s['eksik_yuzde'])} | {s['kalite']} | {s['kaynak']} | {s['arastirma']} |")
    a("")
    notlu = [s for s in satirlar if s["not"]]
    if notlu:
        a("**Notlar**")
        a("")
        for s in notlu:
            a(f"- {s['tur']} {secim_adi(s)}{'' if s['oylama'] == '-' else ' — ' + s['oylama']}: {s['not']}.")
        a("")

    # Referandum alanlari
    a("## Referandumlar: alan denetimi")
    a("")
    a("Ülke sonucu ayrı kayıt değildir; il toplamlarından hesaplanır. *var* = sonuçlu satırların ≥ %95'inde,")
    a("*kısmi* = bir kısmında, *yok* = hiçbirinde.")
    a("")
    a("| Referandum | Düzey | İlçe durumu | EVET | HAYIR | Geçerli | Geçersiz | Katılım | Kayıtlı seçmen | Sandık |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for key, ad, il_al, ilce_al, s in ref_alanlari:
        for duzey, al in (("il", il_al), ("ilçe", ilce_al)):
            durum = s["ilce_verisi"] if duzey == "ilçe" else "–"
            a(f"| {ad} | {duzey} | {durum} | " + " | ".join(al[k] for k in
              ("EVET", "HAYIR", "geçerli", "geçersiz", "katılım", "kayıtlı seçmen", "sandık")) + " |")
    a("")

    # Yerel A/B/C/D
    a("## Yerel seçimler: A/B/C/D sınıflaması")
    a("")
    a("A tam veri (≥ %90) · B kısmi · C yalnız il/genel toplam · D sonuç veri seti yok.")
    a("")
    a("| Yıl | Belediye başkanlığı | Belediye meclisi | İl genel meclisi |")
    a("|---|---|---|---|")
    by = collections.defaultdict(dict)
    for s in satirlar:
        if s["tur"] == "Yerel seçim":
            by[s["yil"]][s["oylama"]] = s
    for y in sorted(by):
        def sinif(s):
            if not s:
                return "–"
            k = s["kalite"]
            if k in ("COMPLETE", "MOSTLY_COMPLETE"):
                h = "A"
            elif k in ("PARTIAL", "VERY_PARTIAL"):
                h = "B"
            elif s["il_verisi"] not in ("0", "0/0") and not s["il_verisi"].startswith("0/"):
                h = "C"
            else:
                h = "D"
            if "yalnız kazanan" in s["not"]:
                return f"{h} (yalnız kazanan)"
            if h == "D":
                return "D"
            return f"{h} (%{fmt(100 - s['eksik_yuzde'])})"
        r = by[y]
        a(f"| {y} | {sinif(r.get('Belediye başkanlığı'))} | {sinif(r.get('Belediye meclisi'))} | "
          f"{sinif(r.get('İl genel meclisi'))} |")
    a("")
    a("1984 ve 1989'u yanlışlıkla \"eksik\" saymayın: başkanlık satırlarının tamamı DİE kitaplarıyla")
    a("teyitli. Bu yıllardaki boşluk meclis sonuçlarında (taranmış kitabın okunamayan satırları).")
    a("")

    # Oncelik tablosu
    a("## Araştırma önceliği (yalnız eksik seçimler)")
    a("")
    a("Öncelik kalite/önem değil, araştırma verimliliğidir: 1 tamamlanmaya çok yakın → 4 neredeyse hiç veri yok.")
    a("")
    a("| Öncelik | Seçim | Eksiklik | Mevcut veri | Araştırılması gereken kaynak türü |")
    a("|---|---|---|---|---|")
    ilmap = collections.defaultdict(collections.Counter)
    for r in il_satirlari:
        ilmap[(r["secim"])][r["durum"]] += 1
    for s in sorted(eksik, key=lambda s: (oncelik(s)[0], s["eksik_yuzde"] or 0, s["yil"])):
        o, oad = oncelik(s)
        if s["kalite"] == "UNKNOWN":
            mevcut = "yok"
            kay = ("İstatistik Umum Müdürlüğü yayınları, il yıllıkları, dönemin gazeteleri" if s["yil"] < 1960
                   else "DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri")
        elif s["secim"] in ILCE_KAYNAGI_YOK:
            mevcut = f"il düzeyi tam ({s['il_verisi']})"
            kay = "Parçalı il çalışmaları (ACADEMIC-002), yerel gazeteler, BCA; ulusal kaynak araması kapandı"
        else:
            c = ilmap.get(s["secim"], {})
            mevcut = f"{s['sonuclu']}/{s['birim']} birim; " + ", ".join(
                f"{n} il {d}" for d, n in sorted(c.items()))
            kay = ARASTIRILACAK.get(s["oylama"], "Kaynak satırı eşleşmeyen birimler için YSK/DİE tutanakları")
            if s["yil"] >= 2009:
                kay = "YSK açık veri (aynı API) — eşleşmeyen satırın kimliği"
            if s["kalite"] == "VERY_PARTIAL" and s["yil"] < 1960:
                kay = "DİE 1950/1955 mahalli seçim yayınları, il yıllıkları, dönemin gazeteleri"
        a(f"| {o} — {oad} | {s['tur']} {secim_adi(s)}{'' if s['oylama'] == '-' else ' ' + kucuk(s['oylama'])} | "
          f"{fmt(s['eksik'])} birim (%{fmt(s['eksik_yuzde'])}) | {mevcut} | {kay} |")
    a("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
