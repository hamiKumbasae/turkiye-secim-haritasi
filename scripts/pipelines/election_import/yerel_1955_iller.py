"""
1955 yerel: 1954'te kurulan Nevşehir, Adıyaman ve Sakarya illerini ve Kırşehir'in il olmadığını
seçim kaydına yansıtır.

Sorun: 1955 kaydı (data/normalized/elections/yerel/1955yerel.json) 1954 öncesi il listesiyle
kurulmuştu: 13 Kasım 1955'te var olan Nevşehir (50), Adıyaman (2) ve Sakarya (54) yoktu; 30.06.1954'te
(6429) kaldırılıp Nevşehir'e bağlanan Kırşehir ise il satırı olarak duruyordu. O "Kırşehir" satırı
aslında Nevşehir sayfasındaki Kırşehir ilçesinin sonucuydu. Bu illerin ilçe sonuçları (yalnız kazanan
parti, 1955'te başkanı meclis seçiyordu) depodaki ayrıştırılmış Vikipedi katmanında var
(data/kaynaklar/wikipedia/yerel/1955yerel.json) ama kayda aktarılmamıştı.

Yapılan (idempotent):
  - il satırı 40 (Kırşehir) kaldırılır; Kırşehir, Nevşehir'in ilçesi olarak eklenir.
  - Nevşehir, Adıyaman, Sakarya il satırları eklenir. İl satırı il merkezi belediyesidir: Nevşehir
    "Merkez", Sakarya "Adapazarı" kaydının kazananı; Adıyaman merkezinin sonucu kaynakta yok.
  - Bu üç ilin ilçe satırları (sadeceKazanan) bugünkü ilçe kimlikleriyle eklenir; sonradan kurulan
    ilçeler apply_idari_merges.py ile bu satırlara katılır.
  - Kaman (Ankara) ve Çiçekdağı (Yozgat) satırları zaten 1955 bağlılığında.

Kullanım (tarihsel_sinirlari_uret.py başta çağırır):
  python3 scripts/pipelines/election_import/yerel_1955_iller.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

KATMAN = ROOT / "data/kaynaklar/wikipedia/yerel/1955yerel.json"
ISARET = "yeniIl1955"
ILLER = {50: "Nevşehir", 2: "Adıyaman", 54: "Sakarya"}
IL_MERKEZI = {50: "Merkez", 54: "Adapazarı"}
# (plaka, kaynaktaki ad) -> bugünkü ilçe kimliği
GEOM = {
    (50, "Merkez"): "TR-D-50-007", (50, "Avanos"): "TR-D-50-002", (50, "Gülşehir"): "TR-D-50-004",
    (50, "Hacıbektaş"): "TR-D-50-005", (50, "Kozaklı"): "TR-D-50-006", (50, "Ürgüp"): "TR-D-50-008",
    (50, "Kırşehir"): "TR-D-40-006", (50, "Mucur"): "TR-D-40-007",
    (2, "Besni"): "TR-D-02-002", (2, "Çelikhan"): "TR-D-02-003", (2, "Gerger"): "TR-D-02-004",
    (2, "Kahta"): "TR-D-02-006",
    (54, "Adapazarı"): "TR-D-54-001", (54, "Akyazı"): "TR-D-54-002", (54, "Geyve"): "TR-D-54-006",
    (54, "Hendek"): "TR-D-54-007", (54, "Karasu"): "TR-D-54-009",
}
NOT_1955 = ("1955'te belediye başkanı halk tarafından doğrudan seçilmiyordu; seçmen parti listeleriyle "
            "belediye meclisi üyelerini seçiyor, meclis de kendi içinden başkanı seçiyordu.")


def main():
    rec = load_election("1955yerel")
    kayitlar = [k for k in json.loads(KATMAN.read_text(encoding="utf-8"))["kayitlar"]
                if k.get("tur") == "ilce" and k.get("plaka") in ILLER]
    rec["iller"] = [i for i in rec["iller"] if i["plaka"] != 40 and not i.get(ISARET)]
    rec["ilceler"] = [r for r in rec["ilceler"] if not r.get(ISARET)]
    var = {(r["plaka"], r["ad"]) for r in rec["ilceler"]}
    eklenen = 0
    for k in kayitlar:
        anahtar = (k["plaka"], k["ad"])
        if anahtar in var:
            raise SystemExit(f"{anahtar} zaten var")
        url = f"https://tr.wikipedia.org/w/index.php?oldid={k['revid']}"
        rec["ilceler"].append({
            "ad": k["ad"], "plaka": k["plaka"], "geomId": GEOM[anahtar], "gecerliOy": None, "katilim": None,
            "secmen": None, "sandik": None, "kazanan": k["kazanan"], "oy": {k["kazanan"]: {"oran": None, "oy": None}},
            "sadeceKazanan": True, "toplamVekil": 0, "vekil": {}, "kaynak_url": url,
            "kaynak": {"ana": "wikipedia", "kaynakKatmani": str(KATMAN.relative_to(ROOT)), "revid": k["revid"],
                       "sayfa": k["sayfa"]},
            ISARET: True,
        })
        eklenen += 1
    for plaka, ad in ILLER.items():
        ilceler = [k for k in kayitlar if k["plaka"] == plaka]
        merkez = next((k for k in ilceler if k["ad"] == IL_MERKEZI.get(plaka)), None)
        il = {"ad": ad, "plaka": plaka, "gecerliOy": None, "katilim": None, "secmen": None, "sandik": None,
              "ilceSayisi": len(ilceler), "toplamVekil": 0, "vekil": {},
              "kaynak_url": f"https://tr.wikipedia.org/w/index.php?oldid={ilceler[0]['revid']}", ISARET: True}
        if merkez:
            il.update({"kazanan": merkez["kazanan"], "oy": {merkez["kazanan"]: {"aday": None, "oran": None, "oy": None}},
                       "not": f"İl merkezi belediyesi ({merkez['ad']}): yalnız kazanan parti. " + NOT_1955})
        else:
            il.update({"kazanan": None, "oy": {},
                       "not": "İl merkezi belediyesinin sonucu kaynakta yok; ilçe sonuçları var. " + NOT_1955})
        rec["iller"].append(il)
    rec["iller"].sort(key=lambda i: i["plaka"])
    save_election("1955yerel", rec)
    print(f"1955yerel: {len(rec['iller'])} il, {eklenen} ilçe satırı eklendi")


if __name__ == "__main__":
    main()
