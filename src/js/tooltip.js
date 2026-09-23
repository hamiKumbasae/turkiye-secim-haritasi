  // ---------------- tooltip ----------------
  const tip = $('#tooltip');
  function showTooltip(e, info){
    const mode = currentMapMode;
    let name, obj, sandikVal;
    if(info.kind==='il'){
      obj = ilByPlaka[info.plaka]; if(!obj) return;
      name = obj.ad; sandikVal = obj.sandik;
    } else if(info.kind==='mahalle'){
      obj = info.mahalleId!=null ? pathByMahalleId[info.mahalleId] && currentMahalleRows.find(r=>r.id===info.mahalleId) : null;
      if(!obj){ tip.innerHTML = '<b>Veri eşleşmedi</b>'; positionTip(e); return; }
      name = obj.ad; sandikVal = null;
    } else {
      obj = info.geomId ? districtByGeomId[info.geomId] : null;
      const geoName = null; // no name in geometry; fall back to obj name
      if(!obj){ tip.innerHTML = '<b>Veri eşleşmedi</b>'; positionTip(e); return; }
      name = obj.ad; sandikVal = obj.sandik;
    }
    if(mode==='meclis2024' && info.kind==='ilce'){
      const m = MECLIS_2024[info.geomId];
      let mhtml = '<b>'+name+'</b>';
      if(m){
        mhtml += '<div class="row"><span>'+(PARTY[m.kazanan]?PARTY[m.kazanan].short:m.kazanan)+' çoğunluğu</span><span>'+(m.partiler[m.kazanan]||0)+'/'+m.toplam+' üye</span></div>';
      } else {
        mhtml += '<div class="row"><span>2024 meclis verisi</span><span>—</span></div>';
      }
      tip.innerHTML = mhtml;
      positionTip(e);
      return;
    }
    let html = '<b>'+name+'</b>';
    const isOranTip = DATA.tur === 'referandum' || DATA.tur === 'yerel' || DATA.tur === 'cumhurbaskanligi' || YEARS_NO_VEKIL.has(currentYear);
    if(mode==='winner'){
      const wOy = obj.oy[obj.kazanan];
      const seatInfo = isOranTip ? ('%'+(wOy&&wOy.oran!=null?wOy.oran.toFixed(2):'0.00')+(wOy?' · '+fmt(wOy.oy)+' oy':''))
        : (info.kind==='il' ? (obj.toplamVekil+' vekil') : ('ilçe kazananı'));
      html += '<div class="row"><span>'+ (obj.kazanan? (PARTY[obj.kazanan]?PARTY[obj.kazanan].short:obj.kazanan) : '—') +' önde</span><span>'+seatInfo+'</span></div>';
    } else if(mode==='parti'){
      const key = currentMapParty;
      const o = obj.oy[key];
      html += '<div class="row"><span>'+(PARTY[key]?PARTY[key].short:key)+'</span><span>%'+(o&&o.oran!=null?o.oran.toFixed(2):'0.00')+(o?' · '+fmt(o.oy)+' oy':'')+'</span></div>';
    } else {
      html += '<div class="row"><span>Katılım</span><span>'+(obj.katilim!=null?'%'+obj.katilim.toFixed(2):'—')+'</span></div>';
    }
    if(sandikVal!=null) html += '<div class="row"><span>Sandık</span><span>'+fmt(sandikVal)+'</span></div>';
    tip.innerHTML = html;
    positionTip(e);
  }
  function positionTip(e){
    tip.style.left = e.clientX+'px';
    tip.style.top = (e.clientY-10)+'px';
    tip.style.opacity = 1;
  }
  function hideTooltip(){ tip.style.opacity=0; }

