  // ---------------- national seat bar (genel secim) / evet-hayir bar (referandum) ----------------
  function renderSeatBar(){
    if(DATA.tur === 'referandum'){ renderRefBar(); return; }
    if(DATA.tur === 'yerel'){ renderYerelBar(); return; }
    if(DATA.tur === 'cumhurbaskanligi'){ renderCBBar(); return; }
    if(YEARS_NO_VEKIL.has(currentYear)){ renderGenelWinnerBar(); return; }
    const track = $('#seatTrack'); track.innerHTML = '';
    const legend = $('#seatLegend'); legend.innerHTML = '';
    const seatTotals = {};
    for(const p of DATA.iller){ for(const [party,n] of Object.entries(p.vekil)){ seatTotals[party]=(seatTotals[party]||0)+n; } }
    const order = MAJOR.includes('Diğer') ? [...MAJOR] : [...MAJOR, 'Diğer'];
    const total = DATA.toplamSandalye;
    const majority = Math.floor(total/2)+1;
    $('#seatbarTitle').textContent = 'Meclis Dağılımı — '+total+' Sandalye';
    $('#majoritySub').textContent = 'Salt çoğunluk için '+majority+' vekil gerekir';
    for(const party of order){
      const n = seatTotals[party] || 0;
      if(n<=0) continue;
      const seg = document.createElement('div');
      seg.className='seatbar-seg';
      seg.style.width = (n/total*100)+'%';
      seg.style.background = partyColor(party);
      seg.title = party+': '+n+' vekil';
      track.appendChild(seg);
    }
    const ml = document.createElement('div');
    ml.className='majority-line'; ml.style.left=(majority/total*100)+'%';
    ml.innerHTML = '<span class="maj-label">'+majority+' · Salt çoğunluk</span>';
    track.appendChild(ml);

    for(const party of order){
      const n = seatTotals[party] || 0;
      if(n<=0) continue;
      const item = document.createElement('div'); item.className='legend-item';
      item.innerHTML = '<span class="swatch" style="background:'+partyColor(party)+'"></span>'+
        '<span class="n">'+n+'</span><b>'+(PARTY[party]?PARTY[party].short:party)+'</b>';
      legend.appendChild(item);
    }
  }

  function renderRefBar(){
    const track = $('#seatTrack'); track.innerHTML = '';
    const legend = $('#seatLegend'); legend.innerHTML = '';
    let evetPct, hayirPct;
    if(DATA.toplamSonuc){
      evetPct = DATA.toplamSonuc.evet_oran; hayirPct = DATA.toplamSonuc.hayir_oran;
    } else {
      let evetOy = 0, hayirOy = 0;
      for(const p of DATA.iller){ evetOy += p.oy['Evet'].oy; hayirOy += p.oy['Hayır'].oy; }
      const total = evetOy + hayirOy;
      evetPct = total ? evetOy/total*100 : 0;
      hayirPct = 100 - evetPct;
    }
    $('#seatbarTitle').textContent = 'Ulusal Sonuç';
    $('#majoritySub').textContent = 'Kabul için geçerli oyların yarısından fazlası gerekir';
    for(const [name, pct] of [['Evet', evetPct], ['Hayır', hayirPct]]){
      const seg = document.createElement('div');
      seg.className='seatbar-seg';
      seg.style.width = pct+'%';
      seg.style.background = partyColor(name);
      seg.title = name+': %'+pct.toFixed(2);
      track.appendChild(seg);
    }
    const ml = document.createElement('div');
    ml.className='majority-line'; ml.style.left='50%';
    ml.innerHTML = '<span class="maj-label">%50</span>';
    track.appendChild(ml);
    for(const [name, pct] of [['Evet', evetPct], ['Hayır', hayirPct]]){
      const item = document.createElement('div'); item.className='legend-item';
      item.innerHTML = '<span class="swatch" style="background:'+partyColor(name)+'"></span>'+
        '<span class="n">%'+pct.toFixed(2)+'</span><b>'+name+'</b>';
      legend.appendChild(item);
    }
  }

  function renderCBBar(){
    const track = $('#seatTrack'); track.innerHTML = '';
    const legend = $('#seatLegend'); legend.innerHTML = '';
    const totals = {};
    for(const p of DATA.iller){ for(const [cand, info] of Object.entries(p.oy)){ totals[cand] = (totals[cand]||0) + info.oy; } }
    const grand = Object.values(totals).reduce((a,b)=>a+b, 0);
    // Bu toplam sadece DATA.iller'den (yurt ici) geliyor - yurtdisi secmeni
    // olan secimlerde "Ulusal" baslik yaniltici olur (bkz. renderNationalSummary
    // ayni gerekce).
    const hasYurtdisi = !!(DATA.yurtdisi && DATA.yurtdisi.oy && Object.keys(DATA.yurtdisi.oy).length);
    $('#seatbarTitle').textContent = hasYurtdisi ? 'Yurt İçi Oy Dağılımı' : 'Ulusal Oy Dağılımı';
    $('#majoritySub').textContent = 'Kazanmak için geçerli oyların yarısından fazlası gerekir';
    for(const cand of MAJOR){
      const n = totals[cand] || 0;
      if(n<=0) continue;
      const pct = grand ? n/grand*100 : 0;
      const seg = document.createElement('div');
      seg.className='seatbar-seg';
      seg.style.width = pct+'%';
      seg.style.background = partyColor(cand);
      seg.title = cand+': %'+pct.toFixed(2);
      track.appendChild(seg);
    }
    const ml = document.createElement('div');
    ml.className='majority-line'; ml.style.left='50%';
    ml.innerHTML = '<span class="maj-label">%50</span>';
    track.appendChild(ml);
    for(const cand of MAJOR){
      const n = totals[cand] || 0;
      if(n<=0) continue;
      const pct = grand ? n/grand*100 : 0;
      const item = document.createElement('div'); item.className='legend-item';
      item.innerHTML = '<span class="swatch" style="background:'+partyColor(cand)+'"></span>'+
        '<span class="n">%'+pct.toFixed(2)+'</span><b>'+(PARTY[cand]?PARTY[cand].short:cand)+'</b>';
      legend.appendChild(item);
    }
  }

  function renderGenelWinnerBar(){
    // 1950/1954/1957/1961: vekil verisi kaynakta guvenilir degil (bkz. YEARS_NO_VEKIL),
    // bu yuzden sandalye yerine il bazinda kazanan parti sayisini gosteriyoruz.
    const track = $('#seatTrack'); track.innerHTML = '';
    const legend = $('#seatLegend'); legend.innerHTML = '';
    const wins = {};
    for(const p of DATA.iller){ wins[p.kazanan] = (wins[p.kazanan]||0) + 1; }
    const total = DATA.iller.length;
    const order = [...MAJOR];
    $('#seatbarTitle').textContent = 'İl Bazında Kazanan Parti (Vekil Verisi Mevcut Değil)';
    $('#majoritySub').textContent = total+' il — bu dönem için parti bazında vekil dağılımı kaynakta yok';
    for(const party of order){
      const n = wins[party] || 0;
      if(n<=0) continue;
      const seg = document.createElement('div');
      seg.className='seatbar-seg';
      seg.style.width = (n/total*100)+'%';
      seg.style.background = partyColor(party);
      seg.title = party+': '+n+' il';
      track.appendChild(seg);
    }
    for(const party of order){
      const n = wins[party] || 0;
      if(n<=0) continue;
      const item = document.createElement('div'); item.className='legend-item';
      item.innerHTML = '<span class="swatch" style="background:'+partyColor(party)+'"></span>'+
        '<span class="n">'+n+'</span><b>'+(PARTY[party]?PARTY[party].short:party)+'</b>';
      legend.appendChild(item);
    }
  }

  function renderYerelBar(){
    const track = $('#seatTrack'); track.innerHTML = '';
    const legend = $('#seatLegend'); legend.innerHTML = '';
    const wins = {};
    for(const p of DATA.iller){ wins[p.kazanan] = (wins[p.kazanan]||0) + 1; }
    const total = DATA.iller.length;
    const order = [...MAJOR];
    // 1950/1955 (contestType=municipal_indirect): belediye baskani halk
    // tarafindan DOGRUDAN secilmiyordu - "belediye başkanlığı" ifadesi
    // modern dogrudan secimlerle ayni sekilde kullanilamaz.
    const isIndirect = DATA.contestType === 'municipal_indirect';
    $('#seatbarTitle').textContent = isIndirect
      ? 'İl Meclisleri — Parti Bazında Çoğunluk Sağlanan İl Sayısı'
      : 'İl Belediyeleri — Parti Bazında Kazanılan İl Sayısı';
    $('#majoritySub').textContent = total+(isIndirect ? ' il meclisi çoğunluğu' : ' il/büyükşehir belediye başkanlığı');
    for(const party of order){
      const n = wins[party] || 0;
      if(n<=0) continue;
      const seg = document.createElement('div');
      seg.className='seatbar-seg';
      seg.style.width = (n/total*100)+'%';
      seg.style.background = partyColor(party);
      seg.title = party+': '+n+' il';
      track.appendChild(seg);
    }
    for(const party of order){
      const n = wins[party] || 0;
      if(n<=0) continue;
      const item = document.createElement('div'); item.className='legend-item';
      item.innerHTML = '<span class="swatch" style="background:'+partyColor(party)+'"></span>'+
        '<span class="n">'+n+'</span><b>'+(PARTY[party]?PARTY[party].short:party)+'</b>';
      legend.appendChild(item);
    }
  }

  function renderYurtdisiCard(){
    const card = $('#yurtdisiCard');
    const yd = DATA.yurtdisi;
    if(!yd || !yd.oy || Object.keys(yd.oy).length===0){ card.style.display='none'; return; }
    card.style.display = '';
    const track = $('#yurtdisiTrack'); track.innerHTML = '';
    const legend = $('#yurtdisiLegend'); legend.innerHTML = '';
    const entries = Object.entries(yd.oy).sort((a,b)=> b[1].oy - a[1].oy);
    $('#yurtdisiSub').textContent = fmt(yd.secmen)+' kayıtlı yurtdışı seçmen · %'+yd.katilim+' katılım'+
      ' · haritaya dahil değildir (il/plaka karşılığı yok)';
    for(const [name, info] of entries){
      const seg = document.createElement('div');
      seg.className='seatbar-seg';
      seg.style.width = info.oran+'%';
      seg.style.background = partyColor(name);
      seg.title = name+': %'+info.oran.toFixed(2);
      track.appendChild(seg);
    }
    for(const [name, info] of entries){
      const item = document.createElement('div'); item.className='legend-item';
      item.innerHTML = '<span class="swatch" style="background:'+partyColor(name)+'"></span>'+
        '<span class="n">%'+info.oran.toFixed(2)+'</span><b>'+(PARTY[name]?PARTY[name].short:name)+'</b>';
      legend.appendChild(item);
    }
  }

