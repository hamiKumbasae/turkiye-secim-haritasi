  // ---------------- theme change redraw ----------------
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', ()=>{
    if(!DATA) return;
    applyMapMode(); renderSeatBar();
    if(selectedPlaka) selectProvince(selectedPlaka);
  });

  // ---------------- year / type switching ----------------
  const TUR_YEARS = {genel: YEAR_ORDER, referandum: REF_YEAR_ORDER, yerel: YEREL_YEAR_ORDER, cumhurbaskanligi: CB_YEAR_ORDER};
  const TUR_LABELS = {genel: YEAR_LABEL, referandum: REF_YEAR_LABEL, yerel: YEREL_YEAR_LABEL, cumhurbaskanligi: CB_YEAR_LABEL};

  function renderYearPicker(){
    const wrap = $('#yearPicker'); wrap.innerHTML = '';
    const order = TUR_YEARS[currentTur];
    const labels = TUR_LABELS[currentTur];
    for(const y of order){
      const btn = document.createElement('button');
      btn.className = 'year-item' + (y===currentYear ? ' active' : '');
      btn.textContent = labels[y];
      btn.addEventListener('click', ()=> loadYear(y));
      wrap.appendChild(btn);
    }
    const active = wrap.querySelector('.year-item.active');
    if(active) active.scrollIntoView({inline:'center', block:'nearest'});
  }

  function switchTur(tur, year){
    currentTur = tur;
    $('#btnTurGenel').classList.toggle('active', tur==='genel');
    $('#btnTurReferandum').classList.toggle('active', tur==='referandum');
    $('#btnTurYerel').classList.toggle('active', tur==='yerel');
    $('#btnTurCB').classList.toggle('active', tur==='cumhurbaskanligi');
    renderYearPicker();
    return loadYear(year || TUR_YEARS[tur][0]);
  }

  // Fetch async oldugu icin hizli art arda yil degistirmede eski istek gec
  // gelip yeniyi ezebilir - her cagriya bir "bilet" verilir, sadece en son
  // cagrinin sonucu uygulanir.
  let loadYearTicket = 0;
  async function loadYear(year){
    const ticket = ++loadYearTicket;
    const oylama = currentOylama;
    cancelDistrictLoad();
    setResultsBusy(true);
    showLoadStatus('Seçim sonuçları yükleniyor…');
    try{
      // Geo (harita siniri) ve secim verisi (il/ilce sonuclari) BAGIMSIZ
      // dosyalar - ikisini paralel fetch etmek, sirayla beklemekten daha hizli.
      const [geo, data] = await Promise.all([ensureGeoForYear(year), fetchElection(year)]);
      if(ticket !== loadYearTicket) return; // bu arada baska bir yil secildi, bu sonuc artik gecersiz
      const kayit = await oylamaKaydi(year, data, oylama);
      if(ticket !== loadYearTicket) return;
      GEO = geo;
      countryProject = computeProjection(GEO.features, PAD);
      currentYear = year;
      currentOylama = kayit.oylama || 'baskan';
      DATA = kayit;
      MAJOR = DATA.majorPartiler;
      ilByPlaka = Object.fromEntries(DATA.iller.map(p => [p.plaka, p]));
      districtsByPlaka = {};
      for(const d of DATA.ilceler){ (districtsByPlaka[d.plaka] ||= []).push(d); }
      districtByGeomId = {};
      for(const d of DATA.ilceler){ if(d.geomId) districtByGeomId[d.geomId] = d; }

      selectedPlaka = null;
      const isRef = DATA.tur === 'referandum';
      const isYerel = DATA.tur === 'yerel';
      const isCB = DATA.tur === 'cumhurbaskanligi';

      $('#detailEmpty').style.display='block';
      $('#detailBody').style.display='none';
      $('#detailEmpty').textContent = 'Bir ile tıklayarak veya arayarak detayları görün.';
      $('#detailViewToggle').style.display='none';
      detailView = 'baskanlik';
      $('#btnTableViewCount').textContent = DATA.iller.length;
      $('#dSeatsLabel').textContent = isRef ? 'Sonuç' : (isYerel || isCB || YEARS_NO_VEKIL.has(currentYear) ? 'Kazanan' : 'Milletvekili');
      $('#tableTitle').textContent = 'Türkiye · '+DATA.ad+' · İl Sonuçları';

      resetMapModeUI();

      renderElectionBar();
      renderNationalSummary();
      renderYearPicker();
      renderOylamaToggle();
      renderSeatBar();
      renderYurtdisiCard();
      renderCountryMap();
      renderTable();
      setResultsBusy(false);
      clearLoadStatus();
      // ilk ile inmeden once ilce sinirlarini arka planda indir (hata olursa ile inerken yeniden denenir)
      setTimeout(() => ensureIlceGeo().catch(() => {}), 0);
      durumuYaz();
    }catch(error){
      if(ticket !== loadYearTicket) return;
      // Keep old results inert: they must not be mistaken for the requested election.
      showLoadStatus('Seçim sonuçları yüklenemedi. Bağlantınızı kontrol edip yeniden deneyin.', () => loadYear(year));
    }
  }

  $('#btnTurGenel').addEventListener('click', ()=> switchTur('genel'));
  $('#btnTurReferandum').addEventListener('click', ()=> switchTur('referandum'));
  $('#btnTurYerel').addEventListener('click', ()=> switchTur('yerel'));
  $('#btnTurCB').addEventListener('click', ()=> switchTur('cumhurbaskanligi'));

  baglantiyiUygula(); // adresteki #secim=... gorunumu, yoksa son genel secim
