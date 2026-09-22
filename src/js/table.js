  // ---------------- table view ----------------
  let sortKey='toplamVekil', sortDir=-1;
  function renderTableHead(){
    const headRow = $('#ilTableHeadRow');
    const oranModeHead = DATA.tur === 'referandum' || DATA.tur === 'yerel' || DATA.tur === 'cumhurbaskanligi' || YEARS_NO_VEKIL.has(currentYear);
    const cols = oranModeHead
      ? [['ad','İl'], ...MAJOR.map(m=>[m, (PARTY[m]?PARTY[m].short:m)+' %']), ['katilim','Katılım %'], ['secmen','Seçmen']]
      : [['ad','İl'], ['toplamVekil','Toplam Vekil'], ...MAJOR.map(m=>[m, PARTY[m]?PARTY[m].short:m]),
         ['katilim','Katılım %'], ['secmen','Seçmen']];
    headRow.innerHTML = cols.map(([key,label])=>'<th data-key="'+key+'">'+label+'</th>').join('');
    $$('#ilTable th').forEach(th=>{
      th.addEventListener('click', ()=>{
        const key = th.dataset.key;
        if(sortKey===key) sortDir*=-1; else { sortKey=key; sortDir = key==='ad'?1:-1; }
        renderTable();
      });
    });
  }
  function renderTable(){
    const oranMode = DATA.tur === 'referandum' || DATA.tur === 'yerel' || DATA.tur === 'cumhurbaskanligi' || YEARS_NO_VEKIL.has(currentYear);
    const defaultSort = oranMode ? MAJOR[0] : 'toplamVekil';
    if(!MAJOR.includes(sortKey) && !['ad','toplamVekil','katilim','secmen'].includes(sortKey)){
      sortKey = defaultSort; sortDir = -1;
    }
    renderTableHead();
    const rows = [...DATA.iller];
    rows.sort((a,b)=>{
      const va = sortKey==='ad' ? a.ad : (MAJOR.includes(sortKey) ? (oranMode ? (a.oy[sortKey]?a.oy[sortKey].oran:-1) : (a.vekil[sortKey]||0)) : a[sortKey]);
      const vb = sortKey==='ad' ? b.ad : (MAJOR.includes(sortKey) ? (oranMode ? (b.oy[sortKey]?b.oy[sortKey].oran:-1) : (b.vekil[sortKey]||0)) : b[sortKey]);
      if(typeof va==='string') return sortDir*va.localeCompare(vb,'tr');
      return sortDir*(va-vb);
    });
    const body = $('#ilTableBody'); body.innerHTML='';
    for(const p of rows){
      const tr = document.createElement('tr');
      // Parti yuzde hucrelerine, gercek oy sayisini da (hover ile) her zaman
      // erisilebilir tutmak icin title niteligi ekleniyor.
      const cells = oranMode
        ? [[p.ad,null], ...MAJOR.map(m=>[p.oy[m]?p.oy[m].oran.toFixed(2):'—', p.oy[m]?fmt(p.oy[m].oy)+' oy':null]),
           [p.katilim!=null?p.katilim.toFixed(2):'—', null], [fmt(p.secmen), null]]
        : [[p.ad,null], [p.toplamVekil,null], ...MAJOR.map(m=>[p.vekil[m]||'—', p.oy[m]?fmt(p.oy[m].oy)+' oy · %'+p.oy[m].oran.toFixed(2):null]),
           [p.katilim!=null?p.katilim.toFixed(2):'—', null], [fmt(p.secmen), null]];
      tr.innerHTML = cells.map(([c,title],i)=>'<td'+(i===0?'':' class="num"')+(title?' title="'+title+'"':'')+'>'+c+'</td>').join('');
      tr.style.cursor='pointer';
      tr.addEventListener('click', ()=>{ $('#btnMapView').click(); drillIntoProvince(p.plaka); });
      body.appendChild(tr);
    }
    $$('#ilTable th').forEach(th=>th.classList.toggle('sorted', th.dataset.key===sortKey));
  }

