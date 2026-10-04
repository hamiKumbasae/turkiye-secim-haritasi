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
    if(!obj.kazanan && obj.not){ tip.innerHTML = html + '<div class="row tip-not"><span>' + obj.not + '</span></div>'; positionTip(e); return; }
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
    } else if(mode==='degisim'){
      const key = currentMapParty;
      const o = oncekiKarsiligi(obj), v = degisimDegeri(obj, key);
      html += '<div class="row"><span>'+escapeHtml(PARTY[key]?PARTY[key].short:key)+'</span><span>'+resultPercentLabel(obj.oy[key])+'</span></div>';
      if(ONCEKI) html += '<div class="row"><span>'+escapeHtml(TUR_LABELS[currentTur][ONCEKI.year])+'</span><span>'+(o && o.oy ? resultPercentLabel(o.oy[key]) : '—')+'</span></div>';
      html += '<div class="row"><span>Değişim</span><span>'+(v==null ? 'karşılaştırılamıyor' : puan(v))+'</span></div>';
    } else {
      html += '<div class="row"><span>Katılım</span><span>'+(obj.katilim!=null?'%'+obj.katilim.toFixed(2):'—')+'</span></div>';
    }
    if(sandikVal!=null) html += '<div class="row"><span>Sandık</span><span>'+fmt(sandikVal)+'</span></div>';
    if(DATA.tur==='yerel' && DATA.contestType!=='municipal_indirect'){
      const alt = DATA.oylama==='igm' ? (info.kind==='il' ? 'İl genel meclisi · il toplamı' : 'İl genel meclisi · ilçenin tamamı')
        : DATA.oylama==='bm' ? (info.kind==='il' ? 'Belediye meclisleri · ildeki tüm belediyeler' : 'İlçe belediyesi meclisi')
        : (info.kind==='il' ? 'İl merkezi belediye başkanlığı (büyükşehirde büyükşehir)' : null);
      if(alt && info.kind!=='mahalle') html += '<div class="row tip-not"><span>' + alt + '</span></div>';
    }
    if(info.kind==='ilce' && obj.ilceGeneliSonuc && !DATA.oylama) html += '<div class="row tip-not"><span>Sonuç: ' + obj.ilceGeneliSonuc + ' (ilçe belediyesi satırı doğrulanamadı)</span></div>';
    if(info.kind==='ilce' && obj.ilMerkeziBelediyesi) html += '<div class="row tip-not"><span>' + (obj.buyuksehirSonucu ? 'Büyükşehir' : 'İl merkezi') + ' belediye başkanlığı sonucu</span></div>';
    if(info.kind==='ilce') html += birlesimNotuHtml(info.geomId);
    tip.innerHTML = html;
    positionTip(e);
  }
  // Tarihsel birlesim poligonu (bu secimde ilce bugunku birden cok ilcenin alanini kapsiyordu):
  // geo/historical/idari/harita_notlari.json -> birlesimler
  function birlesimNotuHtml(geomId){
    const b = ((HARITA_NOTLARI && HARITA_NOTLARI.birlesimler) || {})[geomId];
    if(!b) return '';
    // paylar: mahalle duzeyinde bolunen bugunku ilcenin bu poligona dusen alan payi (ornek 'Ataşehir %60')
    const ad = x => (b.paylar && b.paylar[x] != null) ? x + ' (%' + Math.round(b.paylar[x] * 100) + ')' : x;
    let h = '<div class="row tip-not"><span>Bugünkü sınırlarla: ' + b.ilceler.map(ad).join(', ') + '</span></div>';
    for(const c of (b.cogunluk || [])){
      // kisa, eksiz: 'Konyaaltı: %92 Merkez, Kemer 1 birim'
      const d = (c.digerleri || []).map(x => x[0] + ' ' + x[1] + ' birim').join(', ');
      if(d) h += '<div class="row tip-not"><span>' + c.ad + ': %' + Math.round(c.pay * 100) + ' ' + c.ana + ', ' + d + '</span></div>';
    }
    return h;
  }
  function positionTip(e){
    // kutu imlecin ustunde ortalanir (translate -50%,-100%); dar ekranda kenardan tasmasin
    const w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(Math.max(e.clientX, w/2 + 8), innerWidth - w/2 - 8)+'px';
    tip.style.top = Math.max(e.clientY - 10, h + 8)+'px';
    tip.style.opacity = 1;
  }
  function hideTooltip(){ tip.style.opacity=0; }

