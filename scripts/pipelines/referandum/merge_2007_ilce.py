"""
parse_2007_ilce_pdfs.py'nin urettigi 81 il / 894 ilce kaydini
data/normalized/referandumlar.json'daki "2007referandum" girisine isler —
o girisin su ana kadar BOS olan 'ilceler' listesini doldurur (il kayitlarina
DOKUNMAZ, sadece ilceler ekler).

Kullanim:
  python3 merge_2007_ilce.py <parsed.json>
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

TURKCE_KUCUK = str.maketrans("İIŞÜÖÇĞ", "iışüöçğ")


def turkce_title(s: str) -> str:
    """Python'un varsayilan .title()/.capitalize()'i Turkce İ/I/Ş/Ç/Ğ/Ü/Ö'yu
    bozuyor (bkz. projede daha once 'BAşMAKçı' gibi kayitlar — bu script o
    hatayi TEKRARLAMAMAK icin ozel yazildi). Ilk harf buyuk (Turkce kurallara
    gore: I->i, İ kalır İ ise ilk harf İ->İ zaten doğru), geri kalan kucuk."""
    if not s:
        return s
    first, rest = s[0], s[1:]
    first_upper = first  # zaten buyuk harf (kaynak ALL-CAPS)
    rest_lower = rest.translate(TURKCE_KUCUK).lower()
    return first_upper + rest_lower


def main():
    parsed_path = pathlib.Path(sys.argv[1])
    parsed = json.loads(parsed_path.read_text(encoding="utf-8"))

    secim = load_election("2007referandum")

    il_by_plaka = {il["plaka"]: il for il in secim["iller"]}
    plaka_by_ad = {il["ad"]: il["plaka"] for il in secim["iller"]}
    # Mevcut 906 satırın oyları ve sonradan doğrulanmış tarihsel geometrileri
    # korunur. Ayrıştırmada atlanmış kaynak satırları eklenir; aynı ildeki
    # sayısal imza kimlik kontrolüdür, il sonucundan ilçe türetilmez.
    ilceler = list(secim["ilceler"])
    def imza(plaka, sandik, secmen, gecerli, evet, hayir):
        return (plaka, sandik, secmen, gecerli, evet, hayir)
    mevcut = {imza(r["plaka"], r.get("sandik"), r.get("secmen"), r.get("gecerliOy"),
                   r["oy"]["Evet"]["oy"], r["oy"]["Hayır"]["oy"]) for r in ilceler}
    eklenen = 0
    validation = []

    for il_adi, rows in parsed.items():
        plaka = plaka_by_ad.get(il_adi)
        if plaka is None:
            print(f"UYARI: '{il_adi}' için plaka bulunamadı, atlanıyor")
            continue
        for r in rows:
            gecerli = r["gecerli_oy"] or 0
            evet, hayir = r["evet"] or 0, r["hayir"] or 0
            if evet + hayir != gecerli:
                raise ValueError(f"{il_adi} {r['ilce_ADI']}: Evet + Hayır geçerli oya eşit değil")
            sig = imza(plaka, r["sandik"], r["kayitli_secmen"], gecerli, evet, hayir)
            if sig in mevcut:
                continue
            oran_evet = round(100 * evet / gecerli, 2) if gecerli else 0.0
            oran_hayir = round(100 * hayir / gecerli, 2) if gecerli else 0.0
            ilceler.append({
                "ad": turkce_title(r["ilce_ADI"]),
                "geomId": r["geomId"],
                "plaka": plaka,
                "sandik": r["sandik"],
                "secmen": r["kayitli_secmen"],
                "katilim": round(100 * r["katilan"] / r["kayitli_secmen"], 2) if r["kayitli_secmen"] else None,
                "gecerliOy": gecerli,
                "kazanan": "Evet" if evet >= hayir else "Hayır",
                "oy": {
                    "Evet": {"oy": evet, "oran": oran_evet},
                    "Hayır": {"oy": hayir, "oran": oran_hayir},
                },
                "toplamVekil": 0,
                "vekil": {},
                "kaynak": {"ana": "ysk", "dosya": "data/raw/ysk/referandum-2007-ilce/parsed.json",
                           "adKaynakta": r["ilce_ADI"], "esleme": "2007 genel seçim ilçe kimliği; yalnız geometri"},
            })
            mevcut.add(sig)
            eklenen += 1

    secim["ilceler"] = ilceler

    # dogrulama: il basina ilce toplami vs mevcut il kaydi (TAM esitlik
    # BEKLENMIYOR - 29 ilce eslesmedi, bkz. PROVENANCE.md - ama fark KUCUK olmali)
    by_plaka_sum = {}
    for row in ilceler:
        s = by_plaka_sum.setdefault(row["plaka"], {"evet": 0, "hayir": 0})
        s["evet"] += row["oy"]["Evet"]["oy"]
        s["hayir"] += row["oy"]["Hayır"]["oy"]
    for plaka, sums in sorted(by_plaka_sum.items()):
        il = il_by_plaka.get(plaka)
        if not il:
            continue
        il_evet = il["oy"]["Evet"]["oy"]
        il_hayir = il["oy"]["Hayır"]["oy"]
        diff_pct = abs(sums["evet"] - il_evet) / il_evet * 100 if il_evet else 0
        if diff_pct > 5:
            validation.append(f"plaka {plaka} ({il['ad']}): ilçe toplamı evet={sums['evet']} "
                               f"il kaydı evet={il_evet} (%{diff_pct:.1f} fark)")

    save_election("2007referandum", secim)
    print(f"{eklenen} yeni kaynak satırı; toplam {len(ilceler)} ilçe -> 2007referandum")
    if validation:
        print(f"\n{len(validation)} il için büyük fark (>%5, muhtemelen eksik 'Merkez' ilçesi olan büyükşehirler):")
        for v in validation:
            print(" ", v)


if __name__ == "__main__":
    main()
