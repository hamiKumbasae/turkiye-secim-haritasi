  // ---------------- paylasilabilir baglanti ----------------
  // Gorunum adres cubugundaki # kisminda tutulur: #secim=1977&il=6&ilce=TR-D-06-001&mod=parti&parti=CHP
  // (yerel secimde &oylama=igm|bm). Bu baglantiyla acilan sayfa ayni gorunume gider. Adres
  // replaceState ile guncellenir (her tiklama tarayici gecmisine eklenmez).
  const MODLAR = ['winner', 'katilim', 'parti', 'degisim'];
  let baglantiUygulaniyor = false;
  let seciliIlce = null; // panelde secili ilce (geomId); selectDistrict ayarlar

  function durumParametreleri(){
    const q = new URLSearchParams();
    if(!currentYear) return q;
    q.set('secim', currentYear);
    if(currentTur === 'yerel' && currentOylama && currentOylama !== 'baskan') q.set('oylama', currentOylama);
    const il = view.level === 'country' ? selectedPlaka : view.plaka;
    if(il) q.set('il', il);
    const ilce = view.level === 'mahalle' || view.level === 'meclis-ilce' ? view.geomId : (view.level === 'province' ? seciliIlce : null);
    if(il && ilce) q.set('ilce', ilce);
    if(currentMapMode && currentMapMode !== 'winner'){
      q.set('mod', currentMapMode);
      if((currentMapMode === 'parti' || currentMapMode === 'degisim') && currentMapParty) q.set('parti', currentMapParty);
    }
    return q;
  }
  function durumuYaz(){
    if(baglantiUygulaniyor || !currentYear) return;
    const hash = '#' + durumParametreleri().toString();
    if(location.hash !== hash) history.replaceState(null, '', hash);
  }

  // Acilista (ve adres elle degistirildiginde) baglantidaki gorunume gider; gecersiz ya da eksik
  // parametreler yok sayilir.
  async function baglantiyiUygula(){
    const q = new URLSearchParams(location.hash.slice(1));
    const secim = q.get('secim');
    const tur = secim && Object.keys(TUR_YEARS).find(t => TUR_YEARS[t].includes(secim));
    baglantiUygulaniyor = true;
    try{
      if(!tur){ await switchTur('genel'); return; }
      const oylama = q.get('oylama');
      currentOylama = ['igm', 'bm'].includes(oylama) ? oylama : 'baskan';
      await switchTur(tur, secim);
      if(currentYear !== secim) return; // yuklenemedi ya da bu arada baska secim secildi
      const parti = q.get('parti');
      if(parti && MAJOR.includes(parti)){ currentMapParty = parti; $('#partySelect').value = parti; }
      const mod = q.get('mod');
      const dugme = MODLAR.includes(mod) && $('#modeGroup button[data-mode="' + mod + '"]');
      if(dugme && !dugme.hidden && mod !== 'winner') await setMapMode(mod);
      const il = parseInt(q.get('il'), 10);
      if(il && ilByPlaka[il]){
        await goToProvince(il);
        const ilce = q.get('ilce');
        if(ilce && view.level === 'province' && districtByGeomId[ilce]) await openDistrict(il, ilce);
      }
    }finally{
      baglantiUygulaniyor = false;
      durumuYaz();
    }
  }
  window.addEventListener('hashchange', () => {
    if(!baglantiUygulaniyor && location.hash !== '#' + durumParametreleri().toString()) baglantiyiUygula();
  });

  $('#btnPaylas').addEventListener('click', async () => {
    durumuYaz();
    const btn = $('#btnPaylas');
    try{
      await navigator.clipboard.writeText(location.href);
      btn.textContent = 'Bağlantı kopyalandı ✓';
    }catch(error){
      window.prompt('Bu görünümün bağlantısı:', location.href);
    }
    setTimeout(() => { btn.textContent = 'Bağlantıyı kopyala'; }, 2000);
  });
