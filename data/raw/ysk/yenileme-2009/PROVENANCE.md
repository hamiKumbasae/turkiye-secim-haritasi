# YSK Açık Veri — seçim listesi (2009 yenileme araması)

**Kaynak:** `acikveri.ysk.gov.tr/api/getSecimDetayList` (seçim türü başına seçim listesi).
**Script:** `scripts/pipelines/election_import/secim_listesi.js`, iş akışı `.github/workflows/ysk-yenileme-2009-cek.yml`
(run 41258728603, 2026-11-01; çıktı `ysk-belde-baskan-veri` dalında).

Sonuç: belediye başkanlığı listesinde 2009'dan yalnız `4290` (29 Mart 2009) var. 7 Haziran 2009 yenileme
seçimi açık veride yok (2019 İstanbul ve 2024 yenilemeleri var). Bu yüzden Akyazı, Koçarlı, Mecitözü ve
Şarkikaraağaç'ın yenileme sonuçları Vikipedi il sayfalarından alındı ve iki haber kaynağıyla karşılaştırıldı
(`data/raw/third-party/haber-2009-yenileme/`, `belde_ayir_baskan.py` `YENILEME_2009`).
