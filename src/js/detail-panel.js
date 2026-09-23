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

  // 1950/1955 yerel secimlerinde belediye baskani halk oyuyla degil, meclisin
  // kendi icinden seciliyordu - o yillarda 'oy'/'oran' alanlari null, bunun
  // yerine 'sandalye'/'oranSandalye' (meclis sandalye dagilimi) dolu (bkz.
  // yerel_secimler.json ust-seviye contestType/resultBasis alanlari). Bu
  // fonksiyon her iki durumu da doğru etiketle gosterir - gercek oy yuzdesini
  // meclis sandalye payiyla KARISTIRMAZ.
  function isSeatBased(oy){ return (oy.oy==null || oy.oy===0) && oy.sandalye!=null; }

  function partyRowEl(r){
    const short = PARTY[r.name] ? PARTY[r.name].short : r.name;
    const seatBased = isSeatBased(r.oy);
    const pct = seatBased ? (r.oy.oranSandalye!=null?r.oy.oranSandalye:0) : (r.oy.oran!=null ? r.oy.oran : 0);
    const pctLabel = seatBased ? (r.oy.oranSandalye!=null?'%'+r.oy.oranSandalye.toFixed(1):'—') : (r.oy.oran!=null?'%'+r.oy.oran.toFixed(2):'—');
    const qtyLabel = seatBased ? (r.oy.sandalye!=null?r.oy.sandalye+' meclis sandalyesi':'—') : (fmt(r.oy.oy)+' oy');
    const el = document.createElement('div'); el.className='party-row';
    el.innerHTML = '<div class="prow-top">'+
        '<span class="dot" style="background:'+partyColor(r.name)+'"></span>'+
        '<span class="name">'+short+'</span>'+
        '<span class="pct">'+pctLabel+'</span>'+
        '<span class="oy">'+qtyLabel+'</span>'+
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
    const heroLabel = DATA.tur==='referandum' ? 'Sonuç' : (heroSeatBased ? 'Meclis Çoğunluğu' : 'Kazanan');
    const heroPct = heroOy ? (heroSeatBased ? heroOy.oranSandalye : heroOy.oran) : null;
    setHero(heroLabel, p.kazanan && PARTY[p.kazanan]?PARTY[p.kazanan].short:p.kazanan, p.kazanan, heroPct);

    // 1950/1955 yerel: belediye baskani halk oyuyla degil, meclisin kendi
    // icinden seciliyordu (contestType=municipal_indirect) - kullaniciyi bunun
    // modern bir "kazanan %" olmadigi konusunda uyar (bkz. resultBasis).
    const showSeatNote = DATA.resultBasis==='council_seats' || (DATA.resultBasis==='mixed' && heroSeatBased);
    $('#dInfoNote').style.display = showSeatNote ? 'flex' : 'none';
    if(showSeatNote) $('#dInfoNote').textContent = 'ⓘ Bu seçimde belediye başkanı doğrudan halk tarafından seçilmiyordu. Sonuçlar belediye meclisi dağılımını temel alır.';

    $('#dSeatsLabel').textContent = (DATA.tur !== 'genel' || YEARS_NO_VEKIL.has(currentYear)) ? 'Vekil / Sandalye' : 'Milletvekili';
    $('#dSeats').textContent = (DATA.tur !== 'genel' || YEARS_NO_VEKIL.has(currentYear)) ? (p.toplamVekil || '—') : p.toplamVekil;
    $('#dTurnout').textContent = p.katilim!=null ? '%'+p.katilim.toFixed(2) : '—';
    $('#dSecmen').textContent = p.secmen!=null ? fmt(p.secmen) : '—';
    $('#dGecerli').textContent = p.gecerliOy!=null ? fmt(p.gecerliOy) : '—';
    hideEmptyStatRows();

    // Butun il/ilce'de gercekten oy alan HER parti (baraj alti kucuk partiler ve
    // bagimsizlar dahil) - MAJOR listesi sadece hangilerinin ilk sirada, hangilerinin
    // "digerleri" acilir-kapanir bolumune gidecegini belirliyor.
    const rank = r => isSeatBased(r.oy) ? (r.oy.sandalye||0) : (r.oy.oy||0);
    const allNamed = Object.entries(p.oy).map(([name,oy])=>({name, oy, vekil:(p.vekil&&p.vekil[name])||0}))
      .filter(r=>r.oy && (r.oy.oy>0 || r.oy.sandalye>0));
    const majorSet = new Set(MAJOR);
    const primary = allNamed.filter(r=>majorSet.has(r.name)).sort((a,b)=> rank(b) - rank(a));
    const extra = allNamed.filter(r=>!majorSet.has(r.name)).sort((a,b)=> rank(b) - rank(a));
    // primary bossa (orn. yerel'de MAJOR il-kazananlari listesi bu ilde/ilcede hic
    // gecmiyorsa) en cok oy alan birkac partiyi one al, kalanlari "digerleri"ne birak.
    const rows = primary.length ? primary : extra.splice(0, Math.min(5, extra.length));
    if(DATA.tur !== 'yerel' && p.digerOy>0) rows.push({name:'Diğer', oy:{oy:p.digerOy, oran:p.digerOran}, vekil:0});
    $('#dResultsHead').textContent = (DATA.resultBasis==='council_seats') ? 'Belediye Meclisi Sandalye Dağılımı'
      : (DATA.resultBasis==='mixed') ? 'Sonuçlar (bazı illerde meclis sandalye dağılımı)' : 'Sonuçlar';
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

    $('#dDistrictsLabel').textContent = 'İlçeler';
    $('#districtSearch').style.display='';
    $('#dDistrictList').style.display='';
    renderDistrictList(plaka, '');
    $('#districtSearch').value='';
    $('#districtSearch').oninput = e => renderDistrictList(plaka, e.target.value);
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
    setHero('Kazanan', row.kazanan && PARTY[row.kazanan]?PARTY[row.kazanan].short:row.kazanan, row.kazanan, heroOy && heroOy.oran!=null ? heroOy.oran : null);

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

  function renderDistrictList(plaka, filter){
    const list = (districtsByPlaka[plaka]||[]).filter(d => d.ad.toLocaleLowerCase('tr').includes(filter.toLocaleLowerCase('tr')));
    const el = $('#dDistrictList'); el.innerHTML='';
    if(list.length===0 && YEARS_IL_ONLY.has(currentYear)){
      const msg = document.createElement('div'); msg.className='district-row'; msg.style.opacity=0.6; msg.style.cursor='default';
      msg.textContent = 'Bu dönem için ilçe bazlı veri kaynakta mevcut değil (sadece il seviyesi).';
      el.appendChild(msg);
      return;
    }
    for(const d of list){
      const row = document.createElement('div'); row.className='district-row';
      if(d.geomId) row.dataset.geomId = d.geomId;
      const short = d.kazanan ? (PARTY[d.kazanan]?PARTY[d.kazanan].short:d.kazanan) : '—';
      row.innerHTML = '<span class="dname">'+d.ad+'</span>'+
        '<span class="dwinner"><span class="ddot" style="background:'+(d.kazanan?partyColor(d.kazanan):'var(--map-empty)')+'"></span>'+short+' · '+(d.oy[d.kazanan]?((d.oy[d.kazanan].oran!=null?'%'+d.oy[d.kazanan].oran.toFixed(2)+' · ':'')+fmt(d.oy[d.kazanan].oy)+' oy'):'–')+'</span>';
      if(d.geomId && pathByGeomId[d.geomId]){
        row.addEventListener('mouseenter', ()=> pathByGeomId[d.geomId].classList.add('selected'));
        row.addEventListener('mouseleave', ()=> pathByGeomId[d.geomId].classList.remove('selected'));
      }
      row.addEventListener('click', async ()=>{
        if(!d.geomId) return;
        if(mahalleGeoExistsForDistrict(d.geomId)){
          const rows = await mahalleDataForDistrict(d.geomId);
          if(rows){ renderMahalleMap(plaka, d.geomId, rows); return; }
        }
        highlightDistrictRow(d.geomId);
        if(pathByGeomId[d.geomId]) pathByGeomId[d.geomId].scrollIntoView({block:'nearest'});
      });
      el.appendChild(row);
    }
  }

  function highlightDistrictRow(geomId){
    const d = districtByGeomId[geomId];
    $$('.district-row').forEach(r=>r.classList.toggle('dselected', r.dataset.geomId===geomId));
    if(d){
      const row = $('.district-row[data-geom-id="'+geomId+'"]');
      if(row) row.scrollIntoView({block:'nearest', behavior:'smooth'});
    }
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
      wrap.appendChild(partyRowEl({name, oy:{oy:n, oran: m.toplam ? n/m.toplam*100 : null}, vekil:0}));
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
