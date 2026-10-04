  // ---------------- erisilebilirlik ----------------
  // 1) Renk korlugu dostu palet (Okabe-Ito): acik secimdeki partiler siralarina (MAJOR) gore 7 ayirt
  //    edilebilir renk alir, kalanlar gri. partyColor bunu kullanir; tercih tarayicida saklanir.
  // 2) Klavye ve ekran okuyucu: harita bolgeleri Tab ile gezilir, Enter/Bosluk ile acilir, odakta
  //    ipucu kutusu gosterilir; her bolgenin "Adana: AK Parti önde" gibi bir etiketi vardir.
  // 3) Dokunmatik ekran: haritanin disina dokununca ya da kaydirinca ipucu kutusu kapanir.
  const RENK_KORU_PALET = ['#E69F00', '#0072B2', '#009E73', '#D55E00', '#56B4E9', '#CC79A7', '#F0E442'];
  let renkKoruModu = false;
  try{ renkKoruModu = localStorage.getItem('renkKoruModu') === '1'; }catch(error){ /* depolama kapali */ }
  function renkKoruRengi(name){
    const i = MAJOR ? MAJOR.indexOf(name) : -1;
    return i >= 0 && i < RENK_KORU_PALET.length ? RENK_KORU_PALET[i] : '#9a9a9a';
  }
  function renkKoruDugmesi(){
    const b = $('#btnRenkKoru');
    b.classList.toggle('active', renkKoruModu);
    b.setAttribute('aria-pressed', String(renkKoruModu));
  }
  renkKoruDugmesi();
  $('#btnRenkKoru').addEventListener('click', () => {
    renkKoruModu = !renkKoruModu;
    try{ localStorage.setItem('renkKoruModu', renkKoruModu ? '1' : '0'); }catch(error){ /* depolama kapali */ }
    renkKoruDugmesi();
    if(!DATA) return;
    applyMapMode(); renderSeatBar(); renderTable();
    if(selectedPlaka && view.level === 'country') selectProvince(selectedPlaka);
  });

  const haritaSvg = $('#mapSvg');
  function bolgeKaydi(el){
    if(el.dataset.mahalleId) return currentMahalleRows.find(r => r.id === el.dataset.mahalleId);
    if(el.dataset.geomId && view.level==='meclis-ilce') return MECLIS_2024[el.dataset.geomId];
    if(el.dataset.geomId) return districtByGeomId[el.dataset.geomId];
    if(el.dataset.plaka) return ilByPlaka[+el.dataset.plaka];
    return null;
  }
  function haritayiErisilebilirYap(){
    if(!DATA) return;
    const baslik = view.level === 'country' ? 'Türkiye haritası, illere göre sonuç'
      : (ilByPlaka[view.plaka] ? ilByPlaka[view.plaka].ad : '') + (view.level === 'mahalle' ? ' mahalle haritası' : ' ilçe haritası');
    haritaSvg.setAttribute('role', 'group');
    haritaSvg.setAttribute('aria-label', baslik + '. Bölgeler arasında Tab ile gezinip Enter ile açabilirsiniz.');
    for(const el of haritaSvg.querySelectorAll('path')){
      const r = bolgeKaydi(el);
      if(!r || el.classList.contains('geo-path-nodata')) continue;
      el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'button');
      el.setAttribute('aria-label', r.ad + (r.kazanan ? ': ' + partyShort(r.kazanan) + (view.level==='meclis-ilce' ? ' mecliste en çok sandalye' : ' önde') : ''));
      if(el.dataset.klavye) continue;
      el.dataset.klavye = '1';
      el.addEventListener('keydown', e => {
        if(e.key !== 'Enter' && e.key !== ' ') return;
        e.preventDefault();
        el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
      });
      el.addEventListener('focus', () => {
        const b = el.getBoundingClientRect();
        el.dispatchEvent(new MouseEvent('mousemove', {clientX: b.left + b.width / 2, clientY: b.top + b.height / 2}));
      });
      el.addEventListener('blur', hideTooltip);
    }
  }
  // her cizimden sonra (ulke, il, mahalle; yil ya da mod degisikligi) etiketler yenilenir
  new MutationObserver(() => requestAnimationFrame(haritayiErisilebilirYap)).observe(haritaSvg, {childList: true});

  document.addEventListener('touchstart', e => {
    if(!(e.target.closest && e.target.closest('#mapSvg'))) hideTooltip();
  }, {passive: true});
  window.addEventListener('scroll', hideTooltip, {passive: true});
