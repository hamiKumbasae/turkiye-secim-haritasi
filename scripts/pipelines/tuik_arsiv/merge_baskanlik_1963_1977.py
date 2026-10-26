"""
1963-1977 belediye baskanligi: depodaki kayit (Vikipedi il sayfalari; o sayfalar bu kitaplari kaynak gosteriyor)
DIE kitabinin baskanlik tablosuyla (extract_mahalli_1963_1977.py -> data/kaynaklar/tuik/yerel/<secim>/
belediye_baskanligi.json) karsilastirilir; kitapta dogrulanmis satirin sayilari kayda islenir.

Isleme merge_mahalli.satiri_isle ile (1984-2004 ile ayni kural): kitap satiri ic kontrolden gectiyse (parti
toplami == gecerli oy; 1973/1977'de yuzdeler de) parti oylari ve gecerli oy kitaptan yazilir, Vikipedi'deki aday
adlari korunur; sandik / secmen / katilim yalniz kitabin katilim yuzdesi tutuyorsa. Her degisiklik
kaynak.farklar'da (eski -> yeni), degismeyen satir kaynak.teyit = ["tuik"]. Kitapta toplam tutmayan satir
(1963/1968: tutanaktaki fark) islenmez, kaynak.tuikKullanilmadi'da nedeni yazilir.

Kimlik (tahmin yok; kitap satirinda ad cogu yerde metin katmaninda yok):
  1. ayni ilde secmen (ve okunduysa sandik) birebir ayni TEK kitap satiri;
  2. kitapta okunan ad (merge_mahalli.eslestir: ad / benzerlik / kitap sirasi + sayisal destek);
  3. en az 3 partinin oyu (>= 10) birebir ayni TEK satir.
Il satiri (il merkezi belediyesi) ayni kurallarla; il merkezinin ilce satiri ("Merkez", kaynak 'il satiri') il
satirindan birebir kopyalanir.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/merge_baskanlik_1963_1977.py [secim ...] [--yaz]
"""
import argparse
import collections
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
from common.election_io import load_election, save_election  # noqa: E402
import extract_mahalli_1963_1977 as X  # noqa: E402
import merge_mahalli as M  # noqa: E402

for _s, _c in X.KITAPLAR.items():
    M.KITAPLAR.setdefault(_s, _c)

SECIMLER = ["1963yerel", "1968yerel", "1973yerel", "1977yerel"]
IL_SATIRI_MERKEZ = {"1963yerel"}


def _po(p):
    return {k: (v.get("oy") if isinstance(v, dict) else v) for k, v in (p.get("oy") or {}).items()}


def kimlik_bul(p, adaylar, kullanilan):
    """p (proje satiri) icin kitap satiri ve yontem; yoksa (None, None)."""
    bos = [d for d in adaylar if id(d) not in kullanilan]

    def tek(uyan):
        # 1963 il satiri (il merkezi) ile ayni sayilari tasiyan ilce satiri ("Merkez"): ilce satiri secilir
        if len(uyan) > 1:
            uyan = [d for d in uyan if d["tip"] != "il"]
        return uyan[0] if len(uyan) == 1 else None

    s = p.get("secmen")
    if s:
        d = tek([d for d in bos if d.get("secmen") == s and (not p.get("sandik") or not d.get("sandik")
                                                               or p["sandik"] == d["sandik"])])
        if d:
            return d, "secmen"
    po = _po(p)
    d = tek([d for d in bos if sum(1 for k, o in d["oy"].items() if o >= 10 and po.get(k) == o) >= 3])
    if d:
        return d, "oy"
    return None, None


BAG = "Bağımsız"
BAG_NOT = ("Kitapta \"Bağımsızlar\" sütunu bütün bağımsız adayların toplamıdır; kazanan aday bazında en çok oyu "
           "alandır ({}).")


# Vikipedi kaydinin not parcalari (not birden cok parcanin ard arda yazilmisi). Kitabin satiri islenince
# toplam / oran parcalari (A) eskir: gecerli oy ve oranlar artik kitaptan. Birden cok bagimsiz aday parcalari (D)
# Bagimsiz oyu kitapla degistiyse eskir: kitaptaki deger butun bagimsizlarin toplami.
NOT_BASLARI = [("A", "Kaynak sayfanın 'Toplam' satırı"), ("A", "Sayfadaki 'Toplam' satırı"),
               ("A", "Kaynak sayfadaki parti oyları toplamı"), ("D", "Bu ilde 'Bağımsız'"),
               ("D?", "Şema her parti/anahtar"), ("D", "Bağımsız: birden fazla bağımsız"),
               ("B", 'Kitapta "Bağımsızlar" sütunu')]
BAG_TOPLAM_NOT = "Bağımsız oyu DİE kitabından: bütün bağımsız adayların toplamı."


def not_parcalari(n):
    """[(tur, parca)]: not, bilinen parca baslarindan bolunur; taninmayan parca tur None."""
    import re
    yer = sorted((m.start(), tur) for tur, bas in NOT_BASLARI for m in re.finditer(re.escape(bas), n))
    if not yer or yer[0][0] > 0:
        yer = [(0, None)] + yer
    out = []
    for i, (bas, tur) in enumerate(yer):
        son = yer[i + 1][0] if i + 1 < len(yer) else len(n)
        p = n[bas:son].strip()
        if p:
            if tur == "D?":
                tur = "D" if "'Bağımsız' anahtarı" in p else None
            out.append((tur, p))
    return out


def notu_guncelle(p, bag_degisti, bag_notu):
    """Islenen satirin notu: eskiyen Vikipedi parcalari kaynak.wikipediaNotu'na tasinir."""
    kalan, eski = [], []
    for tur, parca in not_parcalari(p.get("not") or ""):
        if tur == "A" or (tur == "D" and bag_degisti):
            eski.append(parca)
        elif tur != "B":
            kalan.append(parca)
    if bag_degisti and any(t == "D" for t, _ in not_parcalari(p.get("not") or "")):
        kalan.append(BAG_TOPLAM_NOT)
    if bag_notu:
        kalan.append(bag_notu)
    if eski:
        p["kaynak"]["wikipediaNotu"] = " ".join(eski)
    if kalan:
        p["not"] = " ".join(kalan)
    else:
        p.pop("not", None)


def kazanan_belirle(eski, oy, kitap):
    """(kazanan, yontem) ya da (None, neden). Kitabin baskanlik tablosunda "Bağımsızlar" butun bagimsiz adaylarin
    toplami: oy sirasi kazanani yalniz partiler arasinda belirler. Kazanan sirayla: kitabin kendi kazanan sutunu
    (1973); kayittaki (Vikipedi, aday bazinda) kazanan oylarla celismiyorsa o; bir parti butun bagimsizlarin
    toplamindan fazla oy aldiysa o."""
    partiler = {p: o for p, o in oy.items() if p != BAG}
    bag = oy.get(BAG, 0)
    pmax = max(partiler, key=lambda p: partiler[p]) if partiler else None
    en_cok = partiler.get(pmax, 0)
    if kitap:
        if kitap == BAG and en_cok > bag:
            return None, f"kitabın kazanan sütunu Bağımsız ama {pmax} bütün bağımsızlardan çok oy almış"
        if kitap != BAG and partiler.get(kitap, -1) < en_cok:
            return None, f"kitabın kazanan sütunu {kitap} ama {pmax} daha çok oy almış"
        return kitap, "kitabın kazanan sütunu"
    if eski == BAG and BAG in oy:
        return (pmax, "oy (bütün bağımsızlardan çok)") if en_cok > bag else (BAG, "kayıt (Vikipedi)")
    if eski in partiler:
        if partiler[eski] == en_cok:
            return eski, "kayıt (Vikipedi)"
        if en_cok > bag:
            return pmax, "oy (kitapta daha çok oy alan parti)"
        return None, f"kayıttaki kazanan {eski}, kitapta {pmax} daha çok oy almış; bağımsızların toplamı ikisinden de çok (aday bazında belirlenemedi)"
    if pmax and en_cok > bag:
        return pmax, "oy"
    return None, f"kayıttaki kazanan ({eski}) kitapta oy almamış"


def isle(secim, rapor):
    rec = load_election(secim)
    bel = M.kaynak_katmani(secim, "belediye_baskanligi")["satirlar"]
    sayac = collections.Counter()
    die = collections.defaultdict(list)
    for d in bel:
        # il toplami ve Turkiye toplami disindaki satirlar aday. 1963 baskanlik tablosunda il toplami yok, il
        # satiri il merkezi belediyesinin kendisi (Adana: AP 31 548, CHP 20 525, TIP 828 kayitla ayni). 1968-1977'de
        # il satiri il toplami: aday degil (Vikipedi'de bazi il merkezlerine il toplaminin secmeni yazilmis, 1973
        # Amasya 59 765; secmen kimligi yanlis satira baglardi)
        if (d["tip"] in ("ilce", "belde") or (d["tip"] == "il" and secim in IL_SATIRI_MERKEZ)) and d["plaka"]:
            die[d["plaka"]].append(d)
    kullanilan = set()
    yontemler = collections.Counter()

    belirsiz = []

    def bagla(p, d, yontem):
        kullanilan.add(id(d))
        yontemler[yontem] += 1
        eski = copy.deepcopy(p)
        M.satiri_isle(p, d, secim, "belediye_baskanligi", sayac)
        tuik = p["kaynak"]["tuik"]
        tuik["kimlik"] = {"secmen": "seçmen (ve sandık) kitapla birebir",
                          "ad": "kitapta okunan ad", "oy": "≥3 partinin oyu kitapla birebir"}[yontem]
        if "tuikKullanilmadi" in p["kaynak"]:
            return
        oy = _po(p)
        eoy = {q: o for q, o in _po(eski).items() if isinstance(o, int)}
        if eski.get("kazanan") and eoy and eoy.get(eski["kazanan"]) != max(eoy.values()) \
                and BAG not in (eski["kazanan"], max(eoy, key=eoy.get)):
            # kayitta kazanan bilerek en cok oyu alan degil (mazbata iptali: 1968 Giresun, Tokat; 1963 Istanbul;
            # satirin notunda): kitabin oylari kazanani degistirmez
            k, y = eski["kazanan"], "kayıt (mazbata kararı; satırın notunda)"
        else:
            k, y = kazanan_belirle(eski.get("kazanan"), oy, d.get("kazananKitapta"))
        if k is None:
            # kazanan kitaptan belirlenemiyor: satir islenmez, kayit oldugu gibi kalir
            kay = dict(eski.get("kaynak") or {})
            kay["tuik"] = tuik
            kay["tuikKullanilmadi"] = {"neden": y}
            p.clear()
            p.update(eski)
            p["kaynak"] = kay
            belirsiz.append(f"{p['plaka']}:{p['ad']}: {y}")
            return
        p["kazanan"] = k
        tuik["kazananKaynak"] = y
        if k != eski.get("kazanan"):
            p["kaynak"].setdefault("farklar", []).append(
                {"alan": "kazanan", "kaynak": "tuik", "eski": eski.get("kazanan"), "yeni": k})
            p["kaynak"].pop("teyit", None)
        # kazanan en cok oyu alan degil cunku kitapta Bagimsizlar toplami en buyuk: not (mazbata durumunda degil)
        bag_notu = BAG_NOT.format(k) if oy and k != BAG and max(oy, key=lambda q: oy[q]) == BAG \
            and not y.startswith("kayıt (mazbata") else None
        bag_degisti = any(f["alan"] == "oy." + BAG for f in p["kaynak"].get("farklar", []))
        notu_guncelle(p, bag_degisti, bag_notu)

    # 1-3: secmen ve oy esitligi (il satirlari once: il merkezi belediyesi en buyuk satir)
    il_kalan, ilce_kalan = [], []
    for r in rec["iller"]:
        d, y = kimlik_bul(r, die.get(r["plaka"], []), kullanilan)
        if d:
            bagla(r, d, y)
        else:
            il_kalan.append(r)
    ilceler = [r for r in rec["ilceler"] if (r.get("kaynak") or {}).get("ana") != "il satırı"]
    for r in ilceler:
        d, y = kimlik_bul(r, die.get(r["plaka"], []), kullanilan)
        if d:
            bagla(r, d, y)
        else:
            ilce_kalan.append(r)
    # 2: adla (yalniz adi okunan kitap satirlari; zayif eslesme sayisal destekle)
    for pl in sorted({r["plaka"] for r in ilce_kalan}):
        proje = [r for r in ilce_kalan if r["plaka"] == pl]
        adli = [d for d in die.get(pl, []) if id(d) not in kullanilan and len(M._anahtar(M.dad(d))) >= 3]
        for p, d in M.eslestir(proje, adli, sira_esik=0):
            bagla(p, d, "ad")
            ilce_kalan.remove(p)
    # il merkezinin ilce satiri: il satirindan kopya
    il = {r["plaka"]: r for r in rec["iller"]}
    for r in rec["ilceler"]:
        if (r.get("kaynak") or {}).get("ana") == "il satırı" and r["plaka"] in il and "tuik" in (il[r["plaka"]].get("kaynak") or {}):
            src = il[r["plaka"]]
            for alan in ("sandik", "secmen", "katilim", "gecerliOy", "oy", "kazanan"):
                if alan in src:
                    r[alan] = copy.deepcopy(src[alan])
            r["kaynak"] = dict(r["kaynak"], tuik=copy.deepcopy(src["kaynak"]["tuik"]))
            for k in ("teyit", "farklar", "tuikKullanilmadi"):
                if k in src["kaynak"]:
                    r["kaynak"][k] = copy.deepcopy(src["kaynak"][k])
    farkli = [r for r in rec["iller"] + ilceler if (r.get("kaynak") or {}).get("farklar")]
    kazanan_degisen = [f"{r['plaka']}:{r['ad']}" for r in farkli
                       if any(f["alan"] == "kazanan" for f in r["kaynak"]["farklar"])]
    rapor[secim] = {
        "kitapSatiri": sum(len(v) for v in die.values()),
        "baglanan": dict(yontemler),
        "teyit": sum(1 for r in rec["iller"] + ilceler if (r.get("kaynak") or {}).get("teyit")),
        "farkli": len(farkli),
        "tuikKullanilmadi": sum(1 for r in rec["iller"] + ilceler if (r.get("kaynak") or {}).get("tuikKullanilmadi")),
        "baglanamayanIl": [r["ad"] for r in il_kalan],
        "baglanamayanIlce": [f"{r['plaka']}:{r['ad']}" for r in ilce_kalan],
        "kazananDegisen": kazanan_degisen,
        "kazananBelirsiz": belirsiz,
    }
    return rec


def kazanan_farki(eski, yeni):
    """{plaka:ad: (eski kazanan, yeni kazanan)}"""
    e = {(r["plaka"], r["ad"]): r.get("kazanan") for r in eski["iller"] + eski["ilceler"]}
    return {f"{r['plaka']}:{r['ad']}": (e.get((r["plaka"], r["ad"])), r.get("kazanan"))
            for r in yeni["iller"] + yeni["ilceler"] if e.get((r["plaka"], r["ad"])) != r.get("kazanan")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("secimler", nargs="*")
    ap.add_argument("--yaz", action="store_true")
    a = ap.parse_args()
    rapor = {}
    for secim in a.secimler or SECIMLER:
        eski = load_election(secim)
        rec = isle(secim, rapor)
        r = rapor[secim]
        r["kazananDegisen"] = kazanan_farki(eski, rec)
        print(secim, {k: (v if not isinstance(v, (list, dict)) or k == "baglanan" else len(v)) for k, v in r.items()})
        print("  kazanan değişen:", r["kazananDegisen"])
        print("  kazanan belirlenemedi (işlenmedi):", r["kazananBelirsiz"])
        print("  bağlanamayan ilçe:", r["baglanamayanIlce"][:30])
        if a.yaz:
            save_election(secim, rec)
            yol = M.SRC / secim / "baskanlik_birlestirme.json"
            yol.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
