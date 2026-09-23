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
    let html = '<b>'+name+'</b>';
    const isOranTip = DATA.tur === 'referandum' || DATA.tur === 'yerel' || DATA.tur === 'cumhurbaskanligi' || YEARS_NO_VEKIL.has(currentYear);
    if(mode==='winner'){
      const wOy = obj.oy[obj.kazanan];
      const wSeatBased = isSeatBased(wOy);
      const partyLabel = obj.kazanan ? (PARTY[obj.kazanan]?PARTY[obj.kazanan].short:obj.kazanan) : '—';
      const rowLabel = wSeatBased ? ('Meclis çoğunluğu: '+partyLabel) : (partyLabel+' önde');
      const seatInfo = wSeatBased ? (resultPercentLabel(wOy)+' meclis payı'+(wOy.sandalye!=null?' · '+wOy.sandalye+' sandalye':''))
        : isOranTip ? (resultPercentLabel(wOy)+(wOy?' · '+resultQuantity(wOy):''))
        : (info.kind==='il' ? (obj.toplamVekil+' vekil') : ('ilçe kazananı'));
      html += '<div class="row"><span>'+rowLabel+'</span><span>'+seatInfo+'</span></div>';
    } else if(mode==='parti'){
      const key = currentMapParty;
      const o = obj.oy[key];
      html += '<div class="row"><span>'+(PARTY[key]?PARTY[key].short:key)+'</span><span>'+resultPercentLabel(o)+(o?' · '+resultQuantity(o):'')+'</span></div>';
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

