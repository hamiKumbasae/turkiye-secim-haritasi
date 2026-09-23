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
      btn.className = 'year-item' + (y===currentYear ? ' active' : '');
      btn.textContent = labels[y];
      btn.addEventListener('click', ()=> loadYear(y));
      wrap.appendChild(btn);
    }
    const active = wrap.querySelector('.year-item.active');
    if(active) active.scrollIntoView({inline:'center', block:'nearest'});
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

    $('#detailEmpty').style.display='block';
    $('#detailBody').style.display='none';
    $('#detailEmpty').textContent = 'Bir ile tıklayarak veya arayarak detayları görün.';
    $('#btnTableViewCount').textContent = DATA.iller.length;
    $('#dSeatsLabel').textContent = isRef ? 'Sonuç' : (isYerel || isCB || YEARS_NO_VEKIL.has(currentYear) ? 'Kazanan' : 'Milletvekili');
    $('#tableTitle').textContent = 'Türkiye · '+DATA.ad+' · İl Sonuçları';

    resetMapModeUI();

    renderElectionBar();
    renderNationalSummary();
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

  switchTur('genel');
