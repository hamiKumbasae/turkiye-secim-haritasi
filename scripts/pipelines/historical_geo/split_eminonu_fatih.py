"""
Eminonu, digger yeni-ilce-kurulumu vakalarindan (Atasehir, Sancaktepe vb.)
FARKLI bir tarihsel degisiklik: 2008'de YENI bir ilce KURULMADI, var olan
bir ilce (Eminonu) TAMAMEN KALDIRILIP mahalleleriyle birlikte KOMSU bir
ilceye (Fatih) katildi (5747 sayili Kanun, Madde 2 Fikra 2 - "Eminonu
Belediyesinin tuzel kisiligi kaldirilarak mahalleleriyle birlikte Fatih
Belediyesine katilmistir", hicbir ekli-liste/kismi-mahalle ayrimi YOK, TUM
mahalleleriyle birlikte).

Bu yuzden apply_verified_district_merges.py'nin modeli (eski ebeveynin
GUNCEL sekli + emilen COCUGUN mahalleleri = birlesim) burada UYMUYOR: ne
"eski Eminonu" ne "eski Fatih" (Eminonu'suz) bugun AYRI bir modern ilce
olarak var - ikisi de modern Fatih'in (TR-D-34-020) 57 mahallesinin bir
ALT KUMESI. Ustelik 2007referandum'da Eminonu'nun KENDI oy kaydi hala ayri
duruyor (Fatih'in kaydindan farkli) - ikisini TEK bir birlesik poligonda
GOSTEREMEYIZ (biri digerini gizler), her ikisi de KENDI (parcali) tarihsel
poligonunu almali.

Kaynak: modern Fatih'in (TR-D-34-020) 33 mahallesi Eminonu'den geliyor
(Wikipedia + arastirma: Eminonu "33 mahalleden olusuyordu", bu 33 isim
modern Fatih listesiyle ISIM BAZINDA TAM (33/33, kalinti yok) eslesti -
bkz. asagidaki EMINONU_MAHALLE_ADLARI). Kalan 24 mahalle eski Fatih'in
KENDI (Eminonu'ye hic ait olmamis) mahalleleri.

Kullanim:
  python3 scripts/pipelines/historical_geo/split_eminonu_fatih.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
MAHALLE_GEO = ROOT / "geo" / "normalized" / "mahalle_geo.json"
HIST_GEO = ROOT / "geo" / "historical" / "turkiye_ilce_sinirlari_hist_splits.geojson"
DISTRICT_SPLITS = ROOT / "geo" / "historical" / "district_splits.json"

FATIH_GEOMID = "TR-D-34-020"

# Wikipedia + capraz kontrol: Eminonu "33 mahalleden" olusuyordu, bu liste
# modern Fatih'in 57 mahallesiyle ISIM BAZINDA (kisaltma/bosluk farklariyla)
# TAM eslesti - 33/33, kalinti yok.
EMINONU_MAHALLE_ADLARI = [
    "ALEMDAR MAH.", "BALABANAĞA MAH.", "BİNBİRDİREK MAH.", "BEYAZIT MAH.", "CANKURTARAN MAH.",
    "DEMİRTAŞ MAH.", "EMİN SİNAN MAH.", "HACI KADIN MAH.", "HOBYAR MAH.", "HOCA GIYASETTİN MAH.",
    "HOCAPAŞA MAH.", "KALENDERHANE MAH.", "KATİP KASIM MAH.", "KEMALPAŞA MAH.", "KÜÇÜK AYASOFYA MAH.",
    "MİMAR HAYRETTİN MAH.", "MİMAR KEMALETTİN MAH.", "MERCAN MAH.", "MESİHPAŞA MAH.", "MOLLA FENARİ MAH.",
    "MOLLA HÜSREV MAH.", "MUHSİNE HATUN MAH.", "NİŞANCA MAH.", "ŞEHSUVAR BEY MAH.", "RÜSTEMPAŞA MAH.",
    "SARAÇ İSHAK MAH.", "SARIDEMİR MAH.", "SÜLEYMANİYE MAH.", "SULTAN AHMET MAH.", "SURURİ MAH.",
    "TAHTAKALE MAH.", "TAYA HATUN MAH.", "YAVUZ SİNAN MAH.",
]


def main():
    try:
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union
    except ImportError:
        print("UYARI: shapely kurulu degil - atlaniyor. `pip install shapely` ile kurup tekrar calistirin.")
        return

    mahalle_geo = json.loads(MAHALLE_GEO.read_text(encoding="utf-8"))
    fatih_mahalleler = mahalle_geo.get(FATIH_GEOMID, {})
    by_name = {info["ad"]: info for info in fatih_mahalleler.values()}

    assert len(EMINONU_MAHALLE_ADLARI) == 33 and len(set(EMINONU_MAHALLE_ADLARI)) == 33
    missing = [n for n in EMINONU_MAHALLE_ADLARI if n not in by_name]
    if missing:
        raise SystemExit(f"HATA: Eminonu mahalleleri modern Fatih'te bulunamadi: {missing}")

    eminonu_geoms = [shape(by_name[n]["geometry"]) for n in EMINONU_MAHALLE_ADLARI]
    fatih_kalan_names = sorted(set(by_name) - set(EMINONU_MAHALLE_ADLARI))
    fatih_geoms = [shape(by_name[n]["geometry"]) for n in fatih_kalan_names]

    print(f"Eminonu: {len(eminonu_geoms)} mahalle, eski Fatih (kalan): {len(fatih_geoms)} mahalle "
          f"(toplam {len(eminonu_geoms)+len(fatih_geoms)}, modern Fatih'te {len(by_name)} var)")

    hist_geo = json.loads(HIST_GEO.read_text(encoding="utf-8"))
    features_by_id = {f["properties"]["id"]: f for f in hist_geo["features"]}

    for synthetic_id, geoms in [
        ("HIST-Istanbul-Eminonu", eminonu_geoms),
        ("HIST-Istanbul-Fatih", fatih_geoms),
    ]:
        merged = unary_union(geoms)
        new_feature = {
            "type": "Feature",
            "properties": {"id": synthetic_id, "plaka": 34},
            "geometry": mapping(merged),
        }
        old = features_by_id.get(synthetic_id)
        if old is None or json.dumps(old["geometry"], sort_keys=True) != json.dumps(new_feature["geometry"], sort_keys=True):
            features_by_id[synthetic_id] = new_feature
            print(f"guncellendi/eklendi (geometri): {synthetic_id}")

    hist_geo["features"] = sorted(features_by_id.values(), key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist_geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("yazildi:", HIST_GEO)

    splits = json.loads(DISTRICT_SPLITS.read_text(encoding="utf-8"))
    entries = splits.setdefault("34", [])
    # Ikisi de modern Fatih'in (TR-D-34-020) TAMAMINI "gizler" - modern sekli
    # artik hicbir veri satirinin dogrudan kullanmadigi bir "toplam" (hem
    # Eminonu hem eski-Fatih onun bir PARCASI), tek basina ayrica gri/no-data
    # katmaninda GORUNMEMELI.
    for synthetic_id in ("HIST-Istanbul-Eminonu", "HIST-Istanbul-Fatih"):
        want_hide = sorted({FATIH_GEOMID})
        existing = next((e for e in entries if e["syntheticId"] == synthetic_id), None)
        if existing is None:
            entries.append({"hideIds": want_hide, "splitYear": 2008, "syntheticId": synthetic_id})
            print(f"eklendi (district_splits.json): {synthetic_id} -> {want_hide}")
        elif sorted(existing["hideIds"]) != want_hide:
            existing["hideIds"] = want_hide
            print(f"duzeltildi: {synthetic_id} -> {want_hide}")
    DISTRICT_SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazildi:", DISTRICT_SPLITS)


if __name__ == "__main__":
    main()
