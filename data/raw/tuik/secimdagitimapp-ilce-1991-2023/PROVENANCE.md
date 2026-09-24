# TÜİK — 1991-2007 Milletvekili Genel Seçimleri, il ve ilçe sonuçları

**Kaynak:** TÜİK Seçim Dağıtım uygulaması,
`https://biruni.tuik.gov.tr/secimdagitimapp/secim.zul` → "Seçim çevresi ve
ilçelere göre milletvekili genel seçimi sonuçları" (Mutlak sonuç). Aynı tablonun
1961-1987 kısmı: `../secimdagitimapp-ilce-1961-1987/PROVENANCE.md`.

**İndirilme tarihi:** 2026-09-24. 1991, 1995, 1999, 2002, 2007 (her biri bir
seçim çevresi başına bir HTML, cp1254). Klasör adı tablonun yıl aralığını
gösterir. 2011 ve sonrası bilerek indirilmedi, çünkü o yılların ilçe düzeyi
projede zaten YSK'nin resmî açık verisinden var.

**Script:** `scripts/pipelines/genel_ilce_1961_1987/fetch_tuik_ilce.py 1991 1995 1999 2002 2007`

## Dosyalar

`<yıl>/<NN>-<çevre>.html`. `NN` TÜİK listesindeki sıradır, plaka değildir,
çünkü büyük iller birden fazla seçim çevresine bölünür (`06-ankara-1`,
`07-ankara-2`). Rapor her ilçe için ayrıca **şehir** ve **bucak/köy**
kırılımını verir; bu kırılım projede başka hiçbir kaynakta yoktur.

## Nasıl kullanıldı

1991-2007'nin ilçe düzeyi daha önce `mertnuhoglu/secim_verileri`nden geliyordu
(dondurulmuş hâli: `data/kaynaklar/mertnuhoglu/genel/<yıl>.json`). Bu TÜİK
tablosu o değerlerin **yerine konmadı**. Taban mertnuhoglu kaldı; yalnızca
TÜİK'in farklı olduğu ya da tabanda hiç olmayan alanlar TÜİK'ten alındı ve her
satırın `kaynak` alanına eski/yeni değerleriyle yazıldı
(`scripts/pipelines/tuik_arsiv/merge_tuik_ilce_1991_2007.py`).

| Yıl | Birebir aynı (teyitli) | Farklı | Yalnız TÜİK |
|---|---|---|---|
| 1991 | 891 | 3 (Fatih, Gaziosmanpaşa, Eminönü ayrımı) | Eminönü |
| 1995 | 5 | 912 (Yeni Parti oyları tabanda hiç yoktu) | Eminönü |
| 1999 | 919 | 1 (Fatih) | Eminönü |
| 2002 | 921 | 1 (Fatih) | Eminönü |
| 2007 | 921 | 1 (Fatih) | Eminönü |

Fatih: tabanda Fatih ve Eminönü tek satırdı; TÜİK Eminönü'yü ayrı veriyor
(`HIST-Istanbul-Eminonu` / `HIST-Istanbul-Fatih`, 1961-1987 ile aynı).
2007'de projenin "DTP" etiketi (TÜİK'te bağımsız) etiket farkıdır, değer farkı
sayılmadı.

Sorgu: `.venv/bin/python scripts/kaynak.py 1995 İstanbul Fatih`

## Bütünlük

`checksums.sha256`, 2026-09-24 itibarıyla.
