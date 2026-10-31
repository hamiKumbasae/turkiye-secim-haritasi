"""Classify the question bank into parameterised patterns -> eval/soru_kaliplari.yaml.

    python scripts/build_soru_kaliplari.py
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BANK = yaml.safe_load((ROOT / "eval" / "soru_bankasi.yaml").read_text(encoding="utf-8"))
W = {"yüksek": 3, "orta": 2, "düşük": 1}

J = "FROM oy o JOIN birim b ON b.id = o.birim_id JOIN secim s ON s.id = b.secim_id"
NAT = ("ROUND(100 * SUM(CASE WHEN o.aday_parti = {parti} THEN o.oy ELSE 0 END) / SUM(o.oy), 2) AS oran "
       + J + " WHERE s.kod = {secim} AND b.seviye IN ('il','yurtdisi')")

# (id, pattern text, slots, sql template, matcher)
P = [
    ("veri-yok-sandik-bolge", "{birim} için sandık / seçim bölgesi / ülke bazında sonuç",
     {"birim": "sandık | seçim bölgesi | yurt dışı ülke"}, None,
     lambda b: b["answerable"] == "no" and re.search(r"[Ss]andık|bölge|ülke|Gümrük|Yurt dışı|yurt dışı", b["reason"])),
    ("veri-yok-demografi-anket", "{grup} kime oy verdi / anketlerde kim önde",
     {"grup": "yaş | cinsiyet | etnik köken | eğitim | anket"}, None,
     lambda b: b["answerable"] == "no" and re.search(r"demograf|[Cc]insiyet|[Ee]tnik|[Aa]nket|profil|Kamuoyu|[İi]lk kez|geçişleri", b["reason"])),
    ("veri-yok-aday", "{secim}'de seçilen vekil / başkan adı, aday listesi, biyografi",
     {"secim": "seçim"}, None,
     lambda b: b["answerable"] == "no" and re.search(r"[Aa]day|biyograf", b["reason"])),
    ("veri-yok-kapsam", "kapsam dışı seçim/oylama (meclis, belde, muhtar, ara seçim, senato, 1950 öncesi, yenileme)",
     {"secim": "seçim"}, None,
     lambda b: b["answerable"] == "no" and re.search(r"meclis|[Bb]elde|[Mm]uhtar|[Aa]ra seçim|[Ss]enato|1950|[Yy]enilem|[Gg]eçersiz oy|2009 yerel|1957|ilçe düzeyinde", b["reason"])),
    ("veri-yok-diger", "yorum, süreç, takvim, konu dışı ya da netleştirme gereken soru",
     {}, None, lambda b: b["answerable"] == "no"),
    ("takip", "önceki soruyu değiştiren takip: 'peki {il}?', 'ya {secim}?', '{parti}?'",
     {"il": "il", "secim": "seçim", "parti": "parti"}, None, lambda b: b.get("history")),
    ("belirsiz-varsayilan", "belirsiz soru ('2015', '2023 seçimi', 'Erdoğan 2023', aynı adlı birim) → belgeli varsayılan",
     {"secim": "seçim (belirsiz)", "birim": "ilçe/mahalle adı (belirsiz)"}, None,
     lambda b: b["category"] == "takip-belirsiz"),
    ("el-degistiren", "{secim1}'den {secim2}'ye el değiştiren {seviye}ler",
     {"secim1": "seçim", "secim2": "seçim", "seviye": "il | ilçe | mahalle", "il": "il (ilçe/mahalle için)"},
     "SELECT b2.ad, b1.kazanan, b2.kazanan FROM birim b2 JOIN secim s2 ON s2.id = b2.secim_id JOIN secim s1 ON s1.kod = {secim1} "
     "JOIN birim b1 ON b1.secim_id = s1.id AND b1.seviye = b2.seviye AND b1.geom_id = b2.geom_id "
     "WHERE s2.kod = {secim2} AND b2.seviye = {seviye} AND b1.kazanan <> b2.kazanan",
     lambda b: b["category"] == "degisim" and "kazanan" in b["sql"]),
    ("oy-degisimi", "{parti}'nin oyu {secim1}'den {secim2}'ye ({birim}de) nasıl değişti / en çok nerede düştü",
     {"parti": "parti", "secim1": "seçim", "secim2": "seçim", "birim": "Türkiye | il | ilçe"},
     "SELECT b2.ad, o2.oran - o1.oran AS fark ... JOIN birim b1 ON b1.plaka = b2.plaka ... ORDER BY fark",
     lambda b: b["category"] == "degisim"),
    ("tur-karsilastirma", "cumhurbaşkanlığı 1. ve 2. tur arasında {aday} oyu / katılım {birim}de nasıl değişti",
     {"aday": "aday", "birim": "il | Türkiye"},
     "... s1.kod = '2023cb1tur' ... JOIN secim s2 ON s2.kod = '2023cb2tur' ... o2.oran - o1.oran",
     lambda b: b["category"] == "turlar-arasi"),
    ("fark", "{secim}'de {birim}de birinci ile ikinci arasındaki oy / puan farkı; en çekişmeli {seviye}ler",
     {"secim": "seçim", "birim": "Türkiye | il | ilçe", "seviye": "il | ilçe"},
     "SELECT MAX(o.oy) - (SELECT o2.oy FROM oy o2 WHERE o2.birim_id = b.id ORDER BY o2.oy DESC LIMIT 1 OFFSET 1) "
     + J + " WHERE s.kod = {secim} AND b.seviye = {seviye} GROUP BY b.id",
     lambda b: b["category"] == "fark"),
    ("vekil", "{secim}'de {parti} ({il}den) kaç milletvekili çıkardı",
     {"secim": "genel seçim", "parti": "parti (ops.)", "il": "il (ops.)"},
     "SELECT o.aday_parti, SUM(o.vekil) " + J + " WHERE s.kod = {secim} AND b.seviye = 'il' AND o.vekil > 0 GROUP BY o.aday_parti",
     lambda b: b["category"] == "vekil"),
    ("secmen-sayisi", "{secim}'de {birim}de kaç seçmen / sandık vardı",
     {"secim": "seçim", "birim": "Türkiye | il | ilçe | yurt dışı"},
     "SELECT SUM(b.secmen) FROM birim b JOIN secim s ON s.id = b.secim_id WHERE s.kod = {secim} AND b.seviye IN ('il','yurtdisi')",
     lambda b: b["category"] in ("katilim", "zaman-serisi", "rekor-siralama") and re.search(r"seçmen|sandık", b["question"], re.I)
     and "katılım" not in b["question"].lower()),
    ("katilim", "{secim}'de {birim}de katılım kaçtı / en yüksek-düşük katılımlı {seviye}ler",
     {"secim": "seçim", "birim": "Türkiye | il | ilçe", "seviye": "il | ilçe"},
     "SELECT b.ad, b.katilim FROM birim b JOIN secim s ON s.id = b.secim_id WHERE s.kod = {secim} AND b.seviye = {seviye} ORDER BY b.katilim",
     lambda b: b["category"] == "katilim" or "katilim" in b["sql"] and b["category"] == "rekor-siralama"),
    ("zaman-serisi-kazanan", "{birim}de yıllar içinde {tur} seçimlerini kim kazandı",
     {"birim": "il | ilçe", "tur": "genel | yerel"},
     "SELECT s.kod, b.kazanan FROM birim b JOIN secim s ON s.id = b.secim_id WHERE s.tur = {tur} AND b.seviye = {seviye} AND b.plaka = {plaka} ORDER BY s.yil, s.id",
     lambda b: b["category"] == "zaman-serisi" and "kazanan" in b["sql"]),
    ("zaman-serisi-oran", "{parti}'ın {birim}de {tur} seçimlerindeki oyu yıllara göre",
     {"parti": "parti | aday", "birim": "Türkiye | il | ilçe", "tur": "genel | yerel | cb | referandum"},
     "SELECT s.kod, o.oran " + J + " WHERE s.tur = {tur} AND b.seviye = {seviye} AND o.aday_parti = {parti} ORDER BY s.yil, s.id",
     lambda b: b["category"] == "zaman-serisi"),
    ("referandum", "{secim} referandumunda {birim}de Evet/Hayır oranı; Hayır çıkan {seviye}ler",
     {"secim": "referandum", "birim": "Türkiye | il | ilçe | mahalle", "seviye": "il | ilçe"},
     "SELECT o.aday_parti, o.oran " + J + " WHERE s.kod = {secim} AND b.seviye = {seviye} AND o.aday_parti IN ('Evet','Hayır')",
     lambda b: b["category"] == "referandum" or (b["category"] in ("ilce", "mahalle") and "referandum" in b["sql"])),
    ("kac-yerde-birinci", "{secim}'de {parti/aday} kaç {seviye}de birinci oldu / kazandı",
     {"secim": "seçim", "parti": "parti | aday", "seviye": "il | ilçe | mahalle", "il": "il (ilçe/mahalle için)"},
     "SELECT COUNT(*) FROM birim b JOIN secim s ON s.id = b.secim_id WHERE s.kod = {secim} AND b.seviye = {seviye} AND b.kazanan = {parti}",
     lambda b: "COUNT(*)" in b["sql"] and "kazanan" in b["sql"] or ("GROUP BY b.kazanan" in b["sql"])),
    ("nerede-birinci", "{secim}'de {parti/aday}'ın birinci olduğu {seviye}ler hangileri",
     {"secim": "seçim", "parti": "parti | aday", "seviye": "il | ilçe"},
     "SELECT b.ad FROM birim b JOIN secim s ON s.id = b.secim_id WHERE s.kod = {secim} AND b.seviye = {seviye} AND b.kazanan = {parti}",
     lambda b: re.search(r"b\.kazanan = '", b["sql"]) and b["category"] in ("il", "yerel", "cumhurbaskanligi", "ilce", "referandum")),
    ("en-yuksek-dusuk", "{secim}'de {parti/aday}'ın en yüksek / en düşük oy aldığı N {seviye}",
     {"secim": "seçim", "parti": "parti | aday", "seviye": "il | ilçe | mahalle", "n": "sayı", "il": "il (ops.)"},
     "SELECT b.ad, o.oran " + J + " WHERE s.kod = {secim} AND b.seviye = {seviye} AND o.aday_parti = {parti} ORDER BY o.oran DESC LIMIT {n}",
     lambda b: re.search(r"ORDER BY o\.oran (DESC|ASC)", b["sql"]) and "aday_parti = '" in b["sql"]),
    ("birim-sonucu", "{secim}'de {birim}de kim kazandı / partiler yüzde kaç aldı",
     {"secim": "seçim", "birim": "il | ilçe | mahalle", "il": "il (ilçe için zorunlu: aynı adlı ilçeler)"},
     "SELECT o.aday_parti, o.oy, o.oran " + J + " WHERE s.kod = {secim} AND b.seviye = {seviye} AND b.plaka = {plaka} [AND b.ad = {ilce}] ORDER BY o.oy DESC",
     lambda b: b["category"] in ("il", "ilce", "mahalle", "yerel", "cumhurbaskanligi") and "b.seviye IN ('il','yurtdisi')" not in b["sql"]),
    ("ulusal-oy", "{secim}'de {parti/aday} Türkiye genelinde kaç oy / yüzde kaç aldı",
     {"secim": "seçim", "parti": "parti | aday (ops.: tüm partiler)"}, "SELECT " + NAT,
     lambda b: b["category"] in ("ulusal-toplam", "cumhurbaskanligi", "yerel")),
    ("bolge-toplami", "{bolge}de {secim}'de {parti} toplam oyu / kazandığı il sayısı",
     {"bolge": "coğrafi bölge | deprem bölgesi | Trakya (plaka listesi)", "secim": "seçim", "parti": "parti"},
     "... WHERE s.kod = {secim} AND b.seviye = 'il' AND b.plaka IN ({plakalar})",
     lambda b: b["category"] == "bolge"),
    ("capraz", "aynı birimde farklı seçimlerin karşılaştırması (aday vs parti, referandum vs cumhurbaşkanlığı, genel vs yerel)",
     {"secim1": "seçim", "secim2": "seçim", "birim": "Türkiye | il | ilçe"},
     "... JOIN secim s2 ON s2.kod = {secim2} JOIN birim b2 ON b2.secim_id = s2.id AND b2.plaka = b1.plaka ...",
     lambda b: b["category"] == "capraz"),
    ("rekor", "tarihin en yüksek / en düşük / en çok … (tüm seçimler üzerinde sıralama)",
     {"olcu": "oy oranı | oy | il sayısı | parti sayısı"}, None,
     lambda b: b["category"] == "rekor-siralama"),
]

out, left = [], []
assigned = {}
for b in BANK:
    for pid, *_rest in P:
        m = [p for p in P if p[0] == pid][0][4]
        if b.get("answerable") != "no" and not b.get("sql") and pid not in ("veri-yok-diger",):
            pass
        try:
            hit = m(b)
        except (KeyError, TypeError):
            hit = False
        if hit:
            assigned.setdefault(pid, []).append(b)
            break
    else:
        left.append(b["id"])
assert not left, left

rows = []
for pid, text, slots, tmpl, _ in P:
    items = assigned.get(pid, [])
    if not items:
        continue
    ev = sorted({e.strip() for i in items for e in str(i.get("evidence", "")).split(",") if e.strip()})
    rows.append({
        "id": pid, "kalip": text, "yuvalar": slots,
        "agirlik": sum(W[i["frequency"]] for i in items), "soru_sayisi": len(items),
        "siklik": {k: sum(i["frequency"] == k for i in items) for k in ("yüksek", "orta", "düşük")},
        "yanitlanabilir": "hayır" if all(i["answerable"] == "no" for i in items) else (
            "kısmen" if any(i["answerable"] == "partial" for i in items) else "evet"),
        "kaynaklar": ev, "ornekler": [i["id"] for i in items][:8], "sql_sablonu": tmpl,
    })
rows.sort(key=lambda r: (-r["agirlik"], r["id"]))
for k, r in enumerate(rows, 1):
    r["sira"] = k
    order = ["sira", "id", "kalip", "yuvalar", "agirlik", "soru_sayisi", "siklik", "yanitlanabilir", "kaynaklar",
             "ornekler", "sql_sablonu"]
    rows[k - 1] = {key: r[key] for key in order if r.get(key) is not None}

head = """# Soru kalıpları: soru bankasındaki (soru_bankasi.yaml) soruların parametreli kalıplara ayrılmış hali.
# Gelecekteki bir şablon katmanı için veri dosyasıdır; şablon motoru henüz yok. Bkz. docs/SORU_KALIPLARI.md.
# sira: ağırlığa göre (ağırlık = kalıba düşen soruların sıklık puanı toplamı; yüksek 3, orta 2, düşük 1).
# yuvalar: kalıptaki {yuva} adları ve beklenen değer türü. sql_sablonu: {yuva}'lar tırnaklı değerle doldurulur;
# '...' içeren şablonlar yalnız iskelettir (tam sorgu için ornekler'deki gold SQL'e bakın).
# Bu dosyayı scripts/build_soru_kaliplari.py soru bankasından üretir; banka değişince yeniden üretin.

"""
body = yaml.dump({"kaliplar": rows}, allow_unicode=True, sort_keys=False, width=130)
(ROOT / "eval" / "soru_kaliplari.yaml").write_text(head + body, encoding="utf-8")
for r in rows:
    print(r["sira"], r["id"], r["agirlik"], r["soru_sayisi"], r["yanitlanabilir"])
