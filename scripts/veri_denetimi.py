"""
Veri denetimi: data/normalized altindaki BUTUN kirilimlarda (il, ilce, mahalle, meclis, belde, ek
dosyalar) imkansiz ya da birbirini tutmayan degerleri arar ve tek bir rapor yazar.

Veriyi DEGISTIRMEZ; yalniz bulur ve sayar. Bulgularin bir kismi kaynagin kendisinden gelir (ornek:
YSK'de bazi sandiklarda oy kullanan sayisi kayitli seçmenden fazla), bir kismi isleme hatasi olabilir.
Rapor her bulgu turunu ne anlama geldigi ve ornekleriyle birlikte verir.

Kayit denetimleri ("oy" alani parti -> {oy, oran} olan her sozluk bir sonuc kaydi sayilir):
  KATILIM_100_USTU        katilim > %100 ya da oy kullanan > kayitli secmen
  KATILIM_ARALIK_DISI     katilim < 0
  GECERLI_SECMENDEN_FAZLA gecerli oy > kayitli secmen
  OY_TOPLAMI_TUTMUYOR     parti oylari toplami != gecerli oy (fark > max(1, binde 1))
  GECERLI_GECERSIZ_TUTMUYOR gecerli + gecersiz != oy kullanan (fark > max(1, binde 1))
  ORAN_HESAPLA_TUTMUYOR   oran, oy / taban * 100'den 0,11 puandan fazla farkli
  ORAN_ARALIK_DISI        oran < 0 ya da > 100
  OY_NEGATIF_YA_DA_KESIRLI
  KAZANAN_OY_LISTESINDE_YOK
  KAZANAN_DIGER           kazanan "Diğer" (ayristirilmamis toplam)
  KAZANAN_EN_COK_OY_DEGIL bilgi: resmi kazanan sandik toplamindan farkli olabilir (itiraz, yeniden sayim)
  SECMEN_YOK_OY_VAR       kayitli secmen 0/bos ama oy var
  KATILIM_COK_DUSUK       bilgi: katilim < %20
  YINELENEN_KAYIT         ayni dosyada ayni duzeyde ayni kimlik iki kez

Kirilimlar arasi denetimler:
  IL_ILCE_TOPLAMI         genel/referandum/CB: il secmeni ve gecerli oyu != ilcelerinin toplami (> %1)
  MAHALLE_ILCEDEN_BUYUK   bir ilcenin mahalle secmen toplami ilce kaydindan > %1 buyuk
  MAHALLE_SECMEN_SICRAMASI bilgi: ayni mahallenin secmeni ardisik iki secim arasinda 5 kattan fazla degisiyor

Kullanim (repo kokunden):
  python3 scripts/veri_denetimi.py                      # ozet ekrana
  python3 scripts/veri_denetimi.py --md docs/rapor/VERI_DENETIMI.md --json /tmp/denetim.json
  python3 scripts/veri_denetimi.py --ornek 20           # her bulgu turu icin ornek sayisi
  python3 scripts/veri_denetimi.py --csv-klasor docs/rapor/veri_denetimi   # her bulgu turu icin tam liste (CSV)
  python3 scripts/veri_denetimi.py --kontrol docs/rapor/veri_denetimi       # CI: kayitli listede olmayan
                                   # yeni bulgu varsa 1 ile cikar (validate.yml). Veri duzeltilince giderilen
                                   # bulgular yalniz bildirilir; listeyi --md/--csv-klasor ile yenileyin.
"""
import argparse
import collections
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NORM = ROOT / "data" / "normalized"
DIGER = "Diğer"

ACIKLAMA = {
    "KATILIM_100_USTU": ("hata/kaynak", "Katılım %100'ü aşıyor: oy kullanan kayıtlı seçmenden fazla. YSK sandık verisinde de görülür (listede kayıtlı olmayan görevliler o sandıkta oy kullanabiliyor); küçük birimlerde oranı büyütür. Sitede katılım oranı anlamlı değil."),
    "KATILIM_ARALIK_DISI": ("hata", "Katılım negatif."),
    "GECERLI_SECMENDEN_FAZLA": ("hata/kaynak", "Geçerli oy kayıtlı seçmenden fazla (katılım %100 üstüyle aynı kökten)."),
    "OY_TOPLAMI_TUTMUYOR": ("hata", "Parti oylarının toplamı geçerli oya eşit değil: bir partinin oyu eksik ya da fazla."),
    "GECERLI_GECERSIZ_TUTMUYOR": ("hata", "Geçerli + geçersiz oy, oy kullanan sayısını tutmuyor."),
    "ORAN_HESAPLA_TUTMUYOR": ("hata", "Yazılı oran, oy sayısından hesaplanan orandan farklı."),
    "ORAN_ARALIK_DISI": ("hata", "Oran 0–100 dışında."),
    "OY_NEGATIF_YA_DA_KESIRLI": ("hata", "Oy sayısı negatif ya da tam sayı değil."),
    "KAZANAN_OY_LISTESINDE_YOK": ("hata", "Kazanan olarak yazılan parti oy listesinde yok."),
    "KAZANAN_DIGER": ("eksik", "Kazanan 'Diğer' (ayrıştırılmamış küçük partiler toplamı)."),
    "KAZANAN_EN_COK_OY_DEGIL": ("bilgi", "Kazanan, en çok oy alan parti değil. Resmi sonuç sandık toplamından farklı olabilir (itiraz, yeniden sayım, aday düzeyinde belirlenen kazanan); tek tek bakılmalı."),
    "SECMEN_YOK_OY_VAR": ("bilgi", "Kayıtlı seçmen sayısı yok ya da 0, ama oy var; katılım hesaplanamaz."),
    "KATILIM_COK_DUSUK": ("bilgi", "Katılım %20'nin altında; kaynak ya da eşleştirme hatası olabilir."),
    "YINELENEN_KAYIT": ("hata", "Aynı dosyada aynı birim iki kez var."),
    "IL_ILCE_TOPLAMI": ("hata", "İl kaydı, ilçelerinin toplamından %1'den fazla farklı (seçmen ya da geçerli oy)."),
    "MAHALLE_ILCEDEN_BUYUK": ("hata", "Bir ilçenin mahalle seçmen toplamı, ilçe kaydının seçmeninden %1'den fazla büyük."),
    "MAHALLE_SECMEN_SICRAMASI": ("bilgi", "Aynı mahallenin seçmeni ardışık iki seçim arasında 5 kattan fazla değişiyor (eşleştirme hatası ya da gerçek nüfus değişimi)."),
}
# tests/fixtures/known-validation-issues.json: belgelenmis, kaynakla dogrulanmayi bekleyen kayitlar
# (scripts/validate_public_data.py). Raporda "bilinen" diye ayrilir.
BILINEN_KOD = {"OY_TOPLAMI_TUTMUYOR": "vote-scope", "ORAN_HESAPLA_TUTMUYOR": "percent-count",
               "GECERLI_SECMENDEN_FAZLA": "valid-exceeds-voters", "YINELENEN_KAYIT": "duplicate"}
DUZEY_ADI = {"iller": "il", "ilceler": "ilçe", "mahalle": "mahalle", "birimler": "birim", "kayitlar": "kayıt", "beldeler": "belde"}


def tol(n):
    return max(1, abs(n or 0) * 0.001)


class Denetim:
    def __init__(self, ornek_sayisi):
        self.bulgular = collections.defaultdict(list)   # tur -> [bulgu]
        self.sayac = collections.Counter()              # (tur, duzey) -> n
        self.kayit_sayisi = collections.Counter()       # duzey -> n
        self.ornek_sayisi = ornek_sayisi
        fx = ROOT / "tests" / "fixtures" / "known-validation-issues.json"
        self.bilinen = set(json.loads(fx.read_text(encoding="utf-8"))) if fx.exists() else set()
        self._onek = None   # bilinen sorun anahtarinin kayda ait on eki

    def ekle(self, tur, duzey, dosya, birim, detay, belgeli=False):
        bilinen = belgeli or bool(self._onek and BILINEN_KOD.get(tur) and f"{self._onek}/{BILINEN_KOD[tur]}" in self.bilinen)
        self.sayac[(tur, duzey)] += 1
        if bilinen:
            self.sayac[(tur, "bilinen")] += 1
        self.bulgular[tur].append({"duzey": duzey, "dosya": dosya, "birim": birim, "detay": detay, "bilinen": bilinen})

    # ---------------------------------------------------------------- kayit denetimi
    def kayit(self, r, duzey, dosya, birim):
        oy = r.get("oy")
        if not isinstance(oy, dict) or not oy:
            return
        self.kayit_sayisi[duzey] += 1
        sayilar = {}
        for p, v in oy.items():
            o = v.get("oy") if isinstance(v, dict) else v
            if o is None:
                continue
            if not isinstance(o, int) or o < 0:
                self.ekle("OY_NEGATIF_YA_DA_KESIRLI", duzey, dosya, birim, f"{p}: {o}")
                continue
            sayilar[p] = o
            oran = v.get("oran") if isinstance(v, dict) else None
            if oran is not None and not 0 <= oran <= 100:
                self.ekle("ORAN_ARALIK_DISI", duzey, dosya, birim, f"{p}: %{oran}")
        toplam = sum(sayilar.values())
        secmen = r.get("secmen")
        gecerli = r.get("gecerliOy")
        kullanan = r.get("oyKullanan")
        gecersiz = r.get("gecersizOy")
        katilim = r.get("katilim")

        if katilim is not None and katilim > 100:
            kul = kullanan if kullanan is not None else (round(katilim * secmen / 100) if secmen else None)
            self.ekle("KATILIM_100_USTU", duzey, dosya, birim,
                      f"katılım %{katilim}, seçmen {secmen}, oy kullanan {kul}, geçerli parti oyu {toplam}")
        elif secmen and kullanan and kullanan > secmen:
            self.ekle("KATILIM_100_USTU", duzey, dosya, birim, f"seçmen {secmen}, oy kullanan {kullanan}")
        if katilim is not None and katilim < 0:
            self.ekle("KATILIM_ARALIK_DISI", duzey, dosya, birim, f"%{katilim}")
        if katilim is not None and 0 <= katilim < 20 and (secmen or 0) >= 50:
            self.ekle("KATILIM_COK_DUSUK", duzey, dosya, birim, f"katılım %{katilim}, seçmen {secmen}")
        if secmen and gecerli and gecerli > secmen:
            self.ekle("GECERLI_SECMENDEN_FAZLA", duzey, dosya, birim, f"seçmen {secmen}, geçerli {gecerli}")
        if not secmen and toplam > 0 and "secmen" in r:
            self.ekle("SECMEN_YOK_OY_VAR", duzey, dosya, birim, f"seçmen {secmen}, oy {toplam}")
        if gecerli and sayilar and len(sayilar) == len(oy) and abs(toplam - gecerli) > tol(gecerli):
            self.ekle("OY_TOPLAMI_TUTMUYOR", duzey, dosya, birim, f"parti toplamı {toplam}, geçerli {gecerli} (fark {toplam - gecerli:+g})")
        if gecerli is not None and gecersiz is not None and kullanan and abs(gecerli + gecersiz - kullanan) > tol(kullanan):
            self.ekle("GECERLI_GECERSIZ_TUTMUYOR", duzey, dosya, birim, f"geçerli {gecerli} + geçersiz {gecersiz} ≠ oy kullanan {kullanan}")
        # oranlar: taban, oranlarin hangi toplama gore yazildigi (gecerli oy ya da parti toplami)
        if toplam and sayilar:
            tabanlar = [t for t in (gecerli, toplam) if t]
            for p, o in sayilar.items():
                oran = oy[p].get("oran") if isinstance(oy[p], dict) else None
                if oran is None:
                    continue
                if all(abs(oran - o / t * 100) > 0.11 for t in tabanlar):
                    self.ekle("ORAN_HESAPLA_TUTMUYOR", duzey, dosya, birim,
                              f"{p}: yazılı %{oran}, hesaplanan %{o / tabanlar[0] * 100:.2f}")
                    break
        kaz = r.get("kazanan")
        if kaz:
            if kaz == DIGER:
                self.ekle("KAZANAN_DIGER", duzey, dosya, birim, "")
            if kaz not in oy:
                self.ekle("KAZANAN_OY_LISTESINDE_YOK", duzey, dosya, birim, f"kazanan {kaz}")
            elif sayilar and kaz in sayilar:
                enb = max(sayilar, key=sayilar.get)
                if sayilar[enb] > sayilar[kaz]:
                    self.ekle("KAZANAN_EN_COK_OY_DEGIL", duzey, dosya, birim,
                              f"kazanan {kaz} {sayilar[kaz]}, en çok oy {enb} {sayilar[enb]}")

    # ---------------------------------------------------------------- dosya turleri
    def secim_dosyasi(self, yol, mahalle_adi=None):
        d = json.loads(yol.read_text(encoding="utf-8"))
        dosya = str(yol.relative_to(NORM))
        for lv in ("iller", "ilceler"):
            gorulen = collections.Counter()
            klasor = yol.relative_to(NORM).parts[0]
            for r in d.get(lv) or []:
                kimlik = r.get("geomId") or f"{r.get('plaka')}:{r.get('ad')}"
                gorulen[kimlik] += 1
                self._onek = f"{klasor}/{yol.stem}/{lv}/{r.get('geomId') or r.get('plaka')}:{r.get('ad')}"
                self.kayit(r, DUZEY_ADI[lv], dosya, self.ad(r))
                self._onek = None
            for k, n in gorulen.items():
                if n > 1:
                    self.ekle("YINELENEN_KAYIT", DUZEY_ADI[lv], dosya, k, f"{n} kez")
        return d

    def ad(self, r):
        parcalar = [r.get("il"), r.get("ilce"), r.get("belde"), r.get("ad")]
        if r.get("plaka") and not r.get("il"):
            parcalar.insert(0, f"plaka {r['plaka']}")
        return " / ".join(str(p) for p in parcalar if p)

    def genel_yapi(self, o, dosya, yol="", baglam=""):
        """Ek dosyalarda (meclis, belde, yenileme...) 'oy' alani olan her kaydi bulur. Ic ice
        kayitlarda (belde -> tuik) birim adi ust kayittan gelir."""
        if isinstance(o, dict):
            ad = self.ad(o) or baglam or o.get("adKaynakta") or ""
            if isinstance(o.get("oy"), dict) and o["oy"]:
                duzey = yol.rsplit("/", 1)[-1] if yol else "kayıt"
                self.kayit(o, DUZEY_ADI.get(duzey, duzey), dosya, ad or baglam)
                return
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    self.genel_yapi(v, dosya, f"{yol}/{k}", ad or baglam)
        elif isinstance(o, list):
            for v in o:
                self.genel_yapi(v, dosya, yol, baglam)

    # ---------------------------------------------------------------- calistir
    def calistir(self):
        mahalle_adlari = {}
        geo = ROOT / "geo" / "normalized" / "mahalle_geo.json"
        if geo.exists():
            for g, mm in json.loads(geo.read_text(encoding="utf-8")).items():
                for m, v in mm.items():
                    mahalle_adlari[(g, m)] = v.get("ad")

        secimler = {}
        for yol in sorted((NORM / "elections").rglob("*.json")):
            secimler[yol.stem] = (yol, self.secim_dosyasi(yol))

        ilce_adi = {}
        for _, d in secimler.values():
            for r in d.get("ilceler") or []:
                if r.get("geomId"):
                    ilce_adi.setdefault(r["geomId"], f"{r['ad']}")

        # il = ilceler toplami (yalniz genel, referandum, CB: yerelde il kaydi ayri bir yaristir)
        for anahtar, (yol, d) in secimler.items():
            if d.get("tur") not in ("genel", "referandum", "cumhurbaskanligi"):
                continue
            ilce_top = collections.defaultdict(lambda: [0, 0, 0])
            for r in d.get("ilceler") or []:
                t = ilce_top[r.get("plaka")]
                t[0] += r.get("secmen") or 0
                t[1] += r.get("gecerliOy") or 0
                t[2] += 1
            for r in d.get("iller") or []:
                t = ilce_top.get(r.get("plaka"))
                if not t or not t[2]:
                    continue
                # il kaydinda ilceFarki.<alan> = {il, ilceler} varsa fark kaynak yayinin kendisindedir (belgeli)
                fark = r.get("ilceFarki") or {}
                for ad, alan, il_deg, ilce_deg in (("seçmen", "secmen", r.get("secmen"), t[0]),
                                                   ("geçerli oy", "gecerliOy", r.get("gecerliOy"), t[1])):
                    if il_deg and ilce_deg and abs(il_deg - ilce_deg) > il_deg * 0.01:
                        self.ekle("IL_ILCE_TOPLAMI", "il", str(yol.relative_to(NORM)), r.get("ad"),
                                  f"{ad}: il {il_deg}, ilçeler toplamı {ilce_deg} ({(ilce_deg - il_deg) / il_deg * 100:+.1f}%)",
                                  belgeli=fark.get(alan) == {"il": il_deg, "ilceler": ilce_deg})

        # mahalle dosyalari
        onceki_secmen = {}
        mahalle_dir = NORM / "mahalle"
        for yol in sorted(mahalle_dir.glob("*.json"), key=lambda p: p.stem):
            d = json.loads(yol.read_text(encoding="utf-8"))
            dosya = str(yol.relative_to(NORM))
            ilce_kaydi = {}
            if yol.stem in secimler:
                for r in secimler[yol.stem][1].get("ilceler") or []:
                    if r.get("geomId"):
                        ilce_kaydi[r["geomId"]] = r
            simdiki = {}
            for g, mm in d.items():
                s_top = 0
                for m, r in mm.items():
                    birim = f"{ilce_adi.get(g, g)} / {mahalle_adlari.get((g, m), m)}"
                    self.kayit(r, "mahalle", dosya, birim)
                    s = r.get("secmen") or 0
                    s_top += s
                    simdiki[(g, m)] = s
                    o = onceki_secmen.get((g, m))
                    if o and s and min(o, s) >= 20 and max(o, s) / min(o, s) > 5:
                        self.ekle("MAHALLE_SECMEN_SICRAMASI", "mahalle", dosya, birim, f"önceki seçimde {o}, bu seçimde {s}")
                ik = ilce_kaydi.get(g)
                # Ilce kaydi ilce belediyesinin kendi yarisina indirildiyse (belde sandiklari haric),
                # mahalle dosyasi ilcenin butun sandiklarini kapsar: kaynak.yskSatiri'ndaki ilce toplamiyla karsilastir.
                ik_secmen = (((ik or {}).get("kaynak") or {}).get("yskSatiri") or {}).get("secmen") or (ik or {}).get("secmen")
                if ik and ik_secmen and s_top > ik_secmen * 1.01:
                    self.ekle("MAHALLE_ILCEDEN_BUYUK", "mahalle", dosya, ilce_adi.get(g, g),
                              f"mahalleler toplamı {s_top}, ilçe kaydı {ik_secmen}")
            onceki_secmen = simdiki

        # ek dosyalar (meclis haritalari, belde, yenileme/ara, il genel meclisi, belediye meclisi...)
        for alt in ("meclis_harita", "ek"):
            for yol in sorted((NORM / alt).rglob("*.json")):
                d = json.loads(yol.read_text(encoding="utf-8"))
                if alt == "meclis_harita":
                    self.secim_dosyasi(yol)
                else:
                    self.genel_yapi(d, str(yol.relative_to(NORM)))
        return self

    # ---------------------------------------------------------------- rapor
    def ozet_tablosu(self):
        duzeyler = sorted({d for (_, d) in self.sayac} - {"bilinen"})
        satirlar = []
        for tur in ACIKLAMA:
            n = sum(v for (t, d), v in self.sayac.items() if t == tur and d != "bilinen")
            if not n:
                continue
            dagilim = ", ".join(f"{d} {self.sayac[(tur, d)]}" for d in duzeyler if self.sayac[(tur, d)])
            if self.sayac[(tur, "bilinen")]:
                dagilim += f" — {self.sayac[(tur, 'bilinen')]} tanesi zaten belgeli"
            satirlar.append((tur, ACIKLAMA[tur][0], n, dagilim))
        return satirlar

    def markdown(self):
        out = ["# Veri denetimi raporu", "",
               "`python3 scripts/veri_denetimi.py` çıktısı. Veri değiştirilmez; bulgular kaynak ya da işleme kökenli olabilir.", "",
               "## Denetlenen kayıtlar", "",
               "| Düzey | Kayıt |", "|---|---|"]
        out += [f"| {d} | {n:,} |".replace(",", ".") for d, n in sorted(self.kayit_sayisi.items(), key=lambda x: -x[1])]
        out += ["", "## Özet", "", "| Bulgu | Tür | Sayı | Düzeylere göre |", "|---|---|---|---|"]
        out += [f"| `{t}` | {k} | {n} | {dg} |" for t, k, n, dg in self.ozet_tablosu()]
        for tur, (_, aciklama) in ACIKLAMA.items():
            liste = self.bulgular.get(tur)
            if not liste:
                continue
            out += ["", f"## `{tur}` ({len(liste)})", "", aciklama, ""]
            dosyaya = collections.Counter(b["dosya"] for b in liste)
            out.append("Dosyalara göre: " + ", ".join(f"{f} {n}" for f, n in dosyaya.most_common(12))
                       + (" …" if len(dosyaya) > 12 else ""))
            out += ["", "| Dosya | Birim | Ayrıntı |", "|---|---|---|"]
            # once yeni (belgelenmemis) bulgular
            for b in sorted(liste, key=lambda b: b["bilinen"])[: self.ornek_sayisi]:
                out.append(f"| {b['dosya']} | {b['birim']} | {b['detay']}{' (belgeli)' if b['bilinen'] else ''} |")
            if len(liste) > self.ornek_sayisi:
                out.append(f"| … | {len(liste) - self.ornek_sayisi} kayıt daha | |")
        return "\n".join(out) + "\n"


def kontrol(d, klasor: pathlib.Path) -> int:
    """Bulgulari kayitli taban listeyle (klasor/<TUR>.csv) karsilastirir. Anahtar (tur, dosya, duzey,
    birim): ayrinti metnindeki sayilar degisse de ayni bulgu sayilir. Yeni bulgu varsa 1 doner."""
    taban = collections.Counter()
    for yol in sorted(klasor.glob("*.csv")):
        with open(yol, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                taban[(yol.stem, r["dosya"], r["duzey"], r["birim"])] += 1
    simdi, ayrinti = collections.Counter(), {}
    for tur, liste in d.bulgular.items():
        for b in liste:
            k = (tur, b["dosya"], b["duzey"], b["birim"])
            simdi[k] += 1
            ayrinti.setdefault(k, b["detay"])
    yeni, giden = simdi - taban, taban - simdi
    if giden:
        print(f"Bilgi: kayıtlı listedeki {sum(giden.values())} bulgu artık yok (giderilmiş); listeyi yenileyin:"
              " --md docs/rapor/VERI_DENETIMI.md --csv-klasor docs/rapor/veri_denetimi")
    if not yeni:
        print(f"Veri denetimi: yeni bulgu yok ({sum(simdi.values())} bulgu kayıtlı listede).")
        return 0
    print(f"::error title=Veri denetimi::{sum(yeni.values())} yeni bulgu (kayıtlı listede yok)")
    for (tur, dosya, duzey, birim) in sorted(yeni)[:40]:
        print(f"  {tur}  {dosya}  {duzey}  {birim}: {ayrinti[(tur, dosya, duzey, birim)]}")
    if len(yeni) > 40:
        print(f"  … {len(yeni) - 40} tane daha")
    print("Kaynaktan geliyorsa ve beklenense listeyi yenileyip commit'leyin; değilse veriyi düzeltin.")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--md", help="markdown rapor yolu")
    ap.add_argument("--json", help="bütün bulguların JSON dökümü")
    ap.add_argument("--ornek", type=int, default=15, help="her bulgu türü için rapora yazılan örnek sayısı")
    ap.add_argument("--csv-klasor", help="her bulgu türünün tam listesi bu klasöre <TUR>.csv olarak yazılır")
    ap.add_argument("--kontrol", metavar="KLASOR",
                    help="bu klasördeki kayıtlı listede olmayan yeni bulgu varsa 1 ile çık (CI)")
    a = ap.parse_args()
    d = Denetim(a.ornek).calistir()
    if a.kontrol:
        sys.exit(kontrol(d, pathlib.Path(a.kontrol)))
    print("Denetlenen kayıt:", dict(d.kayit_sayisi))
    for t, k, n, dg in d.ozet_tablosu():
        print(f"{t:28s} {k:12s} {n:6d}   {dg}")
    if a.md:
        pathlib.Path(a.md).write_text(d.markdown(), encoding="utf-8")
        print("yazıldı:", a.md)
    if a.csv_klasor:
        klasor = pathlib.Path(a.csv_klasor)
        klasor.mkdir(parents=True, exist_ok=True)
        for eski in klasor.glob("*.csv"):
            eski.unlink()
        for tur in ACIKLAMA:
            liste = d.bulgular.get(tur)
            if not liste:
                continue
            with open(klasor / f"{tur}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["dosya", "duzey", "birim", "ayrinti", "belgeli"])
                for b in sorted(liste, key=lambda b: (b["dosya"], b["birim"])):
                    w.writerow([b["dosya"], b["duzey"], b["birim"], b["detay"], "evet" if b["bilinen"] else ""])
        print("yazıldı:", klasor, f"({sum(1 for _ in klasor.glob('*.csv'))} CSV)")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"kayitSayisi": d.kayit_sayisi, "bulgular": d.bulgular},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
        print("yazıldı:", a.json)


if __name__ == "__main__":
    main()
