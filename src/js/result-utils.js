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
    if(!result) return null;
    return isSeatBased(result) ? result.oranSandalye : result.oran;
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

