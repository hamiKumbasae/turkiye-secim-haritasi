  // ---------------- theme change redraw ----------------
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', ()=>{
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
      btn.className = 'year-btn' + (y===currentYear ? ' active' : '');
      btn.textContent = labels[y];
      btn.addEventListener('click', ()=> loadYear(y));
      wrap.appendChild(btn);
    }
  }

  function switchTur(tur){
    currentTur = tur;
    $('#btnTurGenel').classList.toggle('active', tur==='genel');
    $('#btnTurReferandum').classList.toggle('active', tur==='referandum');
    $('#btnTurYerel').classList.toggle('active', tur==='yerel');
    $('#btnTurCB').classList.toggle('active', tur==='cumhurbaskanligi');
    loadYear(TUR_YEARS[tur][0]);
  }

  async function loadYear(year){
    currentYear = year;
    await ensureGeoForYear(year);
    DATA = BUNDLE.secimler[year];
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
    const titleSuffix = isRef ? ' Referandumu Sonuçları' : (isYerel ? ' Yerel Seçim Sonuçları' : (isCB ? ' Cumhurbaşkanlığı Seçimi Sonuçları' : ' Seçim Sonuçları'));
    $('#pageTitle').textContent = DATA.ad+titleSuffix;
    const scopeLine = isRef ? 'Halk Oylaması' : (isYerel ? 'Belediye başkanlığı' : (isCB ? 'Cumhurbaşkanlığı' : (DATA.toplamSandalye!=null ? DATA.toplamSandalye+' milletvekilliği' : 'Milletvekili genel seçimi')));
    const kaynakLine = currentYear==='2014cb' ? 'Kaynak: YSK Açık Veri Portalı (acikveri.ysk.gov.tr, resmi API)'
      : YEARS_IL_ONLY.has(currentYear) ? 'Kaynak: Türkçe Wikipedia (YSK kesin sonuçlarına dayalı, sadece il seviyesi)'
      : (currentYear==='2009yerel'||currentYear==='2004yerel') ? 'Kaynak: Türkçe Wikipedia (YSK/basın kaynaklı il alt-sayfaları)'
      : 'Kaynak: secim.haberturk.com (YSK kesin sonuçlarına dayalı)';
    $('#metaLine').innerHTML = kaynakLine+'<br>'+
      scopeLine+' · '+DATA.iller.length+' il · '+DATA.ilceler.length+' ilçe';
    $('#detailEmpty').style.display='block';
    $('#detailBody').style.display='none';
    $('#detailEmpty').textContent = 'Bir ile tıklayarak veya arayarak detayları görün.';
    $('#btnTableViewCount').textContent = DATA.iller.length;
    $('#dSeatsLabel').textContent = isRef ? 'Sonuç' : (isYerel || isCB || YEARS_NO_VEKIL.has(currentYear) ? 'Kazanan' : 'Vekil');
    $('#eyebrowText').textContent = isRef ? 'Türkiye · Halk Oylaması (Referandum) · 1961–2017'
      : (isYerel ? 'Türkiye · Yerel Seçimler (Belediye Başkanlığı) · 1984–2024'
      : (isCB ? 'Türkiye · Cumhurbaşkanlığı Seçimleri · 2014–2023' : 'Türkiye · Milletvekili Genel Seçimleri · 1950–2023'));
    $('#mapMode').querySelector('option[value="winner"]').textContent = isRef ? 'Evet / Hayır' : 'Kazanan parti';
    $('#optAkp').textContent = isRef ? 'Evet oy oranı' : (isCB ? '1. Aday oy oranı' : 'AK Parti oy oranı');
    $('#optChp').textContent = isRef ? 'Hayır oy oranı' : (isCB ? '2. Aday oy oranı' : 'CHP oy oranı');

    renderYearPicker();
    renderSeatBar();
    renderYurtdisiCard();
    renderCountryMap();
    renderTable();
  }

  $('#btnTurGenel').addEventListener('click', ()=> switchTur('genel'));
  $('#btnTurReferandum').addEventListener('click', ()=> switchTur('referandum'));
  $('#btnTurYerel').addEventListener('click', ()=> switchTur('yerel'));
  $('#btnTurCB').addEventListener('click', ()=> switchTur('cumhurbaskanligi'));

  loadYear(CB_YEAR_ORDER[0]);
