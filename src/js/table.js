  // ---------------- table view ----------------
  let sortKey='toplamVekil', sortDir=-1;
  let tableFilter='';
  $('#tableSearch').addEventListener('input', e=>{ tableFilter = e.target.value; renderTable(); });
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
    let rows = [...DATA.iller];
    if(tableFilter.trim()){
      const q = tableFilter.toLocaleLowerCase('tr');
      rows = rows.filter(p=>p.ad.toLocaleLowerCase('tr').includes(q));
    }
    rows.sort((a,b)=>{
      const va = sortKey==='ad' ? a.ad : (MAJOR.includes(sortKey) ? (oranMode ? (resultPercent(a.oy[sortKey]) ?? -1) : (a.vekil[sortKey]||0)) : a[sortKey]);
      const vb = sortKey==='ad' ? b.ad : (MAJOR.includes(sortKey) ? (oranMode ? (resultPercent(b.oy[sortKey]) ?? -1) : (b.vekil[sortKey]||0)) : b[sortKey]);
      if(typeof va==='string') return sortDir*va.localeCompare(vb,'tr');
      return sortDir*(va-vb);
    });
    const body = $('#ilTableBody'); body.innerHTML='';
    for(const p of rows){
      const tr = document.createElement('tr');
      // Parti yuzde hucrelerine, gercek oy sayisini da (hover ile) her zaman
      // erisilebilir tutmak icin title niteligi ekleniyor.
      const adCell = '<span class="table-winner-dot" style="background:'+(p.kazanan?partyColor(p.kazanan):'var(--map-empty)')+'"></span>'+p.ad;
      const cells = oranMode
        ? [[adCell,null], ...MAJOR.map(m=>{
            const r = p.oy[m]; const pct = resultPercent(r);
            return [pct!=null ? pct.toFixed(2) : '—', r ? resultQuantity(r) : null];
          }), [p.katilim!=null?p.katilim.toFixed(2):'—', null], [fmt(p.secmen), null]]
        : [[adCell,null], [p.toplamVekil,null], ...MAJOR.map(m=>{
            const r = p.oy[m]; const pct = resultPercent(r);
            return [p.vekil[m]||'—', r ? resultQuantity(r)+(pct!=null?' · %'+pct.toFixed(2):'') : null];
          }), [p.katilim!=null?p.katilim.toFixed(2):'—', null], [fmt(p.secmen), null]];
      tr.innerHTML = cells.map(([c,title],i)=>'<td'+(i===0?'':' class="num"')+(title?' title="'+title+'"':'')+'>'+c+'</td>').join('');
      tr.style.cursor='pointer';
      tr.addEventListener('click', ()=>{ $('#btnMapView').click(); goToProvince(p.plaka); });
      body.appendChild(tr);
    }
    $$('#ilTable th').forEach(th=>th.classList.toggle('sorted', th.dataset.key===sortKey));
  }

  // ---------------- CSV indirme ----------------
  // Acik secimin il ve ilce sonuclari tek tabloda: her parti icin oy, oran (%) ve varsa vekil /
  // meclis sandalyesi. UTF-8 BOM'lu, virgulle ayrilmis (Excel'de Turkce karakterler bozulmasin).
  function csvHucre(v){
    if(v == null) return '';
    const s = String(v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  function csvMetni(){
    const satirlar = [
      ...DATA.iller.map(r => ['il', r]),
      ...(DATA.ilceler || []).filter(r => r.oy && Object.keys(r.oy).length || r.not).map(r => ['ilçe', r]),
    ];
    if(DATA.yurtdisi && DATA.yurtdisi.oy && Object.keys(DATA.yurtdisi.oy).length) satirlar.push(['yurt dışı', Object.assign({ad: 'Yurt dışı'}, DATA.yurtdisi)]);
    const partiler = [...MAJOR];
    for(const [, r] of satirlar) for(const p of Object.keys(r.oy || {})) if(!partiler.includes(p)) partiler.push(p);
    const vekilVar = satirlar.some(([, r]) => r.vekil && Object.keys(r.vekil).length);
    const sandalyeVar = satirlar.some(([, r]) => Object.values(r.oy || {}).some(isSeatBased));
    const bas = ['seçim', 'düzey', 'plaka', 'il', 'ilçe', 'seçmen', 'sandık', 'geçerli oy', 'katılım %', 'kazanan'];
    if(vekilVar) bas.push('toplam vekil');
    for(const p of partiler){
      bas.push(p + ' oy', p + ' %');
      if(vekilVar) bas.push(p + ' vekil');
      if(sandalyeVar) bas.push(p + ' sandalye');
    }
    bas.push('not');
    const ad = csvAnahtari();
    const out = [bas];
    for(const [duzey, r] of satirlar){
      const il = duzey === 'il' ? r.ad : (duzey === 'ilçe' ? (ilByPlaka[r.plaka] || {}).ad : '');
      const row = [ad, duzey, duzey === 'yurt dışı' ? '' : r.plaka, il, duzey === 'ilçe' ? r.ad : '',
                   r.secmen, r.sandik, r.gecerliOy, r.katilim, r.kazanan];
      if(vekilVar) row.push(r.toplamVekil);
      for(const p of partiler){
        const o = (r.oy || {})[p];
        row.push(o ? o.oy : null, o ? (isSeatBased(o) ? null : o.oran) : null);
        if(vekilVar) row.push((r.vekil || {})[p]);
        if(sandalyeVar) row.push(o ? o.sandalye : null);
      }
      row.push(r.not);
      out.push(row);
    }
    return '﻿' + out.map(r => r.map(csvHucre).join(',')).join('\r\n') + '\r\n';
  }
  // secim anahtari (ornek 2023, 2019yerel_bm): dosya adi ve 'seçim' sutunu
  function csvAnahtari(){
    return currentYear + (DATA.oylama && DATA.oylama !== 'baskan' ? '_' + DATA.oylama : '');
  }
  function csvIndir(){
    const blob = new Blob([csvMetni()], {type: 'text/csv;charset=utf-8'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'secim_' + csvAnahtari() + '.csv';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  $('#btnCsv').addEventListener('click', csvIndir);
