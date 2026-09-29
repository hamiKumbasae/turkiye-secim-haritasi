"""
scripts/audit_district_coverage.py'nin ortaya cikardigi "eksik modern ilce"
listesinden, YUKSEK GUVENLE dogrulanmis vakalari gercek tarihsel poligon
birlesimiyle duzeltir. Iki farkli girdi turu isler:

  1. VERIFIED_MERGES (Python, bu dosyada): TEK-EBEVEYNLI, butun bir cocuk
     ilcenin TAMAMININ tek bir eski ilceden ayrildigi, birden fazla kaynakla
     dogrulanmis basit vakalar (Beylikduzu<-Buyukcekmece, Cekmekoy<-Umraniye).

  2. geo/historical/district_mahalle_merges.yaml, confidence: verified
     olan girisler: COK-EBEVEYNLI (bir yeni ilcenin mahalleleri BIRDEN FAZLA
     eski ilceden geldigi) vakalar - kanunun EKLI LISTESINDEKI (resmi, 5747
     sayili kanun) mahalle isimleri GUNCEL mahalle_geo.json ile TAM (kalintisiz)
     eslestirilebildiginde islenir (bkz. o dosyanin basindaki aciklama).
     confidence: partial/research_needed olan girisler BU SCRIPT TARAFINDAN
     ATLANIR - sadece dokumantasyon/ileride-isleme-icin kayit olarak durur.

Her iki turde de deger (oy/katilim/vs.) DEGISTIRILMEZ, sadece hangi
poligonla eslendigi (geomId alani) degisir - gercek, zaten dogrulanmis oy
sayilarinin GORSEL OLARAK dogru (tarihsel) alanda gosterilmesini saglar.

Bir eski ilce (orn. Umraniye) BIRDEN FAZLA kaynaktan parca alabilir (hem
Cekmekoy'un TAMAMINDAN hem Atasehir'in BAZI mahallelerinden) - script butun
katkilari TEK bir birlestirme islemine toplar (iki ayri/celisen sentetik
poligon URETMEZ).

Kullanim:
  python3 scripts/pipelines/historical_geo/apply_verified_district_merges.py

Gereksinim: sadece geometri URETIMI icin shapely+pyyaml gerekir (bir kerelik,
dev-time). Sentetik id'ler/geometri bir kere URETILIP diske YAZILDIGI icin
build.py/CI hicbir zaman bu bagimliliklara ihtiyac duymaz.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

GEO_NORM = ROOT / "geo" / "normalized" / "turkiye_ilce_sinirlari.geojson"
MAHALLE_GEO = ROOT / "geo" / "normalized" / "mahalle_geo.json"
HIST_GEO = ROOT / "geo" / "historical" / "turkiye_ilce_sinirlari_hist_splits.geojson"
DISTRICT_SPLITS = ROOT / "geo" / "historical" / "district_splits.json"
MAHALLE_MERGES_YAML = ROOT / "geo" / "historical" / "district_mahalle_merges.yaml"

# Sentetik id onekleri (ornek: "HIST-Antalya-Merkez") il ADINA gore uretiliyor,
# plakaya gore degil - bu yuzden plaka->il-adi (ascii, bosluksuz) eslemesi
# gerekiyor. 2023 genel secimi (her zaman TUM 81 ili iceren, guncel/stabil bir
# kaynak) kullanilir - secim SONUCU degil, sadece "iller" listesindeki il adi
# icin.
def _ascii_il_adi(ad):
    return (ad.replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g")
            .replace("Ü", "U").replace("ü", "u").replace("Ş", "S").replace("ş", "s")
            .replace("Ö", "O").replace("ö", "o").replace("Ç", "C").replace("ç", "c")
            .replace(" ", ""))


_IL_ADI_BY_PLAKA = None


def il_adi_ascii(plaka):
    global _IL_ADI_BY_PLAKA
    if _IL_ADI_BY_PLAKA is None:
        ref = json.loads((ROOT / "data" / "normalized" / "elections" / "genel" / "2023.json").read_text(encoding="utf-8"))
        _IL_ADI_BY_PLAKA = {i["plaka"]: i["ad"] for i in ref["iller"]}
    return _ascii_il_adi(_IL_ADI_BY_PLAKA[plaka])

# ---------------- tek-ebeveynli, basit vakalar (kanun + coklu kaynak dogrulamasi) ----------------
VERIFIED_MERGES = [
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-014",  # Buyukcekmece
        "whole_child_geomids": ["TR-D-34-012"],  # Beylikduzu (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Buyukcekmece",
        "split_year": 2008,
        # 1991/1995-2007: 2008-oncesi TEK Istanbul genel secimleri ilce-duzeyinde
        # veri iceriyor (bkz. audit_district_coverage.py) - Beylikduzu'nun alani
        # bu yillarda da Buyukcekmece'nin satirina dahildi, ayni duzeltme gecerli.
        # 1992-2008 (1994yerel ... 2007): build_istanbul_1992_2008.py
        "affected_years": ["1991"],
    },
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-037",  # Umraniye
        "whole_child_geomids": ["TR-D-34-016"],  # Cekmekoy (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Umraniye",
        "split_year": 2008,
        # 1992-2008 (1994yerel ... 2007): build_istanbul_1992_2008.py
        "affected_years": ["1991"],
    },
    # --- 1992 dalgasi (3806 sayili Kanun, 27 Mayis 1992 kabul, 3 Haziran 1992
    # Mukerrer Resmi Gazete Sayi 21247 - "Onuc Ilce ve Iki Il Kurulmasi Hakkinda
    # Kanun") - 2008'den TAMAMEN AYRI, cok daha eski bir dalga. Istanbul'da 7
    # ilce kurdu: Avcilar, Bagcilar, Bahcelievler, Gungoren, Maltepe,
    # Sultanbeyli, Tuzla (Esenler bu kanunda YOK, farkli/arastirilmamis bir
    # kaynaktan). Kanunun mahalle-duzeyi ekli listelerine mevzuat.gov.tr/TBMM
    # eski-kanun arsivi uzerinden erisilemedi (SSL/erisim sorunu, TBMM'nin
    # guncel sistemi sadece 2006 sonrasini kapsiyor) - bunun yerine HER
    # ilcenin KENDI RESMI kaymakamlik tarihce sayfasi (Icisleri Bakanligi
    # tashra teskilati, birincil/resmi kurum kaynagi) kullanildi, "whole
    # child" modeliyle (Beylikduzu/Cekmekoy ile ayni desen - TUM modern ilce
    # tek bir eski ebeveynden geldi, mahalle-duzeyi bolunme YOK):
    #   - Bagcilar/Bahcelievler/Gungoren <- Bakirkoy (bagcilar.gov.tr/tarihce,
    #     maltepe.gov.tr/tarihce ile capraz dogrulanan ayni-kanun referansi)
    #   - Maltepe/Sultanbeyli <- Kartal (maltepe.gov.tr/tarihce: "3 Haziran
    #     1992 tarih ve 21247 sayili Resmi Gazete"; sultanbeyli.gov.tr/ilce-tarihi)
    #   - Avcilar <- Kucukcekmece (avcilar.gov.tr/tarihi - 9/10 mahalle GUNCEL
    #     mahalle_geo.json ile tam eslesti, "Mustafa Kemal Pasa" adli 10.
    #     mahalle artik yok/yeniden adlandirilmis ama bu bir GUNCEL poligonu
    #     etkilemiyor - 9/9 guncel Avcilar mahallesi kaynakta var)
    #   - Tuzla <- Pendik (tuzla.gov.tr/tuzlamizin-tarihcesi: "1987'de Pendik
    #     ilcesine baglanmis, 1992'de... Pendik ilcesinden ayrilarak mustakil
    #     ilce yapildi" - Tuzla'nin 1987 ONCESI Kartal'a bagliyken 1987'de
    #     PENDIK'e gectigini de belirtiyor, yani 1992 ANINDAKI dogrudan
    #     ebeveyni Pendik'tir, Kartal degil)
    # Kartal icin bu, Atasehir/Sancaktepe'nin (2008, YAML) YANINDA UCUNCU bir
    # katki - script farkli kaynaklardan gelen katkilari otomatik birlestirir
    # (gather_contributions), tek bir HIST-Istanbul-Kartal poligonu uretir.
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-007",  # Bakirkoy
        "whole_child_geomids": ["TR-D-34-005", "TR-D-34-006", "TR-D-34-022"],  # Bagcilar, Bahcelievler, Gungoren (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Bakirkoy",
        "split_year": 1992,
        "affected_years": ["1991", "1984yerel", "1989yerel"],
    },
    # DIKKAT - Kartal ozel durumu: Kartal HEM 2008 dalgasinin (Atasehir'in 1
    # mahallesi + Sancaktepe'nin 6 mahallesi, YAML'daki "HIST-Istanbul-Kartal"
    # sentetigine gider, affected_years=1994yerel/1999yerel/2004yerel/1995/1999/
    # 2002/2007 - bkz. YAML'daki per-source "affected_years_override") HEM DE
    # 1992 dalgasinin (Maltepe/Sultanbeyli) kaynagi. Bu ikisini AYNI sentetige
    # (HIST-Istanbul-Kartal) koymak YANLIS olurdu: 1995-2007/1994-2004'te
    # Maltepe/Sultanbeyli'nin KENDI gercek veri satiri VAR (1992'de zaten
    # ayrildilar) - eger HIST-Istanbul-Kartal o yillarda da Maltepe/Sultanbeyli'yi
    # icerse, o alan HEM kendi gercek satiriyla HEM bu genis poligonla iki kez
    # cizilir (dogrulandi: shapely ile %100 cakisma olcu ldu, deneme surumunde
    # yakalandi). Cozum: UC AYRI sentetik, uc farkli veri-durumuna gore:
    #  - "HIST-Istanbul-Kartal" (asagida, YAML uzerinden): 1994yerel/1999yerel/
    #    2004yerel/1995/1999/2002/2007 icin - sadece 2008 dalgasi (Atasehir+
    #    Sancaktepe parcalari), Maltepe/Sultanbeyli HARIC (kendi gercek
    #    satirlari var, cakismasin diye).
    #  - "HIST-Istanbul-Kartal1991" (hemen asagida): SADECE "1991" genel icin -
    #    o yil Kadikoy/Uskudar/Umraniye'nin KENDI satirlari da var (ayrica
    #    kendi HIST-*'lerine donuyor), o yuzden Atasehir'in Ferhatpasa'si +
    #    Sancaktepe'nin 6 mahallesini de GUVENLE icerebilir (cakisma yok).
    #  - "HIST-Istanbul-Kartal8489" (daha asagida): 1984yerel/1989yerel icin -
    #    bu cok seyrek yillarda Atasehir/Sancaktepe'nin genisletme mekanizmasi
    #    HIC calismiyor (affected_years'larinda yok), yani Atasehir(003)/
    #    Sancaktepe(029) HICBIR sekilde gizlenmiyor - bu yuzden SADECE Kartal+
    #    Maltepe+Sultanbeyli (Atasehir/Sancaktepe parcasi OLMADAN), o iki
    #    ilcenin geri kalani bu yillarda durustce "veri yok" kalir.
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-025",  # Kartal
        "whole_child_geomids": ["TR-D-34-027", "TR-D-34-032"],  # Maltepe, Sultanbeyli (TAMAMI)
        "mahalle_pieces": [
            ("TR-D-34-003", ["FERHATPAŞA MAH."]),  # Atasehir'in Kartal-kaynakli mahallesi (bkz. YAML atasehir girisi)
            ("TR-D-34-029", [  # Sancaktepe'nin Kartal-kaynakli 6 mahallesi (bkz. YAML sancaktepe girisi)
                "ABDURRAHMANGAZİ MAH.", "AKPINAR MAH.", "OSMANGAZİ MAH.",
                "VEYSEL KARANİ MAH.", "EYÜP SULTAN MAH.", "FATİH MAH.",
            ]),
        ],
        "synthetic_id": "HIST-Istanbul-Kartal1991",
        "split_year": 1992,
        # SADECE "1991" - 1984yerel/1989yerel'de DEGIL (asagidaki notu oku).
        "affected_years": ["1991"],
    },
    # 1984yerel/1989yerel icin UCUNCU bir varyant gerekiyor: bu yillarda
    # Kadikoy/Uskudar KENDI satirlariyla VAR ama Atasehir/Sancaktepe'nin
    # genisletme mekanizmasi bu yillara HIC UYGULANMIYOR (Atasehir/Sancaktepe
    # YAML girislerinin affected_years'i 1984yerel/1989yerel icermiyor) - yani
    # Atasehir(003)/Sancaktepe(029)'nin TAM modern sekli HICBIR sekilde
    # gizlenmiyor o yillarda. Yukaridaki "HIST-Istanbul-Kartal1991" (Ferhatpasa +
    # Sancaktepe'nin 6 mahallesini de iceren) bu yillara uygulansaydi, o kucuk
    # parca HEM kendi (gizlenmemis) Atasehir/Sancaktepe ana hatlarinin icinde
    # HEM bu genis poligonda cizilir - dogrulama testi (artik yil-duyarli)
    # tam da bunu yakaladi. Cozum: 1984yerel/1989yerel icin SADECE Kartal +
    # Maltepe + Sultanbeyli (Atasehir/Sancaktepe parcasi OLMADAN) - o iki
    # ilcenin GERCEK (Kartal-kaynakli olmayan) alani bu yillarda zaten "veri
    # yok" olarak durur, bu DURUST bir bosluk (Kadikoy/Uskudar/Umraniye'nin
    # KENDI 1984/1989 verisi Atasehir/Sancaktepe'ye hic genisletilmedigi icin).
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-025",  # Kartal
        "whole_child_geomids": ["TR-D-34-027", "TR-D-34-032"],  # Maltepe, Sultanbeyli (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Kartal8489",
        "split_year": 1992,
        "affected_years": ["1984yerel", "1989yerel"],
    },
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-026",  # Kucukcekmece
        "whole_child_geomids": ["TR-D-34-004"],  # Avcilar (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Kucukcekmece",
        "split_year": 1992,
        "affected_years": ["1991", "1989yerel"],  # Kucukcekmece 1984yerel'de henuz yok
    },
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-028",  # Pendik
        "whole_child_geomids": ["TR-D-34-036"],  # Tuzla (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Pendik",
        "split_year": 1992,
        "affected_years": ["1991", "1989yerel"],  # Pendik 1984yerel'de henuz yok
    },

    # ================= IZMIR (plaka 35) =================
    # Ayni desen: Karabaglar/Bayrakli 2008 (5747 sayili Kanun), Gaziemir/
    # Narlidere/Balcova/Guzelbahce/Cigli 1992 (3806 sayili Kanun - AYNI
    # kanun Istanbul'daki 1992 dalgasiyla, İzmir'de 5 ilce kuruyor - Guzelbahce
    # kisa sureli "Narlibahce" birlesimi uzerinden, 1993'te 3949 sayili
    # kanunla ayri ilce oldu ama bu 1991/1989 icin ONEMSIZ - o tarihte zaten
    # hepsi Konak'in bir parcasiydi), Beydag/Buca/Menderes 1987-88 (ayri
    # kucuk kanunlar). Kaynaklar: resmi kaymakamlik tarihce sayfalari
    # (karabaglar.gov.tr, buca.gov.tr, menderes.gov.tr, guzelbahce.gov.tr,
    # izgazete.net'in Konak/Karabaglar/Balcova tarihce yazilari - kaymakamlik
    # sayfalariyla capraz dogrulanan gazete kaynaklari) + izgazete.net'in
    # Buca/Menderes/Beydag yazilari (kanun numaralariyla).
    #
    # Konak, UC farkli donem icin UC ayri sentetik gerektiriyor (Kartal'daki
    # AYNI sorun - bkz. o yorumlar): "Konak" (sadece 2008: Karabaglar,
    # 1994yerel+/1995+ icin), "Konak1991" (1992+2008: Karabaglar+Gaziemir+
    # Narlidere+Balcova+Guzelbahce, "1991" + "1989yerel" icin - o yillarda
    # Buca/Menderes'in KENDI satiri zaten var), "Konak84" (TUMU: +Buca+
    # Menderes, SADECE "1984yerel" icin - o yil Buca/Menderes de henuz yok).
    {
        "plaka": 35,
        "old_district_geomid": "TR-D-35-021",  # Konak
        "whole_child_geomids": ["TR-D-35-015"],  # Karabaglar (TAMAMI)
        "synthetic_id": "HIST-Izmir-Konak",
        "split_year": 2008,
        "affected_years": ["1994yerel", "1999yerel", "2004yerel", "1995", "1999", "2002", "2007"],
    },
    {
        "plaka": 35,
        "old_district_geomid": "TR-D-35-021",  # Konak
        "whole_child_geomids": ["TR-D-35-015", "TR-D-35-013", "TR-D-35-024", "TR-D-35-002", "TR-D-35-014"],
        # Karabaglar, Gaziemir, Narlidere, Balcova, Guzelbahce (TAMAMI)
        "synthetic_id": "HIST-Izmir-Konak1991",
        "split_year": 1992,
        "affected_years": ["1991", "1989yerel"],
    },
    {
        "plaka": 35,
        "old_district_geomid": "TR-D-35-021",  # Konak
        "whole_child_geomids": ["TR-D-35-015", "TR-D-35-013", "TR-D-35-024", "TR-D-35-002", "TR-D-35-014",
                                 "TR-D-35-008", "TR-D-35-022"],  # + Buca, Menderes (TAMAMI)
        "synthetic_id": "HIST-Izmir-Konak84",
        "split_year": 1987,
        "affected_years": ["1984yerel"],
    },
    # Karsiyaka: IKI donem - "Karsiyaka" (sadece 2008: Bayrakli, 1994yerel+/
    # 1995+ icin), "Karsiyaka1991" (1992+2008: Bayrakli+Cigli, "1991" +
    # "1989yerel" + "1984yerel" icin - Cigli'nin durumu 1984'te de aynı,
    # Konak'in aksine burada UCUNCU bir varyanta gerek yok).
    {
        "plaka": 35,
        "old_district_geomid": "TR-D-35-017",  # Karsiyaka
        "whole_child_geomids": ["TR-D-35-004"],  # Bayrakli (TAMAMI)
        "synthetic_id": "HIST-Izmir-Karsiyaka",
        "split_year": 2008,
        "affected_years": ["1994yerel", "1999yerel", "2004yerel", "1995", "1999", "2002", "2007"],
    },
    {
        "plaka": 35,
        "old_district_geomid": "TR-D-35-017",  # Karsiyaka
        "whole_child_geomids": ["TR-D-35-004", "TR-D-35-010"],  # Bayrakli, Cigli (TAMAMI)
        "synthetic_id": "HIST-Izmir-Karsiyaka1991",
        "split_year": 1992,
        "affected_years": ["1991", "1989yerel", "1984yerel"],
    },
    {
        "plaka": 35,
        "old_district_geomid": "TR-D-35-025",  # Odemis
        "whole_child_geomids": ["TR-D-35-006"],  # Beydag (TAMAMI)
        "synthetic_id": "HIST-Izmir-Odemis",
        "split_year": 1987,
        "affected_years": ["1984yerel"],
    },
]


def load_yaml_verified_sources():
    """district_mahalle_merges.yaml'daki confidence:verified girislerini,
    VERIFIED_MERGES ile AYNI ic-modele (old_district_geomid -> katkilar)
    donusturur. pyyaml yoksa bos liste doner (script geometri adimini
    atlar, data-patch adimi zaten calisir durumdaki HIST-* id'lere dokunmaz)."""
    try:
        import yaml
    except ImportError:
        print("UYARI: pyyaml kurulu degil - district_mahalle_merges.yaml okunamadi "
              "(mahalle-bazli birlesimler atlandi, sadece VERIFIED_MERGES islendi). "
              "`pip install pyyaml` ile kurup tekrar calistirabilirsiniz.")
        return []

    doc = yaml.safe_load(MAHALLE_MERGES_YAML.read_text(encoding="utf-8"))
    out = []
    for group_key, group in doc.items():
        split_year = group.get("split_year")
        affected_years = group.get("affected_years", [])
        plaka = group.get("plaka")
        if plaka is None:
            continue  # plaka alani olmayan grup - eski/gecis formati, atla
        il_prefix = il_adi_ascii(plaka)
        for district_key, entry in group.items():
            # "verified": kanun metninden birebir isim eslemesi. "verified_full_coverage_inferred":
            # yeni ilcenin TUM mahalleleri kalintisiz atanmis (delik yok) ama bir kismi yapisal/
            # cografi cikarimla (bkz. YAML'daki tanim + her girisin geometry_basis alani) - ikisi
            # de "delik birakma" kisitlamasina uyuyor, sadece metot farkli (durustluk icin etiket
            # ayri tutuluyor).
            if not isinstance(entry, dict) or entry.get("confidence") not in ("verified", "verified_full_coverage_inferred"):
                continue
            new_geomid = entry["new_district_geomid"]
            for src in entry["sources"]:
                name_ascii = _ascii_il_adi(src["old_district_name"])
                # bir SOURCE (orn. Kartal), AYNI eski ilcenin BASKA bir donemde
                # (orn. 1992 dalgasi) FARKLI bir tarihsel genislige sahip
                # olmasi durumunda, o TEK source icin affected_years/synthetic_id
                # override edilebilir (entry/group varsayilanindan farkli) -
                # bkz. Kartal: Atasehir/Sancaktepe (2008) katkisi normal
                # "HIST-Istanbul-Kartal"a gider, ama 1991/1984/1989 icin
                # AYRI (daha genis, Maltepe/Sultanbeyli'yi de iceren)
                # "HIST-Istanbul-Kartal1991" gerekir - cunku o yillarda
                # Maltepe/Sultanbeyli'nin KENDI gercek veri satiri YOK, ama
                # 1994yerel+ icin VAR (cakisma/cift-cizim onlenir).
                years = src.get("affected_years_override", entry.get("affected_years", affected_years))
                if not years:
                    continue  # bu kaynak baska bir betikle isleniyor (bkz. YAML'daki not)
                out.append({
                    "old_district_geomid": src["old_district_geomid"],
                    "mahalle_source_geomid": new_geomid,  # hangi (yeni) ilcenin mahalle_geo'sundan cekilecek
                    "mahalle_names": src["mahalle_names"],
                    "fully_covered_new_geomid": new_geomid,  # bu id, TUM mahalleleri baska ebeveynlere dagitildigi icin ayrica "veri yok" gosterilmemeli
                    "synthetic_id": src.get("synthetic_id_override") or f"HIST-{il_prefix}-{name_ascii}",
                    "split_year": src.get("split_year_override", split_year),
                    "affected_years": years,
                    "plaka": plaka,
                })
    return out


def gather_contributions():
    """(old_district_geomid, synthetic_id) -> {synthetic_id, split_year, affected_years,
    plaka, whole_child_geomids: set, mahalle_pieces: [(source_geomid, [names])], hide: set}

    Anahtar SADECE old_district_geomid DEGIL, (old, synthetic_id) cifti: ayni eski
    ilcenin (orn. Kartal) FARKLI donemler icin FARKLI genislikte iki ayri sentetik
    poligonu olabilir (orn. HIST-Istanbul-Kartal = sadece 2008 dalgasi, HIST-
    Istanbul-Kartal1991 = 2008+1992 dalgalarinin ikisi de - bkz. Kartal'daki yorum)."""
    by_old = {}

    def ensure(m):
        old = m["old_district_geomid"]
        synthetic_id = m.get("synthetic_id") or f"HIST-{il_adi_ascii(m['plaka'])}-{old.split('-')[-1]}"
        key = (old, synthetic_id)
        if key not in by_old:
            by_old[key] = {
                "synthetic_id": synthetic_id,
                "split_year": m["split_year"],
                "affected_years": list(m["affected_years"]),
                "plaka": m["plaka"],
                "whole_child_geomids": set(),
                "mahalle_pieces": [],
                "hide": {old},  # ebeveynin KENDI eski modern sekli her zaman gizlenir (artik sentetige esleniyor)
            }
        else:
            # ayni (old, synthetic_id) icin ikinci bir katki (orn. birden fazla
            # VERIFIED_MERGES/YAML girisi ayni sentetige besleniyor) - affected_years
            # birlestir (tekrar etmeyen), digerleri zaten ayni olmali.
            for y in m["affected_years"]:
                if y not in by_old[key]["affected_years"]:
                    by_old[key]["affected_years"].append(y)
        return by_old[key]

    for m in VERIFIED_MERGES:
        c = ensure(m)
        c["whole_child_geomids"].update(m["whole_child_geomids"])
        c["hide"].update(m["whole_child_geomids"])
        for source_geomid, mahalle_names in m.get("mahalle_pieces", []):
            c["mahalle_pieces"].append((source_geomid, mahalle_names))
            # NOT: source_geomid (orn. Atasehir/Sancaktepe'nin kendi geomId'si)
            # BURADA "hide"e eklenmiyor - o ilcenin TUM guncel sekli baska bir
            # (kendi) HIST girisi tarafindan zaten yonetiliyor, burada sadece
            # BIR KAC mahallesi odunc alinip bu poligona ekleniyor.

    for m in load_yaml_verified_sources():
        c = ensure(m)
        c["mahalle_pieces"].append((m["mahalle_source_geomid"], m["mahalle_names"]))
        c["hide"].add(m["fully_covered_new_geomid"])

    return by_old


def ensure_district_splits_json(contributions):
    """hideIds/splitYear/syntheticId kayitlarini gunceller - shapely GEREKTIRMEZ."""
    splits = json.loads(DISTRICT_SPLITS.read_text(encoding="utf-8"))
    changed = False
    for (old_geomid, _synthetic_id), c in contributions.items():
        plaka_key = str(c["plaka"])
        splits.setdefault(plaka_key, [])
        want_hide_ids = sorted(c["hide"])
        existing_entry = next((e for e in splits[plaka_key] if e["syntheticId"] == c["synthetic_id"]), None)
        if existing_entry is None:
            splits[plaka_key].append({
                "hideIds": want_hide_ids,
                "splitYear": c["split_year"],
                "syntheticId": c["synthetic_id"],
            })
            changed = True
            print(f"eklendi (district_splits.json): {c['synthetic_id']} -> {want_hide_ids}")
        elif sorted(existing_entry["hideIds"]) != want_hide_ids:
            existing_entry["hideIds"] = want_hide_ids
            changed = True
            print(f"duzeltildi (hideIds guncellendi): {c['synthetic_id']} -> {want_hide_ids}")
    if changed:
        DISTRICT_SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")
        print("yazildi:", DISTRICT_SPLITS)


def ensure_geometry(contributions):
    try:
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union
    except ImportError:
        print("UYARI: shapely kurulu degil - sentetik poligon uretimi/guncellemesi "
              "atlandi (zaten uretilmisse dosya degismeden kalir). `pip install "
              "shapely` ile kurup tekrar calistirabilirsiniz.")
        return

    modern = json.loads(GEO_NORM.read_text(encoding="utf-8"))
    by_id = {f["properties"]["id"]: f for f in modern["features"]}
    mahalle_geo = json.loads(MAHALLE_GEO.read_text(encoding="utf-8"))

    hist_geo = json.loads(HIST_GEO.read_text(encoding="utf-8"))
    features_by_id = {f["properties"]["id"]: f for f in hist_geo["features"]}

    def clean(geom):
        # geo/normalized/turkiye_ilce_sinirlari.geojson'daki bazi poligonlarda
        # (orn. Tuzla, TR-D-34-036) daha once hic unary_union'a girmedikleri
        # icin hic tetiklenmemis kucuk self-intersection'lar var (GEOS
        # TopologyException). buffer(0) bu tur gecersizlikleri, GORUNUR sekli
        # DEGISTIRMEDEN (sadece topolojiyi) duzelten standart/guvenli bir
        # shapely idiyomu - kaynak dosya BURADA degistirilmiyor, sadece bu
        # script'in kendi union hesabina giren KOPYA temizleniyor.
        return geom if geom.is_valid else geom.buffer(0)

    changed = False
    for (old_geomid, _synthetic_id), c in contributions.items():
        geoms = [clean(shape(by_id[old_geomid]["geometry"]))]
        for child_id in sorted(c["whole_child_geomids"]):
            geoms.append(clean(shape(by_id[child_id]["geometry"])))
        for source_geomid, mahalle_names in c["mahalle_pieces"]:
            rows = mahalle_geo.get(source_geomid, {})
            by_name = {info["ad"]: info for info in rows.values()}
            for name in mahalle_names:
                info = by_name.get(name)
                if info is None:
                    raise SystemExit(
                        f"HATA: '{name}' mahallesi {source_geomid} icinde bulunamadi "
                        f"(district_mahalle_merges.yaml'daki isim mahalle_geo.json ile "
                        f"eslesmiyor - Turkce karakter/bosluk farki olabilir)."
                    )
                geoms.append(clean(shape(info["geometry"])))

        merged = unary_union(geoms)
        new_feature = {
            "type": "Feature",
            "properties": {"id": c["synthetic_id"], "plaka": c["plaka"]},
            "geometry": mapping(merged),
        }
        old_feature = features_by_id.get(c["synthetic_id"])
        # idempotent: ayni WKT/koordinat setiyle yeniden yazip gereksiz git-diff
        # uretmemek icin, GERCEKTEN farkliysa guncelle.
        if old_feature is None or json.dumps(old_feature["geometry"], sort_keys=True) != json.dumps(new_feature["geometry"], sort_keys=True):
            features_by_id[c["synthetic_id"]] = new_feature
            changed = True
            print(f"guncellendi/eklendi (geometri): {c['synthetic_id']} "
                  f"({len(c['whole_child_geomids'])} butun cocuk + "
                  f"{sum(len(n) for _, n in c['mahalle_pieces'])} mahalle parcasi)")

    if changed:
        hist_geo["features"] = sorted(features_by_id.values(), key=lambda f: f["properties"]["id"])
        HIST_GEO.write_text(json.dumps(hist_geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("yazildi:", HIST_GEO)


def patch_data_rows(contributions):
    by_year = {}
    for (old_geomid, _synthetic_id), c in contributions.items():
        for year in c["affected_years"]:
            by_year.setdefault(year, []).append((old_geomid, c["synthetic_id"]))

    for year, patches in by_year.items():
        secim = load_election(year)
        changed = []
        # ayni yil icin ayni eski ilcenin IKI FARKLI sentetige atanmasi
        # (orn. hem HIST-Istanbul-Kartal hem HIST-Istanbul-Kartal1991) sessizce
        # BIRINI kaybeder (dict overwrite) - bu, affected_years'larin YANLISLIKLA
        # cakistigi bir konfigurasyon hatasi, hemen durdurulmali.
        seen = {}
        for old_geomid, synthetic_id in patches:
            if old_geomid in seen and seen[old_geomid] != synthetic_id:
                raise SystemExit(
                    f"HATA: {year} icin {old_geomid}, iki farkli sentetige "
                    f"atanmaya calisiliyor ({seen[old_geomid]} ve {synthetic_id}) - "
                    f"affected_years'lar yanlislikla cakisiyor olmali."
                )
            seen[old_geomid] = synthetic_id
        patch_map = dict(patches)
        # NOT: plaka'ya gore AYRICA filtrelemeye gerek yok - geomId'ler zaten
        # "TR-D-<plaka>-<sira>" seklinde plaka'yi kendi icinde tasiyor, iki
        # farkli ilin geomId'si asla cakismaz (eskiden burada "plaka==34"
        # sabit kontrolu vardi - Istanbul-disi katkilarin SESSIZCE atlanmasina
        # neden oluyordu, Izmir eklenirken yakalanip duzeltildi).
        for d in secim["ilceler"]:
            if d.get("geomId") in patch_map:
                old = d["geomId"]
                d["geomId"] = patch_map[old]
                changed.append((d["ad"], old, d["geomId"]))
        if changed:
            save_election(year, secim)
            print(f"{year}: guncellendi -> {changed}")
        else:
            print(f"{year}: degisiklik yok (zaten uygulanmis veya eslesen satir yok)")


def main():
    contributions = gather_contributions()
    ensure_geometry(contributions)
    ensure_district_splits_json(contributions)
    patch_data_rows(contributions)


if __name__ == "__main__":
    main()
