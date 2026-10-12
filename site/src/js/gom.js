  // ---------------- gomme (iframe) ----------------
  // "Göm" dugmesi o anki gorunumun (paylasilabilir baglantidaki her sey: secim, il/ilce, mod,
  // parti, karsilastirma) iframe kodunu verir. Kod adresine &gom=1 eklenir: sayfa basindaki kucuk
  // betik <html>'e "gomulu" sinifini koyar ve CSS yalniz baslik, harita, lejant ve kaynak satirini
  // gosterir. &tema=acik|koyu okurun cihaz ayarindan bagimsiz tema secer (haber sayfalarinin
  // cogu acik zeminli oldugu icin varsayilan acik).
  const GOMULU = document.documentElement.classList.contains('gomulu');
  const GOM_TEMA = GOMULU ? new URLSearchParams(location.hash.slice(1)).get('tema') : null;
  const YAYIN_ADRESI = 'https://hamikumbasae.github.io/turkiye-secim-haritasi/';

  // Yerelde (file://) acilmis tek dosya surumu gomulemez: kod yayindaki siteyi gosterir.
  function sayfaAdresi(){
    return /^https?:$/.test(location.protocol) ? location.origin + location.pathname : YAYIN_ADRESI;
  }
  function gomsuzParametreler(){
    const q = durumParametreleri();
    q.delete('gom'); q.delete('tema');
    return q;
  }
  function gomAltGuncelle(){
    $('#gomTamEkran').href = sayfaAdresi() + '#' + gomsuzParametreler().toString();
  }

  function gomAdresi(tema){
    const q = gomsuzParametreler();
    q.set('gom', '1');
    if(tema) q.set('tema', tema);
    return sayfaAdresi() + '#' + q.toString();
  }
  function gomKodu(){
    const adres = gomAdresi($('#gomTema').value);
    const yer = view.level !== 'country' && ilByPlaka[view.plaka] ? ilByPlaka[view.plaka].ad + ' · ' : '';
    const baslik = 'Türkiye Seçim Tarihi Atlası: ' + yer + $('#pageTitle').textContent;
    $('#gomOnizle').href = adres;
    return '<iframe src="' + escapeHtml(adres) + '" width="100%" height="' + $('#gomYukseklik').value +
      '" style="border:0;max-width:100%" loading="lazy" title="' + escapeHtml(baslik) + '"></iframe>';
  }
  function gomKoduYaz(){ $('#gomKod').value = gomKodu(); }

  $('#btnGom').addEventListener('click', () => {
    durumuYaz();
    const yerel = !/^https?:$/.test(location.protocol);
    $('#gomNot').hidden = !yerel;
    $('#gomNot').textContent = yerel ? 'Bu sayfa bilgisayarınızdan açıldığı için kod, yayındaki siteyi (' + YAYIN_ADRESI + ') gösterir.' : '';
    // yan yana iki harita daha kisa yer kaplar
    $('#gomYukseklik').value = KARSI.acik ? '480' : '560';
    gomKoduYaz();
    const pencere = $('#gomPencere');
    if(pencere.showModal) pencere.showModal(); else pencere.setAttribute('open', '');
    $('#gomKod').select();
  });
  $('#gomYukseklik').addEventListener('change', gomKoduYaz);
  // Tek dosya surumunde (file://) veri.html ve veri/ yok: acik veri baglantilari yayindaki siteye gider
  if(GOMULU_VERI) for(const a of $$('a[href="veri.html"]')) a.href = YAYIN_ADRESI + 'veri.html';
  $('#gomTema').addEventListener('change', gomKoduYaz);
  $('#gomKapat').addEventListener('click', () => $('#gomPencere').close());
  $('#gomKopyala').addEventListener('click', async () => {
    const btn = $('#gomKopyala');
    try{ await navigator.clipboard.writeText($('#gomKod').value); btn.textContent = 'Kopyalandı ✓'; }
    catch(error){ $('#gomKod').select(); btn.textContent = 'Seçili, Ctrl+C ile kopyalayın'; }
    setTimeout(() => { btn.textContent = 'Kodu kopyala'; }, 2000);
  });
