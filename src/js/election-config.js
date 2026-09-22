  const PARTY = BUNDLE.partiler;
  const YEAR_ORDER = ['2023','2018','2015Kasim','2015Haziran','2011','2007','2002','1999','1995','1991','1987','1983','1977','1973','1969','1965','1961','1957','1954','1950'];
  const YEAR_LABEL = {'2023':'2023','2018':'2018','2015Kasim':"2015 K",'2015Haziran':"2015 H",'2011':'2011','2007':'2007','2002':'2002','1999':'1999','1995':'1995','1991':'1991','1987':'1987','1983':'1983','1977':'1977','1973':'1973','1969':'1969','1965':'1965','1961':'1961','1957':'1957','1954':'1954','1950':'1950'};
  const REF_YEAR_ORDER = ['2017referandum','2010referandum','2007referandum','1988referandum','1987referandum','1982referandum','1961referandum'];
  const REF_YEAR_LABEL = {'2017referandum':'2017','2010referandum':'2010','2007referandum':'2007','1988referandum':'1988','1987referandum':'1987','1982referandum':'1982','1961referandum':'1961'};
  const YEREL_YEAR_ORDER = ['2024yerel','2019yerel','2014yerel','2009yerel','2004yerel','1999yerel','1994yerel','1989yerel','1984yerel','1977yerel','1973yerel','1968yerel','1963yerel','1955yerel','1950yerel'];
  const YEREL_YEAR_LABEL = {'2024yerel':'2024','2019yerel':'2019','2014yerel':'2014','2009yerel':'2009','2004yerel':'2004','1999yerel':'1999','1994yerel':'1994','1989yerel':'1989','1984yerel':'1984','1977yerel':'1977','1973yerel':'1973','1968yerel':'1968','1963yerel':'1963','1955yerel':'1955','1950yerel':'1950'};
  // 1950-1961 genel secimlerinde vekil (sandalye) verisi onceden (Wikipedia
  // kaynakli) yoktu; artik YSK'nin resmi, TUIK kaynakli 1950-1977 il arsivinden
  // var (bkz. scripts/genel-1950-1977-pipeline/). Bos kalirsa (gelecekte baska
  // bir yil icin ayni durum olursa) buraya eklenebilir.
  const YEARS_NO_VEKIL = new Set([]);
  // 1950-1987 genel secimlerinde ve 1961/1982/1987/1988/2007 referandumlarinda ilce-bazli
  // kaynak yok - sadece il seviyesinde veri var. 2026-09-22: 1950-1977 yerel
  // secimleri de ayni sekilde sadece il merkezi (bkz. SECIM_TAKVIMI.md,
  // data/raw/wikipedia/yerel-1950-1977/PROVENANCE.md) - ilceler yok.
  const YEARS_IL_ONLY = new Set(['1950','1954','1957','1961','1965','1969','1973','1977','1983','1987',
    '1961referandum','1982referandum','1987referandum','1988referandum',
    '1950yerel','1955yerel','1963yerel','1968yerel','1973yerel','1977yerel']);
  // 2026-09-22: 1950-1977 yerel secimleri, digerlerinden farkli bir kaynak
  // notu metni gerektiriyor (YSK'nin bu donem icin il-bazli degil, sadece
  // ULUSAL toplam PDF'i var - bkz. data/raw/ysk/mahalli-1963-1977/PROVENANCE.md).
  const YEARS_YEREL_1950_1977 = new Set(['1950yerel','1955yerel','1963yerel','1968yerel','1973yerel','1977yerel']);
  // 2026-09-22: YSK'nin resmi il-bazli (1950/1954/1957/1961 genel,
  // 1961/1982/1987/1988 referandum) veya il+ilce-bazli (2007referandum,
  // 2014cb) arsivlerine yukseltilen yillar — kaynakLine bunlar icin ozel.
  // 1983/1987 de ikinci oturumda ayni arsiv ailesinden (Milletvekili/1983-
  // 2007/<Il>.pdf) eklendi, 1950-1977 ile ayni davranisi (sadece il) alir.
  const YEARS_YSK_OFFICIAL_IL = new Set(['1950','1954','1957','1961','1965','1969','1973','1977',
    '1983','1987',
    '1961referandum','1982referandum','1987referandum','1988referandum']);
  // 2026-09-22 (ikinci oturum): bu 5 genel secim yilinda IL duzeyi YSK'nin
  // resmi il-bazli arsivine yukseltildi ama ILCE duzeyi hala Github'daki
  // mertnuhoglu/secim_verileri deposundan (bkz. data/raw/ysk/1983-2007/
  // PROVENANCE.md) - yani tek bir "kaynak" etiketi yeterli degil, il ve ilce
  // ayri belirtiliyor.
  const YEARS_IL_YSK_ILCE_GITHUB = new Set(['1991','1995','1999','2002','2007']);
  // 2026-09-22 (ikinci oturum): bu 3 yerel secim yilinda IL MERKEZI YSK'nin
  // resmi arsivine yukseltildi, ILCE duzeyi hala Wikipedia kaynakli (Github
  // degil, bu yuzden ayri bir set - farkli kaynak metni gerekiyor).
  const YEARS_YEREL_IL_YSK_ILCE_WIKI = new Set(['1994yerel','1999yerel','2004yerel']);
  const CB_YEAR_ORDER = ['2023cb2tur','2023cb1tur','2018cb','2014cb'];
  const CB_YEAR_LABEL = {'2023cb2tur':'2023 (2.Tur)','2023cb1tur':'2023 (1.Tur)','2018cb':'2018','2014cb':'2014'};

