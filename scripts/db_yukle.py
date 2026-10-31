"""Projenin işlenmiş verisinin tamamını (data/normalized + mahalle sınırları) MariaDB/MySQL'e yükler.

Kullanım (repo kökünden):
    pip install pymysql
    export DB_PASSWORD='...'
    python3 scripts/db_yukle.py --host 192.168.1.2 --user hami --db secim

Yüklenenler:
    secim, birim, oy  -> elections/ (il, ilçe, yurt dışı) + mahalle/ (mahalle sonuçları)
    mahalle           -> geo/normalized/mahalle_geo.json (mahalle adı + sınır GeoJSON)
    ek_veri           -> ek/, meclis_harita/, partiler.json, meclis_2024.json, secim_takvimi.json
                         (yapıları birbirinden farklı olduğu için dosya başına bir JSON satırı)
Tablolar her çalıştırmada silinip yeniden kurulur; kaynak dosyalara dokunulmaz.
data/raw/ (PDF, HTML taramaları) ham kaynak olduğu için yüklenmez.
"""
import argparse
import json
import os
import time
from pathlib import Path

import pymysql

KOK = Path(__file__).resolve().parent.parent
NORM = KOK / "data" / "normalized"
PAKET = 2000  # tek seferde gönderilen satır sayısı

SEMA = [
    "SET FOREIGN_KEY_CHECKS=0",
    "DROP TABLE IF EXISTS oy",
    "DROP TABLE IF EXISTS birim",
    "DROP TABLE IF EXISTS secim",
    "DROP TABLE IF EXISTS mahalle",
    "DROP TABLE IF EXISTS ek_veri",
    "SET FOREIGN_KEY_CHECKS=1",
    """CREATE TABLE secim (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        kod         VARCHAR(40)  NOT NULL UNIQUE,   -- dosya adı: 2023, 2024yerel, 2017referandum
        tur         VARCHAR(20)  NOT NULL,          -- genel / yerel / cumhurbaskanligi / referandum
        ad          VARCHAR(255),
        yil         SMALLINT,
        toplam_sandalye INT
    )""",
    """CREATE TABLE birim (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        secim_id    INT NOT NULL,
        seviye      ENUM('il','ilce','mahalle','yurtdisi') NOT NULL,
        plaka       TINYINT UNSIGNED,
        ad          VARCHAR(255),
        geom_id     VARCHAR(191),                    -- ilçe: TR-D-01-001, mahalle: k126913
        ust_geom_id VARCHAR(191),                    -- mahallenin bağlı olduğu ilçe
        secmen      INT,
        oy_kullanan INT,
        gecerli_oy  INT,
        sandik      INT,
        katilim     DECIMAL(7,2),
        kazanan     VARCHAR(255),
        toplam_vekil SMALLINT,
        FOREIGN KEY (secim_id) REFERENCES secim(id),
        INDEX (secim_id, seviye, plaka),
        INDEX (geom_id),
        INDEX (ust_geom_id)
    )""",
    """CREATE TABLE oy (
        birim_id    INT NOT NULL,
        aday_parti  VARCHAR(255) NOT NULL,          -- parti, aday ya da Evet/Hayır
        oy          INT,
        oran        DECIMAL(7,2),
        vekil       SMALLINT,
        aday        TEXT,                           -- yerel seçimde belediye başkanı adayı
        FOREIGN KEY (birim_id) REFERENCES birim(id),
        INDEX (birim_id),
        INDEX (aday_parti)
    )""",
    """CREATE TABLE mahalle (
        geom_id     VARCHAR(191) NOT NULL,
        ilce_geom_id VARCHAR(191) NOT NULL,
        ad          VARCHAR(255),
        geometri    LONGTEXT,                       -- GeoJSON geometry
        PRIMARY KEY (ilce_geom_id, geom_id),
        INDEX (geom_id)
    )""",
    """CREATE TABLE ek_veri (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        klasor      VARCHAR(120),                   -- ek/senato, meclis_harita ...
        dosya       VARCHAR(160),
        icerik      LONGTEXT                        -- dosyanın JSON içeriği aynen
    )""",
]


def yil_bul(kod):
    rakam = "".join(ch for ch in kod[:4] if ch.isdigit())
    return int(rakam) if len(rakam) == 4 else None


class Yukleyici:
    def __init__(self, baglanti):
        self.b = baglanti
        self.cur = baglanti.cursor()
        self.oy_tampon = []
        self.n_birim = 0
        self.n_oy = 0

    def birim(self, secim_id, seviye, kayit, ust=None, geom_id=None, ad=None):
        self.cur.execute(
            """INSERT INTO birim (secim_id, seviye, plaka, ad, geom_id, ust_geom_id, secmen,
                   oy_kullanan, gecerli_oy, sandik, katilim, kazanan, toplam_vekil)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (secim_id, seviye, kayit.get("plaka"), ad or kayit.get("ad", "Yurt dışı"),
             geom_id or kayit.get("geomId"), ust, kayit.get("secmen"), kayit.get("oyKullanan"),
             kayit.get("gecerliOy"), kayit.get("sandik"), kayit.get("katilim"),
             kayit.get("kazanan"), kayit.get("toplamVekil")),
        )
        birim_id = self.cur.lastrowid
        self.n_birim += 1
        vekiller = kayit.get("vekil") if isinstance(kayit.get("vekil"), dict) else {}
        for parti, d in (kayit.get("oy") or {}).items():
            if not isinstance(d, dict):
                d = {"oy": d}
            self.oy_tampon.append((birim_id, parti, d.get("oy"), d.get("oran"),
                                   vekiller.get(parti), d.get("aday")))
        if len(self.oy_tampon) >= PAKET:
            self.oylari_yaz()

    def oylari_yaz(self):
        if self.oy_tampon:
            self.cur.executemany(
                "INSERT INTO oy (birim_id, aday_parti, oy, oran, vekil, aday) VALUES (%s,%s,%s,%s,%s,%s)",
                self.oy_tampon,
            )
            self.n_oy += len(self.oy_tampon)
            self.oy_tampon = []

    def bitir(self):
        self.oylari_yaz()
        self.b.commit()


def oku(yol):
    return json.loads(Path(yol).read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="192.168.1.2")
    p.add_argument("--port", type=int, default=3306)
    p.add_argument("--user", default="hami")
    p.add_argument("--db", default="secim")
    p.add_argument("--mahallesiz", action="store_true", help="mahalle sonuçlarını ve sınırlarını atla")
    a = p.parse_args()

    sifre = os.environ.get("DB_PASSWORD")
    if not sifre:
        raise SystemExit("Önce şifreyi ver: export DB_PASSWORD='...'")

    baslangic = time.time()
    b = pymysql.connect(host=a.host, port=a.port, user=a.user, password=sifre,
                        database=a.db, charset="utf8mb4", autocommit=False)
    y = Yukleyici(b)
    for komut in SEMA:
        y.cur.execute(komut)
    b.commit()

    # 1) Seçimler: il / ilçe / yurt dışı
    print("1/4 Seçim sonuçları (il, ilçe, yurt dışı)...")
    secim_idleri = {}
    for yol in sorted((NORM / "elections").glob("*/*.json")):
        kod, veri = yol.stem, oku(yol)
        y.cur.execute(
            "INSERT INTO secim (kod, tur, ad, yil, toplam_sandalye) VALUES (%s,%s,%s,%s,%s)",
            (kod, yol.parent.name, veri.get("ad"), yil_bul(kod), veri.get("toplamSandalye")),
        )
        sid = secim_idleri[kod] = y.cur.lastrowid
        for seviye, anahtar in (("il", "iller"), ("ilce", "ilceler")):
            for kayit in veri.get(anahtar) or []:
                y.birim(sid, seviye, kayit)
        if veri.get("yurtdisi"):
            y.birim(sid, "yurtdisi", veri["yurtdisi"])
        y.bitir()
        print(f"   {yol.parent.name}/{kod}")
    print(f"   -> {len(secim_idleri)} seçim, {y.n_birim} birim, {y.n_oy} oy satırı")

    if not a.mahallesiz:
        # 2) Mahalle adları ve sınırları
        print("2/4 Mahalle adları ve sınırları...")
        geo = oku(KOK / "geo" / "normalized" / "mahalle_geo.json")
        adlar = {}
        tampon, n_mah = [], 0
        for ilce, mahalleler in geo.items():
            for mk, m in mahalleler.items():
                adlar[(ilce, mk)] = m.get("ad")
                tampon.append((mk, ilce, m.get("ad"),
                               json.dumps(m.get("geometry"), ensure_ascii=False, separators=(",", ":"))))
                if len(tampon) >= 500:
                    y.cur.executemany("INSERT IGNORE INTO mahalle VALUES (%s,%s,%s,%s)", tampon)
                    n_mah += len(tampon)
                    tampon = []
        if tampon:
            y.cur.executemany("INSERT IGNORE INTO mahalle VALUES (%s,%s,%s,%s)", tampon)
            n_mah += len(tampon)
        b.commit()
        del geo
        print(f"   -> {n_mah} mahalle")

        # 3) Mahalle sonuçları (en uzun adım)
        print("3/4 Mahalle sonuçları (uzun sürer)...")
        onceki_birim, onceki_oy = y.n_birim, y.n_oy
        for yol in sorted((NORM / "mahalle").glob("*.json")):
            kod = yol.stem
            if kod not in secim_idleri:
                print(f"   ! {kod}: eşleşen seçim yok, atlandı")
                continue
            sid = secim_idleri[kod]
            t = time.time()
            for ilce, mahalleler in oku(yol).items():
                for mk, kayit in mahalleler.items():
                    y.birim(sid, "mahalle", kayit, ust=ilce, geom_id=mk, ad=adlar.get((ilce, mk)))
            y.bitir()
            print(f"   {kod} ({time.time() - t:.0f} sn)")
        print(f"   -> {y.n_birim - onceki_birim} mahalle sonucu, {y.n_oy - onceki_oy} oy satırı")

    # 4) Yapısı farklı ek dosyalar: olduğu gibi JSON
    print("4/4 Ek veriler...")
    ekler = sorted((NORM / "ek").rglob("*.json")) + sorted((NORM / "meclis_harita").glob("*.json"))
    ekler += [NORM / "partiler.json", NORM / "meclis_2024.json", KOK / "data" / "secim_takvimi.json"]
    for yol in ekler:
        if yol.exists():
            y.cur.execute(
                "INSERT INTO ek_veri (klasor, dosya, icerik) VALUES (%s,%s,%s)",
                (str(yol.parent.relative_to(KOK / "data")), yol.name, yol.read_text(encoding="utf-8")),
            )
    b.commit()
    print(f"   -> {len(ekler)} dosya")

    b.close()
    print(f"\nBitti ({(time.time() - baslangic) / 60:.1f} dk). Toplam {y.n_birim} birim, {y.n_oy} oy satırı.")


if __name__ == "__main__":
    main()
