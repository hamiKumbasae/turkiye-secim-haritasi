  // ---------------- province detail ----------------
  let selectedPlaka = null;
  let detailView = 'baskanlik'; // 'baskanlik' | 'meclis' - sadece 2024yerel + MECLIS_PROVINCES'ta anlamli

  function meclisToggleApplicable(plaka){
    return DATA.tur==='yerel' && currentYear==='2024yerel' && MECLIS_PROVINCES.has(plaka);
  }

  // Deger yoksa satiri TAMAMEN gizler ('—' yerine) - eski secimlerde art arda
  // bos alan gostermek yerine, sadece gercekten var olan veriyi listeler.
  function hideEmptyStatRows(){
    for(const id of ['dTurnout','dSecmen','dGecerli','dSeats']){
      const val = $('#'+id);
      const row = val.closest('.stat-row');
      const t = val.textContent;
      row.style.display = (t==='—' || t==='') ? 'none' : '';
    }
  }

  function setHero(label, name, colorKey, pct){
    $('#dHeroLabel').textContent = label;
    $('#dHeroDot').style.background = colorKey ? partyColor(colorKey) : 'var(--map-empty)';
    $('#dHeroName').textContent = name || '—';
    $('#dHeroPct').textContent = pct!=null ? '%'+pct.toFixed(2) : '';
  }

  // isSeatBased/resultPercent/resultQuantity artik result-utils.js'te (paylasimli,
  // tooltip.js/table.js/map.js ile AYNI mantik) - burada tekrar tanimlanmiyor.

  function partyRowEl(r){
    const short = PARTY[r.name] ? PARTY[r.name].short : r.name;
    const pct = resultPercent(r.oy) || 0;
    const el = document.createElement('div'); el.className='party-row';
    el.innerHTML = '<div class="prow-top">'+
        '<span class="dot" style="background:'+partyColor(r.name)+'"></span>'+
        '<span class="name">'+short+'</span>'+
        '<span class="pct">'+resultPercentLabel(r.oy)+'</span>'+
        '<span class="oy">'+resultQuantity(r.oy)+'</span>'+
        (r.vekil>0 ? '<span class="vekil">'+r.vekil+'</span>' : '')+
      '</div>'+
      '<div class="bar-track"><div class="bar-fill" style="width:'+Math.max(pct,0)+'%; background:'+partyColor(r.name)+'"></div></div>';
    return el;
  }

  function selectProvince(plaka){
    selectedPlaka = plaka;
    detailView = 'baskanlik';
    $$('.il-path').forEach(p=>p.classList.toggle('selected', +p.dataset.plaka===plaka));
    const p = ilByPlaka[plaka]; if(!p) return;
    $('#detailEmpty').style.display='none';
    $('#detailBody').style.display='block';
    $('#dName').textContent = p.ad;
    $('#dPlaka').textContent = 'Plaka '+String(plaka).padStart(2,'0');

    const showToggle = meclisToggleApplicable(plaka);
    $('#detailViewToggle').style.display = showToggle ? 'flex' : 'none';
    if(showToggle) $$('#detailViewToggle button').forEach(b=>b.classList.toggle('active', b.dataset.view==='baskanlik'));

    const heroOy = p.kazanan ? p.oy[p.kazanan] : null;
    const heroSeatBased = heroOy && isSeatBased(heroOy);
    // contestType='municipal_indirect' TUM SECIM icin gecerli (1950/1955 yerel) -
    // 1955'te bazi illerde gercek oy sayisi de olsa (resultBasis='mixed'), o ilin
    // belediye baskani YINE meclis tarafindan seciliyordu, sadece oy SAYISI
    // biliniyor. Bu yuzden not/etiket heroSeatBased'e (o ilin veri TURUNE) degil,
    // DATA.contestType'a (secimin KENDI doga bicimine) bakmali.
    const isIndirectElection = DATA.contestType === 'municipal_indirect';
    const heroLabel = DATA.tur==='referandum' ? 'Sonuç'
      : heroSeatBased ? 'Meclis Çoğunluğu'
      : isIndirectElection ? 'Belediye Meclisi Seçiminde Birinci'
      : 'Kazanan';
    const heroPct = heroOy ? resultPercent(heroOy) : null;
    setHero(heroLabel, p.kazanan && PARTY[p.kazanan]?PARTY[p.kazanan].short:p.kazanan, p.kazanan, heroPct);

    // council_seats (1950): TUM iller sandalye-bazli, tek aciklama yeterli.
    // mixed (1955): bazi illerde gercek oy sayisi da biliniyor - kullaniciya
    // bunun il'e gore DEGISTIGINI de soylemek gerekiyor, tek cumlelik
    // "meclis dagilimi" aciklamasi burada yaniltici olurdu.
    $('#dInfoNote').style.display = isIndirectElection ? 'flex' : 'none';
    if(isIndirectElection){
      $('#dInfoNote').textContent = DATA.resultBasis==='mixed'
        ? 'ⓘ Bu seçimde belediye başkanı doğrudan halk tarafından seçilmiyordu. Kaynak kapsamına göre bazı illerde oy sonuçları, bazı illerde meclis sandalye dağılımı gösterilir.'
        : 'ⓘ Bu seçimde belediye başkanı doğrudan halk tarafından seçilmiyordu. Sonuçlar belediye meclisi dağılımını temel alır.';
    }

    $('#dSeatsLabel').textContent = (DATA.tur !== 'genel' || YEARS_NO_VEKIL.has(currentYear)) ? 'Vekil / Sandalye' : 'Milletvekili';
    $('#dSeats').textContent = (DATA.tur !== 'genel' || YEARS_NO_VEKIL.has(currentYear)) ? (p.toplamVekil || '—') : p.toplamVekil;
    $('#dTurnout').textContent = p.katilim!=null ? '%'+p.katilim.toFixed(2) : '—';
    $('#dSecmen').textContent = p.secmen!=null ? fmt(p.secmen) : '—';
    $('#dGecerli').textContent = p.gecerliOy!=null ? fmt(p.gecerliOy) : '—';
    hideEmptyStatRows();

    $('#dResultsHead').textContent = (DATA.resultBasis==='council_seats') ? 'Meclis Sandalye Dağılımı' : 'Sonuçlar';
    renderPartyResults(p);

    // Bu il icin HIC ilce-duzeyi veri yoksa (orn. 1965 genel), "İlçeler"
    // basligi/arama/liste bolumunu hic gostermiyoruz - olmayan bir alt
    // seviyeyi varmis gibi sunmak yaniltici olurdu (bkz. son inceleme).
    const hasDistricts = provinceHasDistrictData(plaka);
    $('#dDistrictsLabel').textContent = 'İlçeler';
    $('#dDistrictsLabel').style.display = hasDistricts ? '' : 'none';
    $('#districtSearch').style.display = hasDistricts ? '' : 'none';
    $('#dDistrictList').style.display = hasDistricts ? '' : 'none';
    if(hasDistricts){
      renderDistrictList(plaka, '');
      $('#districtSearch').value='';
      $('#districtSearch').oninput = e => renderDistrictList(plaka, e.target.value);
    } else {
      $('#dDistrictList').innerHTML='';
    }
  }

  // il (p) VEYA ilce (d) kaydinin oy['<parti>'] sozlugunu #dParties'e cizer -
  // selectProvince ve selectDistrict AYNI mantigi paylasir (kod tekrari yok).
  // Butun il/ilce'de gercekten oy alan HER parti (baraj alti kucuk partiler ve
  // bagimsizlar dahil) - MAJOR listesi sadece hangilerinin ilk sirada, hangilerinin
  // "digerleri" acilir-kapanir bolumune gidecegini belirliyor.
  function renderPartyResults(entity){
    const rank = r => isSeatBased(r.oy) ? (r.oy.sandalye||0) : (r.oy.oy||0);
    const allNamed = Object.entries(entity.oy||{}).map(([name,oy])=>({name, oy, vekil:(entity.vekil&&entity.vekil[name])||0}))
      .filter(r=>r.oy && (r.oy.oy>0 || r.oy.sandalye>0));
    const majorSet = new Set(MAJOR);
    const primary = allNamed.filter(r=>majorSet.has(r.name)).sort((a,b)=> rank(b) - rank(a));
    const extra = allNamed.filter(r=>!majorSet.has(r.name)).sort((a,b)=> rank(b) - rank(a));
    // primary bossa (orn. yerel'de MAJOR il-kazananlari listesi bu ilde/ilcede hic
    // gecmiyorsa) en cok oy alan birkac partiyi one al, kalanlari "digerleri"ne birak.
    const rows = primary.length ? primary : extra.splice(0, Math.min(5, extra.length));
    if(DATA.tur !== 'yerel' && entity.digerOy>0) rows.push({name:'Diğer', oy:{oy:entity.digerOy, oran:entity.digerOran}, vekil:0});
    const wrap = $('#dParties'); wrap.innerHTML='';
    for(const r of rows) wrap.appendChild(partyRowEl(r));
    if(extra.length){
      const details = document.createElement('details'); details.className='party-more';
      const summary = document.createElement('summary');
      summary.textContent = 'Diğer partileri ve bağımsızları göster ('+extra.length+')';
      details.appendChild(summary);
      for(const r of extra) details.appendChild(partyRowEl(r));
      wrap.appendChild(details);
    }
  }

  function selectMahalle(row, plaka, geomId){
    $$('.il-path').forEach(p=>p.classList.toggle('selected', p.dataset.mahalleId===row.id));
    const p = ilByPlaka[plaka];
    const d = districtByGeomId[geomId];
    $('#detailEmpty').style.display='none';
    $('#detailBody').style.display='block';
    $('#detailViewToggle').style.display='none';
    $('#dInfoNote').style.display='none';
    $('#dName').textContent = row.ad;
    $('#dPlaka').textContent = [d?d.ad:null, p?p.ad:null].filter(Boolean).join(', ');

    const heroOy = row.kazanan ? row.oy[row.kazanan] : null;
    setHero('Kazanan', row.kazanan && PARTY[row.kazanan]?PARTY[row.kazanan].short:row.kazanan, row.kazanan, heroOy ? resultPercent(heroOy) : null);

    const gecerli = Object.values(row.oy||{}).reduce((s,o)=>s+(o.oy||0),0);
    $('#dSeatsLabel').textContent = 'Sandık';
    $('#dSeats').textContent = row.sandik!=null ? fmt(row.sandik) : '—';
    $('#dTurnout').textContent = row.katilim!=null ? '%'+row.katilim.toFixed(2) : '—';
    $('#dSecmen').textContent = row.secmen!=null ? fmt(row.secmen) : '—';
    $('#dGecerli').textContent = gecerli ? fmt(gecerli) : '—';
    hideEmptyStatRows();

    const allNamed = Object.entries(row.oy).map(([name,oy])=>({name, oy}))
      .filter(r=>r.oy && r.oy.oy>0)
      .sort((a,b)=> b.oy.oy - a.oy.oy);
    const wrap = $('#dParties'); wrap.innerHTML='';
    for(const r of allNamed) wrap.appendChild(partyRowEl(r));
    $('#districtSearch').style.display='none';
    $('#dDistrictList').style.display='none';
  }

  // Bir ilce kaydinda GERCEK sonuc var mi (bos/hic olusturulmamis 'oy' sozlugu
  // degil) - hem harita (map.js) hem bu panel, tiklanabilir/etkilesimli
  // gosterecegi ilceleri bu kontrolden gecirir (bkz. son inceleme: veri
  // olmayan yerde tiklama alani gorunmemeli).
  function districtHasRealData(d){
    return !!d && !!d.oy && Object.keys(d.oy).length > 0;
  }

  // Bu ilin bu YIL icin GERCEKTEN ilce-duzeyi verisi var mi - map.js'teki
  // renderProvinceMap'in dataFeats.length kontrolüyle AYNI mantik (bkz.
  // goToProvince, selectProvince).
  function provinceHasDistrictData(plaka){
    return (districtsByPlaka[plaka]||[]).some(districtHasRealData);
  }

  function renderDistrictList(plaka, filter){
    const list = (districtsByPlaka[plaka]||[]).filter(d => d.ad.toLocaleLowerCase('tr').includes(filter.toLocaleLowerCase('tr')));
    const el = $('#dDistrictList'); el.innerHTML='';
    const withData = list.filter(districtHasRealData);
    const withoutData = list.filter(d=>!districtHasRealData(d));
    for(const d of withData){
      const row = document.createElement('div'); row.className='district-row';
      if(d.geomId) row.dataset.geomId = d.geomId;
      const short = d.kazanan ? (PARTY[d.kazanan]?PARTY[d.kazanan].short:d.kazanan) : '—';
      const dOy = d.oy[d.kazanan];
      const dPctLabel = dOy ? resultPercentLabel(dOy) : '—';
      const dInfo = dOy ? ((dPctLabel!=='—' ? dPctLabel+' · ' : '')+resultQuantity(dOy)) : '–';
      row.innerHTML = '<span class="dname">'+d.ad+'</span>'+
        '<span class="dwinner"><span class="ddot" style="background:'+(d.kazanan?partyColor(d.kazanan):'var(--map-empty)')+'"></span>'+short+' · '+dInfo+'</span>';
      if(d.geomId && pathByGeomId[d.geomId]){
        row.addEventListener('mouseenter', ()=> pathByGeomId[d.geomId].classList.add('selected'));
        row.addEventListener('mouseleave', ()=> pathByGeomId[d.geomId].classList.remove('selected'));
      }
      row.addEventListener('click', async ()=>{
        if(!d.geomId) return;
        selectDistrict(d, plaka);
        if(mahalleGeoExistsForDistrict(d.geomId)){
          const rows = await mahalleDataForDistrict(d.geomId);
          if(rows){ renderMahalleMap(plaka, d.geomId, rows); return; }
        }
        if(pathByGeomId[d.geomId]) pathByGeomId[d.geomId].scrollIntoView({block:'nearest'});
      });
      el.appendChild(row);
    }
    // Kayit var ama gercek sonuc yok (nadir) - tiklanamaz, soluk, "Veri yok" -
    // hicbir sey listeden tamamen KAYBOLMUYOR ama yaniltici bicimde
    // etkilesimli de gorunmuyor.
    for(const d of withoutData){
      const row = document.createElement('div'); row.className='district-row district-row-empty';
      if(d.geomId) row.dataset.geomId = d.geomId;
      row.innerHTML = '<span class="dname">'+d.ad+'</span><span class="dwinner">Veri yok</span>';
      el.appendChild(row);
    }
  }

  function selectDistrict(d, plaka){
    $$('.il-path').forEach(p=>p.classList.toggle('selected', p.dataset.geomId===d.geomId));
    $$('.district-row').forEach(r=>r.classList.toggle('dselected', r.dataset.geomId===d.geomId));
    const p = ilByPlaka[plaka];
    $('#detailEmpty').style.display='none';
    $('#detailBody').style.display='block';
    $('#detailViewToggle').style.display='none';
    $('#dInfoNote').style.display='none';
    $('#dName').textContent = d.ad;
    $('#dPlaka').textContent = p ? p.ad : '';

    const heroOy = d.kazanan ? d.oy[d.kazanan] : null;
    const heroLabel = DATA.tur==='referandum' ? 'Sonuç' : 'Kazanan';
    setHero(heroLabel, d.kazanan && PARTY[d.kazanan]?PARTY[d.kazanan].short:d.kazanan, d.kazanan, heroOy ? resultPercent(heroOy) : null);

    // Milletvekili sandalyesi il duzeyinde tahsis edilir (secim cevresi = il),
    // ilce kaydinin toplamVekil'i anlamsizdir (hep 0) - bunun yerine ilcenin
    // kendi sandik sayisini goster (yerel/referandum/CB'de zaten anlamli olan alan).
    $('#dSeatsLabel').textContent = DATA.tur==='genel' ? 'Milletvekili' : 'Sandık';
    $('#dSeats').textContent = DATA.tur==='genel' ? (d.toplamVekil || '—') : (d.sandik!=null ? fmt(d.sandik) : '—');
    $('#dTurnout').textContent = d.katilim!=null ? '%'+d.katilim.toFixed(2) : '—';
    $('#dSecmen').textContent = d.secmen!=null ? fmt(d.secmen) : '—';
    $('#dGecerli').textContent = d.gecerliOy!=null ? fmt(d.gecerliOy) : '—';
    hideEmptyStatRows();

    $('#dResultsHead').textContent = 'Sonuçlar';
    renderPartyResults(d);
  }

  // ---------------- 2024 yerel: ilce meclisi ikincil gorunumu (sag panel) ----------------
  // Artik ayri bir harita modu degil - selectProvince'in "İlçe Meclisi" sekmesinden
  // ve buradaki ilce listesinden tetikleniyor (bkz. detailView toggle, asagida).

  function renderDistrictListMeclis(plaka, filter){
    const list = (districtsByPlaka[plaka]||[]).filter(d => d.geomId && d.ad.toLocaleLowerCase('tr').includes(filter.toLocaleLowerCase('tr')));
    const el = $('#dDistrictList'); el.innerHTML='';
    for(const d of list){
      const m = MECLIS_2024[d.geomId];
      const row = document.createElement('div'); row.className='district-row';
      row.dataset.geomId = d.geomId;
      const short = m ? (PARTY[m.kazanan]?PARTY[m.kazanan].short:m.kazanan) : '—';
      row.innerHTML = '<span class="dname">'+d.ad+'</span>'+
        '<span class="dwinner"><span class="ddot" style="background:'+(m?partyColor(m.kazanan):'var(--map-empty)')+'"></span>'+short+(m&&m.toplam?' · '+m.toplam+' üye':'')+'</span>';
      row.addEventListener('click', ()=> renderMeclisIlceMap(plaka, d.geomId));
      el.appendChild(row);
    }
  }

  function renderMeclisOverview(plaka){
    $('#dInfoNote').style.display='none';
    setHero('İlçe Meclisi', 'İlçe seçin', null, null);
    $('#dTurnout').textContent='—'; $('#dSecmen').textContent='—'; $('#dGecerli').textContent='—';
    $('#dSeatsLabel').textContent='Üye'; $('#dSeats').textContent='—';
    hideEmptyStatRows();
    $('#dResultsHead').textContent = 'Bir ilçeye tıklayarak meclis dağılımını görün';
    $('#dParties').innerHTML='';
    $('#dDistrictsLabel').textContent = 'İlçe Meclisleri';
    $('#districtSearch').style.display='';
    $('#dDistrictList').style.display='';
    renderDistrictListMeclis(plaka, '');
    $('#districtSearch').value='';
    $('#districtSearch').oninput = e => renderDistrictListMeclis(plaka, e.target.value);
  }

  function renderMeclisIlceMap(plaka, geomId){
    view = {level:'meclis-ilce', plaka, geomId};
    const f = geoFeatureById[geomId];
    if(!f) return;
    const project = computeProjection([f], PAD);
    svg.innerHTML = '';
    pathByPlaka = {}; pathByGeomId = {};
    const el = document.createElementNS(NS,'path');
    el.setAttribute('d', geomToPath(project, f.geometry));
    el.setAttribute('class','il-path selected');
    el.dataset.geomId = geomId;
    el.addEventListener('mousemove', e=>showTooltip(e, {kind:'ilce', plaka, geomId}));
    el.addEventListener('mouseleave', hideTooltip);
    svg.appendChild(el);
    pathByGeomId[geomId]=el;
    const m = MECLIS_2024[geomId];
    el.setAttribute('fill', m ? partyColor(m.kazanan) : 'var(--map-empty)');

    const p = ilByPlaka[plaka];
    const d = districtByGeomId[geomId];
    $('#mapBreadcrumb').style.display='flex';
    $('#btnBackProvince').style.display='inline-flex';
    $('#mapTitleCountry').style.display='none';
    $('#mapBreadcrumbName').textContent = (p?p.ad:'')+' — '+(d?d.ad:'')+' — 2024 İlçe Meclisi';
    $('#searchBox').value='';
    $('#seqLegendWrap').style.display='none';
    selectMeclisIlce(geomId, plaka);
  }

  function selectMeclisIlce(geomId, plaka){
    $$('.il-path').forEach(p=>p.classList.toggle('selected', p.dataset.geomId===geomId));
    const m = MECLIS_2024[geomId];
    const p = ilByPlaka[plaka];
    $('#detailEmpty').style.display='none';
    $('#detailBody').style.display='block';
    $('#dInfoNote').style.display='none';
    $('#dDistrictsLabel').textContent = 'İlçe Meclisleri';
    $('#districtSearch').style.display='';
    $('#dDistrictList').style.display='';
    renderDistrictListMeclis(plaka, '');
    $$('.district-row').forEach(r=>r.classList.toggle('dselected', r.dataset.geomId===geomId));
    if(!m){
      $('#dName').textContent = (districtByGeomId[geomId]?districtByGeomId[geomId].ad:'');
      $('#dPlaka').textContent = p?p.ad:'';
      setHero('Çoğunluk', null, null, null);
      $('#dTurnout').textContent = '—'; $('#dSecmen').textContent = '—'; $('#dGecerli').textContent = '—';
      $('#dSeatsLabel').textContent = 'Üye'; $('#dSeats').textContent = '—';
      hideEmptyStatRows();
      $('#dResultsHead').textContent = 'Sonuçlar';
      $('#dParties').innerHTML = '<div style="padding:10px 2px; color:var(--ink-3); font-size:12.5px;">2024 yerel ilçe meclisi verisi bu ilçe için mevcut değil.</div>';
      return;
    }
    $('#dName').textContent = m.ad;
    $('#dPlaka').textContent = (p?p.ad:'')+' — 2024 İlçe Meclisi';
    const majPct = m.toplam ? (m.partiler[m.kazanan]||0)/m.toplam*100 : null;
    setHero('Çoğunluk', PARTY[m.kazanan] ? PARTY[m.kazanan].short : m.kazanan, m.kazanan, majPct);
    $('#dTurnout').textContent = '—'; $('#dSecmen').textContent = '—'; $('#dGecerli').textContent = '—';
    $('#dSeatsLabel').textContent = 'Üye'; $('#dSeats').textContent = m.toplam;
    hideEmptyStatRows();
    $('#dResultsHead').textContent = 'Meclis Sandalye Dağılımı';

    const rows = Object.entries(m.partiler).sort((a,b)=>b[1]-a[1]);
    const wrap = $('#dParties'); wrap.innerHTML='';
    for(const [name, n] of rows){
      // Meclis UYE SAYISI - oy DEGIL. {oy:n} sekli isSeatBased()'i yanlislikla
      // atlatip "n oy" yazdiriyordu (bkz. son inceleme) - dogru sekil, partyRowEl'in
      // (result-utils.js uzerinden) sandalye dalina girmesini saglar: "n meclis sandalyesi".
      wrap.appendChild(partyRowEl({name, oy:{oy:null, sandalye:n, oranSandalye: m.toplam ? n/m.toplam*100 : null}, vekil:0}));
    }
  }

  $$('#detailViewToggle button').forEach(b=>{
    b.addEventListener('click', ()=>{
      if(b.classList.contains('active') || !selectedPlaka) return;
      detailView = b.dataset.view;
      $$('#detailViewToggle button').forEach(x=>x.classList.toggle('active', x===b));
      if(detailView==='meclis') renderMeclisOverview(selectedPlaka);
      else selectProvince(selectedPlaka);
    });
  });
