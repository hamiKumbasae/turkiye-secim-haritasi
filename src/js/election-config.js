  const PARTY = BUNDLE.partiler;
  const YEAR_ORDER = ['2023','2018','2015Kasim','2015Haziran','2011','2007','2002','1999','1995','1991','1987','1983','1977','1973','1969','1965','1961','1957','1954','1950'];
  const YEAR_LABEL = {'2023':'2023','2018':'2018','2015Kasim':"2015 K",'2015Haziran':"2015 H",'2011':'2011','2007':'2007','2002':'2002','1999':'1999','1995':'1995','1991':'1991','1987':'1987','1983':'1983','1977':'1977','1973':'1973','1969':'1969','1965':'1965','1961':'1961','1957':'1957','1954':'1954','1950':'1950'};
  const REF_YEAR_ORDER = ['2017referandum','2010referandum','2007referandum','1988referandum','1987referandum','1982referandum','1961referandum'];
  const REF_YEAR_LABEL = {'2017referandum':'2017','2010referandum':'2010','2007referandum':'2007','1988referandum':'1988','1987referandum':'1987','1982referandum':'1982','1961referandum':'1961'};
  const YEREL_YEAR_ORDER = ['2024yerel','2019yerel','2014yerel','2009yerel','2004yerel','1999yerel','1994yerel','1989yerel','1984yerel'];
  const YEREL_YEAR_LABEL = {'2024yerel':'2024','2019yerel':'2019','2014yerel':'2014','2009yerel':'2009','2004yerel':'2004','1999yerel':'1999','1994yerel':'1994','1989yerel':'1989','1984yerel':'1984'};
  // 1950-1961 genel secimlerinde vekil (sandalye) verisi onceden (Wikipedia
  // kaynakli) yoktu; artik YSK'nin resmi, TUIK kaynakli 1950-1977 il arsivinden
  // var (bkz. scripts/genel-1950-1977-pipeline/). Bos kalirsa (gelecekte baska
  // bir yil icin ayni durum olursa) buraya eklenebilir.
  const YEARS_NO_VEKIL = new Set([]);
  // 1950-1987 genel secimlerinde ve 1961/1982/1987/1988/2007 referandumlarinda ilce-bazli
  // kaynak yok - sadece il seviyesinde veri var.
  const YEARS_IL_ONLY = new Set(['1950','1954','1957','1961','1965','1969','1973','1977','1983','1987',
    '1961referandum','1982referandum','1987referandum','1988referandum']);
  // 2026-09-22: YSK'nin resmi il-bazli (1950/1954/1957/1961 genel,
  // 1961/1982/1987/1988 referandum) veya il+ilce-bazli (2007referandum,
  // 2014cb) arsivlerine yukseltilen yillar — kaynakLine bunlar icin ozel.
  const YEARS_YSK_OFFICIAL_IL = new Set(['1950','1954','1957','1961','1965','1969','1973','1977',
    '1961referandum','1982referandum','1987referandum','1988referandum']);
  const CB_YEAR_ORDER = ['2023cb2tur','2023cb1tur','2018cb','2014cb'];
  const CB_YEAR_LABEL = {'2023cb2tur':'2023 (2.Tur)','2023cb1tur':'2023 (1.Tur)','2018cb':'2018','2014cb':'2014'};

