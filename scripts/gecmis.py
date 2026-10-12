"""
Genel seçim geçmişi: her il (plaka) ve her bugünkü ilçe (geomId) için 1950–2023 genel
seçimlerindeki parti oy oranları. Sitenin detay panelindeki "Seçim geçmişi" grafiği bunu okur
(data/gecmis/genel.json, export_static.public_files).

İlçe eşlemesi (bugünkü ilçe → o seçimdeki kayıt), sırayla:
  1. Seçim kaydı ilçenin kendi geomId'sini taşıyor.
  2. geo/historical/idari/ilce_eslesme/<seçim>.csv: geomId_secim ile, olmazsa
     (plaka_secim, ilce_secim) adıyla.
  3. geo/historical/district_splits.json: ilçeyi içine alan sentetik birleşim poligonu.
Kayıt ilçenin kendisine değil, bağlı olduğu ilçeye aitse (ör. Aladağ 1987 öncesi Karaisalı'da)
nokta o ilçenin adını taşır; site bunu içi boş nokta olarak çizer. Tahmin yok: eşlenemeyen
seçim nokta almaz.

Yalnız sitede çizilecek kadarı tutulur: oranı %2 ve üstü partiler, bir ondalık; "Diğer" yok.
"""
import csv
import json
import pathlib
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENEL = ROOT / "data" / "normalized" / "elections" / "genel"
ESLEME = ROOT / "geo" / "historical" / "idari" / "ilce_eslesme"
SPLITS = ROOT / "geo" / "historical" / "district_splits.json"

AYLAR = {"Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6, "Temmuz": 7,
         "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12}
ESIK = 2.0


def _ad(s):
    s = unicodedata.normalize("NFC", s or "").replace("İ", "i").replace("I", "ı").lower()
    return s.replace(" merkez", "").strip()


def _tarih(ad):
    """'5 Haziran 1977' -> 1977.42 (yıl + ay/12): x ekseni için yeter."""
    gun, ay, yil = ad.split()[:3]
    return round(int(yil) + (AYLAR[ay] - 1 + int(gun) / 31) / 12, 3)


def _oranlar(kayit):
    out = {}
    for parti, sonuc in (kayit.get("oy") or {}).items():
        oran = sonuc.get("oran") if isinstance(sonuc, dict) else None
        if parti == "Diğer" or oran is None or oran < ESIK:
            continue
        out[parti] = round(oran, 1)
    return out


def _yukle(path):
    return json.loads(path.read_text(encoding="utf-8"))


def secim_gecmisi():
    anahtarlar = sorted((p.stem for p in GENEL.glob("*.json")), key=lambda k: _tarih(_yukle(GENEL / f"{k}.json")["ad"]))
    secimler = [_yukle(GENEL / f"{k}.json") for k in anahtarlar]
    guncel = secimler[-1]["ilceler"]  # en son seçimin ilçeleri = bugünkü ilçeler

    uye = {}
    for liste in _yukle(SPLITS).values():
        for s in liste:
            for g in s["hideIds"]:
                uye.setdefault(g, []).append(s["syntheticId"])

    il, ilce, tarihsel, parcalar = {}, {}, {}, {}
    for i, (anahtar, kayit) in enumerate(zip(anahtarlar, secimler)):
        for p in kayit["iller"]:
            o = _oranlar(p)
            if o:
                il.setdefault(str(p["plaka"]), []).append([i, o])
        if not kayit["ilceler"]:
            continue
        geomdan = {d["geomId"]: d for d in kayit["ilceler"] if d.get("geomId")}
        addan = {(d["plaka"], _ad(d["ad"])): d for d in kayit["ilceler"]}
        csv_yol = ESLEME / f"{anahtar}.csv"
        esleme = {}
        if csv_yol.exists():
            with csv_yol.open(encoding="utf-8") as f:
                esleme = {r["guncel_geomId"]: r for r in csv.DictReader(f)}
        for d in guncel:
            g = d["geomId"]
            # Adaylar öncelik sırasıyla; oyu olmayan kayıt (ör. 2011'de henüz oy almamış
            # modern ilçe iskeleti) atlanır, sıradaki aday denenir.
            adaylar = [geomdan.get(g)]
            if g in esleme:
                r = esleme[g]
                adaylar += [geomdan.get(r["geomId_secim"]), addan.get((int(r["plaka_secim"]), _ad(r["ilce_secim"])))]
            adaylar += [geomdan[s] for s in uye.get(g, []) if s in geomdan]
            hedef = next((a for a in adaylar if a is not None and _oranlar(a)), None)
            if hedef is None:
                continue
            o = _oranlar(hedef)
            kendisi = hedef.get("geomId") == g or _ad(hedef["ad"]) == _ad(d["ad"])
            nokta = [i, o] if kendisi else [i, o, hedef["ad"]]
            ilce.setdefault(g, []).append(nokta)
            hg = hedef.get("geomId")
            if hg and hg != g:
                # Tarihsel poligona tıklanınca açılacak geçmiş: kendi adını taşıyan bugünkü ilçe.
                # Böyle bir ilçe yoksa (ör. bölünmüş eski Merkez) site parçaları listeler.
                if kendisi:
                    tarihsel[hg] = g
                else:
                    parcalar.setdefault(hg, set()).add(g)

    return {
        "secimler": [{"k": k, "t": _tarih(s["ad"]), "ad": s["ad"]} for k, s in zip(anahtarlar, secimler)],
        "il": il,
        "ilce": ilce,
        "tarihsel": tarihsel,
        "parcalar": {hg: sorted(gs) for hg, gs in sorted(parcalar.items()) if hg not in tarihsel},
        "adlar": {d["geomId"]: d["ad"] for d in guncel},
    }


if __name__ == "__main__":
    veri = secim_gecmisi()
    metin = json.dumps(veri, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(veri['secimler'])} seçim, {len(veri['il'])} il, {len(veri['ilce'])} ilçe, "
          f"{len(veri['tarihsel'])} tarihsel poligon, {len(metin) / 1e6:.2f} MB")
