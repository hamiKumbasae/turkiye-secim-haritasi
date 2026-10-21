  // ---------------- oy/sandalye sonuc yardimcilari ----------------
  // Bir "result" nesnesi (secim kaydindaki oy['<parti>'] girisi) iki farkli
  // sekilde gelebilir: dogrudan-oy secimlerinde {oy, oran[, aday, sandalye]},
  // dolayli/meclis-bazli yerel secimlerde (1950/1955, bkz. contestType=
  // municipal_indirect) {sandalye, oranSandalye} - oy/oran o zaman null'dur.
  // Bu dosya, hangisinin gecerli oldugunu TEK YERDEN belirler; detail-panel.js,
  // tooltip.js, table.js, map.js kendi kafasina gore .oran/.oy secmez, hepsi
  // bu 3 fonksiyonu cagirir - boylece ileride modulere ayrilsa bile (build.py
  // hepsini tek closure'da birlestirmese bile) semantik TEK yerde kalir.

  function isSeatBased(result){
    return !!result && (result.oy==null || result.oy===0) && result.sandalye!=null;
  }

  // Siralama/renk-skalasi/bar-genisligi icin TEK sayisal yuzde - hangi alanin
  // (oran vs oranSandalye) okunacagini cagiran taraf bilmek zorunda degil.
  function resultPercent(result){
    if(!result || result.yuzdeDogrulanmadi) return null;
    const value = isSeatBased(result) ? result.oranSandalye : result.oran;
    return Number.isFinite(value) && value>=0 && value<=100 ? value : null;
  }

  // Insan-okunur yuzde etiketi ('%12.34' / '%12.3' / '—'). Sandalye-bazli
  // kayitlar 1 ondalik, oy-bazli kayitlar 2 ondalik kullanir (projenin
  // onceki, kaynaktaki hassasiyet farkini yansitan konvansiyonu).
  function resultPercentLabel(result){
    const p = resultPercent(result);
    if(p==null) return '—';
    return '%' + (isSeatBased(result) ? p.toFixed(1) : p.toFixed(2));
  }

  // Ham miktar etiketi ('123.456 oy' / '29 meclis sandalyesi' / '—').
  function resultQuantity(result){
    if(!result) return '—';
    if(isSeatBased(result)) return result.sandalye!=null ? result.sandalye+' meclis sandalyesi' : '—';
    return result.oy!=null ? fmt(result.oy)+' oy' : '—';
  }

  // Bir parti anahtarinin GOSTERIM adi ('PARTY[x] ? PARTY[x].short : x' -
  // eskiden 15 farkli yerde tekrar tekrar yazilmisti, artik TEK yerden).
  // 'Diğer' bir parti degil: kaynakta ayri verilmeyen kucuk partilerin toplami. Hicbir siralamada
  // partilerle yarismaz, her listede (panel, tablo, lejant, CSV) en sona konur; kazanan
  // gorunuyorsa adi bunun bir toplam oldugunu soyler.
  const DIGER = 'Diğer';
  function digerSona(liste){
    return liste.includes(DIGER) ? [...liste.filter(p => p !== DIGER), DIGER] : liste;
  }
  function kazananEtiketi(name){
    return name === DIGER ? 'Diğer (ayrıştırılmamış)' : partyShort(name);
  }
  // Mahallede oy kullanan > kayitli secmen (YSK verisinde ~26 bin mahalle kaydi): oran anlamsiz,
  // gosterilmez. Oy sayilari kaynaktaki gibi kalir.
  const KATILIM_ASIM_NOTU = 'ⓘ Katılım hesaplanamıyor: YSK kaydında oy kullanan sayısı kayıtlı seçmenden fazla. Sandık görevlileri ve listede olmayan bazı seçmenler kayıtlı olmadıkları sandıkta oy kullanabildiği için küçük birimlerde görülür. Oy sayıları kaynaktaki gibidir.';
  function katilimEtiketi(obj){
    return obj.katilim != null ? '%' + obj.katilim.toFixed(2) : obj.katilimHesaplanamaz ? 'hesaplanamıyor' : '—';
  }
  const DIGER_KAZANAN_NOTU = 'ⓘ En çok oyu \'Diğer\' alıyor: kaynakta ayrı verilmeyen küçük partilerin toplamı. Bu kayıtta kazanan parti ayrıştırılmamış.';

  function partyShort(name){
    return PARTY[name] ? PARTY[name].short : name;
  }

  // Tablo/tooltip basliklarinda "%" mi "vekil/sandalye sayisi" mi
  // gosterilecegini belirleyen kosul - eskiden table.js/tooltip.js'te
  // ayri ayri (ama birebir ayni) tanimlanmisti.
  function isOranMode(){
    return DATA.tur==='referandum' || DATA.tur==='yerel' || DATA.tur==='cumhurbaskanligi' || YEARS_NO_VEKIL.has(currentYear);
  }

  // Bu secimde ayrica bir "yurtdisi" paneli gosterilecek mi - eskiden
  // seatbar.js/summary.js'te ayri ayri (ama birebir ayni) tanimlanmisti.
  function hasYurtdisiData(){
    return !!(DATA.yurtdisi && DATA.yurtdisi.oy && Object.keys(DATA.yurtdisi.oy).length);
  }

  // Kayit kaynakla dogrulanamadi mi (prepareElection'in isaretleri: oy toplami, yuzde, cift eslesme,
  // gecerli oy > secmen)? Ipucu kutusu ve detay paneli bunu kisa bir uyariyla gosterir.
  function kaynaklaTutmuyor(r){
    return !!r && (!!r.yuzdeDogrulanmadi || !!(r.secmen && r.gecerliOy > r.secmen));
  }
