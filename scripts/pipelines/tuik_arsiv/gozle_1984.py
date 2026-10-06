"""
1984 DIE kitabi (0012953) icin goz okumasi: extract_mahalli_1984.py'nin dorduncu bagimsiz motoru ("gozle").

Mevcut uc okuma (metin katmani, macOS Vision, tesseract) 1984 taramasinin ~6 pt'lik nokta vurusu
rakamlarinda bircok hucreyi yanlis okuyor; belediye meclisi ve il genel meclisi ilce satirlarinin
yaklasik %40'i cozulemiyordu. Bu motor, cozulemeyen satirlarin sayfa goruntusunu satir satir
buyutulmus seritler halinde bir okuyucuya (insan ya da cok kipli model) gosterir ve okunan dizgileri
hucre gozlemi olarak kaydeder. Kurallar degismez: deger hesaplanmaz; cozucu ayni kisitlari arar ve
bir cozum ancak oy alanlarindan en fazla biri tek motora dayaniyorsa kabul edilir. Yani goz okumasi
tek basina bir satiri dogrulayamaz; diger motorlardan en az biriyle ayni degeri okumus olmalidir.

Adimlar:
  hazirla <tablo>   cozulemeyen ilce/il satirlari (sol yuz) ve sag yuzde onlarin +-PENCERE komsu
                    satirlari icin serit goruntuleri + manifest uretir (scratch klasorune).
  kaydet            okunan dizgileri (okuma dosyasi) ocr/gozle_p<sayfa>.json gozlemlerine cevirir.

Okuma dosyasi bicimi (UTF-8 metin): her serit icin goruntudeki etiketle ayni sira, satir basina
  "<sayfa>:<satir_i> <deger> <deger> ..."  (sutun sirasiyla; '-' tire, '_' bos hucre, '?' okunamadi)

Onbellek: data/kaynaklar/tuik/yerel/1984yerel/ocr/gozle_p<sayfa>.json
  {"sayfa", "gozlem": [[metin, guven, ust y, alt y, sol x, sag x], ...], "okuyan", "tarih"}
"""
import collections
import json
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import die_tablo  # noqa: E402
import extract_mahalli_1984 as X  # noqa: E402

DPI = 400
SERIT = 12           # serit basina satir
PENCERE = 3
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def gozle_yol(no):
    return X.OCRDIR / f"gozle_p{no:03d}.json"


def cozulemeyen(tablo):
    d = json.loads((X.OUT / f"{tablo}.json").read_text(encoding="utf-8"))
    out = collections.defaultdict(set)
    for r in d["satirlar"]:
        if r["kontrol"]["durum"] not in X.KABUL and r["tip"] in ("ilce", "il"):
            out[tuple(r["sayfa"])].add(r["adKaynakta"])
    return out


def dikey_kayma(img, o, ys, K, ox=0.0):
    """Metin katmani satir konumlari ile goruntudeki yazi arasindaki dikey kayma (pt): satir bantlarina
    [y+d, y+d+6] dusen siyah piksel orani en buyuk olan d (-8..+4, 0,25 adim)."""
    import numpy as np
    a = np.asarray(img) < 128
    x0, x1 = int((K.e[0] + ox) * o) - 40, int((K.e[-1] + ox) * o)
    profil = a[:, max(0, x0):x1].sum(axis=1)
    en, en_d = -1, 0.0
    for d4 in range(-24, 25):
        d = d4 / 4
        t = 0
        for y in ys:
            t += profil[int((y + d) * o):int((y + d + 6) * o)].sum()
        if t > en:
            en, en_d = t, d
    return en_d


def yatay_kayma(img, o, ys, K, dy, ox=0.0):
    """Sutun sag kenarlari ile goruntu arasindaki yatay kayma (pt): sayilar saga dayali; her kenarin
    hemen solundaki [e+d-18, e+d] seridine dusen siyah piksel en buyuk, sagindaki [e+d, e+d+6] en kucuk
    olan d (-40..+40)."""
    import numpy as np
    a = np.asarray(img) < 128
    satir = np.zeros(a.shape[0], bool)
    for y in ys:
        satir[int((y + dy) * o):int((y + dy + 6) * o)] = True
    profil = a[satir].sum(axis=0)
    en, en_d = None, 0.0
    for d2 in range(-20, 21):
        d = d2 / 2 + ox
        t = 0
        for e in K.e:
            t += profil[max(0, int((e + d - 18) * o)):int((e + d) * o)].sum()
            t -= 3 * profil[int((e + d) * o):int((e + d + 6) * o)].sum()
        if en is None or t > en:
            en, en_d = t, d - ox
    return en_d


def satir_kaymalari(img, o, ys, K, dx, d0):
    """Her satir icin yerel dikey kayma (pt). Sayfanin alt kisminda goruntu metin katmanina gore 3-4 pt
    kayabiliyor (bukuk tarama). Satirlar yukaridan asagi izlenir; her satirda bir onceki satirin
    kaymasinin +-1,5 pt cevresinde, yazi bandini [y+d+0,5, y+d+5,5] dolu, ust ve alt araligi bos
    birakan d secilir."""
    import numpy as np
    a = np.asarray(img) < 128
    x0, x1 = int((K.e[0] + dx) * o) - 40, int((K.e[-1] + dx) * o)
    profil = a[:, max(0, x0):x1].sum(axis=1).astype(float)
    def topla(u, v):
        return profil[max(0, int(u * o)):max(0, int(v * o))].sum()
    out, onceki = [], d0
    for y in ys:
        en, en_d = None, onceki
        for k in range(-6, 7):
            d = onceki + k / 4
            t = topla(y + d + 0.5, y + d + 5.5) - 3 * (topla(y + d - 1.5, y + d - 0.3) + topla(y + d + 6.3, y + d + 7.5))
            if en is None or t > en:
                en, en_d = t, d
        out.append(en_d)
        onceki = en_d
    return out


def satir_egimi(kelimeler, y):
    """satirin metin katmanindaki kelime tepelerine oturtulan dogru: (egim pt/pt, kelimelerin x ortalamasi);
    tepe ~ y + egim * (x - xm). Kelime azsa egim 0."""
    if not kelimeler or len(kelimeler) < 3:
        return 0.0, 300.0
    xs = [(w["x0"] + w["x1"]) / 2 for w in kelimeler]
    ts = [w["top"] for w in kelimeler]
    mx, mt = sum(xs) / len(xs), sum(ts) / len(ts)
    v = sum((x - mx) ** 2 for x in xs)
    if v < 1e-6:
        return 0.0, mx
    b = sum((x - mx) * (t - mt) for x, t in zip(xs, ts)) / v
    return max(-0.03, min(0.03, b)), mx


def hazirla(tablo, klasor):
    klasor = pathlib.Path(klasor)
    klasor.mkdir(parents=True, exist_ok=True)
    pdf = die_tablo.ac(X.PDF)
    ilk, son = X.CFG["tablolar"][tablo]
    hedef = cozulemeyen(tablo)
    yuzler, _ = X.tablo_oku(pdf, ilk, son)
    font = ImageFont.truetype(FONT, 34)
    manifest, n_img = [], 0
    for yz in yuzler:
        a, b = yz["sayfa"]
        adlar = hedef.get((a, b), set())
        if not adlar:
            continue
        sol_i = [i for i, s in enumerate(yz["sol"]) if s["etiket"] in adlar]
        m = len(yz["sag"])
        sag_j = sorted({j for i in sol_i for j in range(max(0, i - PENCERE), min(m, i + PENCERE + 1))})
        for no, satirlar, idx, kenar, alanlar, sol in ((a, yz["sol"], sol_i, yz["kl"], X.SOL, True),
                                                       (b, yz["sag"], sag_j, yz["kr"], X.SAG, False)):
            page = pdf.pages[no - 1]
            K = X.Kenarlar(page, kenar)
            mer = X._satir_merkezleri(page)
            img = page.to_image(resolution=DPI).original.convert("L")
            o = DPI / 72
            # goruntu sayfanin bbox'undan baslar (bu kitapta sol ust kose (-27, 18)); kalan kucuk kayma
            # goruntudeki murekkep dagilimindan
            bx, by = page.bbox[0], page.bbox[1]
            ys_ = [mer.get(s["y"], s["y"]) for s in satirlar]
            dy = dikey_kayma(img, o, [y - by for y in ys_], K, -bx)
            dx = yatay_kayma(img, o, [y - by for y in ys_], K, dy, -bx)
            dx, dy = dx - bx, dy - by
            print(no, "kayma", round(dx + bx, 2), round(dy + by, 2), flush=True)
            tum_y = [mer.get(r["y"], r["y"]) for r in satirlar]
            yerel = dict(zip(range(len(satirlar)), satir_kaymalari(img, o, [y - by for y in tum_y], K, dx, dy + by)))
            gruplar = {g[0]["top"]: g for g in die_tablo._satirlar(page.extract_words(keep_blank_chars=False,
                                                                                   use_text_flow=False))}
            for s0 in range(0, len(idx), SERIT):
                grup = idx[s0:s0 + SERIT]
                bantlar = []
                for i in grup:
                    y = mer.get(satirlar[i]["y"], satirlar[i]["y"])
                    ks = K.at(y)
                    egim, xm = satir_egimi(gruplar.get(satirlar[i]["y"]), y)
                    # sutun sutun kesilir: egik/bukuk taranmis sayfada satir soldan saga yukselip alcaliyor
                    sinir = [18 if sol else ks[0] - 50] + [e + 3 for e in ks[:len(alanlar)]]
                    sinir[-1] += 16
                    parca = []
                    for k in range(len(sinir) - 1):
                        xa, xb = sinir[k], sinir[k + 1]
                        yk = y + egim * ((xa + xb) / 2 - xm)
                        dyi = yerel[i] - by
                        parca.append(img.crop((int((xa + dx) * o), int((yk + dyi - 1.0) * o), int((xb + dx) * o),
                                               int((yk + dyi + 7.0) * o))))
                    bant = Image.new("L", (sum(c.width for c in parca), parca[0].height), 255)
                    xx = 0
                    for c in parca:
                        bant.paste(c, (xx, 0))
                        xx += c.width
                    bantlar.append((i, y, [round(e, 1) for e in ks[:len(alanlar)]], bant))
                    manifest.append({"sayfa": no, "satir": i, "y": round(y, 2), "kenarlar": bantlar[-1][2],
                                     "alanlar": alanlar, "etiket": satirlar[i].get("etiket")})
                gen = max(bn.width for *_, bn in bantlar) + 260
                yuk = sum(bn.height + 10 for *_, bn in bantlar) + 10
                tuval = Image.new("L", (gen, yuk), 255)
                d = ImageDraw.Draw(tuval)
                y_ = 10
                for i, _y, _k, bn in bantlar:
                    d.text((8, y_ + bn.height // 2 - 18), f"{no}:{i}", font=font, fill=0)
                    tuval.paste(bn, (250, y_))
                    d.line([(0, y_ + bn.height + 5), (gen, y_ + bn.height + 5)], fill=170, width=1)
                    y_ += bn.height + 10
                n_img += 1
                tuval.save(klasor / f"{tablo}_{no:03d}_{s0 // SERIT:02d}.png")
    (klasor / f"{tablo}_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    print(tablo, n_img, "şerit,", len(manifest), "satır")


def kaydet(okuma_dosyasi, manifest_dosyalari, okuyan):
    man = {}
    for mf in manifest_dosyalari:
        for m in json.loads(pathlib.Path(mf).read_text(encoding="utf-8")):
            man[(m["sayfa"], m["satir"])] = m
    gozlem = collections.defaultdict(list)
    hata = []
    for satir in pathlib.Path(okuma_dosyasi).read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        anahtar, *degerler = satir.split()
        no, i = map(int, anahtar.split(":"))
        m = man.get((no, i))
        if not m:
            hata.append(f"manifestte yok: {anahtar}")
            continue
        if len(degerler) != len(m["alanlar"]):
            hata.append(f"{anahtar}: {len(degerler)} değer, {len(m['alanlar'])} sütun")
            continue
        for k, v in enumerate(degerler):
            if v in ("_", "?"):
                continue
            x1 = m["kenarlar"][k]
            gozlem[no].append([v, 1.0, m["y"], round(m["y"] + 6.1, 1), round(x1 - 20, 1), x1])
    for no, g in gozlem.items():
        f = gozle_yol(no)
        eski = json.loads(f.read_text(encoding="utf-8"))["gozlem"] if f.exists() else []
        anahtarlar = {(o[2], o[5]) for o in g}
        g = [o for o in eski if (o[2], o[5]) not in anahtarlar] + g
        f.write_text(json.dumps({"sayfa": no, "okuyan": okuyan,
                                 "not": "Sayfa görüntüsünden göz okuması (gozle_1984.py). Kutu: hücrenin sağ kenarı ve "
                                        "satırın metin katmanındaki konumu; değer okunduğu gibi.",
                                 "gozlem": sorted(g, key=lambda o: (o[2], o[5]))},
                                ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for h in hata:
        print("HATA", h)
    print(sum(len(g) for g in gozlem.values()), "gözlem,", len(gozlem), "sayfa")


def oku_gozle(no):
    f = gozle_yol(no)
    return json.loads(f.read_text(encoding="utf-8"))["gozlem"] if f.exists() else []


if __name__ == "__main__":
    if sys.argv[1] == "hazirla":
        hazirla(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "kaydet":
        kaydet(sys.argv[2], sys.argv[3].split(","), sys.argv[4] if len(sys.argv) > 4 else "Claude (görsel okuma)")
