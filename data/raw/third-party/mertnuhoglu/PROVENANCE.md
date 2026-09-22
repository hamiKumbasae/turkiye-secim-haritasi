# Kaynak

`https://github.com/mertnuhoglu/secim_verileri`, commit `f821f0455ae384d538eca485b3b99d58bf9fab91`
(2015-06-04), 2026-09-22'de `codeload.github.com` üzerinden tam depo arşivi
olarak indirildi (`git clone` değil — tek seferlik, tekrar canlı erişim
gerektirmeyen bir snapshot).

Bu depo, memurlar.net'ten kazınmış 1991-2007 genel seçim sonuçlarının il
kodu bazında (01-81) ham (`raw/`), temizlenmiş (`clean/`) ve toparlanmış
(`collected/genel_secim_oylar.csv`, `collected/genel_secim_sandiklar.csv`)
hâllerini içeriyor. Bu projede kullanılan **ilçe düzeyi** 1991/1995/1999/
2002/2007 genel seçim verisi, buradaki `collected/genel_secim_oylar.csv`
dosyasından türetildi (bkz. `../../../../sources.yml` → `legacy_source`
alanları).

## Yeniden üretmek için

```bash
curl -sL https://codeload.github.com/mertnuhoglu/secim_verileri/tar.gz/f821f0455ae384d538eca485b3b99d58bf9fab91 -o repo.tar.gz
tar xzf repo.tar.gz
```

## Bütünlük

`checksums.sha256` dosyasına bakın — bu klasördeki (PROVENANCE.md ve
checksums.sha256 hariç) her dosyanın SHA-256 özeti.
